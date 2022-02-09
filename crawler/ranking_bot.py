import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ranker.settings")
import django

django.setup()
from django.utils import timezone
from django.db.utils import IntegrityError
from crawler.models import Ranked, Following, TrackingApps
import requests


def crawl_app_store_rank(store: int, deal: int, game: int):
    market_type = ["google", "apple", "one"]
    deal_type = ["realtime_rank", "market_rank"]
    app_type = ["game", "app"]
    user_agent = " ".join(
        ["Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
         "AppleWebKit/537.36 (KHTML, like Gecko)",
         "Chrome/98.0.4758.80 Safari/537.36"])
    url = f'https://proxy-insight.mobileindex.com/chart/{deal_type[deal]}'
    headers = {'origin': 'https://www.mobileindex.com',
               'user-agent': user_agent}
    data = {
        "market": market_type[store],
        "appType": app_type[game],
        "dateType": "d",
        "date": timezone.now().strftime("%Y%m%d"),
        "startRank": 0,
        "endRank": 200,
    }

    req = requests.post(url, data=data, headers=headers)
    obj = req.json()
    print(obj.items())
    following_applications = [f[0] for f in Following.objects.values_list("app_name")]
    for i in obj["data"]:
        try:
            item = Ranked(
                date=timezone.now().strftime("%Y%m%d"),
                market=market_type[store],
                deal_type=deal_type[deal],
                app_type=app_type[game],
                rank_type=i.get('rank_type'),
                rank=i.get('rank'),
                icon_url=i.get('icon_url'),
                market_appid=i.get('market_appid'),
                package_name=i.get('package_name'),
                app_name=i.get("app_name")
            )
            item.save()
            app_name = item.app_name
            if app_name in following_applications:
                TrackingApps().from_rank(item)
        except IntegrityError as e:
            print("IntegrityError")
        except AttributeError as e:
            print("AttributeError")


def main():
    for market in range(0, 3):  # "google", "apple", "one"
        for rank in range(0, 2):  # "realtime_rank", "market_rank"
            for app in range(0, 2):  # "game", "app"
                crawl_app_store_rank(market, rank, app)


if __name__ == '__main__':
    main()
