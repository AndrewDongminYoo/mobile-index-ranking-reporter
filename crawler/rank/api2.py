from ninja import NinjaAPI
from ninja.orm import create_schema

from crawler.models import Ranked, Following, TrackingApps, OneStoreDL, App

api = NinjaAPI(title="Application", urls_namespace="v2")

RankedSchema = create_schema(Ranked)
ApplicationSchema = create_schema(App)
FollowingSchema = create_schema(Following)
OneStoreSchema = create_schema(OneStoreDL)
TrackingSchema = create_schema(TrackingApps)


@api.get("/following", tags=["index"])
def show_all_apps(request, *args, **kwargs):
    is_following = App.objects.prefetch_related("trackingapps_set")
