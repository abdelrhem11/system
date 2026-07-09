from rest_framework.routers import DefaultRouter
from .views import GoodsReceiptViewSet, PurchaseOrderViewSet, SupplierViewSet

router = DefaultRouter()
router.register("suppliers", SupplierViewSet)
router.register("purchase-orders", PurchaseOrderViewSet)
router.register("goods-receipts", GoodsReceiptViewSet)
urlpatterns = router.urls
