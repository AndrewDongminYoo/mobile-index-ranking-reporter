import sys

sys.path.append('/home/ubuntu/app-rank/ranker')
import os

os.environ.setdefault("PYTHONUNBUFFERED;", "1")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ranker.settings")
import django

if 'setup' in dir(django):
    django.setup()

import requests
from logging import getLogger
from crawler.models import Ranked, TrackingApps, App, OneStoreDL, AppInformation, Following

logger = getLogger(__name__)
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.80 Safari/537.36"
headers = {'origin': 'https://www.mobileindex.com', 'user-agent': user_agent}


def get_contact_number():
    import re
    for app in App.objects.all():
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
                    google = data.get("google_url") if not data.get("google_url") == "https://play.google.com/store/apps/details?id=" else None
                    new_app = AppInformation.objects.update_or_create(
                        google_url=google
                    )[0]
                if app.market == "apple":
                    apple = data.get("apple_url") if not data.get("apple_url") == "https://apps.apple.com/kr/app/id" else None
                    new_app = AppInformation.objects.update_or_create(
                        apple_url=apple,
                    )[0]
                if app.market == "one":
                    one = data.get("one_url") if not data.get("one_url") == "https://m.onestore.co.kr/mobilepoc/apps/appsDetail.omp?prodId=" else None
                    new_app = AppInformation.objects.update_or_create(
                        one_url=one
                    )[0]
                if response["description"]:
                    phone = re.findall(r"([0-1][0-9]*[\- ]*[0-9]{3,4}[\- ][0-9]{4,}|\+82[0-9\-]+)",
                                       response.get("description"))
                    email = re.findall(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)",
                                       response.get("description"))
                    new_app.contact = ", ".join(phone)
                    new_app.description = ", ".join(email)
                    print(phone, email)
                new_app.save()
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
        for advertisement in response["list"]:
            if advertisement["ads_package"] and "." in advertisement["ads_package"]:
                followings = Following.objects.filter(market_appid=advertisement["ads_package"])
                if followings.exists():
                    followings.first().is_active = True
                    followings.first().save()
                else:
                    following = Following(
                        app_name=advertisement["ads_name"],
                        market_appid=advertisement["ads_package"],
                        is_active=True,
                        market="google",
                    )
                    following.save()


if __name__ == '__main__':
    deduplicate()
