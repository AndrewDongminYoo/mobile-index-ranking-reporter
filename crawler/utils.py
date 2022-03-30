# -*- coding: utf-8 -*-
import os
import sys
import json

sys.path.append('/home/ubuntu/app-rank')
os.environ.setdefault("PYTHON" + "UNBUFFERED", "1")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ranker.settings")
import django

django.setup()
from datetime import datetime, timedelta, date
from django.db.models import Min, Q
from bs4 import BeautifulSoup
from pytz import timezone
from typing import Tuple
import requests
import re
from crawler.models import Ranked, Following, App
from crawler.models import TrackingApps, AppInformation
from ranker.settings import SLACK_WEBHOOK_URL

KST = timezone('Asia/Seoul')
today = datetime.now().astimezone(tz=KST)
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " \
             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.80 Safari/537.36 "
headers = {'origin': 'https://www.mobileindex.com', 'user-agent': user_agent}
MOBILE_INDEX = "https://proxy-insight.mobileindex.com"
GOOGLE_PREFIX = "https://play.google.com/store/apps/details?id="
APPLE_PREFIX = "https://apps.apple.com/kr/app/id"
ONE_PREFIX = "https://m.onestore.co.kr/mobilepoc/apps/appsDetail.omp?prodId="


def post_to_slack(text=None, URL=""):
    if not URL:
        URL = SLACK_WEBHOOK_URL
    headers["Content-Type"] = "application/json"
    data = json.dumps({"text": text})
    requests.post(URL, headers=headers, data=data)


def get_date(date_string=None) -> int:
    if not date_string:
        date_string = datetime.now().astimezone(tz=KST).strftime("%Y%m%d%H%M")
    url = "http://13.125.164.253/cron/new/date"
    res = requests.post(url, data={"date": date_string})
    return res.json()["id"]


def get_soup(market_id, back=True) -> BeautifulSoup:
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
    url = f'{MOBILE_INDEX}/chart/{term}'  # "realtime_rank_v2", "global_rank_v2"
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


def get_google_apps_data_from_soup(google_url: str):
    headers["accept-language"] = "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
    req = requests.get(google_url, headers=headers)
    _soup = BeautifulSoup(req.text, 'html.parser')
    _title = _soup.find("title").text.replace(" - Google Play 앱", "").replace(" - Apps on Google Play", "")
    assert _title != "찾을 수 없음", "잘못된 앱입니다."
    publisher = _soup.select_one("a[href*='/store/apps/dev']")
    _publisher_name = publisher.text if publisher else None
    first = _soup.select_one("a[href*='store/apps/category']")
    _category = first.get("href")[21:] if first else None
    _mailto = _soup.select_one("a[href*='mailto:']")
    _email = _soup.select_one("a[href*='mailto:']").text.replace("email이메일", "") if _mailto else None
    return _title, _publisher_name, _category, _email


def get_information_of_app(data: dict):
    market_appid = data["market_appid"]
    app_url = GOOGLE_PREFIX + market_appid
    title, publisher_name, category, email = get_google_apps_data_from_soup(app_url)
    app_info = AppInformation.objects.update_or_create(
        google_url=app_url,
    )[0]
    app_info.publisher_name = publisher_name
    app_info.email = email
    app = App.objects.update_or_create(
        market_appid=market_appid,
    )[0]
    app.app_name = data['app_name']
    app.icon_url = data['icon_url']
    app.market = data.get('market_name') or data.get("market")
    app.app_url = app_url
    mobile_index = MOBILE_INDEX + "/app/market_info"
    req = requests.post(mobile_index, headers=headers, data={"packageName": market_appid})
    response = req.json()
    res_data = response.get("data")
    app_data = res_data.get("market_info")
    app_info.apple_url = app_data.get("apple_url")
    app_info.one_url = app_data.get("one_url")
    app_info.save()
    print(app_info)
    app.app_info = app_info
    app.save()


def upto_400th_google_play_apps_contact():
    url = MOBILE_INDEX + "/chart/global_rank_v2"
    body = {
        "market": "all",
        "country": "kr",
        "rankType": "gross",
        "appType": "game",
        "date": (today - timedelta(days=1)).strftime("%Y%m%d"),
        "startRank": 101,
        "endRank": 400,
    }
    req = requests.post(url, headers=headers, data=body)
    res = req.json()
    for app_data in res["data"]:
        get_information_of_app(app_data)


def read_information_of_apple_store_app():
    for app in App.objects.filter(market="apple", app_url__isnull=False, app_info=None):
        req = requests.get(app.app_url, headers=headers)
        soup = BeautifulSoup(req.text, "html.parser")
        title = soup.select_one("title").get_text().replace("App Store에서 제공하는 ", "").strip()
        publisher_name = soup.select_one("a[href*='apps.apple.com/kr/developer']").get_text().strip()
        genre_name = soup.select_one("a[href*='itunes.apple.com/kr/genre']").get_text().strip()
        app.app_name = title
        print(app.app_name, publisher_name, genre_name)
        info = AppInformation.objects.get_or_create(apple_url=APPLE_PREFIX + app.market_appid)[0]
        info.publisher_name = publisher_name
        info.category_main = genre_name
        info.apple_url = app.app_url
        info.save()
        app.app_info = info
        app.save()


def read_information_of_one_store_app():
    for app in App.objects.filter(market="one", app_url__isnull=False, app_info=None):
        if not app.app_url or app.app_url.endswith("ERR504"):
            app.app_url = ONE_PREFIX + app.market_appid
            app.save()
        print(app.app_url)
        req = requests.get(app.app_url, headers=headers)
        soup = BeautifulSoup(req.text, "html.parser")
        try:
            title = soup.select_one("title").get_text().replace(" - 원스토어", "")
            publisher_name = soup.select_one("p.detailapptop-co-seller").get_text()
            app.app_name = title
            print(title, publisher_name)
            info = AppInformation.objects.get_or_create(one_url=ONE_PREFIX + app.market_appid)[0]
            info.publisher_name = publisher_name
            info.one_url = app.app_url
            info.save()
            app.app_info = info
        except AttributeError:
            app.delete()
        app.save()


def get_developers_contact_number():
    for app in App.objects.filter(app_info=None, market="google").all():
        url = MOBILE_INDEX + '/app/market_info'
        response = requests.post(url, headers=headers, data={"packageName": app.market_appid}).json()
        data = response["data"].get("market_info")
        app_info = AppInformation.objects.update_or_create(google_url=data.get("google_url"))[0]
        description = data.get("description")
        phone = re.findall(r"([0-1][0-9]*[\- ]*[0-9]{3,4}[\- ][0-9]{4,}|\+82[0-9\-]+)", description)
        email = re.findall(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", description)
        app_info.phone = ", ".join(set(phone))
        app_info.email = ", ".join(set(email))
        print(app_info.phone, app_info.email)
        app_info.save()
        app.app_info = app_info
        app.save()


def get_app_category():
    url = MOBILE_INDEX + "/common/app_info"
    for app in App.objects.all().filter(market="google", app_info__isnull=True):
        market_id = app.market_appid
        req = requests.post(url, headers=headers, data={'packageName': market_id})
        app_data = req.json()["data"]
        app.app_name = app_data['app_name']
        app.icon_url = app_data['icon_url']
        app_info = AppInformation.objects.get_or_create(google_url=GOOGLE_PREFIX + market_id)[0]
        app_info.apple_url = APPLE_PREFIX + app_data['apple_id']
        app_info.publisher_name = app_data['publisher_name']
        app_info.one_url = ONE_PREFIX + app_data['one_id']
        _main = app_data['biz_category_main']
        _subs = app_data['biz_category_sub']
        if (_main and _subs) and (_main != "null" and _subs != "null"):
            app_info.category_main = _main
            app_info.category_sub = _subs
        app.app_info = app_info
        app_info.save()
        app.save()


def get_app_publisher_name():
    url = MOBILE_INDEX + '/common/app_info'
    for app in App.objects.all().filter(app_info=None):
        response = requests.post(url, data={'packageName': app.market_appid}, headers=headers).json()
        data = response["data"]
        publisher_name = data.get('publisher_name')
        app_info = AppInformation.objects.filter(
            Q(google_url=GOOGLE_PREFIX + data.get("package_name")) |
            Q(one_url=ONE_PREFIX + data.get("one_id")) |
            Q(apple_url=APPLE_PREFIX + data.get("apple_id"))
        ).first()
        app_info.publisher_name = publisher_name
        app_info.save()
        app.app_info = app_info
        app.save()


def get_information_of_following_apps():
    for following in Following.objects.filter(market="google"):
        market_appid = following.market_appid
        google_url = GOOGLE_PREFIX + market_appid
        app_info = AppInformation.objects.get_or_create(
            google_url=google_url,
        )[0]
        app = App.objects.update_or_create(
            market_appid=market_appid,
            market="google",
        )[0]
        app.app_url = google_url
        mobile_index = MOBILE_INDEX + "/common/app_info"
        response = requests.post(mobile_index, headers=headers, data={"packageName": market_appid}).json()
        if response["status"]:
            app_data = response["data"]
            print(app_data)
            app_info.publisher_name = app_data["publisher_name"]
            app.icon_url = app_data["icon_url"]
            app.app_name = app_data["app_name"]
            app_info.save()
            print(app_info)
            app.app_info = app_info
            app.save()


if __name__ == '__main__':
    get_information_of_following_apps()
