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
def list_tracking(request: WSGIRequest):
    return TrackingApps.objects.order_by("-created_at").all()


# following "DELETE"
@api.delete("/following/{record_id}", tags=["Tracking Apps"])
def dedupe_or_remove(request: WSGIRequest, record_id: int):
    TrackingApps.objects.filter(id=record_id).delete()
    return api.create_response(request, {"success": True})


# ranking "GET"
@api.get("/ranking", response=List[RankedSchema], tags=["ranking"])
@paginate(LimitOffsetPagination)
def get_ranked_list(request: WSGIRequest):
    return Ranked.objects.order_by("-created_at")


# follow "POST"
@api.post("/follow", response=FollowingSchema, tags=["ranking"])
def add_following_app_and_search(request: WSGIRequest, app_name):
    ranked_app = Ranked.objects.filter(app_name=app_name).order_by("-created_at").first()
    exists_app = Following.objects.filter(app_name=app_name)
    if exists_app.exists():
        return exists_app.first()
    TrackingApps().from_rank(ranked_app)
    instance = Following(app_name=app_name)
    instance.save()
    return instance


# follow "GET"
@api.get("/follow", response=List[FollowingSchema], tags=["ranking"])
@paginate(LimitOffsetPagination)
def create_following(request: WSGIRequest):
    return Following.objects.order_by("-created_at").all()


# follow "DELETE"
@api.delete("/follow/{following_id}", tags=["ranking"])
def delete_following(request: WSGIRequest, following_id: int):
    following = get_object_or_404(Following, id=following_id)
    following.delete()
    return api.create_response(request, {"success": True})


# one "GET"
@api.get("/one", response=List[OneStoreSchema], tags=["one-store"])
@paginate(LimitOffsetPagination)
def get_download_counts_from_apps(request: WSGIRequest):
    return OneStoreDL.objects.filter(created_at__gte=timezone.now() - timedelta(days=1))


# one "GET"
@api.post("/one", response=List[OneStoreSchema], tags=["one-store"])
@paginate(LimitOffsetPagination)
def find_download_counts_of_app_with_name(request: WSGIRequest, query):
    return OneStoreDL.objects.filter(app_name__contains=query).order_by("-downloads")
