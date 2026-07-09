from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from apps.common.audit import log_audit
from .models import GoodsReceipt, PurchaseOrder, Supplier
from .serializers import GoodsReceiptSerializer, PurchaseOrderSerializer, SupplierSerializer


class SupplierViewSet(ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    filterset_fields = ["is_active"]
    search_fields = ["code", "name", "phone", "email", "tax_number"]
    ordering_fields = ["code", "name", "created_at"]

    def perform_create(self, serializer):
        instance = serializer.save()
        log_audit(request=self.request, action="CREATE", instance=instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        log_audit(request=self.request, action="UPDATE", instance=instance)


class PurchaseOrderViewSet(ModelViewSet):
    queryset = PurchaseOrder.objects.select_related("supplier", "warehouse", "created_by").prefetch_related("lines__item", "lines__unit")
    serializer_class = PurchaseOrderSerializer
    filterset_fields = ["status", "supplier", "warehouse"]
    search_fields = ["number", "supplier__name"]
    ordering_fields = ["created_at", "expected_date", "number"]

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        order = self.get_object()
        order.status = PurchaseOrder.Status.APPROVED
        order.save(update_fields=["status", "updated_at"])
        log_audit(request=request, action="APPROVE", instance=order)
        return Response(self.get_serializer(order).data)

    def perform_create(self, serializer):
        instance = serializer.save()
        log_audit(request=self.request, action="CREATE", instance=instance)


class GoodsReceiptViewSet(ModelViewSet):
    http_method_names = ["get", "post", "head", "options"]
    queryset = GoodsReceipt.objects.select_related("purchase_order", "warehouse", "location", "created_by").prefetch_related("lines__order_line__item")
    serializer_class = GoodsReceiptSerializer
    filterset_fields = ["purchase_order", "warehouse", "location"]
    search_fields = ["number", "purchase_order__number"]
    ordering_fields = ["created_at", "number"]

    def perform_create(self, serializer):
        instance = serializer.save()
        log_audit(request=self.request, action="CREATE", instance=instance)
