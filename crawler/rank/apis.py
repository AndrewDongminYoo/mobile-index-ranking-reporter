from typing import List

from django.shortcuts import get_object_or_404
from ninja import NinjaAPI
from ninja.orm import create_schema

from crawler.models import Ranked, Following, TrackingApps

api = NinjaAPI(title="Ninja")
RankedSchema = create_schema(Ranked)
FollowingSchema = create_schema(Following)
TrackingSchema = create_schema(TrackingApps)


@api.get("/search", response=RankedSchema)
def search(request, app_name):
    ranked_app = Ranked.objects.filter(app_name=app_name).order_by("-created_at").first()
    exists_app = Following.objects.filter(app_name=app_name).exists()
    if not exists_app:
        instance = Following(app_name=app_name)
        instance.save()
    return ranked_app


@api.post("/following")
def create_following(request, payload: FollowingSchema):
    tracking = Following.objects.create(**payload.dict())
    return {"id": tracking.id}


@api.get("/tracking", response=List[TrackingSchema])
def list_tracking(request):
    qs = TrackingApps.objects.all()
    return qs


@api.delete("/following/{following_id}")
def delete_following(request, following_id: int):
    following = get_object_or_404(Following, id=following_id)
    following.delete()
    return {"success": True}
