from typing import List

from django.shortcuts import get_object_or_404
from ninja import NinjaAPI
from ninja.orm import create_schema

from crawler.models import Ranked, Following, TrackingApps

api = NinjaAPI(title="Ninja")
RankedSchema = create_schema(Ranked)
FollowingSchema = create_schema(Following)
TrackingSchema = create_schema(TrackingApps)


@api.get("/search", response=RankedSchema, tags=["ranking"])
def search(request, app_name):
    ranked_app = Ranked.objects.filter(app_name=app_name).order_by("-created_at").first()
    exists_app = Following.objects.filter(app_name=app_name).exists()
    if not exists_app:
        instance = Following(app_name=app_name)
        instance.save()
    return api.create_response(request, ranked_app)


@api.post("/following", tags=["ranking"])
def create_following(request, payload: FollowingSchema):
    tracking = Following.objects.create(**payload.dict())
    return api.create_response(request, {"id": tracking.id})


@api.get("/tracking", response=List[TrackingSchema], tags=["ranking"])
def list_tracking(request):
    qs = TrackingApps.objects.all()
    return api.create_response(request, qs)


@api.delete("/following/{following_id}", tags=["ranking"])
def delete_following(request, following_id: int):
    following = get_object_or_404(Following, id=following_id)
    following.delete()
    return api.create_response(request, {"success": True})
