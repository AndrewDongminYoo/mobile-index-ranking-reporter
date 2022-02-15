from django.db import models
# Create your models here.
from django.utils import timezone


class Timestamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    class Meta:
        abstract = True


class App(models.Model):
    def __str__(self):
        return self.app_name

    class Meta:
        verbose_name_plural = "애플리케이션"
        verbose_name = "애플리케이션"

    app_name = models.CharField(max_length=64, verbose_name="앱 이름")
    icon_url = models.URLField(max_length=200, verbose_name="아이콘 이미지")
    package_name = models.CharField(max_length=64, verbose_name="앱 아이디")

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert, force_update, using, update_fields)


class Ranked(Timestamped):
    class Meta:
        verbose_name_plural = "랭킹"
        verbose_name = "랭킹"

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
    app = models.ForeignKey(App, on_delete=models.CASCADE, verbose_name="애플리케이션")
    date = models.CharField(max_length=16, verbose_name="날짜", default=timezone.now().strftime("%Y%m%d%H"))
    deal_type = models.CharField(max_length=16, choices=DEAL_TYPE, verbose_name="기간")
    market = models.CharField(max_length=16, choices=MARKET, verbose_name="마켓명")
    rank_type = models.CharField(max_length=16, choices=RANK_TYPE, verbose_name="순위 타입")
    app_type = models.CharField(max_length=16, choices=[("game", "게임"), ("app", "애플리케이션")], verbose_name="앱 타입")
    market_appid = models.CharField(max_length=64, verbose_name="스토어 아이디")
    rank = models.IntegerField(verbose_name="순위")
    app_name = models.CharField(max_length=64, verbose_name="앱 이름")
    icon_url = models.URLField(max_length=200, verbose_name="아이콘 이미지")
    package_name = models.CharField(max_length=64, verbose_name="앱 아이디")


class Following(Timestamped):
    class Meta:
        verbose_name_plural = "순위 추적"
        verbose_name = "순위 추적"

    app = models.ForeignKey(App, on_delete=models.CASCADE, verbose_name="애플리케이션")
    app_name = models.CharField(max_length=64, verbose_name="앱 이름")


class TrackingApps(Timestamped):
    class Meta:
        verbose_name_plural = "추적 결과"
        verbose_name = "추적 결과"

    app = models.ForeignKey(App, on_delete=models.CASCADE, verbose_name="애플리케이션")
    deal_type = models.CharField(max_length=16, verbose_name="기간")
    market = models.CharField(max_length=16, verbose_name="마켓명")
    rank_type = models.CharField(max_length=16, verbose_name="순위 타입")
    app_name = models.CharField(max_length=64, verbose_name="앱 이름")
    icon_url = models.URLField(max_length=200, verbose_name="아이콘 이미지")
    package_name = models.CharField(max_length=64, verbose_name="앱 아이디")
    rank = models.IntegerField(default=200, verbose_name="순위")
    date_hour = models.CharField(max_length=16, verbose_name="일시")

    def from_rank(self, r: Ranked):
        self.app_id = r.app_id
        self.app_name = r.app_name
        self.package_name = r.package_name
        self.market = r.market
        self.rank = r.rank
        self.deal_type = r.deal_type
        self.rank_type = r.rank_type
        self.icon_url = r.icon_url
        self.date_hour = timezone.now().strftime("%Y%m%d%H")
        self.save()


class OneStoreDL(Timestamped):
    class Meta:
        verbose_name_plural = "원스토어 순위"
        verbose_name = "원스토어 순위"

    app = models.ForeignKey(App, on_delete=models.CASCADE, verbose_name="애플리케이션")
    market_appid = models.CharField(max_length=32, verbose_name="원스토어 ID")
    genre = models.CharField(max_length=128, verbose_name="장르")
    downloads = models.IntegerField(verbose_name="다운로드수", null=True)
    volume = models.CharField(max_length=128, verbose_name="용량")
    released = models.DateField(verbose_name="출시일", null=True)
    icon_url = models.URLField(default=None, verbose_name="앱 아이콘")
    app_name = models.CharField(max_length=128, default=None, verbose_name="앱 이름")
