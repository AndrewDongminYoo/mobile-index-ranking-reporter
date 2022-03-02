import sys

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


def get_one_store_app_download_count(date: TimeIndex, app: App):
    try:
        soup = get_soup(app.market_appid, True)
        d_counts = soup.select_one("li:-soup-contains('다운로드수') > span").text
        d_string = soup.select_one("li:-soup-contains('출시일') > span").text
        genre = soup.select_one("li:-soup-contains('장르') > span").text
        volume = soup.select_one("li:-soup-contains('용량') > span").text
        style = soup.select_one("#header > div > div > div.header-co-right > span").get('style')
        icon_url = style.replace("background-image:url(", "").replace(")", "")

        soup2 = get_soup(app.market_appid, False)
        app_name = soup2.title.get_text().replace(" - 원스토어", "")
        logger.debug(app_name)

        import datetime
        array = [i for i in map(int, d_string.split("."))]
        released = datetime.date(year=array[0], month=array[1], day=array[2])
        download = int(d_counts.replace(",", ""))

        ones_app = OneStoreDL(
            date=date,
            app=app,
            market_appid=app.market_appid,
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
    app = App.objects.get_or_create(
            app_name=app_data.get("app_name"),
            icon_url=app_data.get('icon_url'),
            market_appid=app_data.get("market_appid") or app_data.get("package_name")
        )[0]
    app.save()
    return app


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
                market_appid=_app.market_appid,
                market=app_data.get("market_name"),  # "google", "apple", "one"
                chart_type=app_data.get('rank_type'),
                deal_type=term.replace("_v2", "").replace("global", "market"),  # "realtime_rank", "market_rank"
            )
            item.save()


def get_history(app: Ranked):
    url = 'https://proxy-insight.mobileindex.com/chart/market_rank_history'  # "realtime_rank_v2", "global_rank_v2"
    data = {
        'appId': app.market_appid,
        'market': app.market,
        'appType': app.app_type,
        'startDate': (timezone.now()-timedelta(days=3)).strftime("%Y%m%d%H%M"),
        'endDate': timezone.now().strftime("%Y%m%d%H%M"),
    }
    req = requests.post(url, data=data, headers=headers)
    response = req.json()
    if response["status"]:
        _date = TimeIndex.objects.get_or_create(date=timezone.now().strftime("%Y%m%d%H%M"))[0]
        print(_date)
    return response["data"]


def tracking_rank_flushing():
    following = [f[0] for f in Following.objects.values_list("market_appid")]
    yesterday = timezone.now() - timedelta(days=3)
    for ranked_ in Ranked.objects.filter(created_at__gte=yesterday, market_appid__in=following):
        f_app = Following.objects.filter(market_appid=ranked_.market_appid).first()
        tracking = TrackingApps.objects.update_or_create(
            following=f_app,
            app=ranked_.app,
            deal_type=ranked_.deal_type,
            market=ranked_.market,
            chart_type=ranked_.chart_type,
            app_name=ranked_.app_name,
            icon_url=ranked_.app.icon_url,
            market_appid=ranked_.app.market_appid,
            rank=ranked_.rank,
            date_id=ranked_.date_id,
        )
        if len(tracking):
            tracking[0].save()


def following_one_crawl():
    date = TimeIndex.objects.get_or_create(date=timezone.now().strftime("%Y%m%d%H%M"))[0]
    logger.debug(date)
    for obj in Following.objects.filter(is_active=True).all():
        app = App.objects.filter(market_appid=obj.market_appid).first()
        get_one_store_app_download_count(date, app)


def hourly():
    for deal in ["realtime_rank_v2"]:
        for market in ["all"]:
            for price in ["free"]:
                for game in ["app", "game"]:
                    crawl_app_store_rank(deal, market, price, game)
    following_one_crawl()
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
    daily()
    hourly()
    # following_one_crawl()

