# -*- coding: utf-8 -*-
import json
import re
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Min
from ninja import NinjaAPI
from ninja.orm import create_schema
from datetime import timedelta
from pytz import timezone
from datetime import datetime
from crawler.models import Following, App, TimeIndex, OneStoreDL, Ranked, TrackingApps
from crawler.utils import post_to_slack, get_date, create_app
from crawler.utils import get_data_from_soup, crawl_app_store_rank

KST = timezone('Asia/Seoul')
today = datetime.now().astimezone(tz=KST)
api = NinjaAPI(title="Application", urls_namespace="cron")
ApplicationSchema = create_schema(App)
FollowingSchema = create_schema(Following)
TimeIndexSchema = create_schema(TimeIndex)
OneStoreDLSchema = create_schema(OneStoreDL)
RankedSchema = create_schema(Ranked)


@api.post("/new/following", response=FollowingSchema)
def internal_cron(request: WSGIRequest):
    post_data = request.POST
    for app in Following.objects.filter(is_following=True, expire_date__lt=today):
        app.is_following = False
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
    expire_date = today + timedelta(days=3)
    if following:
        following.is_following = True
        following.expire_date = expire_date
        following.save()
    elif appname and market and market_appid:
        following = Following(
            app_name=appname,
            market_appid=market_appid,
            market=market,
            is_following=True,
            expire_date=expire_date
        )
        following.save()
        print(following)
    return following if following else None


@api.post("/new/date", response=TimeIndexSchema)
def what_date(request: WSGIRequest):
    date_data = request.POST["date"]
    return TimeIndex.objects.get_or_create(date=date_data)[0]


@api.post("/new/downloads", response=OneStoreDLSchema)
def get_one_store_information(market_appid) -> OneStoreDL:
    date_id = get_date()
    app = App.objects.get(market_appid=market_appid)
    genre, volume, icon_url, app_name, released, download = get_data_from_soup(market_appid)
    last_one = OneStoreDL.objects.filter(
        market_appid=market_appid,
        app=app,
    ).last()
    ones_app = OneStoreDL(
        market_appid=market_appid,
        app=app,
        date_id=date_id,
        genre=genre,
        volume=volume,
        downloads=download,
        released=released,
        icon_url=icon_url,
        app_name=app_name,
    )
    ones_app.save()
    rank_diff = ones_app.downloads - last_one.downloads if last_one else 0
    if rank_diff > 2000:
        msg = f"{app_name} 앱 다운로드가 전일 대비 {format(rank_diff, ',')}건 증가했습니다.✈ " \
              + f"`{format(last_one.downloads, ',')}건` -> `{format(ones_app.downloads, ',')}건`"
        post_to_slack(msg)
    return ones_app


@api.post("/new/ranking")
def ranking_crawl(request: WSGIRequest):
    post_data = request.POST
    if post_data["market"] == "one":
        crawl_app_store_rank("global_rank_v2", "one", "game")
        crawl_app_store_rank("global_rank_v2", "one", "app")
    else:
        crawl_app_store_rank("realtime_rank_v2", "all", "game")
        crawl_app_store_rank("realtime_rank_v2", "all", "app")


@api.post("/new/ranking/app", response=RankedSchema)
def new_ranking_app_from_data(request: WSGIRequest, market, game, term):
    app_data = request.POST
    date_id = get_date()
    following = [f.market_appid for f in Following.objects.filter(is_following=True)]
    app = create_app(app_data)
    market_name = app_data["market_name"]
    if not (market == "one" and market_name in ["apple", "google"]):
        item = Ranked(
            app=app,
            date_id=date_id,
            app_type=game,  # "game", "app"
            app_name=app.app_name,
            icon_url=app.icon_url,
            market_appid=app.market_appid,
            rank=app_data.get('rank'),
            market=market_name,  # "google", "apple", "one"
            chart_type=app_data.get('rank_type'),
            deal_type=term.replace("_v2", "").replace("global", "market"),  # "realtime_rank", "market_rank"
        )
        item.save()
        if item.market_appid in following:
            last = TrackingApps.objects.filter(
                market_appid=item.market_appid,
                market=item.market,
                chart_type=item.chart_type,
                app_name=item.app_name,
            ).last()
            tracking = TrackingApps(
                following=Following.objects.get(market_appid=item.market_appid),
                app_id=app.id,
                date_id=date_id,
                deal_type=item.deal_type,
                rank=item.rank,
                market=item.market,
                app_name=item.app_name,
                icon_url=item.icon_url,
                chart_type=item.chart_type,
                market_appid=app.market_appid,
            )
            tracking.save()
            rank_diff = int(tracking.rank) - int(last.rank) if last else 0
            market_str = item.get_market_display()
            if rank_diff <= -1:
                post_to_slack(f" 순위 상승🚀: {item.app_name} {market_str} `{last.rank}위` → `{item.rank}위`")
            if rank_diff >= 1:
                post_to_slack(f" 순위 하락🛬: {item.app_name} {market_str} `{last.rank}위` → `{item.rank}위`")
        return item


@api.post("/new/ranking/high")
def get_highest_rank_of_realtime_ranks_today(request) -> None:
    date_today = get_date(today.strftime("%Y%m%d") + "2300")
    rank_set = Ranked.objects \
        .filter(created_at__gte=today - timedelta(days=1),
                created_at__lte=today,
                market__in=["apple", "google"],
                deal_type="realtime_rank")
    for following in Following.objects.filter(is_following=True, market__in=["apple", "google"]).all():
        market_appid = following.market_appid
        query = rank_set.filter(market_appid=market_appid) \
            .values('market_appid', 'app_name', 'market', 'app_type', 'chart_type', 'icon_url') \
            .annotate(highest_rank=Min('rank'))
        if query:
            first = query[0]
            new_app = TrackingApps.objects.update_or_create(
                market=first.get('market'),
                chart_type=first.get('chart_type'),
                app_name=first.get('app_name'),
                icon_url=first.get('icon_url'),
                deal_type='market_rank',
                market_appid=market_appid,
                app=App.objects.get(market_appid=market_appid),
                following=following,
                date=date_today,
            )[0]
            new_app.rank = first.get('highest_rank')
            new_app.save()
