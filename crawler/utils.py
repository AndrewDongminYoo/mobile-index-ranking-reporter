# -*- coding: utf-8 -*-
import json
import os
import sys

sys.path.append('/home/ubuntu/app-rank')
os.environ.setdefault("PYTHON" + "UNBUFFERED", "1")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ranker.settings")
import django

django.setup()
from datetime import datetime, timedelta, date
from django.db.models import Q, Min
from bs4 import BeautifulSoup
from pytz import timezone
from typing import Tuple
import requests
import re
from logging import getLogger
from crawler.models import Following, App, TrackingApps, Ranked, TimeIndex, StatusCheck
from crawler.models import AppInformation
from ranker.settings import SLACK_WEBHOOK_URL

logger = getLogger(__name__)
KST = timezone('Asia/Seoul')
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " \
             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.80 Safari/537.36 "
headers = {'origin': 'https://www.mobileindex.com', 'user-agent': user_agent}
MOBILE_INDEX = "https://proxy-insight.mobileindex.com"
GOOGLE_PREFIX = "https://play.google.com/store/apps/details?id="
APPLE_PREFIX = "https://apps.apple.com/kr/app/id"
ONE_PREFIX = "https://m.onestore.co.kr/mobilepoc/apps/appsDetail.omp?prodId="


def status_check(market="google", app_type="game"):
    MARKET_TYPE = dict(google="플레이스토어", apple="앱스토어")
    APP_TYPE = dict(game="게임", app="앱")
    ranks = Ranked.objects.filter(market=market, app_type=app_type, deal_type="realtime_rank")
    last_ranks = [ranks.filter(rank=r).last() for r in range(1, 46)]
    app_list = [[app.rank, app.market_appid] for app in last_ranks]
    app_exists = StatusCheck.objects.filter(ranks=app_list, app_type=app_type, market=market).last()
    if not app_exists:
        last_status = StatusCheck.objects.filter(app_type=app_type, market=market).last()
        if last_status and last_status.warns > 10:
            post_to_slack(f"@here {MARKET_TYPE[market]}의 {APP_TYPE[app_type]} 랭킹이 변했습니다. 👏👏👏")
        app_exists = StatusCheck.objects.create(ranks=app_list, app_type=app_type, market=market, warns=0)
    else:
        app_exists.warns += 1
        app_exists.save()
    if app_exists.warns > 10:
        post_to_slack(f"{MARKET_TYPE[market]}의 {APP_TYPE[app_type]} 랭킹이 멈춘 것 같습니다. (⏱ {app_exists.warns}시간)")


def get_following() -> list:
    API_KEY = 'wkoo4ko0g808s0kkossoo4o8ow0kwwg88gw004sg'
    url = f'http://dev.i-screen.kr/channel/rank_ads_list?apikey={API_KEY}'
    req = requests.get(url)
    result = []
    if req.status_code == 200:
        response = req.json()
        for adv_info in response["list"]:
            google_app = dict(
                market_appid=adv_info.get("ads_package"),
                address=adv_info.get("ads_join_url"),
                appname=adv_info.get("ads_name"),
                os_type=adv_info.get("ads_os_type"),
            )
            mobile_index = MOBILE_INDEX + "/app/market_info"
            req = requests.post(mobile_index, headers=headers, data={"packageName": adv_info.get("ads_package")})
            if req.status_code == 200:
                res = req.json()
                if res.get("data"):
                    data = res["data"]
                    if type(data) is dict and data.get("apple_url"):
                        apple_app = dict(
                            market_appid=res.get("apple_id"),
                            address=data.get("apple_url"),
                            appname=adv_info.get("ads_name"),
                            os_type="apple",
                        )
                        url = "http://13.125.164.253/cron/new/following"
                        res = requests.post(url, data=apple_app)
                        if res.status_code == 200:
                            print(res.json())
                            result.append(res.json()["market_appid"])
                    if type(data) is dict and data.get("one_url"):
                        one_app = dict(
                            market_appid=res.get("one_id"),
                            address=data.get("one_url"),
                            appname=adv_info.get("ads_name"),
                            os_type="one",
                        )
                        url = "http://13.125.164.253/cron/new/following"
                        res = requests.post(url, data=one_app)
                        if res.status_code == 200:
                            print(res.json())
                            result.append(res.json()["market_appid"])
            url = "http://13.125.164.253/cron/new/following"
            res = requests.post(url, data=google_app)
            if res.status_code == 200:
                print(res.json())
                result.append(res.json()["market_appid"])
    Following.objects.all().update(is_following=False)
    for market_appid in result:
        Following.objects.filter(market_appid=market_appid).update(is_following=True)
    logger.info(result)
    return result


def post_to_slack(text=None, following=None):
    headers["Content-Type"] = "application/json"
    url = f"http://apprank.i-screen.kr/statistic/{following}" if following else "http://apprank.i-screen.kr"
    data = dict(blocks=[dict(type="section", text=dict(type="mrkdwn", text=text),
                             accessory=dict(type="button", text=dict(type="plain_text", text="자세히보기", emoji=True),
                                            value="click_btn", url=url, action_id="button-action"))])
    requests.post(SLACK_WEBHOOK_URL, headers=headers, data=json.dumps(data))


def get_date(date_string=None) -> int:
    if not date_string:
        date_string = datetime.now().astimezone(tz=KST).strftime("%Y%m%d%H%M")
    time_index = TimeIndex.objects.get_or_create(date=date_string)[0]
    return time_index.id


def get_soup(market_id, back=True) -> BeautifulSoup:
    one_url = "https://m.onestore.co.kr/mobilepoc/"
    if back:
        one_url += f"web/apps/appsDetail/spec.omp?prodId={market_id}"
    else:
        one_url += f"apps/appsDetail.omp?prodId={market_id}"
    response = requests.get(one_url)
    if response.status_code == 200:
        return BeautifulSoup(response.text, "html.parser")


def create_app(app_data: dict) -> App:
    app = App.objects.get_or_create(market_appid=app_data.get('market_appid'))[0]
    app.app_name = app_data.get('app_name')
    app.icon_url = app_data.get('icon_url')
    if app.app_info:
        publisher_name = app_data.get('publisher_name')
        app.app_info.publisher_name = publisher_name
        app.app_info.save()
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
    return app


def get_data_from_soup(market_appid: str) -> Tuple[str, str, str, str, date, int]:
    soup1 = get_soup(market_appid, True)
    soup2 = get_soup(market_appid, False)
    selector = "#container > div.detaildescription-wrap.ty1 > div.detaildescription-list > ul"
    d_counts = soup1.select_one(selector + " > li:nth-child(3) > span").text
    d_string = soup1.select_one(selector + " > li:nth-child(4) > span").text
    genre = soup1.select_one(selector + " > li:nth-child(1) > span").text
    volume = soup1.select_one(selector + " > li:nth-child(2) > span").text
    style = soup1.select_one("#header > div > div > div.header-co-right > span").get('style')
    icon_url = style.replace("background-image:url(", "").replace(")", "")
    app_name = soup2.title.get_text().replace(" - 원스토어", "")
    array = [i for i in map(int, d_string.split("."))]
    released = date(year=array[0], month=array[1], day=array[2])
    download = int(d_counts.replace(",", ""))
    logger.info(f"{market_appid} : {app_name}, {genre}, {volume}, {released}, {download}")
    return genre, volume, icon_url, app_name, released, download


def crawl_app_store_rank(term: str, market: str, game_or_app: str) -> None:
    url = MOBILE_INDEX + '/chart/' + term  # "realtime_rank_v2", "global_rank_v2"
    data = dict(market="all", country="kr", rankType="free", appType=game_or_app, date="", startRank=0, endRank=100)
    if market == "one":
        data["date"] = datetime.now().astimezone(tz=KST).strftime("%Y%m%d")
    response = requests.post(url, data=data, headers=headers).json()
    if response["status"]:
        for app_data in response["data"]:
            url = f"http://13.125.164.253/cron/new/ranking/app?market={market}&game={game_or_app}&term={term}"
            logger.info(f"/app?market={market}&game={game_or_app}&term={term}")
            requests.post(url, data=app_data)


def get_google_apps_data_from_soup(google_url: str):
    headers["accept-language"] = "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
    req = requests.get(google_url, headers=headers)
    _soup = BeautifulSoup(req.text, 'html.parser')
    _title = _soup.find("title").text.replace(" - Google Play 앱", "").replace(" - Apps on Google Play", "")
    if _title != "찾을 수 없음":
        return (None,) * 3
    publisher = _soup.select_one("a[href*='/store/apps/dev']")
    _publisher_name = publisher.text if publisher else None
    first = _soup.select_one("a[href*='store/apps/category']")
    _category = first.get("href")[21:] if first else None
    mailto = _soup.select_one("a[href*='mailto:']")
    _email = mailto.text.replace("email이메일", "") if mailto else None
    return _publisher_name, _category, _email


def get_information_of_app(data: dict):
    market_appid = data["market_appid"]
    app_url = GOOGLE_PREFIX + market_appid
    publisher_name, category, email = get_google_apps_data_from_soup(app_url)
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
    print(res_data)
    app_data = res_data.get("market_info") if res_data and res_data != "The data does not exist." else None
    app_info.apple_url = app_data.get("apple_url") if app_data else None
    app_info.one_url = app_data.get("one_url", ) if app_data else None
    app_info.save()
    print(app_info)
    app.app_info = app_info
    app.save()


def upto_400th_google_play_apps_contact():
    url = MOBILE_INDEX + "/chart/global_rank_v2"
    body = dict(market="all", country="kr", rankType="gross", appType="game",
                date=(datetime.now().astimezone(tz=KST) - timedelta(days=1)).strftime("%Y%m%d"), startRank=101,
                endRank=400)
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
        logger.info(info.apple_url)
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
            logger.info(info.one_url)
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

        data = response.get('data')
        if data != "The data does not exist.":
            market_info = data.get("market_info")
            app_info = AppInformation.objects.update_or_create(google_url=market_info.get("google_url"))[0]
            description = market_info.get("description")
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
        if app_data != "The data does not exist.":
            app.app_name = app_data['app_name']
            app.icon_url = app_data['icon_url']
            app_info = AppInformation.objects.get_or_create(google_url=GOOGLE_PREFIX + market_id)[0]
            app_info.apple_url = APPLE_PREFIX + str(app_data['apple_id']) if app_data['apple_id'] else None
            app_info.publisher_name = app_data['publisher_name']
            app_info.one_url = ONE_PREFIX + str(app_data['one_id']) if app_data['one_id'] else None
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
        if data != "The data does not exist.":
            print(data)
            app_info = AppInformation.objects.filter(
                Q(google_url=GOOGLE_PREFIX + str(data.get("package_name"))) |
                Q(one_url=ONE_PREFIX + str(data.get("one_id"))) |
                Q(apple_url=APPLE_PREFIX + str(data.get("apple_id")))
            ).first()
            app_info.publisher_name = data.get('publisher_name')
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
            logger.info(f"{app.app_name}, {app.market_appid}, {app.icon_url}")
            app_info.save()
            print(app_info)
            app.app_info = app_info
            app.save()


def get_highest_rank_of_realtime_ranks_today() -> None:
    today = datetime.today().date()
    today_now = datetime.now().astimezone(tz=KST)
    date_today: int = get_date(today_now.strftime("%Y%m%d") + "2300")
    rank_set = Ranked.objects \
        .filter(created_at__year=today.year,
                created_at__month=today.month,
                created_at__day=today.day,
                market__in=["apple", "google"],
                deal_type="realtime_rank")
    for following in Following.objects.filter(expire_date__gte=today_now, market__in=["apple", "google"]).all():
        market_appid = following.market_appid
        query = rank_set.filter(market_appid=market_appid) \
            .values('market_appid', 'app_name', 'market', 'app_type', 'chart_type', 'icon_url') \
            .annotate(highest_rank=Min('rank'))
        if query:
            first = query[0]
            app: App = App.objects.get(market_appid=market_appid)
            new_app = TrackingApps.objects.update_or_create(
                market=first.get('market'),
                chart_type=first.get('chart_type'),
                app_name=first.get('app_name'),
                icon_url=first.get('icon_url'),
                deal_type='market_rank',
                market_appid=market_appid,
                app=app,
                following=following,
                date_id=date_today,
            )[0]
            new_app.rank = first.get('highest_rank')
            new_app.save()


def get_apps_history_from_mobile_index(app_name):
    app = Ranked.objects.filter(app_name=app_name).last()
    url = MOBILE_INDEX + "/chart/market_rank_history"
    body = dict(appId=app.market_appid, market=app.market, appType=app.app_type,
                startDate=(datetime.now().astimezone(tz=KST) - timedelta(weeks=3)).strftime("%Y%m%d"),
                endDate=datetime.now().astimezone(tz=KST).strftime("%Y%m%d"))
    req = requests.post(url, headers=headers, data=body)
    res = req.json()
    if res["status"]:
        app_name = res["app_name"]
        icon_url = res["icon_url"]
        market = res["market_name"].lower()
        for app_data in res["data"]:
            _date = app_data["rank_date"].replace("-", "") + "1210"
            free_rank = app_data["rank_free"]
            TrackingApps.objects.get_or_create(
                app=App.objects.get(market_appid=app.market_appid),
                following=Following.objects.get(market_appid=app.market_appid),
                app_name=app_name,
                icon_url=icon_url,
                market=market.replace("store", ""),
                deal_type="market_rank",
                chart_type="free",
                market_appid=app.market_appid,
                date_id=get_date(_date),
                rank=free_rank,
            )


if __name__ == '__main__':
    get_developers_contact_number()
