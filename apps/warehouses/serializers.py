from rest_framework import serializers
from .models import Location, Warehouse, Zone


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ["id", "code", "name_ar", "name_en", "address", "is_active", "created_at", "updated_at", "version"]
        read_only_fields = ["id", "created_at", "updated_at", "version"]


class ZoneSerializer(serializers.ModelSerializer):
    warehouse_name = serializers.CharField(source="warehouse.name_ar", read_only=True)

    class Meta:
        model = Zone
        fields = ["id", "warehouse", "warehouse_name", "code", "name", "created_at"]
        read_only_fields = ["id", "created_at"]


class LocationSerializer(serializers.ModelSerializer):
    warehouse_name = serializers.CharField(source="warehouse.name_ar", read_only=True)
    zone_code = serializers.CharField(source="zone.code", read_only=True)

    class Meta:
        model = Location
        fields = ["id", "warehouse", "warehouse_name", "zone", "zone_code", "parent", "code", "name", "location_type", "capacity", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        zone = attrs.get("zone", getattr(self.instance, "zone", None))
        warehouse = attrs.get("warehouse", getattr(self.instance, "warehouse", None))
        if zone and warehouse and zone.warehouse_id != warehouse.id:
            raise serializers.ValidationError({"zone": "المنطقة لا تتبع المستودع المحدد."})
        return attrs
