import sys
from datetime import timedelta

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
    logger.debug(req.headers)


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
        last_one = OneStoreDL.objects.filter(
            app=app,
            market_appid=app.market_appid,
        ).last()
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
        rank_diff = ones_app.downloads - last_one.downloads if last_one else 0
        if rank_diff > 2000:
            post_to_slack(
                f"""{app_name} 앱 다운로드가 전일 대비 {format(rank_diff, ',')}건 증가했습니다.✈ 
                {format(last_one.downloads, ',')}건 -> {format(ones_app.downloads, ',')}건.""")
        return ones_app
    except AttributeError:
        print("AttributeError")


def create_app(app_data: dict):
    app = App.objects.filter(market_appid=app_data.get("market_appid"))
    if app.exists():
        app = app.first()
        app.app_name = app_data.get("app_name")
        app.icon_url = app_data.get('icon_url')
        app.save()
    else:
        app = App(
            app_name=app_data.get("app_name"),
            market_appid=app_data.get("market_appid"),
            icon_url=app_data.get('icon_url'),
            publisher_name=app_data.get("publisher_name"),
        )
        app.save()
    if app.market_appid.startswith("0000"):
        app.market = "one"
    elif app.market_appid[0].isalpha():
        app.market = "google"
    else:
        app.market = "apple"
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
        following = [f[0] for f in Following.objects.values_list("market_appid")]
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
            if _app.market_appid in following:
                last_one = TrackingApps.objects.filter(
                    market_appid=item.market_appid,
                    deal_type=item.deal_type,
                    market=item.market,
                    chart_type=item.chart_type,
                    app_name=item.app_name,
                ).last()
                tracking = TrackingApps(
                    following=Following.objects.get(market_appid=_app.market_appid),
                    app=_app,
                    date=item.date,
                    deal_type=item.deal_type,
                    market=item.market,
                    chart_type=item.chart_type,
                    app_name=item.app_name,
                    icon_url=item.app.icon_url,
                    market_appid=item.app.market_appid,
                    rank=item.rank,
                )
                tracking.save()
                rank_diff = item.rank - last_one.rank if last_one else 0
                if rank_diff < -2:
                    post_to_slack(
                        f"순위 상승: {item.app_name} 🚀 {item.get_market_display()} {last_one.rank}위 -> {item.rank}위")
                if rank_diff > 2:
                    post_to_slack(
                        f"순위 하락: {item.app_name} 🚑 {item.get_market_display()} {last_one.rank}위 -> {item.rank}위")


def following_one_crawl():
    date = TimeIndex.objects.get_or_create(date=timezone.now().strftime("%Y%m%d%H%M"))[0]
    logger.debug(date)
    for obj in Following.objects.filter(is_active=True, market="one").all():
        app = App.objects.filter(market_appid=obj.market_appid).first()
        get_one_store_app_download_count(date, app)


def hourly():
    for deal in ["realtime_rank_v2"]:
        for market in ["all"]:
            for price in ["free"]:
                for game in ["app", "game"]:
                    crawl_app_store_rank(deal, market, price, game)


def daily():
    for deal in ["global_rank_v2"]:
        for market in ["all"]:
            for price in ["free"]:
                for game in ["app", "game"]:
                    crawl_app_store_rank(deal, market, price, game)
    following_one_crawl()


if __name__ == '__main__':
    hourly()
    # following_one_crawl()
