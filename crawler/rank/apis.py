from datetime import timedelta
from typing import List

from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ninja import NinjaAPI
from ninja.orm import create_schema
from ninja.pagination import paginate, LimitOffsetPagination

from crawler.models import Ranked, Following, TrackingApps, OneStoreDL

api = NinjaAPI(title="Ninja")

RankedSchema = create_schema(Ranked)
FollowingSchema = create_schema(Following)
TrackingSchema = create_schema(TrackingApps)
OneStoreSchema = create_schema(OneStoreDL)


# following "GET"
@api.get("/following", response=List[TrackingSchema], tags=["Tracking Apps"])
@paginate(LimitOffsetPagination)
def list_tracking(request: WSGIRequest, sort="created_at", reverse=True):
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
def get_ranked_list(request: WSGIRequest, sort="created_at", reverse=True):
    print(request.GET)
    if reverse:
        return Ranked.objects.order_by(sort).reverse().all()
    return Ranked.objects.order_by(sort).all()


# follow "POST"
@api.post("/follow", response=FollowingSchema, tags=["ranking"])
def add_following_app_and_search(request: WSGIRequest, app_name):
    print(request.POST)
    ranked_app = Ranked.objects.filter(app_name=app_name).order_by("-created_at").first()
    try:
        TrackingApps().from_rank(ranked_app)
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
def create_following(request: WSGIRequest, sort="created_at", reverse=True):
    print(request.GET)
    if reverse:
        return Following.objects.order_by(sort).reverse().all()
    return Following.objects.order_by(sort).all()


# follow "DELETE"
@api.delete("/follow/{following_id}", tags=["ranking"])
def delete_following(request: WSGIRequest, following_id: int):
    print(request.META)
    following = get_object_or_404(Following, id=following_id)
    following.delete()
    return api.create_response(request, {"success": True})


# one "GET"
@api.get("/one", response=List[OneStoreSchema], tags=["one-store"])
@paginate(LimitOffsetPagination)
def get_download_counts_from_apps(request: WSGIRequest):
    print(request.GET)
    return OneStoreDL.objects.filter(created_at__gte=timezone.now() - timedelta(days=1))


# one "POST"
@api.post("/one", response=List[OneStoreSchema], tags=["one-store"])
@paginate(LimitOffsetPagination)
def find_download_counts_of_app_with_name(request: WSGIRequest, query):
    print(request.POST)
    return OneStoreDL.objects.filter(app_name__contains=query).order_by("-downloads")


# one "GET"
@api.get("/one/{market_appid}", response=List[OneStoreSchema], tags=["one-store"])
@paginate(LimitOffsetPagination)
def get_download_counts_from_one_app(request: WSGIRequest, market_appid: str):
    print(request.GET)
    return OneStoreDL.objects.filter(market_appid=market_appid).order_by("-created_at")
