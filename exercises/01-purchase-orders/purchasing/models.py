from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

MAX_PAYMENT_TERMS_DAYS = 120
MAX_DISCOUNT_PERCENT = 50


class Supplier(models.Model):
    """A company the procurement team buys from."""

    name = models.CharField(max_length=120, unique=True)
    contact_email = models.EmailField()
    payment_terms_days = models.PositiveIntegerField(
        default=30,
        validators=[MaxValueValidator(MAX_PAYMENT_TERMS_DAYS)],
        help_text="Days between approval and the payment due date.",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class PurchaseOrder(models.Model):
    """A request to buy goods from one supplier."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        APPROVED = "approved", "Approved"

    OPEN_STATUSES = (Status.DRAFT, Status.SUBMITTED)

    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="purchase_orders")
    requested_by = models.CharField(max_length=80)
    needed_by = models.DateField()
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.CharField(max_length=80, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.number} ({self.supplier})"

    @property
    def number(self):
        """Human-friendly order number, for example PO-00042."""
        if self.pk is None:
            return None
        return f"PO-{self.pk:05d}"

    @property
    def is_draft(self):
        return self.status == self.Status.DRAFT


class OrderLine(models.Model):
    """One product on a purchase order."""

    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="lines")
    sku = models.CharField(max_length=32)
    description = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    discount_percent = models.PositiveSmallIntegerField(
        default=0,
        validators=[MaxValueValidator(MAX_DISCOUNT_PERCENT)],
    )

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.quantity} x {self.sku}"
