from django.contrib import admin
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import QuerySet
from import_export.admin import ImportExportMixin

from crawler.forms import AppChoiceField
from crawler.models import Following, App
from crawler.models import OneStoreDL
from crawler.models import Ranked
from crawler.models import TrackingApps


# Register your models here.
@admin.action(description="선택된 랭킹 을/를 추적합니다!")
def follow_application(self, request: WSGIRequest, queryset: QuerySet):
    for obj in queryset:
        if type(obj) == App:
            print("hello")
            follow = Following(
                app_name=obj.app_name,
                app=obj,
            )
            follow.save()
        elif type(obj) in [Ranked, OneStoreDL]:
            print("hi")
            app_name = obj.app_name
            app_id = obj.app_id
            app = App.objects.filter(pk=app_id).first()
            following = Following(
                app_name=app_name,
                app=app,
            )
            following.save()


@admin.action(description="선택된 앱 을/를 중복 정리합니다!")
def dedupe_application(self, request: WSGIRequest, queryset: QuerySet):
    app_list = []
    app_names = []
    for obj in queryset:
        app_name = obj.app_name
        app_id = obj.package_name
        if (app_name, app_id,) in app_list or app_name in app_names:
            obj.delete()
        else:
            app_names.append(app_name)
            app_list.append((app_name, app_id,))


class AppAdmin(admin.ModelAdmin):
    list_display = ["app_name", "package_name", "icon_url"]
    search_fields = ["app_name", "package_name"]
    actions = [dedupe_application, follow_application]


class RankedAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ["app", "package_name", "rank", "market", "deal_type", "rank_type", "created_at"]
    search_fields = ["app_name", "market_appid", "package_name"]
    actions = [follow_application, ]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "app":
            return AppChoiceField(queryset=App.objects.order_by("app_name").all())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class FollowingAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ["app", "created_at", "is_active", "package_name"]
    list_select_related = ["app"]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "app":
            return AppChoiceField(queryset=App.objects.order_by("app_name").all())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class TrackingAppsAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ["app", "package_name", "market", "rank", "deal_type", "rank_type", "created_at"]
    search_fields = ["app_name", "package_name", ]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "app":
            return AppChoiceField(queryset=App.objects.order_by("app_name").all())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class OneStoreDLAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ["app", "market_appid", "genre", "downloads", "volume", "released", "created_at"]
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
