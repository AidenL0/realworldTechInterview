from django.contrib import admin

from . import services
from .models import OrderLine, PurchaseOrder, Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ["name", "contact_email", "payment_terms_days", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name", "contact_email"]


class OrderLineInline(admin.TabularInline):
    model = OrderLine
    extra = 0


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ["id", "supplier", "requested_by", "status", "needed_by", "total"]
    list_filter = ["status", "supplier"]
    search_fields = ["requested_by", "notes"]
    inlines = [OrderLineInline]

    @admin.display(description="Total")
    def total(self, order):
        return services.order_total(order)
