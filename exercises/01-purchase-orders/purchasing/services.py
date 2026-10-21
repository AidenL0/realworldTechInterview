"""Business rules for purchase orders: money, status changes and payment dates."""
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .exceptions import Conflict
from .models import OrderLine, PurchaseOrder

CENT = Decimal("0.01")
ZERO = Decimal("0.00")


def to_money(amount):
    """Round an amount to whole cents, with halves rounded up."""
    return Decimal(amount).quantize(CENT, rounding=ROUND_HALF_UP)


# --- Money -------------------------------------------------------------------


def line_total(line):
    """Price of one line after its discount."""
    gross = line.unit_price * line.quantity
    discount = line.unit_price * line.discount_percent / 100
    return to_money(gross - discount)


def order_total(order):
    """Sum of the order's line totals."""
    return sum((line_total(line) for line in order.lines.all()), ZERO)


def line_count(order):
    return len(order.lines.all())


# --- Dates and counts --------------------------------------------------------


def payment_due_date(order):
    """The date the supplier must be paid by, or None until the order is approved."""
    if order.approved_at is None:
        return None
    approved_on = timezone.localdate(order.approved_at)
    return approved_on + timedelta(days=order.supplier.payment_terms_days)


def open_order_count(supplier):
    """Number of the supplier's orders that are still in draft or awaiting approval."""
    return supplier.purchase_orders.filter(status__in=PurchaseOrder.OPEN_STATUSES).count()


# --- Status changes ----------------------------------------------------------


def ensure_status(order, expected, message):
    if order.status != expected:
        raise Conflict(message)


def ensure_draft(order, message):
    ensure_status(order, PurchaseOrder.Status.DRAFT, message)


@transaction.atomic
def submit_order(order):
    ensure_draft(order, "Only draft orders can be submitted.")
    if not order.lines.exists:
        raise ValidationError({"lines": ["Add at least one line before submitting the order."]})
    order.status = PurchaseOrder.Status.SUBMITTED
    order.submitted_at = timezone.now()
    order.save(update_fields=["status", "submitted_at", "updated_at"])
    return order


@transaction.atomic
def add_line(order, *, sku, description, quantity, unit_price, discount_percent=0):
    ensure_draft(order, "Lines can only be added to draft orders.")
    line = OrderLine.objects.create(
        purchase_order=order,
        sku=sku,
        description=description,
        quantity=quantity,
        unit_price=unit_price,
        discount_percent=discount_percent,
    )
    order.save(update_fields=["updated_at"])
    return line
