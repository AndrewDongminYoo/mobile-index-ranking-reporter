# -*- coding: utf-8 -*-
from ninja import NinjaAPI
from datetime import timedelta
from django.utils import timezone
from crawler.models import Following
from django.db import DataError, IntegrityError

api = NinjaAPI(title="Application", urls_namespace="cron")


@api.post("/")
def internal_cron(request):
    for app in Following.objects.filter(is_active=True, expire_date__lt=timezone.now()):
        app.is_active = False
        app.save()
        return "OK"
    adv_info = request.POST
    market_appid = adv_info.get("market_appid")
    address = adv_info.get("address")
    appname = adv_info.get("appname")
    os_type = adv_info.get("os_type")
    import re
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
            expire_date=timezone.now() + timedelta(days=7)
        )
        following.save()
        print(following)
