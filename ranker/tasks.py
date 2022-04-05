import os
import requests
from celery import Celery
from celery.schedules import crontab
from django_celery_beat.models import PeriodicTask

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ranker.settings')
app = Celery('ranker', broker="redis://localhost:6379/0")
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):

    sender.add_periodic_task(
        crontab(minute=0),
        crawl_app_store_hourly.s(),
        name="crawl app store hourly"
    )

    sender.add_periodic_task(
        crontab(minute=10, hour=0),
        crawl_app_store_daily.s(),
        name="crawl app store daily"
    )

    sender.add_periodic_task(
        crontab(minute="*/15"),
        ive_korea_internal_api.s(),
        name="ive korea internal api"
    )

    sender.add_periodic_task(
        crontab(minute=10, hour=12),
        following_one_crawl.s(),
        name="following one crawl"
    )


@app.task
def ive_korea_internal_api():
    url = "http://13.125.164.253/cron/update/following"
    requests.post(url)


@app.task
def following_one_crawl():
    url = "http://13.125.164.253/v2/follow/list"
    res = requests.get(url).json()
    url = "http://13.125.164.253/cron/new/downloads"
    for obj in res["items"]:
        market_appid = obj["market_appid"]
        if obj["market"] == "one":
            print(market_appid)
            requests.post(url, data={"market_appid": market_appid})


@app.task
def crawl_app_store_hourly():
    url = "http://13.125.164.253/cron/new/ranking"
    requests.post(url, data={"market": "all"})
    url = "http://13.125.164.253/cron/new/ranking/high"
    requests.post(url)


@app.task
def crawl_app_store_daily():
    url = "http://13.125.164.253/cron/new/ranking"
    requests.post(url, data={"market": "one"})


app.conf.beat_schedule = {
    "crawl app store hourly": {
        "task": "tasks.crawl_app_store_hourly",
        "schedule": crontab(minute=0),
        "args": (),
    },

    "crawl app store daily": {
        "task": "tasks.crawl_app_store_daily",
        "schedule": crontab(minute=10, hour=0),
        "args": (),
    },

    "ive korea internal api": {
        "task": "tasks.ive_korea_internal_api",
        "schedule": crontab(minute="*/15"),
        "args": (),
    },

    "following one crawl": {
        "task": "tasks.following_one_crawl",
        "schedule": crontab(minute=10, hour=12),
        "args": (),
    }
}
