# -*- coding: utf-8 -*-
import datetime
import re
from django.core.handlers.wsgi import WSGIRequest
from ninja import NinjaAPI
from ninja.orm import create_schema
from datetime import timedelta
from django.utils import timezone
from crawler.models import Following, App, TimeIndex

api = NinjaAPI(title="Application", urls_namespace="cron")
ApplicationSchema = create_schema(App)
FollowingSchema = create_schema(Following)
TimeIndexSchema = create_schema(TimeIndex)


@api.post("/new/following", response=FollowingSchema)
def internal_cron(request: WSGIRequest):
    post_data = request.POST
    for app in Following.objects.filter(is_active=True, expire_date__lt=timezone.now()):
        app.is_active = False
        app.save()
    market_appid = post_data.get("market_appid")
    address = post_data.get("address")
    appname = post_data.get("appname")
    os_type = post_data.get("os_type")
    google = re.compile(r'^\w+(\.\w+)+$')
    apple = re.compile(r'^\d{9,11}$')
    one = re.compile(r'^0000\d{5,6}$')
    market = ""
    if google.fullmatch(market_appid) and os_type == "2":
        market = "google"
    elif one.fullmatch(market_appid) and os_type == "3":
        market = "one"
    elif apple.fullmatch(market_appid) and os_type == "1":
        market = "apple"
    else:
        market_appID = re.findall(r'\d{9,11}$', address)
        if market_appID:
            market_appid = market_appID[0]
            market = "one" if market_appid.startswith("0000") else "apple"
            print(market_appid)
        elif re.search(r'[a-z]+(\.\w+)+$', address):
            market_appid = re.compile(r'[a-z]+(\.\w+)+$').search(address)[0]
            market = "google"
            print(market_appid)
    following = Following.objects.filter(market=market, market_appid=market_appid).first()
    if following:
        following.is_active = True
        following.expire_date = timezone.now() + timedelta(days=7)
        following.save()
    elif appname and market and market_appid:
        following = Following(
            app_name=appname,
            market_appid=market_appid,
            market=market,
            is_active=True,
            expire_date=timezone.now() + timedelta(days=6)
        )
        following.save()
        print(following)
    return following if following else None


@api.post("/new/app", response=ApplicationSchema)
def create_app_and_return(request: WSGIRequest):
    app_data = request.POST
    app = App.objects.get_or_create(market_appid=app_data['market_appid'])[0]
    app.app_name = app_data.get('app_name')
    app.icon_url = app_data.get('icon_url')
    if app.app_info:
        app.app_info.publisher_name = app_data.get('publisher_name')
    if app.market_appid.startswith("0000"):
        app.market = "one"
        app.app_url = "https://m.onestore.co.kr/mobilepoc/apps/appsDetail.omp?prodId=" + app.market_appid
    elif app.market_appid[0].isalpha():
        app.market = "google"
        app.app_url = "https://play.google.com/store/apps/details?id=" + app.market_appid
    else:
        app.market = "apple"
        app.app_url = "https://apps.apple.com/kr/app/id" + app.market_appid
    app.save()
    print(app.market_appid, app.app_name)
    return app


@api.post("/new/date", response=TimeIndexSchema)
def what_date(request: WSGIRequest):
    date_data = request.POST["date"]
    return TimeIndex.objects.get_or_create(date=date_data)[0]
