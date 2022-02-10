from datetime import timedelta

from django.db.models import Min
from django.shortcuts import render
from django.utils import timezone

from crawler.models import TrackingApps, Ranked, OneStoreDL


def statistic(request, market=None, deal=None, app=None):
    # 전체 차트 (등록 하지 않은 애플리케이션) 무료/유료/매출 순위
    apps = Ranked.objects.filter(created_at__gte=timezone.now() - timedelta(hours=1))
    market_app = apps.filter(market=market, deal_type=deal, app_type=app).order_by("created_at")
    # market_app = market_app.values("app_name", "icon_url", "package_name", "rank", "rank_type")
    return render(request, "statistic.html", {"apps": market_app})


def my_rank(request):
    # 등록한 애플리케이션 최근 3일 차트
    apps = TrackingApps.objects.filter(created_at__gte=timezone.now() - timedelta(days=3))
    ratings = apps.values("created_at__date", "app_name", "market", "deal_type", "rank_type").annotate(
        rank=Min("rank")).values("created_at__date", "icon_url", "app_name", "market", "deal_type", "rank_type",
                                 "rank").order_by("-created_at__date")
    return render(request, "my_rank.html", {"apps": ratings})


def ranking(request):
    # 랭킹 변동 테이블 (및 분류)
    apps = OneStoreDL.objects.filter(created_at__gte=timezone.now() - timedelta(days=1))
    return render(request, "ranking.html", {"apps": apps})
