from django.contrib import admin

from crawler.models import Following
from crawler.models import OneStoreDL
from crawler.models import Ranked
from crawler.models import TrackingApps


# Register your models here.


@admin.register(Ranked)
class Ranked(admin.ModelAdmin):
    list_display = ["date", "market", "deal_type", "rank_type", "rank", "app_name"]


@admin.register(Following)
class Following(admin.ModelAdmin):
    list_display = ["app_name"]


@admin.register(TrackingApps)
class TrackingApps(admin.ModelAdmin):
    list_display = ["app_name", "package_name", "market", "rank"]


@admin.register(OneStoreDL)
class OneStoreDL(admin.ModelAdmin):
    list_display = ["market_appid", "genre", "downloads", "volume", "released"]
