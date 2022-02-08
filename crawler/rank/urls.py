from rest_framework import routers

from crawler.rank.apis import RankedApplicationView

router = routers.DefaultRouter()
router.register(r'rank', RankedApplicationView)
