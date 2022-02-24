import sys

from django.db.models import Q

sys.path.append('/home/ubuntu/app-rank/ranker')
import os

os.environ.setdefault("PYTHONUNBUFFERED;", "1")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ranker.settings")
import django

if 'setup' in dir(django):
    django.setup()

import requests
from django.utils import timezone
from logging import getLogger
from datetime import timedelta
from crawler.models import Ranked, Following, TrackingApps, App, TimeIndex, OneStoreDL

logger = getLogger(__name__)
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.80 Safari/537.36"
headers = {'origin': 'https://www.mobileindex.com', 'user-agent': user_agent}


def post_to_slack(text=None):
    import requests
    import json
    url = 'https://hooks.slack.com/services/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'
    _headers = {'Content-type': 'application/json'}
    body = json.dumps({"text": text})
    req = requests.post(url, headers=_headers, data=body)
    logger.debug(req.status_code)


def get_soup(market_id, back=True):
    one_url = "https://m.onestore.co.kr/mobilepoc/"
    if back:
        one_url += f"web/apps/appsDetail/spec.omp?prodId={market_id}"
    else:
        one_url += f"apps/appsDetail.omp?prodId={market_id}"
    from bs4 import BeautifulSoup
    response = requests.get(one_url)
    if response.status_code == 200:
        return BeautifulSoup(response.text, "html.parser")


def get_one_store_app_download_count(date: TimeIndex, market_id: str, app: App):
    try:
        soup = get_soup(market_id, True)
        d_counts = soup.select_one("li:-soup-contains('다운로드수') > span").text
        d_string = soup.select_one("li:-soup-contains('출시일') > span").text
        genre = soup.select_one("li:-soup-contains('장르') > span").text
        volume = soup.select_one("li:-soup-contains('용량') > span").text
        style = soup.select_one("#header > div > div > div.header-co-right > span").get('style')
        icon_url = style.replace("background-image:url(", "").replace(")", "")

        soup2 = get_soup(market_id, False)
        app_name = soup2.title.get_text().replace(" - 원스토어", "")
        logger.debug(app_name)

        import datetime
        array = [i for i in map(int, d_string.split("."))]
        released = datetime.date(year=array[0], month=array[1], day=array[2])
        download = int(d_counts.replace(",", ""))

        ones_app = OneStoreDL(
            date_id=date.id,
            app_id=app.id,
            market_appid=market_id,
            downloads=download,
            genre=genre,
            volume=volume,
            released=released,
            icon_url=icon_url,
            app_name=app_name,
        )
        ones_app.save()
        return ones_app
    except AttributeError:
        pass


def create_app(app_data: dict):
    app = App.objects.filter(Q(app_name=app_data.get("app_name"))
                             | Q(icon_url=app_data.get('icon_url'))
                             | Q(market_appid=app_data.get("market_appid")))
    if not app.exists():
        app = App(
            app_name=app_data.get("app_name"),
            icon_url=app_data.get('icon_url'),
            market_appid=app_data.get("market_appid")
        )
        app.package_name = app_data.get("package_name")
        app.save()
        print(app)
        return app
    print(app)
    return app.first()


def crawl_app_store_rank(term: str, market: str, price: str, game_or_app: str):
    """
    param deal: "realtime_rank_v2", "global_rank_v2"
    param market: "all", "google"(global)
    param price: "gross", "paid", "free"
    param game: "app", "game"
    return: Ranked
    """
    url = f'https://proxy-insight.mobileindex.com/chart/{term}'  # "realtime_rank_v2", "global_rank_v2"
    data = {
        "market": market,  # "all", "google"
        "country": "kr",
        "rankType": price,  # "gross", "paid", "free"
        "appType": game_or_app,  # "game", "app"
        "date": timezone.now().strftime("%Y%m%d"),
        "startRank": 1,
        "endRank": 100,
    }
    req = requests.post(url, data=data, headers=headers)
    response = req.json()
    if response["status"]:
        _date = TimeIndex.objects.get_or_create(date=timezone.now().strftime("%Y%m%d%H%M"))[0]
        print(_date)
        for app_data in response["data"]:
            logger.debug(app_data)
            _app = create_app(app_data)

            item = Ranked(
                app_id=_app.id,
                date_id=_date.id,
                app_type=game_or_app,  # "game", "app"
                app_name=_app.app_name,
                icon_url=_app.icon_url,
                rank=app_data.get('rank'),
                package_name=_app.package_name,
                market_appid=_app.market_appid,
                market=app_data.get("market_name"),  # "google", "apple", "one"
                chart_type=app_data.get('rank_type'),
                deal_type=term.replace("_v2", "").replace("global", "market"),  # "realtime_rank", "market_rank"
            )
            item.save()


def tracking_rank_flushing():
    following = [f[0] for f in Following.objects.values_list("package_name")]
    yesterday = timezone.now() - timedelta(days=3)
    for item in Ranked.objects.filter(created_at__gte=yesterday, app_name__in=following):
        tracking = TrackingApps.objects.get_or_create(
            app=item.app,
            deal_type=item.deal_type,
            market=item.market,
            chart_type=item.chart_type,
            app_name=item.app_name,
            icon_url=item.app.icon_url,
            package_name=item.app.package_name,
            rank=item.rank,
            date_id=item.date_id,
        )
        tracking[0].save()
    weekdays = timezone.now() - timedelta(days=7)
    for old in TrackingApps.objects.filter(created_at__lt=weekdays):
        old.delete()


def following_crawl():
    date = TimeIndex.objects.get_or_create(date=timezone.now().strftime("%Y%m%d%H%M"))[0]
    logger.debug(date)
    for obj in Following.objects.filter(is_active=True).all():
        appid = obj.app_id
        app = App.objects.filter(pk=appid).first()
        get_one_store_app_download_count(date, app.package_name, app)


def hourly():
    for deal in ["realtime_rank_v2"]:
        for market in ["all"]:
            for price in ["free"]:
                for game in ["app", "game"]:
                    crawl_app_store_rank(deal, market, price, game)
    following_crawl()
    tracking_rank_flushing()
    post_to_slack("정기 크롤링 완료")


def daily():
    for deal in ["global_rank_v2"]:
        for market in ["all"]:
            for price in ["gross", "paid", "free"]:
                for game in ["app", "game"]:
                    crawl_app_store_rank(deal, market, price, game)
    post_to_slack("일간 크롤링 완료")


if __name__ == '__main__':
    # daily()
    hourly()

