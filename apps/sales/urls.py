from rest_framework.routers import DefaultRouter
from .views import CustomerViewSet, SalesOrderViewSet, ShipmentViewSet

router = DefaultRouter()
router.register("customers", CustomerViewSet)
router.register("sales-orders", SalesOrderViewSet)
router.register("shipments", ShipmentViewSet)
urlpatterns = router.urls
