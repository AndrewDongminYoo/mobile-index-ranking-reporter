# -*- coding: utf-8 -*-
import os
import sys
from datetime import timedelta

sys.path.append('/home/ubuntu/app-rank')
os.environ.setdefault("PYTHONUNBUFFERED;", "1")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ranker.settings")
import django

django.setup()

import requests
from bs4 import BeautifulSoup
from logging import getLogger
from django.db.models import Q
from django.utils import timezone
from django.db import DataError, IntegrityError
from crawler.models import Ranked, Following, TrackingApps, App, OneStoreDL, AppInformation

logger = getLogger(__name__)
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.80 Safari/537.36"
headers = {'origin': 'https://www.mobileindex.com', 'user-agent': user_agent}

GOOGLE_PREFIX = "https://play.google.com/store/apps/details?id="
APPLE_PREFIX = "https://apps.apple.com/kr/app/id"
ONE_PREFIX = "https://m.onestore.co.kr/mobilepoc/apps/appsDetail.omp?prodId="


def set_apps_url_for_all():
    """
    등록되어 있는 모든 애플리케이션의 url을 설정한다.
    :return: None
    """

    def correct_path(url):
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.url

    for app in App.objects.all().filter(Q(app_info=None) | Q(app_url=None)):
        if app.market == "google":
            if not app.app_url:
                app.app_url = correct_path(GOOGLE_PREFIX + app.market_appid)
            app_info = AppInformation.objects.filter(google_url=app.app_url)
            if app_info.exists():
                app.app_info = app_info.first()
        elif app.market == "apple":
            if not app.app_url:
                app.app_url = correct_path(APPLE_PREFIX + app.market_appid)
            app_info = AppInformation.objects.filter(apple_url=app.app_url)
            if app_info.exists():
                app.app_info = app_info.first()
        elif app.market == "one":
            if not app.app_url:
                app.app_url = correct_path(ONE_PREFIX + app.market_appid)
            app_info = AppInformation.objects.filter(one_url=app.app_url)
            if app_info.exists():
                app.app_info = app_info.first()
        app.save()


def get_developers_contact_number():
    """
    앱 개발자의 이메일과 연락처를 추출한다.
    :return: None
    """
    import re
    for app in App.objects.filter(app_info=None).all():
        url = 'https://proxy-insight.mobileindex.com/app/market_info'
        body = {
            "packageName": app.market_appid,
        }
        req = requests.post(url, body, headers=headers)
        if req.status_code == 200:
            response = req.json()
            try:
                data = response.get("data").get("market_info")
                new_app_info = AppInformation(), True
                if app.market == "google":
                    google = data.get("google_url") if data.get("google_url") != GOOGLE_PREFIX else None
                    if google:
                        new_app_info = AppInformation.objects.update_or_create(
                            google_url=google
                        )[0]
                    print(new_app_info.google_url)
                elif app.market == "apple":
                    apple = data.get("apple_url") if data.get("apple_url") != APPLE_PREFIX else None
                    if apple:
                        new_app_info = AppInformation.objects.update_or_create(
                            apple_url=apple,
                        )[0]
                    print(new_app_info.apple_url)
                elif app.market == "one":
                    one = data.get("one_url") if data.get("one_url") != ONE_PREFIX else None
                    if one:
                        new_app_info = AppInformation.objects.update_or_create(
                            one_url=one
                        )[0]
                    print(new_app_info.one_url)
                logger.info(new_app_info)
                if response["description"]:
                    phone = re.findall(r"([0-1][0-9]*[\- ]*[0-9]{3,4}[\- ][0-9]{4,}|\+82[0-9\-]+)",
                                       response.get("description"))
                    email = re.findall(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)",
                                       response.get("description"))
                    new_app_info.phone = ", ".join(set(phone))
                    new_app_info.email = ", ".join(set(email))
                    print(phone, email)
                new_app_info.save()
                app.app_info = new_app_info
                app.save()
            except KeyError:
                print(app.id, "key")
            except AttributeError:
                pass


def application_deduplicate():
    """
    마켓 아이디가 중복된 앱은 모두 제거한다.
    :return: None
    """
    array = dict()
    for app in App.objects.all().order_by("id"):
        if app.market_appid not in array.keys():
            array[app.market_appid] = app
        else:
            print(app.app_name)
            for a in Ranked.objects.filter(app=app):
                a.app = array[app.market_appid]
                a.save()
            for b in TrackingApps.objects.filter(app=app):
                b.app = array[app.market_appid]
                b.save()
            for c in OneStoreDL.objects.filter(app=app):
                c.app = array[app.market_appid]
                c.save()
            app.delete()


def application_information_deduplicate():
    """
    마켓 아이디가 중복된 앱은 모두 제거한다.
    :return: None
    """
    dicto = dict()
    for app_info in AppInformation.objects.all().order_by("-id"):
        if app_info.google_url not in dicto.keys():
            dicto[app_info.google_url] = app_info
        else:
            for a in App.objects.filter(app_info=app_info):
                a.app_info = dicto[app_info.google_url]
            dicto[app_info.google_url].apple_url = app_info.apple_url if app_info.apple_url else dicto[
                app_info.google_url].apple_url
            dicto[app_info.google_url].one_url = app_info.one_url if app_info.one_url else dicto[
                app_info.google_url].one_url
            dicto[app_info.google_url].email = app_info.email if app_info.email else dicto[app_info.google_url].email
            dicto[app_info.google_url].phone = app_info.phone if app_info.phone else dicto[app_info.google_url].phone
            app_info.delete()


def edit_apps_market():
    """
    마켓 아이디를 보고 앱의 마켓을 추측 및 수정한다.
    :return: None
    """
    for app in App.objects.all().filter(market=""):
        if app.market_appid.startswith("0000"):
            app.market = "one"
        elif app.market_appid[0].isalpha():
            app.market = "google"
        else:
            app.market = "apple"
        app.save()


def tracked_app_dedupe():
    """
    추적 결과 중 중복된 앱을 제거한다.
    :return: None
    """
    app_list = []
    for ranked in TrackingApps.objects.all():
        reg = ranked.created_at.strftime("%Y%m%d%H%M")
        fol = ranked.following_id
        app = ranked.app_id
        rnk = ranked.rank
        if (reg, fol, app, rnk) not in app_list:
            app_list.append((reg, fol, app, rnk))
        else:
            ranked.delete()


def ive_korea_internal_api():
    """
    아이브코리아 내부 API를 호출해 앱 정보를 등록한다.
    :return: None
    """
    API_KEY = 'wkoo4ko0g808s0kkossoo4o8ow0kwwg88gw004sg'
    url = f'http://dev.i-screen.kr/channel/rank_ads_list?apikey={API_KEY}'
    req = requests.get(url)

    if req.status_code == 200:
        response = req.json()
        for adv_info in response["list"]:
            # print(adv_info)
            print(adv_info["ads_name"], adv_info["ads_package"], adv_info["ads_join_url"])
            market = None
            market_appid = adv_info.get("ads_package")
            address = adv_info.get("ads_join_url")
            appname = adv_info.get("ads_name")
            os_type = adv_info.get("ads_os_type")
            import re
            google = re.compile(r'^\w+(\.\w+)+$')
            apple = re.compile(r'^\d{9,11}$')
            one = re.compile(r'^0000\d{5,6}$')
            if google.fullmatch(market_appid) and os_type == "2":
                market = "google"
            elif one.fullmatch(market_appid) and os_type == "3":
                market = "one"
            elif apple.fullmatch(market_appid) and os_type == "1":
                market = "apple"
            else:
                market_appID = re.findall(r'\d{9,11}$', address)
                if market_appID:
                    market_appid = market_appID[0]
                    market = "one" if market_appid.startswith("0000") else "apple"
                    print(market_appid)
                elif re.search(r'[a-z]+(\.\w+)+$', address):
                    market_appid = re.compile(r'[a-z]+(\.\w+)+$').search(address)[0]
                    market = "google"
                    print(market_appid)
                else:
                    continue
            followings = Following.objects.filter(market=market, market_appid=market_appid)
            if followings.exists():
                following = followings.first()
                following.is_active = True
                following.expire_date = timezone.now() + timedelta(days=7)
                following.save()
            else:
                try:
                    following = Following(
                        app_name=appname,
                        market_appid=market_appid,
                        market=market,
                        is_active=True,
                        expire_date=timezone.now() + timedelta(days=7)
                    )
                    following.save()
                    print(following)
                except DataError as e:
                    print(market_appid, e)
                except IntegrityError as e:
                    print(market_appid, e)
    for app in Following.objects.filter(is_active=True, expire_date__lt=timezone.now()):
        app.is_active = False
        app.save()


def get_app_history(app: Ranked):
    """
    특정 앱의 추적 결과 히스토리를 가져온다.(내부결과아님. 모바일인덱스)
    :param app: 랭킹에 추적된 앱
    :return: 해당 앱의 추적 결과 히스토리
    """
    url = 'https://proxy-insight.mobileindex.com/chart/market_rank_history'  # "realtime_rank_v2", "global_rank_v2"
    data = {
        'appId': app.market_appid,
        'market': app.market,
        'appType': app.app_type,
        'startDate': (timezone.now() - timedelta(days=3)).strftime("%Y%m%d%H%M"),
        'endDate': timezone.now().strftime("%Y%m%d%H%M"),
    }
    req = requests.post(url, data=data, headers=headers)
    response = req.json()
    if response["status"]:
        # _date = TimeIndex.objects.get_or_create(date=timezone.now().strftime("%Y%m%d%H%M"))[0]
        # print(_date)
        return response["data"]


def get_app_category():
    """
    앱 카테고리를 가져와 세팅한다.
    :return: None
    """
    url = "https://proxy-insight.mobileindex.com/common/app_info"
    for app in App.objects.all().filter(market="google", app_info__isnull=True):
        data = {
            'packageName': app.market_appid,
        }
        req = requests.post(url, data=data, headers=headers)
        response = req.json()
        if response["status"]:
            main_category = response["data"]['biz_category_main']
            sub_category = response["data"]['biz_category_sub']
            app_name = response["data"]['app_name']
            icon_url = response["data"]['icon_url']
            publisher_name = response["data"]['publisher_name']
            apple_id = response["data"]['apple_id']
            one_id = response["data"]['one_id']
            app.icon_url = icon_url
            if app_name:
                app.app_name = app_name
            if app.app_info:
                app_info = app.app_info
            else:
                app_info = AppInformation.objects.filter(google_url=GOOGLE_PREFIX + app.market_appid)
            if main_category and sub_category:
                if main_category != "null" and sub_category != "null":
                    app_info.category_main = main_category
                    app_info.category_sub = sub_category
            if publisher_name and icon_url:
                app_info.publisher_name = publisher_name
                print(publisher_name, icon_url)
            if apple_id and one_id:
                app_info.apple_url = APPLE_PREFIX + apple_id
                app_info.one_url = ONE_PREFIX + one_id
            app_info.save()
            app.save()
            print(apple_id, one_id, app.app_info)


def get_app_publisher_name():
    """
    앱의 퍼블리셔를 가져와 세팅한다.
    :return: None
    """
    url = 'https://proxy-insight.mobileindex.com/common/app_info'
    for app in App.objects.all().filter(app_info=None):
        data = {
            'packageName': app.market_appid,
        }
        req = requests.post(url, data=data, headers=headers)
        response = req.json()
        if response["status"]:
            data = response["data"]
            publisher_name = data.get('publisher_name')
            if app.market == "googl e":
                info = AppInformation.objects.filter(google_url__contains=data.get("package_name"))
                if info.exists():
                    app_info = info.first()
                    app_info.publisher_name = publisher_name
                    app_info.save()
                    app.app_info = app_info
            if app.market == "one":
                info = AppInformation.objects.filter(one_url__contains=data.get("one_id"))
                if info.exists():
                    app_info = info.first()
                    app_info.publisher_name = publisher_name
                    app_info.save()
                    app.app_info = app_info
            if app.market == "apple":
                info = AppInformation.objects.filter(apple_url__contains=data.get("apple_id"))
                if info.exists():
                    app_info = info.first()
                    app_info.publisher_name = publisher_name
                    app_info.save()
                    app.app_info = app_info
            print(app.market, app.app_info.publisher_name, app.app_info.category_main, app.app_info.category_sub)
            app.save()


def get_google_apps_data_from_soup(google_url: str):
    headers["accept-language"] = "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
    req = requests.get(google_url, headers=headers)
    s = BeautifulSoup(req.text, 'html.parser')
    t = s.find("title").text.replace(" - Google Play 앱", "").replace(" - Apps on Google Play", "")
    if t == "찾을 수 없음":
        t = None
    publisher = s.select_one("a[href*='/store/apps/dev']")
    p = publisher.text if publisher else None
    first = s.select_one("a[href*='store/apps/category']")
    c = first.get("href")[21:] if first else None
    if s.select_one("a[href*='mailto:']"):
        e = s.select_one("a[href*='mailto:']").text.replace("email이메일", "")
    else:
        e = None
    return t, p, c, e


def read_information_of_google_app():
    category_map = {
        "BOOKS_AND_REFERENCE": ("도서/참고자료", "도서/전자도서"),
        "BUSINESS": ("비즈니스/산업", "비즈니스툴"),
        "COMICS": ("도서/참고자료", "만화/웹소설"),
        "COMMUNICATION": ("소셜네트워크", "메신저/전화/영상통화"),
        "DATING": ("소셜네트워크", "소개팅/채팅"),
        "EDUCATION": ("교육", "기타교육"),
        "PARENTING": ("교육", "임신/출산"),
        "ENTERTAINMENT": ("엔터테인먼트", "동영상스트리밍"),
        "EVENTS": ("엔터테인먼트", "유머/재미"),
        "FINANCE": ("금융", "송금/결제"),
        "FOOD_AND_DRINK": ("식음료", "식음료브랜드/멤버십"),
        "GAME_ACTION": ("게임", "액션게임"),
        "GAME_ADVENTURE": ("게임", "어드벤처게임"),
        "GAME_ARCADE": ("게임", "아케이드게임"),
        "GAME_BOARD": ("게임", "보드게임"),
        "GAME_CARD": ("게임", "카드게임"),
        "GAME_WORD": ("게임", "단어게임"),
        "GAME_CASINO": ("게임", "카지노게임"),
        "GAME_CASUAL": ("게임", "캐주얼게임"),
        "GAME_MUSIC": ("게임", "리듬/타일게임"),
        "GAME_PUZZLE": ("게임", "퍼즐게임"),
        "GAME_RACING": ("게임", "레이싱게임"),
        "GAME_ROLE_PLAYING": ("게임", "롤플레잉게임"),
        "GAME_SIMULATION": ("게임", "시뮬레이션게임"),
        "GAME_SPORTS": ("게임", "스포츠게임"),
        "GAME_STRATEGY": ("게임", "전략게임"),
        "GAME_TRIVIA": ("게임", "퀴즈게임"),
        "HEALTH_AND_FITNESS": ("건강/의료", "건강정보"),
        "LIFESTYLE": ("라이프스타일", "라이프스타일"),
        "MAPS_AND_NAVIGATION": ("여행/교통", "지도/네비게이션"),
        "MEDICAL": ("건강/의료", "기타병의원"),
        "HOUSE_AND_HOME": ("가정/생활", "가구/인테리어"),
        "FAMILY": ("가정/생활", "가족"),
        "MUSIC_AND_AUDIO": ("엔터테인먼트", "음악"),
        "PERSONALIZATION": ("퍼스널", "테마/폰트/알림음"),
        "NEWS_AND_MAGAZINES": ("도서/참고자료", "뉴스/잡지"),
        "PHOTOGRAPHY": ("사진", "카메라"),
        "PRODUCTIVITY": ("생산성", "기록/일정관리"),
        "SHOPPING": ("패션/의류", "종합패션몰"),
        "SOCIAL": ("소셜네트워크", "SNS/커뮤니티"),
        "SPORTS": ("스포츠/레저", "기타스포츠"),
        "TOOLS": ("유틸리티", "폰관리"),
        "VIDEO_PLAYERS": ("엔터테인먼트", "동영상스트리밍"),
        "TRAVEL_AND_LOCAL": ("여행/교통", "국내숙박"),
    }

    for app in App.objects.filter(app_url__isnull=False, market="google", app_info=None):
        if app.app_info:
            app.app_info.google_url = app.app_url
            if app.app_url:
                title, publisher_name, category, email = get_google_apps_data_from_soup(app.app_url)
                app.app_name = title
                app.app_info.email = email
                app.app_info.publisher_name = publisher_name
                if category and (category in category_map.keys()):
                    app.app_info.category_main = category_map[category][0]
                    app.app_info.category_sub = category_map[category][1]
                    print(category_map[category])
                else:
                    logger.info(category)
                app.app_info.save()
                app.save()
        else:
            info = AppInformation.objects.filter(google_url__contains=app.market_appid)
            if info.exists():
                app.app_info = info.first()
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
            if app.app_info:
                app.app_info.publisher_name = publisher_name
                app.app_info.one_url = app.app_url
                app.app_info.save()
            else:
                info = AppInformation.objects.filter(one_url__contains=app.market_appid)
                if info.exists():
                    app.app_info = info.first()
                    app.save()
        except AttributeError:
            app.app_url = ""
        app.save()


def read_information_of_apple_store_app():
    for app in App.objects.filter(market="apple", app_url__isnull=False, app_info=None):

        req = requests.get(app.app_url, headers=headers)
        soup = BeautifulSoup(req.text, "html.parser")
        try:
            title = soup.select_one("title").get_text().replace("App Store에서 제공하는 ", "").strip()
            publisher_name = soup.select_one("a[href*='apps.apple.com/kr/developer']").get_text().strip()
            genre_name = soup.select_one("a[href*='itunes.apple.com/kr/genre']").get_text().strip()
            app.app_name = title
            print(app.app_name, publisher_name, genre_name)
            if app.app_info:
                app.app_info.publisher_name = publisher_name
                app.app_info.category_main = genre_name
                app.app_info.apple_url = app.app_url
                app.app_info.save()
            else:
                info = AppInformation.objects.filter(apple_url__contains=app.market_appid)
                app.app_info = info.first() if info.exists() else None
                app.save()
            app.save()
        except AttributeError:
            app.app_url = ""
            app.save()


def upto_400th_google_play_apps_contact():
    url = "https://proxy-insight.mobileindex.com/chart/global_rank_v2"
    body = {
        "market": "all",
        "country": "kr",
        "rankType": "gross",
        "appType": "game",
        "date": (timezone.now() - timedelta(days=1)).strftime("%Y%m%d"),
        "startRank": 101,
        "endRank": 400,
    }
    req = requests.post(url, headers=headers, data=body)
    res = req.json()
    for data in res["data"]:
        market = data['market_name']
        app_name = data['app_name']
        icon_url = data['icon_url']
        market_appid = data['market_appid']
        if market == "google":
            app_url = GOOGLE_PREFIX + market_appid
            title, publisher_name, category, email = get_google_apps_data_from_soup(app_url)
            app_info = AppInformation.objects.update_or_create(
                google_url=app_url,
            )[0]
            app_info.publisher_name = publisher_name
            app_info.email = email
            app_info.save()
            app = App.objects.update_or_create(
                market_appid=market_appid,
            )[0]
            app.app_name = app_name
            app.icon_url = icon_url
            app.market = market
            app.app_url = app_url
            app.app_info = app_info
            app.save()
            mobile_index_app = "https://proxy-insight.mobileindex.com/app/market_info"
            req = requests.post(mobile_index_app, headers=headers, data={"packageName": market_appid})
            if req.status_code == 200:
                response = req.json()
                data = response.get("data")
                if type(data) == dict:
                    data = data.get("market_info")
                    app_info.apple_url = data.get("apple_url") if data.get("apple_url") != APPLE_PREFIX else None
                    app_info.one_url = data.get("one_url") if data.get("one_url") != ONE_PREFIX else None
                    app_info.save()
                    print(app_info)


def good_morning_half_past_ten_daily():
    ive_korea_internal_api()
    read_information_of_google_app()
    read_information_of_one_store_app()
    read_information_of_apple_store_app()
    upto_400th_google_play_apps_contact()


if __name__ == '__main__':
    upto_400th_google_play_apps_contact()
    # ive_korea_internal_api()
