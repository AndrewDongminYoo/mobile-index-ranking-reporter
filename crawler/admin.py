from django.contrib import admin

from crawler.models import Following
from crawler.models import Ranked


# Register your models here.


@admin.register(Ranked)
class Ranked(admin.ModelAdmin):
    list_display = ["_date", "market", "deal_type", "rank_type", "rank", "app_name"]


@admin.register(Following)
class Following(admin.ModelAdmin):
    list_display = ["app_name", "package_name", "market"]
