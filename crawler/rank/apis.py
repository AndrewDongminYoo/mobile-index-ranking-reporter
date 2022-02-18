from datetime import timedelta
from typing import List

from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ninja import NinjaAPI
from ninja.orm import create_schema
from ninja.pagination import paginate, LimitOffsetPagination

from crawler.models import Ranked, Following, TrackingApps, OneStoreDL, TimeIndex, App
from crawler.ranking_bot_v2 import daily

api = NinjaAPI(title="Ninja")

RankedSchema = create_schema(Ranked)
ApplicationSchema = create_schema(App)
FollowingSchema = create_schema(Following)
OneStoreSchema = create_schema(OneStoreDL)
TrackingSchema = create_schema(TrackingApps)


# following "GET"
@api.get("/following", response=List[TrackingSchema], tags=["Tracking Apps"])
@paginate(LimitOffsetPagination)
def list_tracking(request: WSGIRequest, sort="created_at", reverse=True):
    """
    ## parameters:
    - request: WSGIRequest
    - sort: "id", "created_at", "deal_type", "app_name", "icon_url", "market_appid", "package_name", "rank"
    - reverse: reversed or not
    """
    print(request.GET)
    if reverse:
        return TrackingApps.objects.order_by(sort).reverse().all()
    return TrackingApps.objects.order_by(sort).all()


# following "DELETE"
@api.delete("/following/{record_id}", tags=["Tracking Apps"])
def dedupe_or_remove(request: WSGIRequest, record_id: int):
    find = TrackingApps.objects.filter(id=record_id)
    if find.exists():
        find.delete()
        return api.create_response(request, {"success": True})
    return api.create_response(request, {"success": False})


# ranking "GET"
@api.get("/ranking", response=List[RankedSchema], tags=["ranking"])
@paginate(LimitOffsetPagination)
def get_ranked_list(request: WSGIRequest,
                    store="google",
                    rtype="free",
                    deal="market",
                    game="app",
                    sort="created_at",
                    reverse=True):
    """
    ## parameters:
    - request: WSGIRequest
    - store: apple, google, one-store
    - rtype: gross, free, paid
    - deal: **realtime**_rank, **market**_rank(daily)
    - game: game or app
    - sort: "id", "created_at", "deal_type", "app_name", "icon_url", "market_appid", "package_name", "rank"
    - reverse: reversed or not
    """
    print(request.GET)
    query_set = Ranked.objects \
        .filter(rank_type__startswith=rtype) \
        .filter(market__startswith=store) \
        .filter(deal_type__startswith=deal) \
        .filter(app_type=game)
    timestamps = min([ts.id for ts in TimeIndex.objects.filter(date=query_set.last().date)])
    query_set = query_set.filter(date_id__gte=timestamps)
    if reverse:
        return query_set.order_by(sort).reverse().all()
    return query_set.order_by(sort).all()


# one "POST"
@api.post("/ranking", response=List[ApplicationSchema], tags=["ranking"])
@paginate(LimitOffsetPagination)
def find_app_with_query(request: WSGIRequest, query):
    print(request.POST)
    query_set = App.objects.filter(Q(app_name__icontains=query) | Q(package_name__icontains=query))
    return query_set.order_by("app_name").all()


# follow "POST"
@api.post("/follow", response=FollowingSchema, tags=["ranking"])
def add_following_app_and_search(request: WSGIRequest,
                                 app_name):
    print(request.POST)
    ranked_app = Ranked.objects.filter(app_name=app_name).order_by("-created_at").first()
    try:
        tracking = TrackingApps(
            app=ranked_app.app,
            deal_type=ranked_app.deal_type,
            market=ranked_app.market,
            rank_type=ranked_app.rank_type,
            app_name=app_name,
            icon_url=ranked_app.app.icon_url,
            package_name=ranked_app.app.package_name,
            rank=ranked_app.rank,
            date_id=ranked_app.date_id,
        )
        tracking.save()
    except AttributeError:
        pass
    exists_app = Following.objects.filter(app_name=app_name)
    if exists_app.exists():
        return exists_app.first()
    instance = Following(app_name=app_name)
    return instance.save()


# follow "GET"
@api.get("/follow", response=List[FollowingSchema], tags=["ranking"])
@paginate(LimitOffsetPagination)
def view_following(request: WSGIRequest,
                   sort="created_at",
                   reverse=True):
    """
    ## parameters:
    - request: WSGIRequest
    - sort: "id", "created_at", "deal_type", "app_name", "icon_url", "market_appid", "package_name", "rank"
    - reverse: reversed or not
    """
    print(request.GET)
    if reverse:
        return Following.objects.order_by(sort).reverse().all()
    return Following.objects.order_by(sort).all()


# follow "DELETE"
@api.delete("/follow/{following_id}", tags=["ranking"])
def delete_following(request: WSGIRequest,
                     following_id: int):
    print(request.META)
    following = get_object_or_404(Following, id=following_id)
    following.delete()
    return api.create_response(request, {"success": True})


# one "GET"
@api.get("/one", response=List[OneStoreSchema], tags=["one-store"])
@paginate(LimitOffsetPagination)
def get_download_counts_from_apps(request: WSGIRequest,
                                  sort="created_at",
                                  reverse=True):
    """
    ## parameters:
    - request: WSGIRequest
    - sort: "id", "created_at", "deal_type", "app_name", "icon_url", "market_appid", "package_name", "rank"
    - reverse: reversed or not
    """
    print(request.GET)
    query_set = OneStoreDL.objects.filter(created_at__gte=timezone.now() - timedelta(days=2)).order_by(sort)
    if reverse:
        return query_set.reverse()
    return query_set.all()


# one "POST"
@api.post("/one", response=List[OneStoreSchema], tags=["one-store"])
@paginate(LimitOffsetPagination)
def find_download_counts_of_app_with_name(request: WSGIRequest,
                                          query,
                                          sort="downloads",
                                          reverse=True):
    """
    ## parameters:
    - request: WSGIRequest
    - sort: "id", "created_at", "deal_type", "app_name", "icon_url", "market_appid", "package_name", "rank"
    - reverse: reversed or not
    """
    print(request.POST)
    query_set = OneStoreDL.objects.filter(app_name__contains=query).order_by(sort)
    if reverse:
        return query_set.reverse()
    return query_set.all()


# one "GET"
@api.get("/one/{market_appid}", response=List[OneStoreSchema], tags=["one-store"])
@paginate(LimitOffsetPagination)
def get_download_counts_from_one_app(request: WSGIRequest,
                                     market_appid: str,
                                     sort="created_at",
                                     reverse=True):
    """
    ## parameters:
    - request: WSGIRequest
    - sort: "id", "created_at", "deal_type", "app_name", "icon_url", "market_appid", "package_name", "rank"
    - reverse: reversed or not
    - market_appid:
    """
    print(request.GET)
    query_set = OneStoreDL.objects.filter(market_appid=market_appid).order_by(sort)
    if reverse:
        return query_set.reverse()
    return query_set.all()


# crawler "POST"
@api.post("/crawl", tags=["crawling"])
def forced_crawling(request: WSGIRequest):
    daily()
    return api.create_response(request, {"success": True})
