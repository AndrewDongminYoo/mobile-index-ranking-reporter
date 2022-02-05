from django.contrib import admin

from crawler.models import Ranked


# Register your models here.


@admin.register(Ranked)
class Ranked(admin.ModelAdmin):
    list_display = ["market", "deal_type", "rank_type", "rank", "app_name"]
