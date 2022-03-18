# -*- coding: utf-8 -*-
import os
import sys
import datetime
import json
from datetime import timedelta
from slacker import Slacker

sys.path.append('/home/ubuntu/app-rank/ranker')
os.environ.setdefault("PYTHONUNBUFFERED;", "1")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ranker.settings")
import django

from ranker import settings
if 'setup' in dir(django):
    django.setup()
import requests
from bs4 import BeautifulSoup
from django.utils import timezone
from logging import getLogger
from django.db.models import Min, Q
from crawler.models import Ranked, Following, TrackingApps, App, TimeIndex, OneStoreDL

logger = getLogger(__name__)
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.80 Safari/537.36"
headers = {'origin': 'https://www.mobileindex.com', 'user-agent': user_agent}


def post_to_slack(text=None):
    try:
        url = settings.SLACK_WEBHOOK_URL
        body = json.dumps({"text": text})
        req = requests.post(url, headers={'Content-type': 'application/json'}, data=body)
        import time
        time.sleep(0.5)
        print(req.json())
        print(req.status_code)
        print(req.text)
        logger.debug(req.headers)
    except Exception as e:
        logger.error(e)


def get_soup(market_id, back=True):
    one_url = "https://m.onestore.co.kr/mobilepoc/"
    if back is True:
        one_url += f"web/apps/appsDetail/spec.omp?prodId={market_id}"
    else:
        one_url += f"apps/appsDetail.omp?prodId={market_id}"
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

        array = [i for i in map(int, d_string.split("."))]
        released = datetime.date(year=array[0], month=array[1], day=array[2])
        download = int(d_counts.replace(",", ""))
        last_one = OneStoreDL.objects.filter(
            app=app,
            market_appid=app.market_appid,
        )
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
        rank_diff = ones_app.downloads - last_one.last().downloads if last_one.exists() else 0
        if rank_diff > 2000 and last_one.exists():
            post_to_slack(f"""{app_name} 앱 다운로드가 전일 대비 {format(rank_diff, ',')}건 증가했습니다.✈\n 
            {format(last_one.last().downloads, ',')}건 -> {format(ones_app.downloads, ',')}건.""")
        return ones_app
    except AttributeError:
        print("AttributeError")


def create_app(app_data: dict):
    app = App.objects.get_or_create(
        market_appid=app_data['market_appid'],
    )[0]
    app.app_name = app_data.get('app_name')
    app.icon_url = app_data.get('icon_url')
    if app.app_info:
        app.app_info.publisher_name = app_data.get('publisher_name')
    if app.market_appid.startswith("0000"):
        app.market = "one"
        app.app_url = "https://m.onestore.co.kr/mobilepoc/apps/appsDetail.omp?prodId=" + app.market_appid
    elif app.market_appid[0].isalpha():
        app.market = "google"
        app.app_url = "https://play.google.com/store/apps/details?id=" + app.market_appid
    else:
        app.market = "apple"
        app.app_url = "https://apps.apple.com/kr/app/id" + app.market_appid
    app.save()
    print(app.market_appid, app.app_name)
    return app


def crawl_app_store_rank(term: str, market: str, game_or_app: str):
    post_to_slack("크롤링 시작")
    url = f'https://proxy-insight.mobileindex.com/chart/{term}'  # "realtime_rank_v2", "global_rank_v2"
    data = {
        "market": "all",  # "all", "google"
        "country": "kr",
        "rankType": "free",  # "gross", "paid", "free"
        "appType": game_or_app,  # "game", "app"
        "date": "",
        "startRank": 0,
        "endRank": 100,
    }
    if market == "one":
        data["date"] = timezone.now().strftime("%Y%m%d")
    response = requests.post(url, data=data, headers=headers).json()
    if response["status"]:
        date = TimeIndex.objects.get_or_create(date=timezone.now().strftime("%Y%m%d%H%M"))[0]
        following = [f[0] for f in Following.objects.values_list("market_appid")]
        logger.debug(following)
        for app_data in response["data"]:
            logger.debug(app_data)
            app = create_app(app_data)
            market_name = app_data.get("market_name")
            if market == "one" and market_name in ["apple", "google"]:
                pass
            else:
                item = Ranked(
                    app=app, date=date,
                    app_type=game_or_app,  # "game", "app"
                    app_name=app.app_name,
                    icon_url=app.icon_url,
                    market_appid=app.market_appid,
                    rank=app_data.get('rank'),
                    market=market_name,  # "google", "apple", "one"
                    chart_type=app_data.get('rank_type'),
                    deal_type=term.replace("_v2", "").replace("global", "market"),  # "realtime_rank", "market_rank"
                )
                item.save()
                print(item.app_name)
                logger.info(item.app_name)
                if app.market_appid in following:
                    last_one = TrackingApps.objects.filter(
                        market_appid=item.market_appid,
                        deal_type=item.deal_type,
                        market=item.market,
                        chart_type=item.chart_type,
                        app_name=item.app_name,
                    )
                    tracking = TrackingApps(
                        following=Following.objects.filter(market_appid=app.market_appid).first(),
                        app=app, date=date,
                        deal_type=item.deal_type,
                        rank=item.rank,
                        market=item.market,
                        app_name=item.app_name,
                        icon_url=app.icon_url,
                        chart_type=item.chart_type,
                        market_appid=app.market_appid,
                    )
                    tracking.save()
                    rank_diff = (tracking.rank - last_one.last().rank) if last_one.exists() else 0
                    market_string = item.get_market_display()
                    if last_one.exists() and rank_diff < -2:
                        print(
                            f"순위 상승: {item.app_name} {market_string} {last_one.last().rank}위 -> {item.rank}위")
                        post_to_slack(
                            f"순위 상승: {item.app_name} {market_string} {last_one.last().rank}위 -> {item.rank}위")
                    if last_one.exists() and rank_diff > 2:
                        print(
                            f"순위 하락: {item.app_name} {market_string} {last_one.last().rank}위 -> {item.rank}위")
                        post_to_slack(
                            f"순위 하락: {item.app_name} {market_string} {last_one.last().rank}위 -> {item.rank}위")


def following_one_crawl():
    date = TimeIndex.objects.get_or_create(date=timezone.now().strftime("%Y%m%d%H%M"))[0]
    logger.debug(date)
    for obj in Following.objects.filter(is_active=True, market="one").all():
        app = App.objects.filter(market_appid=obj.market_appid).first()
        get_one_store_app_download_count(date, app)


def get_highest_rank_of_realtime_ranks_today():
    pres = timezone.now().strftime("%Y%m%d") + "0000"
    last = (timezone.now() - timedelta(days=1)).strftime("%Y%m%d") + "0000"
    today = TimeIndex.objects.get_or_create(date=pres)[0]
    yesterday = TimeIndex.objects.get_or_create(date=last)[0]
    rank_set = Ranked.objects \
        .filter(date__id__gte=yesterday.id, date__id__lte=today.id) \
        .filter(Q(market="apple") | Q(market="google"))
    apps = set([r.market_appid for r in rank_set])
    for market_appid in apps:
        app = rank_set.filter(market_appid=market_appid) \
            .values('market_appid', 'app_name', 'market', 'app_type', 'chart_type', 'icon_url') \
            .annotate(highest_rank=Min('rank')).first()
        new_app = Ranked(
            market=app.get('market'),
            rank=app.get('highest_rank'),
            deal_type='market_rank',
            app_type=app.get('app_type'),
            chart_type=app.get('chart_type'),
            app_name=app.get('app_name'),
            market_appid=market_appid,
            app=App.objects.get(market_appid=market_appid),
            date=today
        )
        new_app.save()


def every_o_clock_hourly():
    crawl_app_store_rank("realtime_rank_v2", "all", "game")
    crawl_app_store_rank("realtime_rank_v2", "all", "app")


def good_afternoon_twelve_ten_daily():
    crawl_app_store_rank("global_rank_v2", "one", "game")
    crawl_app_store_rank("global_rank_v2", "one", "app")
    following_one_crawl()


def good_deep_night_twelve_ten_daily():
    following_one_crawl()
    get_highest_rank_of_realtime_ranks_today()


if __name__ == '__main__':
    post_to_slack("크롤러 알람 파업 상태")
