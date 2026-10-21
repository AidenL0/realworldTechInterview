import pytest

from purchasing.models import Supplier

SUPPLIERS_URL = "/api/suppliers/"


@pytest.mark.django_db
def test_create_supplier_returns_201_with_defaults(api_client):
    response = api_client.post(
        SUPPLIERS_URL,
        {"name": "Harborline Metals", "contact_email": "sales@harborline.example"},
        format="json",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == Supplier.objects.get().id
    assert body["name"] == "Harborline Metals"
    assert body["payment_terms_days"] == 30
    assert body["is_active"] is True
    assert body["open_orders"] == 0


@pytest.mark.django_db
def test_create_supplier_rejects_payment_terms_over_120(api_client):
    response = api_client.post(
        SUPPLIERS_URL,
        {"name": "Slowpay Goods", "contact_email": "ap@slowpay.example", "payment_terms_days": 121},
        format="json",
    )

    assert response.status_code == 400
    assert "payment_terms_days" in response.json()
    assert Supplier.objects.count() == 0


@pytest.mark.django_db
def test_list_suppliers_sorted_by_name(api_client, make_supplier):
    make_supplier(name="Zephyr Tools")
    make_supplier(name="Alder Paper Co")
    make_supplier(name="Maple Freight")

    response = api_client.get(SUPPLIERS_URL)

    assert response.status_code == 200
    assert [s["name"] for s in response.json()] == ["Alder Paper Co", "Maple Freight", "Zephyr Tools"]


@pytest.mark.django_db
def test_list_suppliers_filtered_by_inactive(api_client, make_supplier):
    make_supplier(name="Active Supplies", is_active=True)
    retired = make_supplier(name="Retired Supplies", is_active=False)

    response = api_client.get(SUPPLIERS_URL, {"active": "false"})

    assert response.status_code == 200
    assert [s["id"] for s in response.json()] == [retired.id]
