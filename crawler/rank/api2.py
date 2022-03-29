from datetime import timedelta
from typing import List

from django.db.models import Q, Min
from django.utils import timezone
from ninja import NinjaAPI, Schema
from ninja.orm import create_schema
from ninja.pagination import LimitOffsetPagination, paginate

from crawler.models import Ranked, Following, TrackingApps, OneStoreDL, App

api = NinjaAPI(title="Application", urls_namespace="v2")

RankedSchema = create_schema(Ranked)
ApplicationSchema = create_schema(App)
FollowingSchema = create_schema(Following)
OneStoreSchema = create_schema(OneStoreDL)
TrackingSchema = create_schema(TrackingApps, depth=1)


class EmptySchema(Schema):
    pass


@api.get("/tracked", response=List[TrackingSchema], tags=["index"])
@paginate(LimitOffsetPagination)
def show_all_tracking_apps(request):
    """추적 결과 전부"""
    print(request)
    return TrackingApps.objects.all()


@api.get("/tracking/last", response={200: TrackingSchema, 204: EmptySchema}, tags=["index"])
def show_last_tracking_app(request):
    """팔로잉 아이디로 추적 결과 리스트"""
    following = request.GET.get("app")
    tracking = TrackingApps.objects.filter(
        following_id=following,
        chart_type="free").order_by("-created_at")
    if tracking.exists():
        return 200, tracking.first()
    else:
        return 204, ""


@api.get("/tracking", response=List[TrackingSchema], tags=["index"])
@paginate(LimitOffsetPagination)
def show_all_tracking_apps_with_following(request):
    """팔로잉 아이디로 추적 결과 리스트"""
    following = request.GET.get("following")
    return TrackingApps.objects.filter(following_id=following).order_by("-created_at")


@api.get("/tracking/statistics", response=List[TrackingSchema], tags=["index"])
@paginate(LimitOffsetPagination)
def show_details_of_hourly_ranks(request):
    app_id = request.GET.get("app")
    deal_type = request.GET.get("deal_type") or "realtime_rank"
    d_day = timezone.now() - timedelta(days=3)
    return TrackingApps.objects \
        .filter(following_id=app_id,
                deal_type=deal_type,
                created_at__gte=d_day,
                created_at__minute=0,
                chart_type="free")


@api.get("/tracking/daily", response=List[TrackingSchema], tags=["index"])
@paginate(LimitOffsetPagination)
def show_details_of_daily_ranks(request):
    app_id = request.GET.get("app")
    w_day = timezone.now() - timedelta(days=14)
    return TrackingApps.objects \
        .filter(following_id=app_id,
                deal_type="market_rank",
                created_at__gte=w_day,
                chart_type="free")


# one "POST"
@api.post("/ranking", response=List[ApplicationSchema], tags=["ranking"])
@paginate(LimitOffsetPagination)
def find_app_with_query(request, query):
    query_set = App.objects.filter(Q(app_name__icontains=query) | Q(market_appid__icontains=query))
    return query_set.order_by("app_name").all()


@api.get("/follow/list", response=List[FollowingSchema], tags=["index"])
@paginate(LimitOffsetPagination)
def load_all_following(request):
    """팔로우 중인 앱 리스트"""
    return Following.objects.all().filter(is_active=True)


@api.get("/downloads", response=List[OneStoreSchema], tags=["index"])
@paginate(LimitOffsetPagination)
def show_details_of_downloads(request):
    """앱 기준으로 원스토어 다운로드수 리스트"""
    appid = request.GET.get("app")
    time3 = timezone.now() - timedelta(days=3)
    return OneStoreDL.objects \
        .filter(market_appid=appid,
                created_at__gte=time3).order_by("created_at")


@api.get("/down/last", response={200: OneStoreSchema, 204: EmptySchema}, tags=["index"])
def show_details_of_downloads_last(request):
    """앱 기준으로 원스토어 다운로드 수 리스트"""
    market_appid = request.GET.get("app")
    app = OneStoreDL.objects.filter(market_appid=market_appid).order_by("-created_at")
    if app.exists():
        return 200, app.first()
    else:
        return 204, ""
