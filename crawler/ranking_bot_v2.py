import os

from django.db import IntegrityError

from ranker.utils.slack import post_to_slack

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ranker.settings")
import django

if 'setup' in dir(django):
    django.setup()
from django.utils import timezone
from datetime import timedelta
import requests
from crawler.models import Ranked, Following, TrackingApps, App, TimeIndex
from crawler.ranking_bot import get_one_store_app_download_count

user_agent = " ".join(
    ["Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
     "AppleWebKit/537.36 (KHTML, like Gecko)",
     "Chrome/98.0.4758.80 Safari/537.36"])
headers = {'origin': 'https://www.mobileindex.com',
           'user-agent': user_agent}


def crawl_app_store_rank(deal: str, market: str, price: str, game: str):
    """
    param deal: "realtime_rank_v2", "global_rank_v2"
    param market: "all", "google"(global)
    param price: "gross", "paid", "free"
    param game: "app", "game"
    return: Ranked
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
    if obj["status"]:
        print(obj.items())
        date = TimeIndex.objects.get_or_create(date=timezone.now().strftime("%Y%m%d%H%M"))[0]
        for app_data in obj["data"]:
            try:
                query = App.objects.filter(app_name__icontains=app_data.get("app_name"))
                package_name = app_data.get("market_appid")
                if query.exists():
                    app = query.first()
                    if package_name:
                        app.package_name = package_name
                        app.save()
                else:
                    app = App(
                        app_name=app_data.get("app_name"),
                        package_name=package_name or "com.example.app",
                        icon_url=app_data.get('icon_url'),
                    )
                    app.save()

                item = Ranked(
                    app_id=app.id,
                    app_name=app.app_name,
                    icon_url=app.icon_url,
                    date_id=date.id,
                    package_name=app.package_name,
                    market_appid=app_data.get('market_appid'),
                    market=app_data.get("market_name"),  # "google", "apple", "one"
                    deal_type=deal.removesuffix("_v2").replace("global", "market"),  # "realtime_rank", "market_rank"
                    app_type=game,  # "game", "app"
                    rank=app_data.get('rank'),
                    rank_type=app_data.get('rank_type'),
                )
                item.save()

            except IntegrityError:
                pass
            except AttributeError:
                pass


def tracking_rank_flushing():
    following_applications = [f[0] for f in Following.objects.values_list("app_name")]
    yesterday = timezone.now() - timedelta(days=3)
    for item in Ranked.objects.filter(created_at__gte=yesterday, app_name__in=following_applications):
        app_name = item.app_name
        date_id = item.date_id
        if TrackingApps.objects.filter(app_name=app_name, date_id=date_id).exists():
            pass
        else:
            print(app_name)
            tracking = TrackingApps(
                app=item.app,
                deal_type=item.deal_type,
                market=item.market,
                rank_type=item.rank_type,
                app_name=app_name,
                icon_url=item.app.icon_url,
                package_name=item.app.package_name,
                rank=item.rank,
                date_id=date_id,
            )
            tracking.save()
    weekdays = timezone.now() - timedelta(days=7)
    for old in TrackingApps.objects.filter(created_at__lt=weekdays):
        old.delete()


def following_crawl():
    date = TimeIndex.objects.get_or_create(date=timezone.now().strftime("%Y%m%d%H%M"))[0]
    print(date)
    for obj in Following.objects.filter(is_active=True).all():
        appid = obj.app_id
        app = App.objects.filter(pk=appid).first()
        get_one_store_app_download_count(date, app.package_name, app)


def hourly():
    for deal in ["realtime_rank_v2"]:
        for market in ["all"]:
            for price in ["paid", "free"]:
                for game in ["app", "game"]:
                    crawl_app_store_rank(deal, market, price, game)
    following_crawl()


def daily():
    post_to_slack("일간 크롤링 시작")
    for deal in ["global_rank_v2"]:
        for market in ["all"]:
            for price in ["gross", "paid", "free"]:
                for game in ["app", "game"]:
                    crawl_app_store_rank(deal, market, price, game)
    tracking_rank_flushing()


if __name__ == '__main__':
    # daily()
    # hourly()
    following_crawl()
