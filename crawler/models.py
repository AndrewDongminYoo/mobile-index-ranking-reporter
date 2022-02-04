from django.db import models

# Create your models here.


class Timestamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Ranked(Timestamped):
    DEAL_TYPE = (
        ("real_rank", "실시간"),
        ("market_rank", "일간")
    )
    MARKET = (
        ("google", "구글플레이"),
        ("apple", "앱스토어"),
        ("one", "원스토어")
    )
    RANK_TYPE = (
        ("free", "무료 순위"),
        ("paid", "유료 순위"),
        ("gross", "매출 순위")
    )
    _date = models.CharField(max_length=16)
    deal_type = models.CharField(max_length=16, choices=DEAL_TYPE)
    market = models.CharField(max_length=16, choices=MARKET)
    rank_type = models.CharField(max_length=16, choices=RANK_TYPE)
    app_name = models.TextField(max_length=64)
    icon_url = models.URLField(max_length=200)
    market_appid = models.TextField(max_length=64)
    package_name = models.TextField(max_length=64)
    rank = models.IntegerField()
