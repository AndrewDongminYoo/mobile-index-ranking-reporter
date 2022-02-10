from django.contrib import admin

from crawler.models import Following
from crawler.models import OneStoreDL
from crawler.models import Ranked
from crawler.models import TrackingApps


# Register your models here.


@admin.register(Ranked)
class Ranked(admin.ModelAdmin):
    list_display = ["app_name", "rank", "market", "deal_type", "rank_type", "created_at"]


@admin.register(Following)
class Following(admin.ModelAdmin):
    list_display = ["app_name", "created_at"]


@admin.register(TrackingApps)
class TrackingApps(admin.ModelAdmin):
    list_display = ["app_name", "package_name", "market", "rank", "market", "deal_type", "rank_type", "created_at"]


@admin.register(OneStoreDL)
class OneStoreDL(admin.ModelAdmin):
    list_display = ["app_name", "market_appid", "genre", "downloads", "volume", "released", "created_at"]
