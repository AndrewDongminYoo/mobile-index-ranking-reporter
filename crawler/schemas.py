from ninja import ModelSchema

from crawler.models import Ranked


class RankedSchema(ModelSchema):
    class Config:
        model = Ranked
        model_fields = "__all__"
