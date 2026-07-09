import csv
from django.db.models import DecimalField, F, Sum, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.inventory.models import Item, StockBalance, StockMovement


@extend_schema(responses=inline_serializer("InventoryReport", fields={"items_count": serializers.IntegerField(), "balances_count": serializers.IntegerField(), "stock_value": serializers.DecimalField(max_digits=20, decimal_places=4), "movements_count": serializers.IntegerField()}))
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def inventory_report(request):
    balances = StockBalance.objects.select_related("item", "warehouse", "location").order_by("warehouse__code", "item__code")
    if request.query_params.get("format") == "csv":
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="inventory-report.csv"'
        writer = csv.writer(response)
        writer.writerow(["item_code", "item_name", "warehouse", "location", "quantity", "reserved_quantity", "available_quantity", "average_cost"])
        for balance in balances:
            writer.writerow([balance.item.code, balance.item.name_ar, balance.warehouse.name_ar, balance.location.code, balance.quantity, balance.reserved_quantity, balance.available_quantity, balance.average_cost])
        return response
    totals = balances.aggregate(stock_value=Coalesce(Sum(F("quantity") * F("average_cost")), Value(0), output_field=DecimalField(max_digits=20, decimal_places=4)))
    return Response({"items_count": Item.objects.count(), "balances_count": balances.count(), "stock_value": totals["stock_value"], "movements_count": StockMovement.objects.count()})
