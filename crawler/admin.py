from django.contrib import admin
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import QuerySet
from import_export.admin import ImportExportMixin

from crawler.forms import AppChoiceField, FollowingChoiceField
from crawler.models import Following, App
from crawler.models import OneStoreDL
from crawler.models import Ranked
from crawler.models import TrackingApps


# Register your models here.
@admin.action(description=f"선택된 애플리케이션 을/를 추적합니다!")
def follow_application(self, request: WSGIRequest, queryset: QuerySet):
    for obj in queryset:
        if type(obj) == App:
            follow = Following(
                app_name=obj.app_name,
                package_name=obj.package_name,
                market_appid=obj.market_appid,
                is_active=True,
            )
            follow.save()
        elif type(obj) in [Ranked, OneStoreDL]:
            app = App.objects.filter(pk=obj.app_id).first()
            following = Following(
                app_name=app.app_name,
                package_name=app.package_name,
                market_appid=app.market_appid,
                is_active=True,
            )
            following.save()


class AppAdmin(admin.ModelAdmin):
    list_display = ['id', 'app_name', 'package_name', 'market_appid']
    search_fields = ["app_name", "package_name", "market_appid"]
    actions = [follow_application]


class RankedAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ['rank', 'app', 'market', 'deal_type', 'app_type', 'chart_type', 'app_name', 'date', 'market_appid']
    search_fields = ["app_name", "market_appid", "package_name"]
    actions = [follow_application]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "app":
            return AppChoiceField(queryset=App.objects.order_by("app_name").all())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class FollowingAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ['id', 'app_name', 'package_name', 'market_appid', 'is_active']
    search_fields = ["app_name", "market_appid", "package_name"]


class TrackingAppsAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ['app', 'following', 'deal_type', 'market', 'chart_type', 'rank', 'date']
    search_fields = ["app_name", "market_appid", "package_name"]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "following":
            return FollowingChoiceField(queryset=Following.objects.order_by("app_name").all())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class OneStoreDLAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ['id', 'app', 'market_appid', 'genre', 'downloads', 'volume', 'released']
    search_fields = ["app_name", "market_appid", ]
    actions = [follow_application, ]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "app":
            return AppChoiceField(queryset=App.objects.order_by("app_name").all())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(App, AppAdmin)
admin.site.register(Ranked, RankedAdmin)
admin.site.register(Following, FollowingAdmin)
admin.site.register(TrackingApps, TrackingAppsAdmin)
admin.site.register(OneStoreDL, OneStoreDLAdmin)
