from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from apps.common.models import TimeStampedModel
from apps.inventory.models import Item, Unit
from apps.warehouses.models import Location, Warehouse


class StockCountSession(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "مسودة"
        COUNTING = "COUNTING", "قيد العد"
        APPROVED = "APPROVED", "معتمد"
        CANCELLED = "CANCELLED", "ملغي"

    number = models.CharField(max_length=40, unique=True)
    warehouse = models.ForeignKey(Warehouse, related_name="stock_counts", on_delete=models.PROTECT)
    location = models.ForeignKey(Location, null=True, blank=True, related_name="stock_counts", on_delete=models.PROTECT)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT, db_index=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="stock_count_sessions", on_delete=models.PROTECT)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="approved_stock_count_sessions", on_delete=models.PROTECT)

    def __str__(self):
        return self.number


class StockCountLine(TimeStampedModel):
    session = models.ForeignKey(StockCountSession, related_name="lines", on_delete=models.CASCADE)
    item = models.ForeignKey(Item, related_name="stock_count_lines", on_delete=models.PROTECT)
    location = models.ForeignKey(Location, related_name="stock_count_lines", on_delete=models.PROTECT)
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT)
    system_quantity = models.DecimalField(max_digits=16, decimal_places=3, default=0)
    counted_quantity = models.DecimalField(max_digits=16, decimal_places=3, validators=[MinValueValidator(Decimal("0"))])
    difference_quantity = models.DecimalField(max_digits=16, decimal_places=3, default=0)
    notes = models.TextField(blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["session", "item", "location"], name="uq_count_session_item_location")]
