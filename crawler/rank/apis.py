from ninja import NinjaAPI
from ninja.responses import Response

from crawler.models import Ranked, Following

api = NinjaAPI(title="Ninja")


@api.get("/search")
def search(request, app_name):
    ranked_app = Ranked.objects.filter(app_name=app_name).order_by("-created_at").first()
    instance = Following(app_name=app_name)
    instance.save()
    return Response(ranked_app)
