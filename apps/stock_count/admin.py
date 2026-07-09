from django.contrib import admin
from .models import StockCountLine, StockCountSession

admin.site.register([StockCountSession, StockCountLine])
