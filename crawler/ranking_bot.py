import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ranker.settings")
import django

if 'setup' in dir(django):
    django.setup()
from django.utils import timezone
from django.db.utils import IntegrityError
from crawler.models import Ranked, Following, TrackingApps, OneStoreDL
import requests

market_type = ["google", "apple", "one"]
deal_type = ["realtime_rank", "market_rank"]
app_type = ["game", "app"]
user_agent = " ".join(
    ["Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
     "AppleWebKit/537.36 (KHTML, like Gecko)",
     "Chrome/98.0.4758.80 Safari/537.36"])
headers = {'origin': 'https://www.mobileindex.com',
           'user-agent': user_agent}


def get_one_store_app_download_count(appid: str):
    one_url = "https://m.onestore.co.kr/mobilepoc/web/apps/appsDetail/spec.omp?prodId=" + appid
    from bs4 import BeautifulSoup
    response = requests.get(one_url).text
    soup = BeautifulSoup(response, "html.parser")
    download = soup.select_one("li:-soup-contains('다운로드수') > span").text
    d_string = soup.select_one("li:-soup-contains('출시일') > span").text
    genre = soup.select_one("li:-soup-contains('장르') > span").text
    volume = soup.select_one("li:-soup-contains('용량') > span").text
    import datetime
    array = [i for i in map(int, d_string.split("."))]
    released = datetime.date(year=array[0], month=array[1], day=array[2])
    d_counts = int(download.replace(",", ""))
    ones_app = OneStoreDL(
        market_appid=appid,
        downloads=d_counts,
        genre=genre,
        volume=volume,
        released=released
    )
    ones_app.save()


def crawl_app_store_rank(store: int, deal: int, game: int):
    url = f'https://proxy-insight.mobileindex.com/chart/{deal_type[deal]}'
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
            market_appid = i.get('market_appid')
            if market_type[store] == "one":
                get_one_store_app_download_count(market_appid)
            item = Ranked(
                date=timezone.now().strftime("%Y%m%d"),
                market=market_type[store],
                deal_type=deal_type[deal],
                app_type=app_type[game],
                rank_type=i.get('rank_type'),
                rank=i.get('rank'),
                icon_url=i.get('icon_url'),
                market_appid=market_appid,
                package_name=i.get('package_name'),
                app_name=i.get("app_name")
            )
            item.save()
            app_name = item.app_name
            if app_name in following_applications:
                TrackingApps().from_rank(item)
        except IntegrityError as e:
            pass
        except AttributeError as e:
            pass


def main():
    for market in range(0, 3):  # "google", "apple", "one"
        for rank in range(0, 2):  # "realtime_rank", "market_rank"
            for app in range(0, 2):  # "game", "app"
                crawl_app_store_rank(market, rank, app)


if __name__ == '__main__':
    main()
