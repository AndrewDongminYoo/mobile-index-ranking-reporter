from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import render, redirect
from crawler.models import TrackingApps, Following, App


def index(request: WSGIRequest):
    if not request.user.is_superuser:
        return redirect("/admin")
    return render(request, "index.html")


def rank(request: WSGIRequest, following_id: int):
    following = Following.objects.get(id=following_id)
    package_name = following.market_appid
    tracked = TrackingApps.objects.order_by("-created_at").filter(following=following)
    if request.user.is_superuser and tracked.exists():
        app = tracked.select_related("app__app_info").last().app
    else:
        app = App.objects.get(market_appid=following.market_appid)
    return render(request, "rank.html", {"following": following, "app": app, "package_name": package_name})


def redirect_to_rank(request: WSGIRequest):
    package_name: str = request.GET.get('pkg')
    market_name: str = request.GET.get('mkt')
    if package_name and market_name:
        following = Following.objects.filter(market_appid=package_name, market=market_name).first()
        return redirect("/statistic/{}".format(following.id))
