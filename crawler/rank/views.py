from datetime import timedelta

from django.db.models import Min
from django.shortcuts import render
from django.utils import timezone

from crawler.models import TrackingApps


def get_kst():
    return timezone.now() + timedelta(hours=9)


def index(request):
    apps = TrackingApps.objects.filter(created_at__gte=get_kst() - timedelta(days=3))
    ratings = (
        apps.values("created_at__date", "app_name", "market", "deal_type", "rank_type")
            .annotate(rank=Min("rank"))
            .values("created_at__date", "icon_url", "app_name", "market", "deal_type", "rank_type", "rank")
            .order_by("-created_at__date")
    )
    return render(request, "statistic.html", {"apps": ratings})
