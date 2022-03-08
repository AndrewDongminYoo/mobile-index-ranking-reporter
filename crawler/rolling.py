from datetime import timedelta

from django.db import DataError

from crawler.models import AppInformation
from crawling import *

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
        print(app_info)
        if app_info:
            app.app_info = app_info
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
                new_app = AppInformation(), True
                if app.market == "google":
                    google = data.get("google_url") if not data.get("google_url") == GOOGLE_PREFIX else None
                    if google:
                        new_app = AppInformation.objects.update_or_create(
                            google_url=google
                        )[0]
                    else:
                        new_app = AppInformation.objects.update_or_create(
                            google_url=GOOGLE_PREFIX + app.market_appid
                        )[0]
                    print(new_app.google_url)
                if app.market == "apple":
                    apple = data.get("apple_url") if not data.get("apple_url") == APPLE_PREFIX else None
                    if apple:
                        new_app = AppInformation.objects.update_or_create(
                            apple_url=apple,
                        )[0]
                    else:
                        new_app = AppInformation.objects.update_or_create(
                            apple_url=APPLE_PREFIX + app.market_appid
                        )[0]
                    print(new_app.apple_url)
                if app.market == "one":
                    one = data.get("one_url") if not data.get("one_url") == ONE_PREFIX else None
                    if one:
                        new_app = AppInformation.objects.update_or_create(
                            one_url=one
                        )[0]
                    else:
                        new_app = AppInformation.objects.update_or_create(
                            one_url=ONE_PREFIX + app.market_appid
                        )[0]
                    print(new_app.one_url)
                logger.info(new_app)
                if response["description"]:
                    phone = re.findall(r"([0-1][0-9]*[\- ]*[0-9]{3,4}[\- ][0-9]{4,}|\+82[0-9\-]+)",
                                       response.get("description"))
                    email = re.findall(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)",
                                       response.get("description"))
                    new_app.contact = ", ".join(set(phone))
                    new_app.description = ", ".join(set(email))
                    print(phone, email)
                new_app.save()
                app.app_info = new_app
                app.save()
            except KeyError:
                print(app.id, "key")
            except AttributeError:
                print(app.id, "attr")


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
                package = adv_info.get("ads_join_url")\
                    .replace("https://onesto.re", "")\
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
                    except DataError:
                        print(package)


def get_history(app: Ranked):
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
        _date = TimeIndex.objects.get_or_create(date=timezone.now().strftime("%Y%m%d%H%M"))[0]
        print(_date)
    return response["data"]


if __name__ == '__main__':
    # ive_korea_internal_api()
    get_app_url()
    # get_contact_number()
