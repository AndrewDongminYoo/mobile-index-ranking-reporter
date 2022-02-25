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
@paginate(LimitOffsetPagination)
def show_all_tracking_apps(request):
    """추적 결과 전부"""
    print(request)
    return TrackingApps.objects.all()


@api.get("/tracking/last", response=TrackingSchema, tags=["index"])
def show_last_tracking_app(request):
    """팔로잉 아이디로 추적 결과 리스트"""
    following = request.GET.get("app")
    return TrackingApps.objects.filter(following_id=following).order_by("-created_at").first()


@api.get("/tracking", response=List[TrackingSchema], tags=["index"])
@paginate(LimitOffsetPagination)
def show_all_tracking_apps_with_following(request):
    """팔로잉 아이디로 추적 결과 리스트"""
    following = request.GET.get("following")
    return TrackingApps.objects.filter(following_id=following).order_by("-created_at")


@api.post("/search", response=List[ApplicationSchema], tags=["index"])
@paginate(LimitOffsetPagination)
def search_apps_with_query(request):
    """앱 이름 혹은 마켓 아이디 검색하기"""
    query = request.POST.get('query')
    return App.objects.filter(Q(app_name__search=query) | Q(market_appid__search=query)).all()


@api.post("/follow/new", response=FollowingSchema, tags=["index"])
def new_follow_register(request):
    """새로운 팔로우할 앱 등록하기"""
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
    """팔로우 중인 앱 리스트"""
    return Following.objects.all()


@api.get("/downloads", response=List[OneStoreSchema], tags=["index"])
@paginate(LimitOffsetPagination)
def show_details_of_downloads(request):
    """앱 기준으로 원스토어 다운로드수 리스트"""
    appid = request.GET.get("app")
    time3 = timezone.now() - timedelta(hours=30)
    OneStoreDL.objects\
        .filter(app_id=appid, created_at__gte=time3)\
        .values_list("downloads")


@api.get("/down/last", response=OneStoreSchema, tags=["index"])
def show_details_of_downloads_last(request):
    """앱 기준으로 원스토어 다운로드수 리스트"""
    appid = request.GET.get("app")
    app = OneStoreDL.objects.filter(app_id=appid).order_by("-created_at").first()
    return app if app else OneStoreSchema()


@api.get("/detail-2", response=List[TrackingSchema], tags=["index"])
@paginate(LimitOffsetPagination)
def show_details_of_highest_ranks(request):
    """앱 아이디 기준으로 일별 추적결과 리턴"""
    appid = request.GET.get("app")
    d_day = timezone.now() - timedelta(days=3)
    return TrackingApps.objects\
        .filter(app_id=appid, created_at__gte=d_day)\
        .annotate(min_rank=Min("rank"))\
        .values("app_name", "min_rank", "date")
