from django.db.models import Q

from crawling import *
from datetime import timedelta
from django.db import DataError
from crawler.models import AppInformation

GOOGLE_PREFIX = "https://play.google.com/store/apps/details?id="
APPLE_PREFIX = "https://apps.apple.com/kr/app/id"
ONE_PREFIX = "https://m.onestore.co.kr/mobilepoc/apps/appsDetail.omp?prodId="


def get_app_url():
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


def get_contact_number():
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


def deduplicate():
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


def app_market():
    for app in App.objects.all().filter(market=""):
        if app.market_appid.startswith("0000"):
            app.market = "one"
        elif app.market_appid[0].isalpha():
            app.market = "google"
        else:
            app.market = "apple"
        app.save()


def ranked_dedupe():
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
    API_KEY = 'wkoo4ko0g808s0kkossoo4o8ow0kwwg88gw004sg'
    url = f'http://dev.i-screen.kr/channel/rank_ads_list?apikey={API_KEY}'
    req = requests.get(url)

    if req.status_code == 200:
        response = req.json()
        print(response)
        for adv_info in response["list"]:
            package = adv_info.get("ads_package")
            market = "google"
            if package.endswith("//"):
                package = ""
                pass
            elif adv_info.get("ads_join_url").startswith("https://apps.apple.com/kr/app/id"):
                market = "apple"
                package = adv_info.get("ads_join_url")\
                    .replace("https://apps.apple.com/kr/app/id", "")
            elif adv_info.get("ads_os_type") == "3":
                market = "one"
                package = adv_info.get("ads_join_url") \
                    .replace("https://onesto.re/", "") \
                    .replace("https://m.onestore.co.kr/mobilepoc/apps/appsDetail.omp?prodId=", "")
            if package:
                followings = Following.objects.filter(market_appid=package)
                if followings.exists():
                    followings.first().is_active = True
                    followings.first().save()
                else:
                    try:
                        following = Following(
                            app_name=adv_info["ads_name"],
                            market_appid=package,
                            is_active=True,
                            market=market,
                        )
                        following.save()
                        post_to_slack(f"{market} 스토어 {following.app_name} 앱 추적이 정기 등록 됐습니다.")
                    except DataError:
                        print(package)


def get_app_history(app: Ranked):
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
                app.category_main = main_category if main_category != "null" else None
                app.category_sub = sub_category if sub_category != "null" else None
                app.save()
                print(app.app_name, app.category_main, app.category_sub)
            else:
                print(app.app_name, main_category, sub_category)


def get_app_publisher_name():
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


if __name__ == '__main__':
    get_app_publisher_name()
    # get_app_url()
    # get_contact_number()
    # get_app_category()
