from rest_framework.routers import DefaultRouter
from .views import StockCountSessionViewSet

router = DefaultRouter()
router.register("stock-count-sessions", StockCountSessionViewSet)
urlpatterns = router.urls
