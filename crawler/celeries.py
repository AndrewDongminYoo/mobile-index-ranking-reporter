# -*- coding: utf-8 -*-
import os
import sys
from kombu.utils import encoding

sys.modules['celery.utils.encoding'] = encoding
os.environ.setdefault("PYTHON" + "UNBUFFERED", "1")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ranker.settings")

from celery import Celery

app = Celery('tasks', broker='redis://localhost:6379/0')
app.config_from_object('', namespace='CELERY')
app.autodiscover_tasks()

import django

django.setup()

import pytz
from django_celery_beat.models import CrontabSchedule, PeriodicTask

every_o_clock, _ = CrontabSchedule.objects.get_or_create(
    minute='0',
    hour='*',
    day_of_week='*',
    day_of_month='*',
    month_of_year='*',
    timezone=pytz.timezone("Asia/Seoul")
)

every_ten_minutes, _ = CrontabSchedule.objects.get_or_create(
    minute='*/10',
    hour='*',
    day_of_week='*',
    day_of_month='*',
    month_of_year='*',
    timezone=pytz.timezone("Asia/Seoul")
)

every_night, _ = CrontabSchedule.objects.get_or_create(
    minute='10',
    hour='0',
    day_of_week='*',
    day_of_month='*',
    month_of_year='*',
    timezone=pytz.timezone("Asia/Seoul")
)

every_lunch_time, _ = CrontabSchedule.objects.get_or_create(
    minute='10',
    hour='12',
    day_of_week='*',
    day_of_month='*',
    month_of_year='*',
    timezone=pytz.timezone("Asia/Seoul")
)

task1, _ = PeriodicTask.objects.get_or_create(
    name='crawling_every_o_clock',
    task='crawler.cron.crawl_app_store_hourly',
    crontab=every_o_clock,
    enabled=True
)

task2, _ = PeriodicTask.objects.get_or_create(
    name='every_ten_minutes',
    task='crawler.cron.ive_korea_internal_api',
    crontab=every_ten_minutes,
    enabled=True
)

task3, _ = PeriodicTask.objects.get_or_create(
    name='every_lunch_time',
    task='crawler.cron.following_one_crawl',
    crontab=every_lunch_time,
    enabled=True
)

task4, _ = PeriodicTask.objects.get_or_create(
    name='every_night',
    task='crawler.cron.crawl_app_store_daily',
    crontab=every_night,
    enabled=True
)
