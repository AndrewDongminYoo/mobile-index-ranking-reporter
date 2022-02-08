from ninja import NinjaAPI
from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response

from crawler.models import Ranked
from crawler.rank.serializer import RankedApplicationSerializer
from crawler.rank.serializer import RankingFollowingSerializer

api = NinjaAPI(title="Ninja")


class RankedApplicationView(viewsets.ModelViewSet):
    queryset = Ranked.objects.order_by("created_at")
    serializer_class = RankedApplicationSerializer

    def create(self, request):
        serializer = RankingFollowingSerializer(data=request.data)
        if serializer.is_valid():
            rtn = serializer.create(request, serializer.data)
            return Response(RankedApplicationView(rtn).data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def partial_update(self, request):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def destroy(self, request):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(data=instance, status=status.HTTP_204_NO_CONTENT)

    def list(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
