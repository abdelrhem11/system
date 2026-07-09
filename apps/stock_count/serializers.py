from django.db import transaction
from rest_framework import serializers
from apps.inventory.models import StockBalance, StockMovement
from apps.inventory.services import record_movement
from .models import StockCountLine, StockCountSession


class StockCountLineSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="item.name_ar", read_only=True)
    location_code = serializers.CharField(source="location.code", read_only=True)
    unit_name = serializers.CharField(source="unit.name_ar", read_only=True)

    class Meta:
        model = StockCountLine
        fields = ["id", "item", "item_name", "location", "location_code", "unit", "unit_name", "system_quantity", "counted_quantity", "difference_quantity", "notes"]
        read_only_fields = ["id", "system_quantity", "difference_quantity"]


class StockCountSessionSerializer(serializers.ModelSerializer):
    lines = StockCountLineSerializer(many=True)
    warehouse_name = serializers.CharField(source="warehouse.name_ar", read_only=True)
    location_code = serializers.CharField(source="location.code", read_only=True)

    class Meta:
        model = StockCountSession
        fields = ["id", "number", "warehouse", "warehouse_name", "location", "location_code", "status", "notes", "created_by", "approved_by", "lines", "created_at", "updated_at"]
        read_only_fields = ["id", "status", "created_by", "approved_by", "created_at", "updated_at"]

    def validate(self, attrs):
        location = attrs.get("location")
        warehouse = attrs.get("warehouse")
        if location and warehouse and location.warehouse_id != warehouse.id:
            raise serializers.ValidationError({"location": "الموقع لا يتبع المستودع المحدد."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        lines = validated_data.pop("lines")
        session = StockCountSession.objects.create(created_by=self.context["request"].user, status=StockCountSession.Status.COUNTING, **validated_data)
        for line in lines:
            balance = StockBalance.objects.filter(item=line["item"], warehouse=session.warehouse, location=line["location"]).first()
            system_quantity = balance.quantity if balance else 0
            counted_quantity = line["counted_quantity"]
            StockCountLine.objects.create(session=session, system_quantity=system_quantity, difference_quantity=counted_quantity - system_quantity, **line)
        return session

    @transaction.atomic
    def update(self, instance, validated_data):
        lines = validated_data.pop("lines", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        if lines is not None and instance.status != StockCountSession.Status.APPROVED:
            instance.lines.all().delete()
            for line in lines:
                balance = StockBalance.objects.filter(item=line["item"], warehouse=instance.warehouse, location=line["location"]).first()
                system_quantity = balance.quantity if balance else 0
                counted_quantity = line["counted_quantity"]
                StockCountLine.objects.create(session=instance, system_quantity=system_quantity, difference_quantity=counted_quantity - system_quantity, **line)
        return instance


def approve_session(*, session, user):
    with transaction.atomic():
        if session.status == StockCountSession.Status.APPROVED:
            return session
        for line in session.lines.select_related("item", "location", "unit"):
            if line.difference_quantity:
                record_movement(user=user, validated_data={"movement_type": StockMovement.Type.STOCK_COUNT, "reference_number": session.number, "reference_type": "STOCK_COUNT", "item": line.item, "warehouse": session.warehouse, "location": line.location, "quantity": line.difference_quantity, "unit": line.unit, "unit_cost": 0, "notes": line.notes or session.notes})
        session.status = StockCountSession.Status.APPROVED
        session.approved_by = user
        session.save(update_fields=["status", "approved_by", "updated_at"])
        return session
