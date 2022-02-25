from datetime import timedelta
from typing import List

from django.db.models import Min
from django.db.models import Q
from django.utils import timezone
from ninja import NinjaAPI
from ninja.orm import create_schema
from ninja.pagination import LimitOffsetPagination, paginate

from crawler.models import Ranked, Following, TrackingApps, OneStoreDL, App

api = NinjaAPI(title="Application", urls_namespace="v2")

RankedSchema = create_schema(Ranked)
ApplicationSchema = create_schema(App)
FollowingSchema = create_schema(Following)
OneStoreSchema = create_schema(OneStoreDL)
TrackingSchema = create_schema(TrackingApps)


@api.get("/tracked", response=List[TrackingSchema], tags=["index"])
def show_all_tracking_apps(request):
    print(request)
    return TrackingApps.objects.all()


@api.get("/tracking", response=List[TrackingSchema], tags=["index"])
@paginate(LimitOffsetPagination)
def show_all_tracking_apps(request):
    following = request.GET.get("following")
    return TrackingApps.objects.filter(following_id=following)


@api.post("/search", response=ApplicationSchema, tags=["index"])
def search_apps_with_query(request):
    query = request.POST.get('query')
    return App.objects.filter(Q(app_name__search=query) | Q(market_appid__search=query)).all()


@api.post("/follow/new", response=FollowingSchema, tags=["index"])
def new_follow_register(request):
    app_data = request.POST
    follow = Following.objects.get_or_create(
        app_name=app_data.get('app_name'),
        package_name=app_data.get('package_name'),
        market_appid=app_data.get('market_appid'),
        is_active=True,
    )[0]
    follow.save()
    return follow


@api.get("/follow/list", response=List[FollowingSchema], tags=["index"])
@paginate(LimitOffsetPagination)
def load_all_following(request):
    return Following.objects.all()


@api.get("/detail-1", response=List[OneStoreSchema], tags=["index"])
def show_details_of_downloads(request):
    appid = request.GET.get("app")
    time3 = timezone.now() - timedelta(hours=30)
    return OneStoreDL.objects\
        .filter(app_id=appid, created_at__gte=time3)\
        .values_list("downloads")


@api.get("/detail-2", response=List[TrackingSchema], tags=["index"])
def show_details_of_highest_ranks(request):
    appid = request.GET.get("app")
    d_day = timezone.now() - timedelta(days=3)
    return TrackingApps.objects\
        .filter(app_id=appid, created_at__gte=d_day)\
        .annotate(min_rank=Min("rank"))\
        .values("app_name", "min_rank", "date")
