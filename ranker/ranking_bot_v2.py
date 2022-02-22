import sys
sys.path.append('home/ubuntu/app-rank/ranker/settings.py')
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ranker.settings")
import django
if 'setup' in dir(django):
    django.setup()
import requests
from django.utils import timezone
from django.db import IntegrityError
from datetime import timedelta
from crawler.models import Ranked, Following, TrackingApps, App, TimeIndex, OneStoreDL

user_agent = " ".join(
    ["Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
     "AppleWebKit/537.36 (KHTML, like Gecko)",
     "Chrome/98.0.4758.80 Safari/537.36"])
headers = {'origin': 'https://www.mobileindex.com',
           'user-agent': user_agent}


def post_to_slack(text=None):
    import requests
    import json
    url = 'https://hooks.slack.com/services/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'
    _headers = {'Content-type': 'application/json'}
    body = json.dumps({"text": text})
    req = requests.post(url, headers=_headers, data=body)
    print(req.status_code)


def get_soup(appid, back=True):
    one_url = "https://m.onestore.co.kr/mobilepoc/web/apps/appsDetail/spec.omp?prodId=" + appid \
        if back else "https://m.onestore.co.kr/mobilepoc/apps/appsDetail.omp?prodId=" + appid
    from bs4 import BeautifulSoup
    response = requests.get(one_url)
    if response.status_code == 200:
        return BeautifulSoup(response.text, "html.parser")


def get_one_store_app_download_count(date: TimeIndex, appid: str, app: App):
    try:
        soup = get_soup(appid, True)
        download = soup.select_one("li:-soup-contains('다운로드수') > span").text
        d_string = soup.select_one("li:-soup-contains('출시일') > span").text
        genre = soup.select_one("li:-soup-contains('장르') > span").text
        volume = soup.select_one("li:-soup-contains('용량') > span").text
        style = soup.select_one("#header > div > div > div.header-co-right > span").get('style')
        icon_url = style.removeprefix("background-image:url(").removesuffix(")")

        soup2 = get_soup(appid, False)
        app_name = soup2.title.get_text().removesuffix(" - 원스토어")
        print(app_name)

        import datetime
        array = [i for i in map(int, d_string.split("."))]
        released = datetime.date(year=array[0], month=array[1], day=array[2])
        d_counts = int(download.replace(",", ""))

        ones_app = OneStoreDL(
            date_id=date.id,
            app_id=app.id,
            market_appid=appid,
            downloads=d_counts,
            genre=genre,
            volume=volume,
            released=released,
            icon_url=icon_url,
            app_name=app_name,
        )
        ones_app.save()
    except AttributeError:
        pass


def crawl_app_store_rank(deal: str, market: str, price: str, game: str):
    """
    param deal: "realtime_rank_v2", "global_rank_v2"
    param market: "all", "google"(global)
    param price: "gross", "paid", "free"
    param game: "app", "game"
    return: Ranked
    """
    url = f'https://proxy-insight.mobileindex.com/chart/{deal}'  # "realtime_rank_v2", "global_rank_v2"
    data = {
        "market": market,  # "all", "google"
        "country": "kr",
        "rankType": price,  # "gross", "paid", "free"
        "appType": game,  # "game", "app"
        "date": timezone.now().strftime("%Y%m%d"),
        "startRank": 1,
        "endRank": 100,
    }

    req = requests.post(url, data=data, headers=headers)
    obj = req.json()
    if obj["status"]:
        print(obj.items())
        date = TimeIndex.objects.get_or_create(date=timezone.now().strftime("%Y%m%d%H%M"))[0]
        for app_data in obj["data"]:
            try:
                query = App.objects.filter(app_name__icontains=app_data.get("app_name"))
                package_name = app_data.get("market_appid")
                if query.exists():
                    app = query.first()
                    if package_name:
                        app.package_name = package_name
                        app.save()
                else:
                    app = App(
                        app_name=app_data.get("app_name"),
                        package_name=package_name or "com.example.app",
                        icon_url=app_data.get('icon_url'),
                    )
                    app.save()

                item = Ranked(
                    app_id=app.id,
                    app_name=app.app_name,
                    icon_url=app.icon_url,
                    date_id=date.id,
                    package_name=app.package_name,
                    market_appid=app_data.get('market_appid'),
                    market=app_data.get("market_name"),  # "google", "apple", "one"
                    deal_type=deal.removesuffix("_v2").replace("global", "market"),  # "realtime_rank", "market_rank"
                    app_type=game,  # "game", "app"
                    rank=app_data.get('rank'),
                    rank_type=app_data.get('rank_type'),
                )
                item.save()

            except IntegrityError:
                pass
            except AttributeError:
                pass


def tracking_rank_flushing():
    following_applications = [f[0] for f in Following.objects.values_list("app_name")]
    yesterday = timezone.now() - timedelta(days=3)
    for item in Ranked.objects.filter(created_at__gte=yesterday, app_name__in=following_applications):
        app_name = item.app_name
        date_id = item.date_id
        if TrackingApps.objects.filter(app_name=app_name, date_id=date_id).exists():
            pass
        else:
            print(app_name)
            tracking = TrackingApps(
                app=item.app,
                deal_type=item.deal_type,
                market=item.market,
                rank_type=item.rank_type,
                app_name=app_name,
                icon_url=item.app.icon_url,
                package_name=item.app.package_name,
                rank=item.rank,
                date_id=date_id,
            )
            tracking.save()
    weekdays = timezone.now() - timedelta(days=7)
    for old in TrackingApps.objects.filter(created_at__lt=weekdays):
        old.delete()


def following_crawl():
    date = TimeIndex.objects.get_or_create(date=timezone.now().strftime("%Y%m%d%H%M"))[0]
    print(date)
    for obj in Following.objects.filter(is_active=True).all():
        appid = obj.app_id
        app = App.objects.filter(pk=appid).first()
        get_one_store_app_download_count(date, app.package_name, app)


def hourly():
    for deal in ["realtime_rank_v2"]:
        for market in ["all"]:
            for price in ["paid", "free"]:
                for game in ["app", "game"]:
                    crawl_app_store_rank(deal, market, price, game)
    following_crawl()


def daily():
    post_to_slack("일간 크롤링 시작")
    for deal in ["global_rank_v2"]:
        for market in ["all"]:
            for price in ["gross", "paid", "free"]:
                for game in ["app", "game"]:
                    crawl_app_store_rank(deal, market, price, game)
    tracking_rank_flushing()


if __name__ == '__main__':
    # daily()
    # hourly()
    following_crawl()
