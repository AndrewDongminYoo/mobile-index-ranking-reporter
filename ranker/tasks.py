import os
import requests
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ranker.settings')

app = Celery('ranker')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()


@app.task
def add(x, y):
    return x + y


@app.task(ignore_result=True)
def ive_korea_internal_api():
    url = "http://13.125.164.253/cron/update/following"
    requests.post(url)


@app.task(ignore_result=True)
def following_one_crawl():
    url = "http://13.125.164.253/v2/follow/list"
    res = requests.get(url).json()
    url = "http://13.125.164.253/cron/new/downloads"
    for obj in res["items"]:
        market_appid = obj["market_appid"]
        if obj["market"] == "one":
            print(market_appid)
            requests.post(url, data={"market_appid": market_appid})


@app.task(ignore_result=True)
def crawl_app_store_hourly():
    url = "http://13.125.164.253/cron/new/ranking"
    requests.post(url, data={"market": "all"})
    url = "http://13.125.164.253/cron/new/ranking/high"
    requests.post(url)


@app.task(ignore_result=True)
def crawl_app_store_daily():
    url = "http://13.125.164.253/cron/new/ranking"
    requests.post(url, data={"market": "one"})
