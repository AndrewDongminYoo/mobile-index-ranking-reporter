from datetime import timedelta
from typing import List

from django.db.models import Min
from django.db.models import Q
from django.utils import timezone
from ninja import NinjaAPI
from ninja.orm import create_schema

from crawler.models import Ranked, Following, TrackingApps, OneStoreDL, App

api = NinjaAPI(title="Application", urls_namespace="v2")

RankedSchema = create_schema(Ranked)
ApplicationSchema = create_schema(App)
FollowingSchema = create_schema(Following)
OneStoreSchema = create_schema(OneStoreDL)
TrackingSchema = create_schema(TrackingApps)


@api.get("/tracked", response=List[RankedSchema], tags=["index"])
def show_all_apps(request, *args, **kwargs):
    """
    TODO:
    내가 팔로우 하는 모든 앱을 가져온다.
    각 앱의 정보 기본적으로 앱 아이콘과 패키지명)
    원스토어 앱의 경우 가장 최근의 다운로드 수를 첨부한다.
    일별 가장 높은 데이터(Min)를 리턴한다.
    """
    return Following.objects.all()


@api.post("/search", tags=["index"])
def search_with_query(request, *args, **kwargs):
    """
    TODO:
    쿼리를 받고,
    그 단어를 '앱 이름'에 포함하고 있는 앱과, (OR)
    그 단어를 '패키지명'에 포함하고 있는 앱을
    함께 리턴한다.
    """
    query = request.POST.get('query')
    return App.objects.filter(Q(app_name__search=query) | Q(market_appid__search=query)).all()


@api.get("/detail", tags=["index"])
def show_details(request, *args, **kwargs):
    """
    TODO:
    특정 앱을 자세히 보려고 클릭하면,
    그 앱의 최근 추적 결과 30건을 리턴한다.
    # 최근 30건(30시간) 동안의 추적 결과를 모두 가져온 다음 앱에 따라 그룹바이한다. -> 다운로드 수만
    # 최근 3일간 날짜별 최고 랭킹!!!!!! 변화 기록 (히스토리)
    (순위권 밖에 있을 때는 200위로 설정)
    """
    appid = request.GET.get("app")
    time3 = timezone.now() - timedelta(hours=30)
    d_day = timezone.now() - timedelta(days=3)

    downloads = OneStoreDL.objects.filter(app_id=appid,
                                          created_at__gte=time3).values_list("downloads")
    queryset = TrackingApps.objects\
        .filter(app_id=appid, created_at__gte=d_day)\
        .annotate(min_rank=Min("rank"))\
        .values("app_name", "min_rank", "date")
    return
