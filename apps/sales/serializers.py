from django.db import transaction
from rest_framework import serializers
from apps.inventory.models import StockMovement
from apps.inventory.services import record_movement
from .models import Customer, SalesOrder, SalesOrderLine, Shipment, ShipmentLine


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "code", "name", "phone", "email", "tax_number", "address", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class SalesOrderLineSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="item.name_ar", read_only=True)
    unit_name = serializers.CharField(source="unit.name_ar", read_only=True)

    class Meta:
        model = SalesOrderLine
        fields = ["id", "item", "item_name", "unit", "unit_name", "quantity", "unit_price", "shipped_quantity"]
        read_only_fields = ["id", "shipped_quantity"]


class SalesOrderSerializer(serializers.ModelSerializer):
    lines = SalesOrderLineSerializer(many=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    warehouse_name = serializers.CharField(source="warehouse.name_ar", read_only=True)

    class Meta:
        model = SalesOrder
        fields = ["id", "number", "customer", "customer_name", "warehouse", "warehouse_name", "status", "notes", "created_by", "lines", "created_at", "updated_at"]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    @transaction.atomic
    def create(self, validated_data):
        lines = validated_data.pop("lines")
        order = SalesOrder.objects.create(created_by=self.context["request"].user, **validated_data)
        SalesOrderLine.objects.bulk_create([SalesOrderLine(order=order, **line) for line in lines])
        return order

    @transaction.atomic
    def update(self, instance, validated_data):
        lines = validated_data.pop("lines", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        if lines is not None and instance.status == SalesOrder.Status.DRAFT:
            instance.lines.all().delete()
            SalesOrderLine.objects.bulk_create([SalesOrderLine(order=instance, **line) for line in lines])
        return instance


class ShipmentLineSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="order_line.item.name_ar", read_only=True)

    class Meta:
        model = ShipmentLine
        fields = ["id", "order_line", "item_name", "quantity"]
        read_only_fields = ["id"]


class ShipmentSerializer(serializers.ModelSerializer):
    lines = ShipmentLineSerializer(many=True)
    order_number = serializers.CharField(source="sales_order.number", read_only=True)
    warehouse_name = serializers.CharField(source="warehouse.name_ar", read_only=True)
    location_code = serializers.CharField(source="location.code", read_only=True)

    class Meta:
        model = Shipment
        fields = ["id", "number", "sales_order", "order_number", "warehouse", "warehouse_name", "location", "location_code", "notes", "created_by", "lines", "created_at"]
        read_only_fields = ["id", "created_by", "created_at"]

    def validate(self, attrs):
        if attrs["location"].warehouse_id != attrs["warehouse"].id:
            raise serializers.ValidationError({"location": "الموقع لا يتبع المستودع المحدد."})
        if attrs["sales_order"].warehouse_id != attrs["warehouse"].id:
            raise serializers.ValidationError({"warehouse": "المستودع لا يطابق أمر البيع."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        lines = validated_data.pop("lines")
        shipment = Shipment.objects.create(created_by=self.context["request"].user, **validated_data)
        for line in lines:
            shipment_line = ShipmentLine.objects.create(shipment=shipment, **line)
            order_line = shipment_line.order_line
            order_line.shipped_quantity += shipment_line.quantity
            order_line.save(update_fields=["shipped_quantity", "updated_at"])
            record_movement(user=self.context["request"].user, validated_data={"movement_type": StockMovement.Type.SALE, "reference_number": shipment.number, "reference_type": "SHIPMENT", "item": order_line.item, "warehouse": shipment.warehouse, "location": shipment.location, "quantity": shipment_line.quantity, "unit": order_line.unit, "unit_cost": 0, "notes": shipment.notes})
        order = shipment.sales_order
        total = sum(line.quantity for line in order.lines.all())
        shipped = sum(line.shipped_quantity for line in order.lines.all())
        order.status = SalesOrder.Status.SHIPPED if shipped >= total else SalesOrder.Status.PARTIALLY_SHIPPED
        order.save(update_fields=["status", "updated_at"])
        return shipment
