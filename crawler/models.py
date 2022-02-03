from django.db import models

# Create your models here.


class Timestamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Ranked(Timestamped):
    RANK_TYPE = (
        ("free", "무료 순위"),
        ("paid", "유료 순위"),
        ("gross", "매출 순위")
    )
    app_name = models.TextField(max_length=64)
    icon_url = models.URLField(max_length=200)
    market_appid = models.TextField(max_length=64)
    package_name = models.TextField(max_length=64)
    rank = models.IntegerField()
    rank_type = models.CharField(choices=RANK_TYPE)
