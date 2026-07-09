from django.db.models import DecimalField, F, Sum, Value
from django.db.models.functions import Coalesce
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from apps.common.audit import log_audit
from .models import Brand, Category, Item, StockBalance, StockMovement, Unit, UnitConversion
from .serializers import BrandSerializer, CategorySerializer, ItemSerializer, StockBalanceSerializer, StockMovementSerializer, UnitConversionSerializer, UnitSerializer
from .services import record_movement

@extend_schema_view(by_barcode=extend_schema(parameters=[OpenApiParameter("barcode", str, OpenApiParameter.PATH)]))
class ItemViewSet(ModelViewSet):
    serializer_class = ItemSerializer
    filterset_fields = ["category", "brand", "base_unit", "is_active", "tracks_expiry"]
    search_fields = ["code", "name_ar", "name_en", "barcodes__value"]
    ordering_fields = ["code", "name_ar", "created_at", "minimum_stock"]

    def get_queryset(self):
        return Item.objects.select_related("category", "brand", "base_unit", "primary_location").prefetch_related("barcodes").annotate(available_quantity=Coalesce(Sum(F("balances__quantity") - F("balances__reserved_quantity")), Value(0), output_field=DecimalField(max_digits=16, decimal_places=3)))

    @action(detail=False, methods=["get"], url_path=r"barcode/(?P<barcode>[^/.]+)")
    def by_barcode(self, request, barcode=None):
        item = self.get_queryset().get(barcodes__value=barcode)
        return Response(self.get_serializer(item).data)

class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    search_fields = ["name_ar", "name_en"]

class BrandViewSet(ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    search_fields = ["name"]

class UnitViewSet(ModelViewSet):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    search_fields = ["code", "name_ar", "name_en"]

class UnitConversionViewSet(ModelViewSet):
    queryset = UnitConversion.objects.select_related("item", "from_unit", "to_unit")
    serializer_class = UnitConversionSerializer
    filterset_fields = ["item", "from_unit", "to_unit"]

class StockBalanceViewSet(ReadOnlyModelViewSet):
    queryset = StockBalance.objects.select_related("item", "warehouse", "location")
    serializer_class = StockBalanceSerializer
    filterset_fields = ["item", "warehouse", "location"]
    ordering_fields = ["quantity", "updated_at"]

class StockMovementViewSet(ModelViewSet):
    http_method_names = ["get", "post", "head", "options"]
    queryset = StockMovement.objects.select_related("item", "warehouse", "location", "unit", "created_by")
    serializer_class = StockMovementSerializer
    filterset_fields = ["movement_type", "item", "warehouse", "location", "is_approved"]
    search_fields = ["reference_number", "item__code", "item__name_ar"]
    ordering_fields = ["created_at", "quantity", "total_cost"]

    def perform_create(self, serializer):
        serializer.instance = record_movement(user=self.request.user, validated_data=serializer.validated_data)
        log_audit(request=self.request, action="CREATE", instance=serializer.instance)

@extend_schema(responses=inline_serializer("DashboardSummary", fields={"items_count": serializers.IntegerField(), "stock_value": serializers.DecimalField(max_digits=20, decimal_places=4), "low_stock_count": serializers.IntegerField(), "movements_today": serializers.IntegerField()}))
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_summary(request):
    totals = StockBalance.objects.aggregate(stock_value=Coalesce(Sum(F("quantity") * F("average_cost")), Value(0), output_field=DecimalField(max_digits=20, decimal_places=4)))
    low_stock = Item.objects.annotate(total=Coalesce(Sum("balances__quantity"), Value(0), output_field=DecimalField())).filter(total__lt=F("minimum_stock")).count()
    return Response({"items_count": Item.objects.count(), "stock_value": totals["stock_value"], "low_stock_count": low_stock, "movements_today": StockMovement.objects.filter(created_at__date=__import__("django").utils.timezone.localdate()).count()})
