from django.contrib import admin
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import QuerySet
from import_export.admin import ImportExportMixin

from crawler.models import App
from crawler.models import Following
from crawler.models import OneStoreDL
from crawler.models import Ranked
from crawler.models import TrackingApps


@admin.action(description=f"선택된 애플리케이션 을/를 추적합니다!")
def follow_application(self, request: WSGIRequest, queryset: QuerySet):
    for obj in queryset:
        if type(obj) is Ranked:
            app = App.objects.filter(pk=obj.app_id).first()
            following = Following(
                app_name=app.app_name,
                market_appid=app.market_appid,
                market=app.market,
                is_active=True,
            )
            following.save()
        elif type(obj) is OneStoreDL:
            app = App.objects.filter(pk=obj.app_id).first()
            following = Following(
                app_name=app.app_name,
                market_appid=app.market_appid,
                is_active=True,
                market="one",
            )
            following.save()


class AppAdmin(admin.ModelAdmin):
    list_display = ['id', 'app_name', 'market_appid']
    search_fields = ["app_name", "market_appid"]


class RankedAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ['rank', 'app', 'market', 'deal_type', 'app_type', 'chart_type', 'app_name', 'date', 'market_appid']
    search_fields = ["app_name", "market_appid"]
    actions = [follow_application]


class FollowingAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ['id', 'app_name', 'market_appid', 'market', 'is_active']
    search_fields = ["app_name", "market_appid"]


class TrackingAppsAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ['app', 'following', 'market', 'deal_type', 'chart_type', 'rank', 'date']
    search_fields = ["app_name", "market_appid"]


class OneStoreDLAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ['id', 'app', 'market_appid', 'genre', 'date', 'downloads', 'volume', 'released']
    search_fields = ["app_name", "market_appid"]
    actions = [follow_application, ]


admin.site.register(App, AppAdmin)
admin.site.register(Ranked, RankedAdmin)
admin.site.register(Following, FollowingAdmin)
admin.site.register(TrackingApps, TrackingAppsAdmin)
admin.site.register(OneStoreDL, OneStoreDLAdmin)
