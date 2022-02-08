from datetime import timedelta

from django.shortcuts import render
from django.utils import timezone

from crawler.models import TrackingApps


def get_kst():
    return timezone.now() + timedelta(hours=9)


def index(request):
    apps = TrackingApps.objects.filter(created_at__gte=get_kst() - timedelta(days=3))
    return render(request, "statistic.html", {"apps": apps})
