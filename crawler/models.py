from django.db import models
# Create your models here.


class Timestamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    class Meta:
        abstract = True


class TimeIndex(models.Model):
    class Meta:
        verbose_name = "스크랩 시간"
        verbose_name_plural = "스크랩한 시간"

    def __str__(self):
        return self.date
    date = models.CharField(max_length=16, verbose_name="날짜", db_index=True)


class App(models.Model):
    class Meta:
        verbose_name_plural = "애플리케이션"
        verbose_name = "애플리케이션"

    def __str__(self):
        return self.app_name

    app_name = models.CharField(max_length=64, verbose_name="앱 이름")
    icon_url = models.URLField(max_length=200, verbose_name="아이콘 이미지")
    market_appid = models.CharField(max_length=64, verbose_name="스토어 아이디")


class Ranked(Timestamped):
    class Meta:
        verbose_name_plural = "랭킹"
        verbose_name = "랭킹"

    DEAL_TYPE = (("realtime_rank", "실시간"), ("market_rank", "일간"))
    MARKET = (("google", "구글 플레이"), ("apple", "앱 스토어"), ("one", "원 스토어"))
    CHART_TYPE = (("free", "무료 순위"), ("paid", "유료 순위"), ("gross", "매출 순위"))
    APP_TYPE = (("game", "게임"), ("app", "애플리케이션"))

    market = models.CharField(max_length=16, choices=MARKET, verbose_name="마켓명")
    deal_type = models.CharField(max_length=16, choices=DEAL_TYPE, verbose_name="기간")
    app_type = models.CharField(max_length=16, choices=APP_TYPE, verbose_name="앱 타입")
    chart_type = models.CharField(max_length=16, choices=CHART_TYPE, verbose_name="차트 타입")

    app_name = models.CharField(max_length=64, verbose_name="앱 이름")
    date = models.ForeignKey(TimeIndex, on_delete=models.DO_NOTHING)
    app = models.ForeignKey(App, on_delete=models.CASCADE, verbose_name="애플리케이션")
    market_appid = models.CharField(max_length=64, verbose_name="스토어 ID")
    rank = models.IntegerField(verbose_name="순위")
    icon_url = models.URLField(max_length=200, verbose_name="아이콘 이미지")


class Following(Timestamped):
    class Meta:
        verbose_name_plural = "순위 추적"
        verbose_name = "순위 추적"

    app_name = models.CharField(max_length=64, verbose_name="앱 이름")
    market_appid = models.CharField(max_length=64, null=True, verbose_name="패키지명")
    is_active = models.BooleanField(default=True, verbose_name="추적 중 여부")
    market = models.CharField(max_length=16, choices=Ranked.MARKET, verbose_name="마켓명")


class TrackingApps(Timestamped):
    class Meta:
        verbose_name_plural = "추적 결과"
        verbose_name = "추적 결과"

    app = models.ForeignKey(App, on_delete=models.CASCADE, verbose_name="애플리케이션")
    following = models.ForeignKey(Following, verbose_name="추적 ID", on_delete=models.CASCADE)

    deal_type = models.CharField(max_length=16, verbose_name="기간")
    market = models.CharField(max_length=16, verbose_name="마켓명")
    chart_type = models.CharField(max_length=16, verbose_name="차트 타입")
    app_name = models.CharField(max_length=64, verbose_name="앱 이름")
    icon_url = models.URLField(max_length=200, verbose_name="아이콘 이미지")
    market_appid = models.CharField(max_length=64, null=True, verbose_name="패키지명")
    rank = models.IntegerField(default=200, verbose_name="순위")
    date = models.ForeignKey(TimeIndex, on_delete=models.DO_NOTHING)


class OneStoreDL(Timestamped):
    class Meta:
        verbose_name_plural = "원스토어 순위"
        verbose_name = "원스토어 순위"

    app = models.ForeignKey(App, on_delete=models.CASCADE, verbose_name="애플리케이션")
    market_appid = models.CharField(max_length=32, verbose_name="스토어 ID")
    app_name = models.CharField(max_length=128, verbose_name="앱 이름")
    icon_url = models.URLField(default=None, verbose_name="앱 아이콘")
    genre = models.CharField(max_length=128, verbose_name="장르")
    downloads = models.IntegerField(verbose_name="다운로드수", null=True)
    volume = models.CharField(max_length=128, verbose_name="용량")
    date = models.ForeignKey(TimeIndex, on_delete=models.DO_NOTHING)
    released = models.DateField(verbose_name="출시일", null=True)
