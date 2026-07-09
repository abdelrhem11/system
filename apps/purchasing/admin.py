from django.contrib import admin
from .models import GoodsReceipt, GoodsReceiptLine, PurchaseOrder, PurchaseOrderLine, Supplier

admin.site.register([Supplier, PurchaseOrder, PurchaseOrderLine, GoodsReceipt, GoodsReceiptLine])
