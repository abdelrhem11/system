from rest_framework.routers import DefaultRouter
from .views import LocationViewSet, WarehouseViewSet, ZoneViewSet
router = DefaultRouter()
router.register("warehouses", WarehouseViewSet)
router.register("zones", ZoneViewSet)
router.register("locations", LocationViewSet)
urlpatterns = router.urls

