import pytest


def lines_url(order):
    return f"/api/purchase-orders/{order.id}/lines/"


@pytest.mark.django_db
def test_add_line_returns_201(api_client, make_order):
    order = make_order()

    response = api_client.post(
        lines_url(order),
        {"sku": "cbl-usbc-2m", "description": "USB-C cable, 2 m", "quantity": 5, "unit_price": "3.20"},
        format="json",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["sku"] == "CBL-USBC-2M"
    assert body["discount_percent"] == 0
    assert body["line_total"] == "16.00"
    assert order.lines.count() == 1


@pytest.mark.django_db
def test_add_line_to_submitted_order_returns_409(api_client, make_order):
    order = make_order(status="submitted")

    response = api_client.post(
        lines_url(order),
        {"sku": "MON-27", "description": "27-inch monitor", "quantity": 1, "unit_price": "219.00"},
        format="json",
    )

    assert response.status_code == 409
    assert order.lines.count() == 0
