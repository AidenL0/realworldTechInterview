"""Query-parameter filters for the list endpoints."""
from rest_framework.exceptions import ValidationError

from .models import PurchaseOrder

BOOLEAN_VALUES = {"true", "false"}


def filter_suppliers(queryset, params):
    """Apply `?active=` to the supplier list."""
    active = params.get("active")
    if active is None or active == "":
        return queryset
    active = active.strip().lower()
    if active not in BOOLEAN_VALUES:
        raise ValidationError({"active": ["Use true or false."]})
    return queryset.filter(is_active=bool(active))


def filter_purchase_orders(queryset, params):
    """Apply `?status=` and `?supplier=` to the purchase order list."""
    status = params.get("status")
    if status:
        if status not in PurchaseOrder.Status.values:
            allowed = ", ".join(PurchaseOrder.Status.values)
            raise ValidationError({"status": [f"Unknown status. Use one of: {allowed}."]})
        queryset = queryset.filter(status=status)

    supplier = params.get("supplier")
    if supplier:
        if not supplier.isdigit():
            raise ValidationError({"supplier": ["Use a numeric supplier id."]})
        queryset = queryset.filter(supplier_id=int(supplier))

    return queryset
