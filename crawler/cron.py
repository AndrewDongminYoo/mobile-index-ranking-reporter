import requests

from crawler.utils import get_highest_rank_of_realtime_ranks_today
from crawler.utils import crawl_app_store_rank


def following_one_crawl():
    url = "http://13.125.164.253/v2/follow/list"
    res = requests.get(url).json()
    for obj in res["items"]:
        market_appid = obj["market_appid"]
        if obj["market"] == "one":
            print(market_appid)
            url = "http://13.125.164.253/cron/new/downloads"
            requests.post(url, data={"market_appid": market_appid})


def crawl_app_store_hourly():
    crawl_app_store_rank("realtime_rank_v2", "all", "game")
    crawl_app_store_rank("realtime_rank_v2", "all", "app")

    get_highest_rank_of_realtime_ranks_today()


def crawl_app_store_daily():
    crawl_app_store_rank("global_rank_v2", "one", "game")
    crawl_app_store_rank("global_rank_v2", "one", "app")


if __name__ == '__main__':
    crawl_app_store_hourly()
