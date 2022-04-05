import requests
from logging import getLogger

logger = getLogger(__name__)


def ive_korea_internal_api():
    try:
        url = "http://13.125.164.253/cron/update/following"
        requests.post(url)
    except Exception as e:
        logger.info(e)
        ive_korea_internal_api()


def following_one_crawl():
    url = "http://13.125.164.253/v2/follow/list"
    res = requests.get(url).json()
    url = "http://13.125.164.253/cron/new/downloads"
    for obj in res["items"]:
        try:
            market_appid = obj["market_appid"]
            if obj["market"] == "one":
                print(market_appid)
                requests.post(url, data={"market_appid": market_appid})
        except Exception as e:
            logger.info(e)
            following_one_crawl()


def crawl_app_store_hourly():
    try:
        url = "http://13.125.164.253/cron/new/ranking"
        requests.post(url, data={"market": "all"})
        url = "http://13.125.164.253/cron/new/ranking/high"
        requests.post(url)
    except Exception as e:
        logger.info(e)
        crawl_app_store_hourly()


def crawl_app_store_daily():
    try:
        url = "http://13.125.164.253/cron/new/ranking"
        requests.post(url, data={"market": "one"})
    except Exception as e:
        logger.info(e)
        crawl_app_store_daily()


if __name__ == '__main__':
    following_one_crawl()
