import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ranker.settings")
import django

if 'setup' in dir(django):
    django.setup()
from django.utils import timezone
from django.db.utils import IntegrityError
import requests
from crawler.models import Ranked, Following, TrackingApps, App
from crawler.ranking_bot import get_one_store_app_download_count

user_agent = " ".join(
    ["Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
     "AppleWebKit/537.36 (KHTML, like Gecko)",
     "Chrome/98.0.4758.80 Safari/537.36"])
headers = {'origin': 'https://www.mobileindex.com',
           'user-agent': user_agent}


def crawl_app_store_rank(deal: str, market: str, price: str, game: str):
    """
    :param deal: "realtime_rank_v2", "global_rank_v2"
    :param market: "all", "google"(global)
    :param price: "gross", "paid", "free"
    :param game: "app", "game"
    :return: Ranked
    """
    url = f'https://proxy-insight.mobileindex.com/chart/{deal}'  # "realtime_rank_v2", "global_rank_v2"
    data = {
        "market": market,  # "all", "google"
        "country": "kr",
        "rankType": price,  # "gross", "paid", "free"
        "appType": game,  # "game", "app"
        "date": timezone.now().strftime("%Y%m%d"),
        "startRank": 1,
        "endRank": 100,
    }

    req = requests.post(url, data=data, headers=headers)
    obj = req.json()
    following_applications = [f[0] for f in Following.objects.values_list("app_name")]
    if obj["status"]:
        print(obj.items())
        for i in obj["data"]:
            try:
                app = App.objects.filter(app_name=i.get("app_name"))
                if app.exists():
                    app.app_name = i.get("app_name")
                    app.package_name = i.get('package_name')
                    app.icon_url = i.get('icon_url')
                else:
                    app = App(
                        app_name=i.get("app_name"),
                        package_name=i.get('package_name'),
                        icon_url=i.get('icon_url'),
                    )
                app.save()

                item = Ranked(
                    app_id=app.id,
                    app_name=i.get("app_name"),
                    icon_url=i.get('icon_url'),
                    market_appid=i.get('market_appid'),
                    market=i.get("market_name"),  # "google", "apple", "one"
                    package_name=i.get('package_name'),
                    date=timezone.now().strftime("%Y%m%d"),
                    deal_type=deal.removesuffix("_v2").replace("global", "market"),  # "realtime_rank", "market_rank"
                    app_type=game,  # "game", "app"
                    rank=i.get('rank'),
                    rank_type=i.get('rank_type'),
                )
                item.save()
                if i.get("market_name") == "one":
                    get_one_store_app_download_count(item.market_appid)
                app_name = item.app_name
                if app_name in following_applications:
                    TrackingApps().from_rank(item)
            except IntegrityError:
                pass
            except AttributeError:
                pass


def hourly():
    for deal in ["realtime_rank_v2"]:
        for market in ["all"]:
            for price in ["gross", "paid", "free"]:
                for game in ["app", "game"]:
                    crawl_app_store_rank(deal, market, price, game)


def daily():
    for deal in ["global_rank_v2"]:
        for market in ["all"]:
            for price in ["gross", "paid", "free"]:
                for game in ["app", "game"]:
                    crawl_app_store_rank(deal, market, price, game)


if __name__ == '__main__':
    hourly()
    daily()
