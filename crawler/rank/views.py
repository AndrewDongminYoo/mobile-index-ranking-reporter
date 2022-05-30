import re

import requests
from django.core.handlers.wsgi import WSGIRequest
from django.db import DataError
from django.shortcuts import render, redirect
from crawler.models import TrackingApps, Following, App
from crawler.utils import unquote_url

app_pattern = r"([a-z]+\.[a-z]+\.[a-z]+|\d{10,11})"


def index(request: WSGIRequest):
    if not request.user.is_superuser:
        return redirect("/admin")
    return render(request, "index.html")


def rank(request: WSGIRequest, following_id: int):
    following = Following.objects.get(id=following_id)
    package_name = following.market_appid
    tracked = TrackingApps.objects.filter(following=following)
    if request.user.is_superuser and tracked.exists():
        app = tracked.select_related("app__app_info").last().app
    else:
        app = App.objects.get_or_create(market_appid=following.market_appid)[0]
        app.market = following.market
        app.app_name = following.app_name
        app.icon_url = following.icon_url
        app.save()
    return render(request, "rank.html", {"following": following, "app": app, "package_name": package_name})


def redirect_to_rank(request: WSGIRequest):
    market_name: str = request.GET.get('mkt')
    tracker_url: str = unquote_url(request.GET.get('pkg'))
    icon_url: str = unquote_url(request.GET.get('ico'))
    if tracker_url and tracker_url.startswith("http"):
        req = requests.get(
            url=tracker_url,
            headers=request.headers,
            allow_redirects=True
        )
        tracker_url = req.url
    market_appid = re.findall(app_pattern, tracker_url, re.I)
    print(market_appid)
    if market_name and market_appid:
        following = Following.objects.filter(
            market_appid=market_appid.pop(),
            market=market_name,
        ).first()
        if following:
            try:
                following.icon_url = icon_url
                following.save()
            except DataError:
                pass
            return redirect("/statistic/{}".format(following.id))
    return render(request, "index.html")


def privacy(request: WSGIRequest):
    return render(request, "privacy.html")
