from django.contrib import admin
from django.db import models

from crawler.forms import AppChoiceField
from crawler.models import Following, App
from crawler.models import OneStoreDL
from crawler.models import Ranked
from crawler.models import TrackingApps


# Register your models here.


@admin.register(Ranked)
class Ranked(admin.ModelAdmin):
    list_display = ["app_name", "rank", "market", "deal_type", "rank_type", "created_at"]
    actions = []

    def get_action_choices(self, request, default_choices=models.BLANK_CHOICE_DASH):
        print(default_choices)
        return super().get_action_choices(request, default_choices)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "app":
            return AppChoiceField(queryset=App.objects.order_by("app_name").all())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_search_results(self, request, queryset, search_term):
        print("search")
        return super().get_search_results(request, queryset, search_term)


@admin.register(Following)
class Following(admin.ModelAdmin):
    list_display = ["app_name", "created_at"]
    list_select_related = ["app"]


@admin.register(TrackingApps)
class TrackingApps(admin.ModelAdmin):
    list_display = ["app_name", "package_name", "market", "rank", "deal_type", "rank_type", "created_at"]


@admin.register(OneStoreDL)
class OneStoreDL(admin.ModelAdmin):
    list_display = ["app_name", "market_appid", "genre", "downloads", "volume", "released", "created_at"]
