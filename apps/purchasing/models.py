from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from apps.common.models import TimeStampedModel
from apps.inventory.models import Item, Unit
from apps.warehouses.models import Location, Warehouse


class Supplier(TimeStampedModel):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=160)
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    tax_number = models.CharField(max_length=40, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    def __str__(self):
        return self.name


class PurchaseOrder(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "مسودة"
        APPROVED = "APPROVED", "معتمد"
        PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED", "مستلم جزئياً"
        RECEIVED = "RECEIVED", "مستلم"
        CANCELLED = "CANCELLED", "ملغي"

    number = models.CharField(max_length=40, unique=True)
    supplier = models.ForeignKey(Supplier, related_name="purchase_orders", on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, related_name="purchase_orders", on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)
    expected_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT)

    def __str__(self):
        return self.number


class PurchaseOrderLine(TimeStampedModel):
    order = models.ForeignKey(PurchaseOrder, related_name="lines", on_delete=models.CASCADE)
    item = models.ForeignKey(Item, related_name="purchase_lines", on_delete=models.PROTECT)
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=16, decimal_places=3, validators=[MinValueValidator(Decimal("0.001"))])
    unit_cost = models.DecimalField(max_digits=16, decimal_places=4, default=0, validators=[MinValueValidator(Decimal("0"))])
    received_quantity = models.DecimalField(max_digits=16, decimal_places=3, default=0)


class GoodsReceipt(TimeStampedModel):
    number = models.CharField(max_length=40, unique=True)
    purchase_order = models.ForeignKey(PurchaseOrder, related_name="receipts", on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, related_name="goods_receipts", on_delete=models.PROTECT)
    location = models.ForeignKey(Location, related_name="goods_receipts", on_delete=models.PROTECT)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT)

    def __str__(self):
        return self.number


class GoodsReceiptLine(TimeStampedModel):
    receipt = models.ForeignKey(GoodsReceipt, related_name="lines", on_delete=models.CASCADE)
    order_line = models.ForeignKey(PurchaseOrderLine, related_name="receipt_lines", on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=16, decimal_places=3, validators=[MinValueValidator(Decimal("0.001"))])
    unit_cost = models.DecimalField(max_digits=16, decimal_places=4, default=0, validators=[MinValueValidator(Decimal("0"))])
