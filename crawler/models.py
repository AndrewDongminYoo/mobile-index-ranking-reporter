from django.db import models
# Create your models here.
from django.utils import timezone


class Timestamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Ranked(Timestamped):
    DEAL_TYPE = (
        ("realtime_rank", "실시간"),
        ("market_rank", "일간")
    )
    MARKET = (
        ("google", "구글 플레이"),
        ("apple", "앱 스토어"),
        ("one", "원 스토어")
    )
    RANK_TYPE = (
        ("free", "무료 순위"),
        ("paid", "유료 순위"),
        ("gross", "매출 순위")
    )
    date = models.CharField(max_length=16)
    deal_type = models.CharField(max_length=16, choices=DEAL_TYPE)
    market = models.CharField(max_length=16, choices=MARKET)
    rank_type = models.CharField(max_length=16, choices=RANK_TYPE)
    app_name = models.CharField(max_length=64)
    icon_url = models.URLField(max_length=200)
    market_appid = models.CharField(max_length=64)
    package_name = models.CharField(max_length=64)
    rank = models.IntegerField()


class Following(Timestamped):
    app_name = models.CharField(max_length=64)


class TrackingApps(Timestamped):
    deal_type = models.CharField(max_length=16)
    market = models.CharField(max_length=16)
    rank_type = models.CharField(max_length=16)
    app_name = models.CharField(max_length=64)
    icon_url = models.URLField(max_length=200)
    package_name = models.CharField(max_length=64)
    rank = models.IntegerField(default=200)
    date_hour = models.CharField(max_length=16)

    def from_rank(self, r: Ranked):
        self.app_name = r.app_name
        self.package_name = r.package_name
        self.market = r.market
        self.rank = r.rank
        self.deal_type = r.deal_type
        self.rank_type = r.rank_type
        self.icon_url = r.icon_url
        self.date_hour = timezone.now().strftime("%Y%m%d%H")
        self.save()
