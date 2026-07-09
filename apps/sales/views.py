from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from apps.common.audit import log_audit
from .models import Customer, SalesOrder, Shipment
from .serializers import CustomerSerializer, SalesOrderSerializer, ShipmentSerializer


class CustomerViewSet(ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    filterset_fields = ["is_active"]
    search_fields = ["code", "name", "phone", "email", "tax_number"]
    ordering_fields = ["code", "name", "created_at"]

    def perform_create(self, serializer):
        instance = serializer.save()
        log_audit(request=self.request, action="CREATE", instance=instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        log_audit(request=self.request, action="UPDATE", instance=instance)


class SalesOrderViewSet(ModelViewSet):
    queryset = SalesOrder.objects.select_related("customer", "warehouse", "created_by").prefetch_related("lines__item", "lines__unit")
    serializer_class = SalesOrderSerializer
    filterset_fields = ["status", "customer", "warehouse"]
    search_fields = ["number", "customer__name"]
    ordering_fields = ["created_at", "number"]

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        order = self.get_object()
        order.status = SalesOrder.Status.APPROVED
        order.save(update_fields=["status", "updated_at"])
        log_audit(request=request, action="APPROVE", instance=order)
        return Response(self.get_serializer(order).data)

    def perform_create(self, serializer):
        instance = serializer.save()
        log_audit(request=self.request, action="CREATE", instance=instance)


class ShipmentViewSet(ModelViewSet):
    http_method_names = ["get", "post", "head", "options"]
    queryset = Shipment.objects.select_related("sales_order", "warehouse", "location", "created_by").prefetch_related("lines__order_line__item")
    serializer_class = ShipmentSerializer
    filterset_fields = ["sales_order", "warehouse", "location"]
    search_fields = ["number", "sales_order__number"]
    ordering_fields = ["created_at", "number"]

    def perform_create(self, serializer):
        instance = serializer.save()
        log_audit(request=self.request, action="CREATE", instance=instance)
