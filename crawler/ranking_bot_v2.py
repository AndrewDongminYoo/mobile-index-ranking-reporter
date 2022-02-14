import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ranker.settings")
import django

if 'setup' in dir(django):
    django.setup()
from django.utils import timezone
from django.db.utils import IntegrityError
from crawler.models import Ranked, Following, TrackingApps, OneStoreDL
import requests

user_agent = " ".join(
    ["Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
     "AppleWebKit/537.36 (KHTML, like Gecko)",
     "Chrome/98.0.4758.80 Safari/537.36"])
headers = {'origin': 'https://www.mobileindex.com',
           'user-agent': user_agent}


def get_soup(appid, back=True):
    one_url = "https://m.onestore.co.kr/mobilepoc/web/apps/appsDetail/spec.omp?prodId=" + appid \
        if back else "https://m.onestore.co.kr/mobilepoc/apps/appsDetail.omp?prodId=" + appid
    from bs4 import BeautifulSoup
    response = requests.get(one_url).text
    return BeautifulSoup(response, "html.parser")


def get_one_store_app_download_count(appid: str):
    soup = get_soup(appid, True)
    download = soup.select_one("li:-soup-contains('다운로드수') > span").text
    d_string = soup.select_one("li:-soup-contains('출시일') > span").text
    genre = soup.select_one("li:-soup-contains('장르') > span").text
    volume = soup.select_one("li:-soup-contains('용량') > span").text
    style = soup.select_one("#header > div > div > div.header-co-right > span").get('style')
    icon_url = style.removeprefix("background-image:url(").removesuffix(")")

    soup2 = get_soup(appid, False)
    app_name = soup2.title.get_text().removesuffix(" - 원스토어")
    print(app_name)

    import datetime
    array = [i for i in map(int, d_string.split("."))]
    released = datetime.date(year=array[0], month=array[1], day=array[2])
    d_counts = int(download.replace(",", ""))
    ones_app = OneStoreDL(
        market_appid=appid,
        downloads=d_counts,
        genre=genre,
        volume=volume,
        released=released,
        icon_url=icon_url,
        app_name=app_name,
    )
    ones_app.save()


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
                item = Ranked(
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