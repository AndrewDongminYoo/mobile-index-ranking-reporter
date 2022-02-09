from typing import List

from ninja import NinjaAPI

from crawler.models import Ranked, Following
from crawler.schemas import RankedSchema

api = NinjaAPI(title="Ninja")


@api.get("/search", response=RankedSchema)
def search(request, app_name):
    ranked_app = Ranked.objects.filter(app_name=app_name).order_by("-created_at").first()
    exists_app = Following.objects.filter(app_name=app_name).exists()
    if not exists_app:
        instance = Following(app_name=app_name)
        instance.save()
    return ranked_app


@api.post("/search", response=List[RankedSchema])
def get_ranked_list(request):
    pass
