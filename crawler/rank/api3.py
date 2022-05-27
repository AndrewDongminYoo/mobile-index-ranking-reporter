# -*- coding: utf-8 -*-
import re
from datetime import datetime
from datetime import timedelta

from django.core.handlers.wsgi import WSGIRequest
from django.http import QueryDict
from ninja import NinjaAPI, Schema
from ninja.orm import create_schema
from pytz import timezone

from crawler.models import Following, App, TimeIndex, OneStoreDL, Ranked, TrackingApps
from crawler.utils import get_data_from_soup, create_app
from crawler.utils import post_to_slack, get_date

KST = timezone('Asia/Seoul')
api = NinjaAPI(title="Application", urls_namespace="cron")
ApplicationSchema = create_schema(App)
FollowingSchema = create_schema(Following)
TimeIndexSchema = create_schema(TimeIndex)
OneStoreDLSchema = create_schema(OneStoreDL)
RankedSchema = create_schema(Ranked)


class EmptySchema(Schema):
    pass


@api.post("/new/following", response={200: FollowingSchema, 204: EmptySchema})
def internal_cron(request: WSGIRequest):
    post_data = request.POST
    mkt_app = post_data.get("market_appid")
    address = post_data.get("address")
    appname = post_data.get("appname")
    os_type = post_data.get("os_type")
    icon_url = post_data.get("icon_url")
    GOOGLE = re.compile(r'^\w+(\.\w+)+$')
    APPLES = re.compile(r'^\d{9,11}$')
    ONESTO = re.compile(r'^0000\d{5,6}$')
    market = ""
    if GOOGLE.fullmatch(mkt_app) and os_type == "2":
        market = "google"
    elif ONESTO.fullmatch(mkt_app) and os_type == "3":
        market = "one"
    elif APPLES.fullmatch(mkt_app) and os_type == "1":
        market = "apple"
    else:
        extract_appid = re.findall(r'\d{9,11}$', address)
        if extract_appid:
            mkt_app = extract_appid[0]
            market = "one" if mkt_app.startswith("0000") else "apple"
            print(mkt_app)
        elif re.search(r'[a-z]+(\.\w+)+$', address):
            mkt_app = re.compile(r'[a-z]+(\.\w+)+$').search(address)[0]
            market = "google"
            print(mkt_app)
    following = Following.objects.filter(market=market, market_appid=mkt_app).first()
    expire_date = datetime.now().astimezone(tz=KST) + timedelta(days=5)
    if following:
        following.expire_date = expire_date
        following.save()
        return 200, following
    elif appname and market and mkt_app:
        following = Following(
            market=market,
            app_name=appname,
            market_appid=mkt_app,
            expire_date=expire_date,
            icon_url=icon_url,
        )
        following.save()
        print(following)
        return 200, following
    else:
        return 204, ""


@api.post("/new/date", response=TimeIndexSchema)
def what_date(request: WSGIRequest):
    date_data = request.POST["date"]
    return TimeIndex.objects.get_or_create(date=date_data)[0]


@api.post("/new/downloads", response=OneStoreDLSchema)
def get_one_store_information(request: WSGIRequest) -> OneStoreDL:
    market_appid = request.POST["market_appid"]
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
        genre=genre,
        volume=volume,
        date_id=date_id,
        icon_url=icon_url,
        released=released,
        app_name=app_name,
        downloads=download,
    )
    ones_app.save()
    following = Following.objects.get(market_appid=market_appid)
    following.icon_url = icon_url
    following.app_name = app_name
    following.save()
    rank_diff = ones_app.downloads - last_one.downloads if last_one else 0
    if rank_diff > 2000:
        msg = f"원스토어 {app_name} 앱 다운로드가 전일 대비 {format(rank_diff, ',')}건 증가했습니다.✈ " \
              + f"`{format(last_one.downloads, ',')}건` -> `{format(ones_app.downloads, ',')}건`"
        post_to_slack(text=msg, following=following.id)
    return ones_app


@api.post("/new/ranking/app", response=RankedSchema)
def new_ranking_app_from_data(request: WSGIRequest, market, game, term):
    market_app_list = [f.market_appid for f in Following.objects.filter(is_following=True)]
    following_app_list = [f.market_appid for f in
                          Following.objects.filter(expire_date__gte=datetime.now().astimezone(tz=KST))]
    app_data: QueryDict = request.POST
    date_id: int = get_date()
    app: App = create_app(app_data)
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
        if item.market_appid in following_app_list:
            last = TrackingApps.objects.filter(
                market_appid=item.market_appid,
                market=item.market,
                chart_type=item.chart_type,
                app_name=item.app_name,
            ).last()
            following_app = Following.objects.get(market_appid=item.market_appid)
            tracking = TrackingApps(
                following=following_app,
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
            market_str = item.get_market_display()
            LIVE = "*LIVE*" if item.market_appid in market_app_list else ""
            text = ""
            if not last:
                text = f" 순위 진입! {LIVE}🤔 {item.app_name} {market_str} `{item.rank}위`"
                # TODO : 순위가 n위 내 일 때만 알림?
            else:
                if int(tracking.rank) < int(last.rank):
                    text = f" 순위 상승 {LIVE}🚀 {item.app_name} {market_str} `{last.rank}위` → `{item.rank}위`"
                if int(tracking.rank) > int(last.rank):
                    text = f" 순위 하락 {LIVE}🛬 {item.app_name} {market_str} `{last.rank}위` → `{item.rank}위`"
            post_to_slack(text=text, following=following_app.id) if text else None
        return item
