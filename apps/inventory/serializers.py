from rest_framework import serializers
from .models import Barcode, Brand, Category, Item, StockBalance, StockMovement, Unit, UnitConversion


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name_ar", "name_en", "parent"]


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["id", "name"]


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ["id", "code", "name_ar", "name_en"]


class BarcodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Barcode
        fields = ["id", "value", "is_primary"]


class ItemSerializer(serializers.ModelSerializer):
    barcodes = BarcodeSerializer(many=True, required=False)
    available_quantity = serializers.DecimalField(max_digits=16, decimal_places=3, read_only=True)
    category_name = serializers.CharField(source="category.name_ar", read_only=True)
    brand_name = serializers.CharField(source="brand.name", read_only=True)
    base_unit_name = serializers.CharField(source="base_unit.name_ar", read_only=True)

    class Meta:
        model = Item
        fields = ["id", "code", "name_ar", "name_en", "category", "category_name", "brand", "brand_name", "base_unit", "base_unit_name", "primary_location", "minimum_stock", "description", "weight", "dimensions", "tracks_expiry", "is_active", "barcodes", "available_quantity", "created_at", "updated_at", "version"]
        read_only_fields = ["id", "available_quantity", "created_at", "updated_at", "version"]

    def create(self, validated_data):
        barcodes = validated_data.pop("barcodes", [])
        item = Item.objects.create(**validated_data)
        Barcode.objects.bulk_create([Barcode(item=item, **barcode) for barcode in barcodes])
        return item


class UnitConversionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitConversion
        fields = ["id", "item", "from_unit", "to_unit", "factor"]


class StockBalanceSerializer(serializers.ModelSerializer):
    available_quantity = serializers.DecimalField(max_digits=16, decimal_places=3, read_only=True)

    class Meta:
        model = StockBalance
        fields = ["id", "item", "warehouse", "location", "quantity", "reserved_quantity", "available_quantity", "average_cost", "updated_at", "version"]


class StockMovementSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="item.name_ar", read_only=True)
    warehouse_name = serializers.CharField(source="warehouse.name_ar", read_only=True)
    location_code = serializers.CharField(source="location.code", read_only=True)

    class Meta:
        model = StockMovement
        fields = ["id", "movement_type", "reference_number", "reference_type", "item", "item_name", "warehouse", "warehouse_name", "location", "location_code", "quantity", "unit", "unit_cost", "total_cost", "quantity_before", "quantity_after", "created_by", "notes", "is_approved", "approved_by", "created_at"]
        read_only_fields = ["id", "total_cost", "quantity_before", "quantity_after", "created_by", "is_approved", "approved_by", "created_at"]

    def validate(self, attrs):
        if attrs["location"].warehouse_id != attrs["warehouse"].id:
            raise serializers.ValidationError({"location": "الموقع لا يتبع المستودع المحدد."})
        return attrs
