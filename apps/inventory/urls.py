from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import BrandViewSet, CategoryViewSet, ItemViewSet, StockBalanceViewSet, StockMovementViewSet, UnitConversionViewSet, UnitViewSet, dashboard_summary
router = DefaultRouter()
router.register("items", ItemViewSet, basename="item")
router.register("categories", CategoryViewSet)
router.register("brands", BrandViewSet)
router.register("units", UnitViewSet)
router.register("unit-conversions", UnitConversionViewSet)
router.register("stock-balances", StockBalanceViewSet)
router.register("stock-movements", StockMovementViewSet)
urlpatterns = [path("dashboard/summary/", dashboard_summary)] + router.urls

