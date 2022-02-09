from datetime import timedelta

from django.db.models import Min
from django.shortcuts import render
from django.utils import timezone

from crawler.models import TrackingApps


def get_kst():
    return timezone.now() + timedelta(hours=9)


def statistic(request):
    # 전체 차트 (등록 하지 않은 애플리케이션) 무료/유료/매출 순위
    return render(request, "statistic.html")


def my_rank(request):
    # 등록한 애플리케이션 최근 3일 차트
    apps = TrackingApps.objects.filter(created_at__gte=get_kst() - timedelta(days=3))
    ratings = apps.values("created_at__date", "app_name", "market", "deal_type", "rank_type").annotate(
        rank=Min("rank")).values("created_at__date", "icon_url", "app_name", "market", "deal_type", "rank_type",
                                 "rank").order_by("-created_at__date")
    return render(request, "my_rank.html", {"apps": ratings})


def ranking(request):
    # 랭킹 변동 테이블 (및 분류)
    return render(request, "ranking.html")
