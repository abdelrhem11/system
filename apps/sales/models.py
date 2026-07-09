from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from apps.common.models import TimeStampedModel
from apps.inventory.models import Item, Unit
from apps.warehouses.models import Location, Warehouse


class Customer(TimeStampedModel):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=160)
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    tax_number = models.CharField(max_length=40, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    def __str__(self):
        return self.name


class SalesOrder(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "مسودة"
        APPROVED = "APPROVED", "معتمد"
        PARTIALLY_SHIPPED = "PARTIALLY_SHIPPED", "مصروف جزئياً"
        SHIPPED = "SHIPPED", "مصروف"
        CANCELLED = "CANCELLED", "ملغي"

    number = models.CharField(max_length=40, unique=True)
    customer = models.ForeignKey(Customer, related_name="sales_orders", on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, related_name="sales_orders", on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT)

    def __str__(self):
        return self.number


class SalesOrderLine(TimeStampedModel):
    order = models.ForeignKey(SalesOrder, related_name="lines", on_delete=models.CASCADE)
    item = models.ForeignKey(Item, related_name="sales_lines", on_delete=models.PROTECT)
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=16, decimal_places=3, validators=[MinValueValidator(Decimal("0.001"))])
    unit_price = models.DecimalField(max_digits=16, decimal_places=4, default=0, validators=[MinValueValidator(Decimal("0"))])
    shipped_quantity = models.DecimalField(max_digits=16, decimal_places=3, default=0)


class Shipment(TimeStampedModel):
    number = models.CharField(max_length=40, unique=True)
    sales_order = models.ForeignKey(SalesOrder, related_name="shipments", on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, related_name="shipments", on_delete=models.PROTECT)
    location = models.ForeignKey(Location, related_name="shipments", on_delete=models.PROTECT)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT)

    def __str__(self):
        return self.number


class ShipmentLine(TimeStampedModel):
    shipment = models.ForeignKey(Shipment, related_name="lines", on_delete=models.CASCADE)
    order_line = models.ForeignKey(SalesOrderLine, related_name="shipment_lines", on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=16, decimal_places=3, validators=[MinValueValidator(Decimal("0.001"))])
