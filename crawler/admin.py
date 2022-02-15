from django.contrib import admin
from import_export.admin import ImportExportMixin

from crawler.forms import AppChoiceField
from crawler.models import Following, App
from crawler.models import OneStoreDL
from crawler.models import Ranked
from crawler.models import TrackingApps


# Register your models here.


class RankedAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ["app_name", "package_name", "rank", "market", "deal_type", "rank_type", "created_at"]
    search_fields = ["app_name", "market_appid", "package_name"]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "app":
            return AppChoiceField(queryset=App.objects.order_by("app_name").all())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class FollowingAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ["app_name", "created_at"]
    list_select_related = ["app"]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "app":
            return AppChoiceField(queryset=App.objects.order_by("app_name").all())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class TrackingAppsAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ["app_name", "package_name", "market", "rank", "deal_type", "rank_type", "created_at"]
    search_fields = ["app_name", "package_name", ]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "app":
            return AppChoiceField(queryset=App.objects.order_by("app_name").all())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class OneStoreDLAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ["app_name", "market_appid", "genre", "downloads", "volume", "released", "created_at"]
    search_fields = ["app_name", "market_appid", ]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "app":
            return AppChoiceField(queryset=App.objects.order_by("app_name").all())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Ranked, RankedAdmin)
admin.site.register(Following, FollowingAdmin)
admin.site.register(TrackingApps, TrackingAppsAdmin)
admin.site.register(OneStoreDL, OneStoreDLAdmin)
