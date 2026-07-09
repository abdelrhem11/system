from django.contrib import admin
from .models import Barcode, Brand, Category, Item, StockBalance, StockMovement, Unit, UnitConversion

admin.site.register([Barcode, Brand, Category, Item, StockBalance, StockMovement, Unit, UnitConversion])

