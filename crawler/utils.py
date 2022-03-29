from crawler.models import Ranked, TrackingApps, Following, App
from datetime import datetime, timedelta, date
from django.db.models import Min
from bs4 import BeautifulSoup
from pytz import timezone
from typing import Tuple
import requests

KST = timezone('Asia/Seoul')
today = datetime.now().astimezone(tz=KST)
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " \
             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.80 Safari/537.36 "
headers = {'origin': 'https://www.mobileindex.com', 'user-agent': user_agent}


def post_to_slack(text=None, URL=""):
    requests.post(URL, headers={'Content-Type': 'application/json'}, data=f'{"text": "{text}"}')


def get_date(date_string=None) -> int:
    if not date_string:
        date_string = datetime.now().astimezone(tz=KST).strftime("%Y%m%d%H%M")
    url = "http://13.125.164.253/cron/new/date"
    url = "http://127.0.0.1:8000/cron/new/date"
    res = requests.post(url, data={"date": date_string})
    return res.json()["id"]


def get_soup(market_id, back=True):
    one_url = "https://m.onestore.co.kr/mobilepoc/"
    if back:
        one_url += f"web/apps/appsDetail/spec.omp?prodId={market_id}"
    else:
        one_url += f"apps/appsDetail.omp?prodId={market_id}"
    response = requests.get(one_url)
    if response.status_code == 200:
        return BeautifulSoup(response.text, "html.parser")


def create_app(app_data: dict) -> dict:
    url = "http://13.125.164.253/cron/new/app"
    url = "http://127.0.0.1:8000/cron/new/app"
    res = requests.post(url, data=app_data)
    return res.json()


def get_data_from_soup(market_appid: str) -> Tuple[str, str, str, str, date, int]:
    soup1 = get_soup(market_appid, True)
    soup2 = get_soup(market_appid, False)
    d_counts = soup1.select_one("li:-soup-contains('다운로드수') > span").text
    d_string = soup1.select_one("li:-soup-contains('출시일') > span").text
    genre = soup1.select_one("li:-soup-contains('장르') > span").text
    volume = soup1.select_one("li:-soup-contains('용량') > span").text
    style = soup1.select_one("#header > div > div > div.header-co-right > span").get('style')
    icon_url = style.replace("background-image:url(", "").replace(")", "")
    app_name = soup2.title.get_text().replace(" - 원스토어", "")
    array = [i for i in map(int, d_string.split("."))]
    released = date(year=array[0], month=array[1], day=array[2])
    download = int(d_counts.replace(",", ""))
    return genre, volume, icon_url, app_name, released, download


def crawl_app_store_rank(term: str, market: str, game_or_app: str) -> None:
    url = f'https://proxy-insight.mobileindex.com/chart/{term}'  # "realtime_rank_v2", "global_rank_v2"
    data = {
        "market": "all", "country": "kr",
        "rankType": "free", "appType": game_or_app,
        "date": "", "startRank": 0, "endRank": 100
    }
    if market == "one":
        data["date"] = datetime.now().astimezone(tz=KST).strftime("%Y%m%d")
    response = requests.post(url, data=data, headers=headers).json()
    date_id = get_date()
    following = [f.market_appid for f in Following.objects.filter(is_active=True)]
    if response["status"]:
        for app_data in response["data"]:
            app = create_app(app_data)
            market_name = app_data["market_name"]
            if not (market == "one" and market_name in ["apple", "google"]):
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
                if item.market_appid in following:
                    last = TrackingApps.objects.filter(
                        market_appid=item.market_appid,
                        market=item.market,
                        chart_type=item.chart_type,
                        app_name=item.app_name,
                    ).last()
                    tracking = TrackingApps(
                        following=Following.objects.get(market_appid=item.market_appid),
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
                    rank_diff = tracking.rank - last.rank if last else 0
                    market_str = item.get_market_display()
                    if rank_diff <= -1:
                        post_to_slack(f" 순위 상승🚀: {item.app_name} {market_str} `{last.rank}위` → `{item.rank}위`")
                    if rank_diff >= 1:
                        post_to_slack(f" 순위 하락🛬: {item.app_name} {market_str} `{last.rank}위` → `{item.rank}위`")


def get_highest_rank_of_realtime_ranks_today() -> None:
    date_today = get_date(datetime.now().astimezone(tz=KST).strftime("%Y%m%d") + "2300")
    rank_set = Ranked.objects \
        .filter(created_at__gte=today - timedelta(days=1),
                created_at__lte=today,
                market__in=["apple", "google"],
                deal_type="realtime_rank")
    for following in Following.objects.filter(is_active=True, market__in=["apple", "google"]).all():
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
