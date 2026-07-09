from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from apps.common.models import TimeStampedModel
from apps.warehouses.models import Location, Warehouse

class Category(TimeStampedModel):
    name_ar = models.CharField(max_length=120)
    name_en = models.CharField(max_length=120, blank=True)
    parent = models.ForeignKey("self", null=True, blank=True, related_name="children", on_delete=models.PROTECT)

    def __str__(self):
        return self.name_ar

class Brand(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.name

class Unit(TimeStampedModel):
    code = models.CharField(max_length=20, unique=True)
    name_ar = models.CharField(max_length=60)
    name_en = models.CharField(max_length=60, blank=True)

    def __str__(self):
        return self.name_ar

class Item(TimeStampedModel):
    code = models.CharField(max_length=40, unique=True)
    name_ar = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200, blank=True)
    category = models.ForeignKey(Category, related_name="items", on_delete=models.PROTECT)
    brand = models.ForeignKey(Brand, null=True, blank=True, related_name="items", on_delete=models.PROTECT)
    base_unit = models.ForeignKey(Unit, related_name="items", on_delete=models.PROTECT)
    primary_location = models.ForeignKey(Location, null=True, blank=True, related_name="primary_items", on_delete=models.PROTECT)
    minimum_stock = models.DecimalField(max_digits=14, decimal_places=3, default=0, validators=[MinValueValidator(Decimal("0"))])
    description = models.TextField(blank=True)
    weight = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    dimensions = models.JSONField(default=dict, blank=True)
    tracks_expiry = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        indexes = [models.Index(fields=["name_ar", "is_active"], name="item_name_active_idx")]

    def __str__(self):
        return f"{self.code} - {self.name_ar}"

class Barcode(TimeStampedModel):
    item = models.ForeignKey(Item, related_name="barcodes", on_delete=models.CASCADE)
    value = models.CharField(max_length=100, unique=True)
    is_primary = models.BooleanField(default=False)

class UnitConversion(TimeStampedModel):
    item = models.ForeignKey(Item, related_name="unit_conversions", on_delete=models.CASCADE)
    from_unit = models.ForeignKey(Unit, related_name="conversions_from", on_delete=models.PROTECT)
    to_unit = models.ForeignKey(Unit, related_name="conversions_to", on_delete=models.PROTECT)
    factor = models.DecimalField(max_digits=14, decimal_places=6, validators=[MinValueValidator(Decimal("0.000001"))])

    class Meta:
        constraints = [models.UniqueConstraint(fields=["item", "from_unit", "to_unit"], name="uq_item_unit_conversion")]

class StockBalance(TimeStampedModel):
    item = models.ForeignKey(Item, related_name="balances", on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, related_name="balances", on_delete=models.PROTECT)
    location = models.ForeignKey(Location, related_name="balances", on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=16, decimal_places=3, default=0)
    reserved_quantity = models.DecimalField(max_digits=16, decimal_places=3, default=0, validators=[MinValueValidator(Decimal("0"))])
    average_cost = models.DecimalField(max_digits=16, decimal_places=4, default=0, validators=[MinValueValidator(Decimal("0"))])

    class Meta:
        constraints = [models.UniqueConstraint(fields=["item", "warehouse", "location"], name="uq_stock_balance_location")]
        indexes = [models.Index(fields=["warehouse", "item"], name="balance_wh_item_idx")]

    @property
    def available_quantity(self):
        return self.quantity - self.reserved_quantity

class StockMovement(TimeStampedModel):
    class Type(models.TextChoices):
        OPENING="OPENING", "رصيد أول المدة"
        PURCHASE="PURCHASE", "شراء"
        TRANSFER_IN="TRANSFER_IN", "تحويل وارد"
        TRANSFER_OUT="TRANSFER_OUT", "تحويل صادر"
        PURCHASE_RTN="PURCHASE_RTN", "مرتجع شراء"
        SALE="SALE", "بيع"
        SALE_RTN="SALE_RTN", "مرتجع بيع"
        INTERNAL_USE="INTERNAL_USE", "صرف داخلي"
        STOCK_COUNT="STOCK_COUNT", "جرد"
        DAMAGE="DAMAGE", "إتلاف"
        ADJUSTMENT="ADJUSTMENT", "تصحيح"

    movement_type = models.CharField(max_length=20, choices=Type.choices, db_index=True)
    reference_number = models.CharField(max_length=60, db_index=True)
    reference_type = models.CharField(max_length=40, blank=True)
    item = models.ForeignKey(Item, related_name="movements", on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, related_name="movements", on_delete=models.PROTECT)
    location = models.ForeignKey(Location, related_name="movements", on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=16, decimal_places=3)
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT)
    unit_cost = models.DecimalField(max_digits=16, decimal_places=4, default=0, validators=[MinValueValidator(Decimal("0"))])
    total_cost = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    quantity_before = models.DecimalField(max_digits=16, decimal_places=3)
    quantity_after = models.DecimalField(max_digits=16, decimal_places=3)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="stock_movements", on_delete=models.PROTECT)
    notes = models.TextField(blank=True)
    is_approved = models.BooleanField(default=False, db_index=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="approved_stock_movements", on_delete=models.PROTECT)

    class Meta:
        indexes = [models.Index(fields=["item", "warehouse", "created_at"], name="movement_item_wh_date_idx")]
