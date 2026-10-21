import pytest

from purchasing.models import PurchaseOrder

ORDERS_URL = "/api/purchase-orders/"


def order_url(order, action=""):
    return f"{ORDERS_URL}{order.id}/{action}"


@pytest.mark.django_db
def test_create_order_starts_as_draft(api_client, make_supplier, in_two_weeks):
    supplier = make_supplier(name="Kestrel Office Supply")

    response = api_client.post(
        ORDERS_URL,
        {
            "supplier": supplier.id,
            "requested_by": "Jordan Blake",
            "needed_by": in_two_weeks.isoformat(),
            "notes": "Printer paper for Q3",
        },
        format="json",
    )

    assert response.status_code == 201
    body = response.json()
    order = PurchaseOrder.objects.get()
    assert body["id"] == order.id
    assert body["number"] == f"PO-{order.id:05d}"
    assert body["status"] == "draft"
    assert body["supplier_name"] == "Kestrel Office Supply"
    assert body["lines"] == []
    assert body["total"] == "0.00"


@pytest.mark.django_db
def test_create_order_for_inactive_supplier_returns_400(api_client, make_supplier, in_two_weeks):
    supplier = make_supplier(is_active=False)

    response = api_client.post(
        ORDERS_URL,
        {"supplier": supplier.id, "requested_by": "Jordan Blake", "needed_by": in_two_weeks.isoformat()},
        format="json",
    )

    assert response.status_code == 400
    assert "supplier" in response.json()
    assert PurchaseOrder.objects.count() == 0


@pytest.mark.django_db
def test_list_orders_filtered_by_status(api_client, make_order):
    make_order(status="draft")
    submitted = make_order(status="submitted")
    make_order(status="approved")

    response = api_client.get(ORDERS_URL, {"status": "submitted"})

    assert response.status_code == 200
    assert [o["id"] for o in response.json()] == [submitted.id]


@pytest.mark.django_db
def test_list_orders_filtered_by_supplier_newest_first(api_client, make_supplier, make_order):
    supplier = make_supplier()
    first = make_order(supplier=supplier)
    make_order()
    second = make_order(supplier=supplier)

    response = api_client.get(ORDERS_URL, {"supplier": supplier.id})

    assert response.status_code == 200
    assert [o["id"] for o in response.json()] == [second.id, first.id]


@pytest.mark.django_db
def test_order_detail_includes_discounted_line_totals(api_client, make_order, make_line):
    order = make_order()
    make_line(order, quantity=4, unit_price="25.00", discount_percent=10)
    make_line(order, quantity=2, unit_price="12.50")

    response = api_client.get(order_url(order))

    assert response.status_code == 200
    body = response.json()
    assert [line["line_total"] for line in body["lines"]] == ["90.00", "25.00"]
    assert body["line_count"] == 2
    assert body["total"] == "115.00"


@pytest.mark.django_db
def test_update_submitted_order_returns_409(api_client, make_order):
    order = make_order(status="submitted")

    response = api_client.patch(order_url(order), {"notes": "Please rush"}, format="json")

    assert response.status_code == 409


@pytest.mark.django_db
def test_submit_order_with_lines(api_client, make_order, make_line):
    order = make_order()
    make_line(order, quantity=3)

    response = api_client.post(order_url(order, "submit/"))

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "submitted"
    assert body["submitted_at"] is not None


@pytest.mark.django_db
def test_submit_order_without_lines_returns_400(api_client, make_order):
    order = make_order()

    response = api_client.post(order_url(order, "submit/"))

    assert response.status_code == 400
