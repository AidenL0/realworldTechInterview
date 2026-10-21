"""Replace all data with a small, realistic data set for the browsable API.

Run it as often as you like: it deletes every supplier, order and line first.
"""
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from purchasing.models import OrderLine, PurchaseOrder, Supplier

SUPPLIERS = [
    # name, contact email, payment terms (days), active
    ("Brightwater Lab Equipment", "orders@brightwater-lab.example", 45, True),
    ("Ironbark Industrial Parts", "sales@ironbark-parts.example", 60, True),
    ("Kestrel Office Supply", "accounts@kestrel-office.example", 30, True),
    ("Lanternfield Furniture", "trade@lanternfield.example", 30, True),
    ("Quillmark Printing", "hello@quillmark-print.example", 15, False),
    ("Tidewell Packaging", "orders@tidewell-pack.example", 90, True),
]

# supplier, requested by, needed in N days, status, created N days ago, approver, notes, lines
# Each line is (sku, description, quantity, unit price, discount percent).
ORDERS = [
    (
        "Kestrel Office Supply", "Priya Raman", 10, "approved", 21, "Marcus Lee",
        "Quarterly restock for the third floor.",
        [
            ("PAP-A4-500", "A4 copier paper, 500 sheets", 40, "4.85", 10),
            ("PEN-GEL-BLK", "Black gel pens, box of 12", 15, "6.20", 0),
            ("TONER-K-210", "Black toner cartridge", 6, "72.50", 5),
        ],
    ),
    (
        "Brightwater Lab Equipment", "Grace Okafor", 21, "submitted", 6, "",
        "Replacement pipettes for the QA lab.",
        [
            ("PIP-10UL", "Single-channel pipette, 0.5-10 uL", 4, "189.00", 0),
            ("TIP-10UL-960", "Filter tips 10 uL, rack of 960", 10, "38.75", 15),
        ],
    ),
    (
        "Ironbark Industrial Parts", "Tomas Ortega", 30, "draft", 2, "",
        "Spare parts for line 2 maintenance window.",
        [
            ("BRG-6204-2RS", "Sealed ball bearing 6204-2RS", 24, "7.35", 0),
            ("BELT-V-A42", "V-belt, A42", 8, "12.90", 0),
        ],
    ),
    (
        "Lanternfield Furniture", "Priya Raman", 45, "submitted", 4, "",
        "Desks and chairs for the new hires in January.",
        [
            ("DSK-SIT-140", "Sit-stand desk, 140 cm", 6, "429.00", 12),
            ("CHR-ERG-02", "Ergonomic task chair", 6, "245.00", 12),
        ],
    ),
    (
        "Tidewell Packaging", "Marcus Lee", 14, "approved", 35, "Dana Whitfield",
        "",
        [
            ("BOX-DW-40", "Double-wall shipping box, 40 cm", 500, "1.18", 8),
            ("TAPE-PP-48", "Packing tape 48 mm, roll", 72, "2.15", 0),
            ("WRAP-BUB-50", "Bubble wrap, 50 m roll", 10, "24.60", 0),
        ],
    ),
    (
        "Kestrel Office Supply", "Grace Okafor", 7, "draft", 1, "",
        "Whiteboard supplies for the training room.",
        [
            ("MRK-WB-4", "Whiteboard markers, 4 colours", 12, "5.40", 0),
        ],
    ),
    (
        "Brightwater Lab Equipment", "Dana Whitfield", 60, "draft", 0, "",
        "Draft: waiting for the updated quote.",
        [],
    ),
    (
        "Ironbark Industrial Parts", "Marcus Lee", 5, "approved", 12, "Priya Raman",
        "Urgent: conveyor motor failed.",
        [
            ("MTR-075KW", "Three-phase motor, 0.75 kW", 1, "318.40", 0),
            ("CPL-JAW-19", "Jaw coupling, 19 mm bore", 2, "21.75", 0),
        ],
    ),
]


class Command(BaseCommand):
    help = "Delete all purchasing data and load a realistic sample data set."

    @transaction.atomic
    def handle(self, *args, **options):
        OrderLine.objects.all().delete()
        PurchaseOrder.objects.all().delete()
        Supplier.objects.all().delete()

        suppliers = {}
        for name, email, terms, active in SUPPLIERS:
            suppliers[name] = Supplier.objects.create(
                name=name,
                contact_email=email,
                payment_terms_days=terms,
                is_active=active,
            )

        now = timezone.now()
        today = timezone.localdate()
        line_count = 0
        for supplier_name, requester, needed_in, status, age_days, approver, notes, lines in ORDERS:
            created_at = now - timedelta(days=age_days, hours=3)
            order = PurchaseOrder.objects.create(
                supplier=suppliers[supplier_name],
                requested_by=requester,
                needed_by=today + timedelta(days=needed_in),
                notes=notes,
                status=status,
            )
            for sku, description, quantity, price, discount in lines:
                OrderLine.objects.create(
                    purchase_order=order,
                    sku=sku,
                    description=description,
                    quantity=quantity,
                    unit_price=Decimal(price),
                    discount_percent=discount,
                )
                line_count += 1

            changes = {"created_at": created_at}
            if status in (PurchaseOrder.Status.SUBMITTED, PurchaseOrder.Status.APPROVED):
                changes["submitted_at"] = created_at + timedelta(hours=2)
            if status == PurchaseOrder.Status.APPROVED:
                changes["approved_by"] = approver
                changes["approved_at"] = created_at + timedelta(days=1)
            # update() skips auto_now_add, so the sample orders get realistic ages.
            PurchaseOrder.objects.filter(pk=order.pk).update(**changes)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(SUPPLIERS)} suppliers, {len(ORDERS)} purchase orders and {line_count} order lines."
            )
        )
