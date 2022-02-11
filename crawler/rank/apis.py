from datetime import timedelta
from typing import List

from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Min
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ninja import NinjaAPI
from ninja.orm import create_schema

from crawler.models import Ranked, Following, TrackingApps, OneStoreDL

api = NinjaAPI(title="Ninja")

RankedSchema = create_schema(Ranked)
FollowingSchema = create_schema(Following)
TrackingSchema = create_schema(TrackingApps)
OneStoreSchema = create_schema(OneStoreDL)


# following "GET"
@api.get("/following", response=List[TrackingSchema], tags=["ranking"])
def list_tracking(request: WSGIRequest):
    apps = TrackingApps \
        .objects \
        .filter(created_at__gte=timezone.now() - timedelta(days=3)) \
        .values("created_at__date",
                "app_name", "market",
                "deal_type", "rank_type").annotate(rank=Min("rank")) \
        .values("created_at__date", "icon_url", "app_name", "market", "deal_type", "rank_type", "rank") \
        .order_by("-created_at__date")
    return api.create_response(request, apps)


# following "DELETE"
@api.delete("/following", tags=["Tracking Apps"])
def dedupe_or_remove(request: WSGIRequest):
    return api.create_response(request)


# ranking "GET"
@api.get("/ranking", response=List[RankedSchema], tags=["ranking"])
def get_ranked_list(request: WSGIRequest):
    apps = Ranked.objects.filter(created_at__gte=timezone.now() - timedelta(days=1))
    apps = Ranked.objects.filter(created_at__gte=timezone.now() - timedelta(hours=1))
    market_app = apps.filter().order_by("created_at")
    return api.create_response(request, apps)


# follow "POST"
@api.get("/follow", response=RankedSchema, tags=["ranking"])
def search(request: WSGIRequest, app_name):
    ranked_app = Ranked.objects.filter(app_name=app_name).order_by("-created_at").first()
    exists_app = Following.objects.filter(app_name=app_name).exists()
    if not exists_app:
        instance = Following(app_name=app_name)
        instance.save()
    return api.create_response(request, ranked_app)


# follow "GET"
@api.post("/follow", tags=["ranking"])
def create_following(request: WSGIRequest, payload: FollowingSchema):
    following = Following.objects.create(**payload.dict())
    return api.create_response(request, {"id": following.id})


# follow "DELETE"
@api.delete("/follow/{following_id}", tags=["ranking"])
def delete_following(request: WSGIRequest, following_id: int):
    following = get_object_or_404(Following, id=following_id)
    following.delete()
    return api.create_response(request, {"success": True})


# one "GET"
@api.get("/one", response=List[OneStoreSchema], tags=["one-store"])
def get_download_counts_from_apps(request: WSGIRequest):
    apps = OneStoreDL.objects.filter(created_at__gte=timezone.now() - timedelta(days=1))
    return api.create_response(request, apps)


# one "POST"
@api.post("/one", response=List[OneStoreSchema], tags=["one-store"])
def find_download_counts_of_app_with_name(request: WSGIRequest):
    return api.create_response(request)
