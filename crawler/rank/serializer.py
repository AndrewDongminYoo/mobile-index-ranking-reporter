from rest_framework import serializers

from crawler.models import Ranked, Following


class RankedApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ranked
        exclude = ("market_appid",)


class RankingFollowingSerializer(serializers.Serializer):
    app_name = serializers.CharField(max_length=64)
    package_name = serializers.CharField(max_length=64)
    market = serializers.CharField(max_length=32)

    def update(self, instance, validated_data):
        instance.market = validated_data.get("market")
        instance.app_name = validated_data.get("app_name")
        instance.package_name = validated_data.get("package_name")
        return instance.save()

    def create(self, validated_data):
        instance = Following()
        instance.market = validated_data.get("market")
        instance.app_name = validated_data.get("app_name")
        instance.package_name = validated_data.get("package_name")
        return instance.save()
