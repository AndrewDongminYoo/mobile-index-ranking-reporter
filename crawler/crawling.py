# -*- coding: utf-8 -*-
import os
import sys
import datetime
from datetime import timedelta
sys.path.append('/home/ubuntu/app-rank')
os.environ.setdefault("PYTHON" + "UNBUFFERED", "1")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ranker.settings")
import django

if 'setup' in dir(django):
    django.setup()
import requests
from django.utils import timezone
from backports.zoneinfo import ZoneInfo
from logging import getLogger
from django.db.models import Min
from crawler.utils import post_to_slack, get_soup, get_date, create_app
from crawler.models import Ranked, Following, TrackingApps, App, OneStoreDL

logger = getLogger(__name__)
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " \
             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.80 Safari/537.36 "
headers = {'origin': 'https://www.mobileindex.com', 'user-agent': user_agent}


def get_one_store_information(market_appid):
    date_id = get_date(timezone.now().strftime("%Y%m%d%H%M"))
    app = App.objects.get(market_appid=market_appid)
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

        array = [i for i in map(int, d_string.split("."))]
        released = datetime.date(year=array[0], month=array[1], day=array[2])
        download = int(d_counts.replace(",", ""))
        last_one = OneStoreDL.objects.filter(
            app_id=app["id"],
            market_appid=app.market_appid,
        ).last()
        ones_app = OneStoreDL(
            date_id=date_id,
            app_id=app["id"],
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
            msg = f"{app_name} 앱 다운로드가 전일 대비 {format(rank_diff, ',')}건 증가했습니다.✈ " \
                  + f"`{format(last_one.downloads, ',')}건` -> `{format(ones_app.downloads, ',')}건`"
            post_to_slack(msg)
        return ones_app
    except AttributeError:
        print("AttributeError")


def crawl_app_store_rank(term: str, market: str, game_or_app: str):
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
        date_id = get_date(timezone.now().strftime("%Y%m%d%H%M"))
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
                    app_id=app["id"],
                    date_id=date_id,
                    app_type=game_or_app,  # "game", "app"
                    app_name=app["app_name"],
                    icon_url=app["icon_url"],
                    market_appid=app["market_appid"],
                    rank=app_data.get('rank'),
                    market=market_name,  # "google", "apple", "one"
                    chart_type=app_data.get('rank_type'),
                    deal_type=term.replace("_v2", "").replace("global", "market"),  # "realtime_rank", "market_rank"
                )
                item.save()
                print(item.app_name)
                logger.info(item.app_name)
                if item.market_appid in following:
                    last_one = TrackingApps.objects.filter(
                        market_appid=item.market_appid,
                        market=item.market,
                        chart_type=item.chart_type,
                        app_name=item.app_name,
                    ).last()
                    tracking = TrackingApps(
                        following=Following.objects.filter(market_appid=item.market_appid).first(),
                        app_id=app["id"],
                        date_id=date_id,
                        deal_type=item.deal_type,
                        rank=item.rank,
                        market=item.market,
                        app_name=item.app_name,
                        icon_url=item.icon_url,
                        chart_type=item.chart_type,
                        market_appid=app["market_appid"],
                    )
                    tracking.save()
                    rank_diff = tracking.rank - last_one.rank if last_one else 0
                    market_string = item.get_market_display()
                    if rank_diff <= -1:
                        print(f"순위 상승🚀: {item.app_name} {market_string} `{last_one.rank}위` → `{item.rank}위`")
                        logger.debug(f"순위 상승🚀: {item.app_name} {market_string} `{last_one.rank}위` → `{item.rank}위`")
                        post_to_slack(f" 순위 상승🚀: {item.app_name} {market_string} `{last_one.rank}위` → `{item.rank}위`")
                    if rank_diff >= 1:
                        print(f"순위 하락🛬: {item.app_name} {market_string} `{last_one.rank}위` → `{item.rank}위`")
                        logger.debug(f"순위 하락🛬: {item.app_name} {market_string} `{last_one.rank}위` → `{item.rank}위`")
                        post_to_slack(f" 순위 하락🛬: {item.app_name} {market_string} `{last_one.rank}위` → `{item.rank}위`")


def get_highest_rank_of_realtime_ranks_today():
    date_today = get_date(timezone.localdate(timezone=ZoneInfo(key='Asia/Seoul')).strftime("%Y%m%d") + "2300")
    rank_set = Ranked.objects \
        .filter(created_at__gte=timezone.now() - timedelta(days=1),
                created_at__lte=timezone.now(),
                market__in=["apple", "google"],
                deal_type="realtime_rank")
    for following in Following.objects.filter(is_active=True, market__in=["apple", "google"]).all():
        try:
            market_appid = following.market_appid
            query = rank_set.filter(market_appid=market_appid) \
                .values('market_appid', 'app_name', 'market', 'app_type', 'chart_type', 'icon_url') \
                .annotate(highest_rank=Min('rank'))
            if query:
                first = query[0]
                new_app = TrackingApps.objects.update_or_create(
                    market=first.get('market'),
                    chart_type=first.get('chart_type'),
                    app_name=first.get('app_name'),
                    icon_url=first.get('icon_url'),
                    deal_type='market_rank',
                    market_appid=market_appid,
                    app=App.objects.get(market_appid=market_appid),
                    following=following,
                    date=date_today,
                )[0]
                new_app.rank = first.get('highest_rank')
                new_app.save()
        except Exception as e:
            logger.debug(e)
            print(e)


def every_o_clock_hourly():
    crawl_app_store_rank("realtime_rank_v2", "all", "game")
    crawl_app_store_rank("realtime_rank_v2", "all", "app")
    get_highest_rank_of_realtime_ranks_today()


def good_afternoon_twelve_ten_daily():
    crawl_app_store_rank("global_rank_v2", "one", "game")
    crawl_app_store_rank("global_rank_v2", "one", "app")


if __name__ == '__main__':
    good_afternoon_twelve_ten_daily()
    every_o_clock_hourly()
