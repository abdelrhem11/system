from django.db import transaction
from rest_framework import serializers
from apps.inventory.models import StockMovement
from apps.inventory.services import record_movement
from .models import GoodsReceipt, GoodsReceiptLine, PurchaseOrder, PurchaseOrderLine, Supplier


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ["id", "code", "name", "phone", "email", "tax_number", "address", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class PurchaseOrderLineSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="item.name_ar", read_only=True)
    unit_name = serializers.CharField(source="unit.name_ar", read_only=True)

    class Meta:
        model = PurchaseOrderLine
        fields = ["id", "item", "item_name", "unit", "unit_name", "quantity", "unit_cost", "received_quantity"]
        read_only_fields = ["id", "received_quantity"]


class PurchaseOrderSerializer(serializers.ModelSerializer):
    lines = PurchaseOrderLineSerializer(many=True)
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    warehouse_name = serializers.CharField(source="warehouse.name_ar", read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = ["id", "number", "supplier", "supplier_name", "warehouse", "warehouse_name", "status", "expected_date", "notes", "created_by", "lines", "created_at", "updated_at"]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    @transaction.atomic
    def create(self, validated_data):
        lines = validated_data.pop("lines")
        order = PurchaseOrder.objects.create(created_by=self.context["request"].user, **validated_data)
        PurchaseOrderLine.objects.bulk_create([PurchaseOrderLine(order=order, **line) for line in lines])
        return order

    @transaction.atomic
    def update(self, instance, validated_data):
        lines = validated_data.pop("lines", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        if lines is not None and instance.status == PurchaseOrder.Status.DRAFT:
            instance.lines.all().delete()
            PurchaseOrderLine.objects.bulk_create([PurchaseOrderLine(order=instance, **line) for line in lines])
        return instance


class GoodsReceiptLineSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="order_line.item.name_ar", read_only=True)

    class Meta:
        model = GoodsReceiptLine
        fields = ["id", "order_line", "item_name", "quantity", "unit_cost"]
        read_only_fields = ["id"]


class GoodsReceiptSerializer(serializers.ModelSerializer):
    lines = GoodsReceiptLineSerializer(many=True)
    order_number = serializers.CharField(source="purchase_order.number", read_only=True)
    warehouse_name = serializers.CharField(source="warehouse.name_ar", read_only=True)
    location_code = serializers.CharField(source="location.code", read_only=True)

    class Meta:
        model = GoodsReceipt
        fields = ["id", "number", "purchase_order", "order_number", "warehouse", "warehouse_name", "location", "location_code", "notes", "created_by", "lines", "created_at"]
        read_only_fields = ["id", "created_by", "created_at"]

    def validate(self, attrs):
        if attrs["location"].warehouse_id != attrs["warehouse"].id:
            raise serializers.ValidationError({"location": "الموقع لا يتبع المستودع المحدد."})
        if attrs["purchase_order"].warehouse_id != attrs["warehouse"].id:
            raise serializers.ValidationError({"warehouse": "المستودع لا يطابق أمر الشراء."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        lines = validated_data.pop("lines")
        receipt = GoodsReceipt.objects.create(created_by=self.context["request"].user, **validated_data)
        for line in lines:
            receipt_line = GoodsReceiptLine.objects.create(receipt=receipt, **line)
            order_line = receipt_line.order_line
            order_line.received_quantity += receipt_line.quantity
            order_line.save(update_fields=["received_quantity", "updated_at"])
            record_movement(user=self.context["request"].user, validated_data={"movement_type": StockMovement.Type.PURCHASE, "reference_number": receipt.number, "reference_type": "GOODS_RECEIPT", "item": order_line.item, "warehouse": receipt.warehouse, "location": receipt.location, "quantity": receipt_line.quantity, "unit": order_line.unit, "unit_cost": receipt_line.unit_cost, "notes": receipt.notes})
        order = receipt.purchase_order
        total = sum(line.quantity for line in order.lines.all())
        received = sum(line.received_quantity for line in order.lines.all())
        order.status = PurchaseOrder.Status.RECEIVED if received >= total else PurchaseOrder.Status.PARTIALLY_RECEIVED
        order.save(update_fields=["status", "updated_at"])
        return receipt
