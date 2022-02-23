from datetime import timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Min
from django.shortcuts import render
from django.utils import timezone

from crawler.models import TrackingApps, Ranked, OneStoreDL, TimeIndex


@staff_member_required
def index(request: WSGIRequest):
    return render(request, "index.html")


def statistic(request: WSGIRequest, market=None, deal=None, app=None):
    # 전체 차트 (등록 하지 않은 애플리케이션) 무료/유료/매출 순위
    market_app = Ranked.objects.filter(market=market, deal_type=deal, app_type=app).order_by("-created_at")
    timestamps = min([ts.id for ts in TimeIndex.objects.filter(date=Ranked.objects.last().date)])
    apps = market_app.filter(date_id__gte=timestamps)
    return render(request, "statistic.html", {"apps": apps})


def my_rank(request: WSGIRequest):
    # 등록한 애플리케이션 최근 3일 차트
    apps = TrackingApps.objects.filter(created_at__gte=timezone.now() - timedelta(days=3))
    ratings = apps.values("created_at__date", "app_name", "market", "deal_type", "rank_type").annotate(
        rank=Min("rank")).values("created_at__date", "icon_url", "app_name", "market", "deal_type", "rank_type",
                                 "rank").order_by("-created_at__date")
    return render(request, "my_rank.html", {"apps": ratings})


def ranking(request: WSGIRequest):
    # 원 스토어 랭킹 변동 테이블 (및 분류)
    apps = OneStoreDL.objects.filter(created_at__gte=timezone.now() - timedelta(days=1))
    return render(request, "ranking.html", {"apps": apps})


def app_register(request: WSGIRequest):
    return render(request, "register.html")
