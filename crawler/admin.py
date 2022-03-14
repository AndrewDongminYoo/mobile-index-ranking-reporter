from django.contrib import admin
from django.db.models import QuerySet
from import_export.admin import ImportExportMixin

from crawler.models import App
from crawler.models import AppInformation
from crawler.models import Following
from crawler.models import OneStoreDL
from crawler.models import Ranked
from crawler.models import TrackingApps


# Register your models here.
@admin.action(description="선택된 애플리케이션 을/를 추적합니다!")
def follow_application(self, request, queryset: QuerySet):
    for obj in queryset:
        if type(obj) == App:
            follow = Following(
                app_name=obj.app_name,
                package_name=obj.package_name,
                market_appid=obj.market_appid,
                is_active=True,
            )
            follow.save()
        elif type(obj) is OneStoreDL:
            app = App.objects.filter(pk=obj.app_id).first()
            following = Following(
                app_name=app.app_name,
                market_appid=app.market_appid,
                is_active=True,
                market="one",
            )
            following.save()
        elif type(obj) is Following:
            obj.is_active = True
            obj.save()


def email_callable(app):
    if app.app_info:
        return app.app_info.email


def phone_callable(app):
    if app.app_info:
        return app.app_info.phone


class AppAdmin(admin.ModelAdmin):
    list_display = ['id', 'app_name', 'market', 'market_appid', email_callable, phone_callable]
    readonly_fields = [email_callable, phone_callable]
    search_fields = ["app_name", "app_url"]
    filter_fields = ["market"]

    def has_add_permission(self, request):
        return False


class AppInformationAdmin(admin.ModelAdmin):
    list_display = ['email', 'phone', 'google_url', 'apple_url', 'one_url']
    search_fields = ['google_url', 'apple_url', 'one_url']

    def has_add_permission(self, request):
        return False


class RankedAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ['rank', 'app', 'market', 'deal_type', 'app_type', 'chart_type', 'market_appid']
    search_fields = ["app_name", "market_appid"]
    actions = [follow_application]
    filter_fields = ["market", "deal_type", "app_type", "chart_type"]

    def has_add_permission(self, request):
        return False


class FollowingAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ['id', 'app_name', 'market_appid', 'market', 'is_active']
    search_fields = ["app_name", "market_appid"]
    actions = [follow_application]


class TrackingAppsAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ['app', 'following', 'market', 'deal_type', 'chart_type', 'rank', 'date']
    search_fields = ["app_name", "market_appid"]

    def has_add_permission(self, request):
        return False


class OneStoreDLAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ['id', 'app', 'market_appid', 'genre', 'date', 'downloads', 'volume', 'released']
    search_fields = ["app_name", "market_appid"]
    actions = [follow_application, ]

    def has_add_permission(self, request):
        return False


admin.site.register(App, AppAdmin)
admin.site.register(AppInformation, AppInformationAdmin)
admin.site.register(Ranked, RankedAdmin)
admin.site.register(Following, FollowingAdmin)
admin.site.register(TrackingApps, TrackingAppsAdmin)
admin.site.register(OneStoreDL, OneStoreDLAdmin)
