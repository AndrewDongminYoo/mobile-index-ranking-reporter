from crawling import *
from bs4 import BeautifulSoup
from django.db import DataError, IntegrityError
from django.db.models import Q

from crawler.models import AppInformation

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

    for app in App.objects.all().filter(app_info=None):
        app_info = None
        if app.market == "google":
            if not app.app_url:
                app.app_url = correct_path(GOOGLE_PREFIX + app.market_appid)
            app_info = AppInformation.objects.filter(google_url=app.app_url)
            if app_info.exists():
                app_info = app_info.first()
        elif app.market == "apple":
            if not app.app_url:
                app.app_url = correct_path(APPLE_PREFIX + app.market_appid)
            app_info = AppInformation.objects.filter(apple_url=app.app_url)
            if app_info.exists():
                app_info = app_info.first()
        elif app.market == "one":
            if not app.app_url:
                app.app_url = correct_path(ONE_PREFIX + app.market_appid)
            app_info = AppInformation.objects.filter(one_url=app.app_url)
            if app_info.exists():
                app_info = app_info.first()
        if app_info:
            app.app_info = app_info
            print(app_info)
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
                    google = data.get("google_url") if not data.get("google_url") == GOOGLE_PREFIX else None
                    if google:
                        new_app_info = AppInformation.objects.update_or_create(
                            google_url=google
                        )[0]
                    else:
                        new_app_info = AppInformation.objects.update_or_create(
                            google_url=GOOGLE_PREFIX + app.market_appid
                        )[0]
                    print(new_app_info.google_url)
                if app.market == "apple":
                    apple = data.get("apple_url") if not data.get("apple_url") == APPLE_PREFIX else None
                    if apple:
                        new_app_info = AppInformation.objects.update_or_create(
                            apple_url=apple,
                        )[0]
                    else:
                        new_app_info = AppInformation.objects.update_or_create(
                            apple_url=APPLE_PREFIX + app.market_appid
                        )[0]
                    print(new_app_info.apple_url)
                if app.market == "one":
                    one = data.get("one_url") if not data.get("one_url") == ONE_PREFIX else None
                    if one:
                        new_app_info = AppInformation.objects.update_or_create(
                            one_url=one
                        )[0]
                    else:
                        new_app_info = AppInformation.objects.update_or_create(
                            one_url=ONE_PREFIX + app.market_appid
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
                    if new_app_info.phone and new_app_info.email:
                        post_to_slack(
                            f"{app.market} {app.app_name} 앱의 연락처는 {new_app_info.phone}, 이메일은 {new_app_info.email} 입니다.")
                    elif new_app_info.phone:
                        post_to_slack(f"{app.market} {app.app_name} 앱의 연락처는 {new_app_info.phone}입니다.")
                    elif new_app_info.email:
                        post_to_slack(f"{app.market} {app.app_name} 앱의 이메일은 {new_app_info.email} 입니다.")
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
                    post_to_slack(f"{following.get_market_display()} {following.app_name} 앱 추적이 정기 등록 됐습니다.")
                except DataError:
                    print(market_appid)
                except IntegrityError:
                    print(market_appid)
    for app in Following.objects.filter(expire_date__lt=timezone.now()):
        post_to_slack(f"{app.get_market_display()} {app.app_name} 추적기한종료🪂")
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
    url = "https://proxy-insight.mobileindex.com/app/data_summary"
    for app in App.objects.all().filter(Q(category_main=None) | Q(category_sub=None)):
        data = {
            'packageName': app.market_appid,
        }
        req = requests.post(url, data=data, headers=headers)
        response = req.json()
        if response["status"]:
            main_category = response["data"]['biz_category_main']
            sub_category = response["data"]['biz_category_sub']
            if main_category and sub_category:
                if main_category != "null" and sub_category != "null":
                    app.category_main = main_category
                    app.category_sub = sub_category
                    app.save()
                    print(app.app_name, app.category_main, app.category_sub)
            else:
                print(app.app_name, "카테고리 없음")


def get_app_publisher_name():
    """
    앱의 퍼블리셔를 가져와 세팅한다.
    :return: None
    """
    url = 'https://proxy-insight.mobileindex.com/common/app_info'
    for app in App.objects.all().filter(publisher_name=None):
        data = {
            'packageName': app.market_appid,
        }
        req = requests.post(url, data=data, headers=headers)
        response = req.json()
        if response["status"]:
            data = response["data"]
            app.publisher_name = data['publisher_name']
            if app.market == "google":
                info = AppInformation.objects.filter(google_url__contains=data.get("package_name"))
                if info.exists():
                    app.app_info = info.first()
                    for a in App.objects.filter(app_info=info.first()):
                        a.publisher_name = app.publisher_name
                        a.category_main = app.category_main
                        a.category_sub = app.category_sub
                        a.save()
            if app.market == "one":
                info = AppInformation.objects.filter(one_url__contains=data.get("one_id"))
                if info.exists():
                    app.app_info = info.first()
                    for a in App.objects.filter(app_info=info.first()):
                        a.publisher_name = app.publisher_name
                        a.category_main = app.category_main
                        a.category_sub = app.category_sub
                        a.save()
            if app.market == "apple":
                info = AppInformation.objects.filter(apple_url__contains=data.get("apple_id"))
                if info.exists():
                    app.app_info = info.first()
                    for a in App.objects.filter(app_info=info.first()):
                        a.publisher_name = app.publisher_name
                        a.category_main = app.category_main
                        a.category_sub = app.category_sub
                        a.save()
            print(app.market, app.publisher_name, app.category_main, app.category_sub)
            app.save()


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
        "MUSIC_AND_AUDIO": ("엔터테인먼트", "음악"),
        "PERSONALIZATION": ("퍼스널", "테마/폰트/알림음"),
        "PHOTOGRAPHY": ("사진", "카메라"),
        "PRODUCTIVITY": ("생산성", "기록/일정관리"),
        "SHOPPING": ("패션/의류", "종합패션몰"),
        "SOCIAL": ("소셜네트워크", "SNS/커뮤니티"),
        "SPORTS": ("스포츠/레저", "기타스포츠"),
        "TOOLS": ("유틸리티", "폰관리"),
        "VIDEO_PLAYERS": ("엔터테인먼트", "동영상스트리밍"),
        "TRAVEL_AND_LOCAL": ("여행/교통", "국내숙박"),
    }

    def get_data_from_soup(google_url: str):
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
        e = None
        if s.select_one("a[href*='mailto:']"):
            e = s.select_one("a[href*='mailto:']").text.replace("email이메일", "")
        return t, p, c, e

    def get_category(application: App, categories: tuple):
        application.category_main = categories[0]
        application.category_sub = categories[1]
        application.save()

    for app in App.objects.filter(app_url__isnull=False, market="google", category_main=None):
        url: str = app.app_url
        print(url)
        title, publisher_name, category, email = get_data_from_soup(url)
        if app.app_info:
            app.app_info.email = email
            app.app_info.google_url = url
            app.app_info.save()
            for a in App.objects.filter(app_info=app.app_info):
                a.app_name = title
                a.publisher_name = publisher_name
                if category in category_map.keys():
                    get_category(a, category_map[category])
                else:
                    print(category)


def read_information_of_one_store_app():
    for app in App.objects.filter(market="one", app_url__isnull=False):
        url = app.app_url
        req = requests.get(url)
        soup = BeautifulSoup(req.text, "html.parser")
        try:
            title = soup.select_one("title").get_text().replace(" - 원스토어", "")
            publisher_name = soup.select_one("p.detailapptop-co-seller").get_text()
            app.app_name = title
            app.publisher_name = publisher_name
            print(app.app_name, app.publisher_name)
            if app.app_info:
                app.app_info.apple_url = url
                app.app_info.save()
            app.save()
        except AttributeError:
            app.app_url = ""
            app.save()


def read_information_of_apple_store_app():
    for app in App.objects.filter(market="apple", app_url__isnull=False):
        url = app.app_url
        req = requests.get(url)
        soup = BeautifulSoup(req.text, "html.parser")
        try:
            title = soup.select_one("title").get_text().replace("App Store에서 제공하는 ", "").strip()
            publisher_name = soup.select_one("a[href*='apps.apple.com/kr/developer']").get_text().strip()
            genre_name = soup.select_one("a[href*='itunes.apple.com/kr/genre']").get_text().strip()
            app.app_name = title
            app.publisher_name = publisher_name
            app.category_main = genre_name
            print(app.app_name, app.publisher_name, genre_name)
            if app.app_info:
                app.app_info.apple_url = url
                app.app_info.save()
            app.save()
        except AttributeError:
            app.app_url = ""
            app.save()


if __name__ == '__main__':
    # ive_korea_internal_api()
    # edit_apps_market()
    # set_apps_url_for_all()
    # get_developers_contact_number()
    # get_app_category()
    # get_app_publisher_name()
    read_information_of_google_app()
    read_information_of_one_store_app()
    read_information_of_apple_store_app()
