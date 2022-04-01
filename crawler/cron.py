import requests


def ive_korea_internal_api():
    url = "http://13.125.164.253/cron/update/following"
    requests.post(url)


def following_one_crawl():
    url = "http://13.125.164.253/v2/follow/list"
    res = requests.get(url).json()["items"]
    url = "http://13.125.164.253/cron/new/downloads"
    for obj in res:
        market_appid = obj["market_appid"]
        requests.post(url, data={"market_appid": market_appid})


def crawl_app_store_hourly():
    url = "http://13.125.164.253/cron/new/ranking"
    requests.post(url, data={"market": "all"})
    url = "http://13.125.164.253/cron/new/ranking/high"
    requests.post(url)


def crawl_app_store_daily():
    url = "http://13.125.164.253/cron/new/ranking"
    requests.post(url, data={"market": "one"})


if __name__ == '__main__':
    crawl_app_store_hourly()
