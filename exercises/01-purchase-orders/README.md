# Purchase Orders API

## Overview

A company's procurement team uses this REST API to manage suppliers and purchase orders. An
employee creates a **draft** order for one supplier, adds the products they need as order lines,
and **submits** it. A different person then **approves** it, which also fixes the date the supplier
must be paid by.

The API is built with Django and Django REST Framework (DRF) on SQLite. It is mostly written, but
it doesn't fully match this specification, and one endpoint hasn't been built yet.

**Your task:**

1. Make every endpoint behave exactly as this document describes. Wherever the code and this
   document disagree, this document is correct.
2. Implement the endpoint described in [Feature to implement](#feature-to-implement).

Your solution is graded by the visible tests in `tests/` plus hidden tests that check the same
rules. You don't need to add tests, and changing the visible tests won't change your score.

## Project layout

| Path | What's in it |
|---|---|
| `procurement/` | Django project: settings and root URLs |
| `purchasing/models.py` | `Supplier`, `PurchaseOrder` and `OrderLine` |
| `purchasing/serializers.py` | Request validation and response shapes |
| `purchasing/views.py` | API views |
| `purchasing/filters.py` | Query-parameter filters for the list endpoints |
| `purchasing/services.py` | Business rules: money, status changes, payment dates |
| `purchasing/urls.py` | API routes |
| `purchasing/management/commands/seed.py` | Sample data loader |
| `tests/` | Visible tests |

## Data model

### Supplier

| Field | Type | Rules |
|---|---|---|
| `id` | integer | Read-only. |
| `name` | string | Required. At most 120 characters. Must be unique. |
| `contact_email` | string | Required. A valid email address. |
| `payment_terms_days` | integer | Optional, default `30`. From 0 to 120. The number of days between an order's approval and its payment due date. |
| `is_active` | boolean | Optional, default `true`. Purchase orders can't be raised for an inactive supplier. |
| `open_orders` | integer | Read-only, computed. The number of this supplier's purchase orders whose status is `draft` or `submitted`. |
| `created_at` | datetime | Read-only. |

### Purchase order

| Field | Type | Rules |
|---|---|---|
| `id` | integer | Read-only. |
| `number` | string | Read-only, computed. `PO-` followed by the id padded with zeros to 5 digits. For example, id 42 is `PO-00042`. |
| `supplier` | integer | Required. The id of an **active** supplier. |
| `supplier_name` | string | Read-only. The supplier's name. |
| `requested_by` | string | Required. At most 80 characters. The employee who needs the goods. |
| `needed_by` | date | Required, `YYYY-MM-DD`. Today or later. |
| `notes` | string | Optional. |
| `status` | string | Read-only. `draft`, `submitted` or `approved`. See [Order status](#order-status). |
| `lines` | list | Read-only. The order's lines, in the order they were added. Only in the full representation. |
| `line_count` | integer | Read-only, computed. The number of lines on the order. |
| `total` | decimal string | Read-only, computed. See [Money](#money). |
| `submitted_at` | datetime or `null` | Read-only. When the order was submitted. |
| `approved_by` | string | Read-only. Who approved the order; `""` until it's approved. |
| `approved_at` | datetime or `null` | Read-only. When the order was approved. |
| `payment_due_date` | date or `null` | Read-only, computed. The date part of `approved_at` (UTC) plus the supplier's `payment_terms_days`. `null` until the order is approved. |
| `created_at` | datetime | Read-only. |
| `updated_at` | datetime | Read-only. |

### Order line

| Field | Type | Rules |
|---|---|---|
| `id` | integer | Read-only. |
| `sku` | string | Required. At most 32 characters. Stored in upper case: `cbl-usbc-2m` is saved as `CBL-USBC-2M`. |
| `description` | string | Required. At most 200 characters. |
| `quantity` | integer | Required. At least 1. |
| `unit_price` | decimal string | Required. At most 2 decimal places. At least `0.01`. |
| `discount_percent` | integer | Optional, default `0`. From 0 to 50. |
| `line_total` | decimal string | Read-only, computed. See [Money](#money). |

### Money

- A line's **gross amount** is `quantity × unit_price`.
- `line_total` is the gross amount minus `discount_percent` percent of the gross amount, rounded to
  2 decimal places with halves rounded up (`ROUND_HALF_UP`).
  - 4 × `25.00` with a 10% discount: 100.00 − 10.00 = `"90.00"`.
  - 1 × `10.25` with a 10% discount: 10.25 − 1.025 = 9.225, which rounds to `"9.23"`.
- An order's `total` is the sum of its rounded `line_total` values. An order with no lines has a
  total of `"0.00"`.
- Money is always returned as a string with exactly two decimal places.

### Order status

```
draft ──submit──▶ submitted ──approve──▶ approved
```

- New orders always start as `draft`.
- `status` changes **only** through the submit and approve endpoints. It's read-only everywhere
  else: if a request body for create or update includes `status` (or any other read-only field),
  that field is ignored.
- Only `draft` orders can be edited or get new lines.
- A request that isn't allowed in the order's current status returns `409 Conflict` and changes
  nothing.

## Endpoints

All paths start with `/api/`. Request and response bodies are JSON. Lists aren't paginated.

**Errors**

| Status | When | Body |
|---|---|---|
| `400 Bad Request` | A field or query parameter is invalid | An object that maps each invalid field to a list of messages, for example `{"supplier": ["..."]}` |
| `404 Not Found` | No object has the id in the path | `{"detail": "..."}` |
| `405 Method Not Allowed` | The method isn't listed below (for example `PUT` or `DELETE`) | `{"detail": "..."}` |
| `409 Conflict` | The order's status doesn't allow the request | `{"detail": "..."}` |

The exact wording of error messages isn't graded. Status codes and the field names in `400`
responses are.

| # | Method | Path | Purpose |
|---|---|---|---|
| 1 | `GET` | `/api/suppliers/` | List suppliers |
| 2 | `POST` | `/api/suppliers/` | Create a supplier |
| 3 | `GET` | `/api/suppliers/{id}/` | Get a supplier |
| 4 | `GET` | `/api/purchase-orders/` | List purchase orders |
| 5 | `POST` | `/api/purchase-orders/` | Create a purchase order |
| 6 | `GET` | `/api/purchase-orders/{id}/` | Get a purchase order |
| 7 | `PATCH` | `/api/purchase-orders/{id}/` | Update a draft purchase order |
| 8 | `POST` | `/api/purchase-orders/{id}/lines/` | Add a line to a draft order |
| 9 | `POST` | `/api/purchase-orders/{id}/submit/` | Submit a draft order |
| 10 | `POST` | `/api/purchase-orders/{id}/approve/` | Approve a submitted order (**to implement**) |

### 1. List suppliers

`GET /api/suppliers/`

Returns all suppliers, sorted by `name` from A to Z.

| Query parameter | Effect |
|---|---|
| `active` | `true`: only active suppliers. `false`: only inactive suppliers. Any other value: `400`. When it's left out, every supplier is returned. |

Response `200 OK`:

```json
[
  {
    "id": 1,
    "name": "Brightwater Lab Equipment",
    "contact_email": "orders@brightwater-lab.example",
    "payment_terms_days": 45,
    "is_active": true,
    "open_orders": 2,
    "created_at": "2026-10-21T15:37:25.809273Z"
  },
  {
    "id": 5,
    "name": "Quillmark Printing",
    "contact_email": "hello@quillmark-print.example",
    "payment_terms_days": 15,
    "is_active": false,
    "open_orders": 0,
    "created_at": "2026-10-21T15:37:25.813763Z"
  }
]
```

Status codes: `200`; `400` for an invalid `active` value.

### 2. Create a supplier

`POST /api/suppliers/`

Request:

```json
{
  "name": "Harborline Metals",
  "contact_email": "sales@harborline.example",
  "payment_terms_days": 45
}
```

Response `201 Created`:

```json
{
  "id": 7,
  "name": "Harborline Metals",
  "contact_email": "sales@harborline.example",
  "payment_terms_days": 45,
  "is_active": true,
  "open_orders": 0,
  "created_at": "2026-10-21T15:37:28.484051Z"
}
```

Status codes: `201`; `400` if a field breaks a rule in [Supplier](#supplier), for example a
duplicate `name` or `payment_terms_days` above 120.

### 3. Get a supplier

`GET /api/suppliers/{id}/`

Response `200 OK`: one supplier, in the same shape as in the list.

Status codes: `200`; `404`.

### 4. List purchase orders

`GET /api/purchase-orders/`

Returns orders **newest first**: by `created_at`, latest first; orders with the same `created_at`
are sorted by `id`, highest first. Each item is the short representation below, without `notes`,
`lines` or the approval fields.

| Query parameter | Effect |
|---|---|
| `status` | Only orders with this status. Must be `draft`, `submitted` or `approved`; any other value returns `400`. |
| `supplier` | Only orders for the supplier with this id. Must be a whole number; anything else returns `400`. |

The two parameters can be combined.

Response `200 OK` for `GET /api/purchase-orders/?status=submitted`:

```json
[
  {
    "id": 4,
    "number": "PO-00004",
    "supplier": 4,
    "supplier_name": "Lanternfield Furniture",
    "requested_by": "Priya Raman",
    "needed_by": "2026-12-05",
    "status": "submitted",
    "line_count": 2,
    "total": "3558.72",
    "created_at": "2026-10-17T12:37:25.814457Z"
  },
  {
    "id": 2,
    "number": "PO-00002",
    "supplier": 1,
    "supplier_name": "Brightwater Lab Equipment",
    "requested_by": "Grace Okafor",
    "needed_by": "2026-11-11",
    "status": "submitted",
    "line_count": 2,
    "total": "1085.38",
    "created_at": "2026-10-15T12:37:25.814457Z"
  }
]
```

Status codes: `200`; `400` for an invalid `status` or `supplier` value.

### 5. Create a purchase order

`POST /api/purchase-orders/`

Request:

```json
{
  "supplier": 3,
  "requested_by": "Jordan Blake",
  "needed_by": "2026-11-04",
  "notes": "Printer paper for the fourth floor"
}
```

The new order is always a `draft` with no lines. Read-only fields in the request, such as
`status`, are ignored.

Response `201 Created`, the full representation:

```json
{
  "id": 9,
  "number": "PO-00009",
  "supplier": 3,
  "supplier_name": "Kestrel Office Supply",
  "requested_by": "Jordan Blake",
  "needed_by": "2026-11-04",
  "notes": "Printer paper for the fourth floor",
  "status": "draft",
  "lines": [],
  "line_count": 0,
  "total": "0.00",
  "submitted_at": null,
  "approved_by": "",
  "approved_at": null,
  "payment_due_date": null,
  "created_at": "2026-10-21T15:37:28.563641Z",
  "updated_at": "2026-10-21T15:37:28.563666Z"
}
```

Status codes: `201`; `400` if a field breaks a rule in [Purchase order](#purchase-order): a
missing field, an unknown or inactive supplier, or a `needed_by` date in the past.

### 6. Get a purchase order

`GET /api/purchase-orders/{id}/`

Response `200 OK`: the full representation, including `lines`:

```json
{
  "id": 9,
  "number": "PO-00009",
  "supplier": 3,
  "supplier_name": "Kestrel Office Supply",
  "requested_by": "Jordan Blake",
  "needed_by": "2026-11-04",
  "notes": "Deliver to loading dock B",
  "status": "submitted",
  "lines": [
    {
      "id": 16,
      "sku": "PAP-A4-500",
      "description": "A4 copier paper, 500 sheets",
      "quantity": 40,
      "unit_price": "4.85",
      "discount_percent": 10,
      "line_total": "174.60"
    }
  ],
  "line_count": 1,
  "total": "174.60",
  "submitted_at": "2026-10-21T15:37:28.654492Z",
  "approved_by": "",
  "approved_at": null,
  "payment_due_date": null,
  "created_at": "2026-10-21T15:37:28.563641Z",
  "updated_at": "2026-10-21T15:37:28.654570Z"
}
```

Status codes: `200`; `404`.

### 7. Update a purchase order

`PATCH /api/purchase-orders/{id}/`

Send any of `supplier`, `requested_by`, `needed_by` and `notes`. They follow the same rules as on
create. Read-only fields in the request, such as `status`, are ignored.

Request:

```json
{
  "notes": "Deliver to loading dock B"
}
```

Response `200 OK`: the full, updated order.

Status codes: `200`; `400`; `404`; `409` if the order isn't a draft (the order isn't changed).

### 8. Add a line to an order

`POST /api/purchase-orders/{id}/lines/`

Request:

```json
{
  "sku": "pap-a4-500",
  "description": "A4 copier paper, 500 sheets",
  "quantity": 40,
  "unit_price": "4.85",
  "discount_percent": 10
}
```

Response `201 Created`, the new line:

```json
{
  "id": 16,
  "sku": "PAP-A4-500",
  "description": "A4 copier paper, 500 sheets",
  "quantity": 40,
  "unit_price": "4.85",
  "discount_percent": 10,
  "line_total": "174.60"
}
```

Status codes: `201`; `400` if a field breaks a rule in [Order line](#order-line); `404`; `409` if
the order isn't a draft (no line is added).

### 9. Submit an order

`POST /api/purchase-orders/{id}/submit/`

No request body. Moves a `draft` order to `submitted` and sets `submitted_at` to the current time.
An order must have at least one line to be submitted.

Response `200 OK`: the full, updated order.

Status codes: `200`; `400` if the order has no lines (it stays a `draft`); `404`; `409` if the
order isn't a draft.

## Feature to implement

### 10. Approve an order

`POST /api/purchase-orders/{id}/approve/`

The route exists, but the view currently returns `501 Not Implemented`. Implement it.

Request:

```json
{
  "approver": "Dana Whitfield"
}
```

Rules:

- `approver` is required. It must be a non-blank string of at most 80 characters. Leading and
  trailing spaces are removed. Otherwise return `400` with an `approver` key.
- Only `submitted` orders can be approved. Any other status returns `409`.
- Nobody can approve their own order. If `approver` matches the order's `requested_by`, ignoring
  upper/lower case and leading/trailing spaces, return `400` with an `approver` key.
- On success, set `status` to `approved`, `approved_by` to the approver and `approved_at` to the
  current time, then return `200` with the full order. Its `payment_due_date` is now filled in
  (see [Purchase order](#purchase-order)).
- When the request is rejected, the order isn't changed.

Response `200 OK` (the supplier's `payment_terms_days` is 30):

```json
{
  "id": 9,
  "number": "PO-00009",
  "supplier": 3,
  "supplier_name": "Kestrel Office Supply",
  "requested_by": "Jordan Blake",
  "needed_by": "2026-11-04",
  "notes": "Deliver to loading dock B",
  "status": "approved",
  "lines": [
    {
      "id": 16,
      "sku": "PAP-A4-500",
      "description": "A4 copier paper, 500 sheets",
      "quantity": 40,
      "unit_price": "4.85",
      "discount_percent": 10,
      "line_total": "174.60"
    }
  ],
  "line_count": 1,
  "total": "174.60",
  "submitted_at": "2026-10-21T15:37:28.654492Z",
  "approved_by": "Dana Whitfield",
  "approved_at": "2026-10-21T15:37:28.683886Z",
  "payment_due_date": "2026-11-20",
  "created_at": "2026-10-21T15:37:28.563641Z",
  "updated_at": "2026-10-21T15:37:28.684021Z"
}
```

Status codes: `200`; `400`; `404`; `409` if the order isn't `submitted`.

## Environment

The harness has already installed Django, Django REST Framework, pytest and pytest-django, and VS
Code is set up to use that Python. When the exercise starts, the database is migrated and loaded
with sample data. Run these commands from this folder:

| Task | Command |
|---|---|
| Run the visible tests | `pytest tests -q` |
| Run a single test file | `pytest tests/test_suppliers.py -q` |
| Start the development server | `python manage.py runserver` |
| Reload the sample data | `python manage.py seed` |
| Recreate the database tables (after deleting `db.sqlite3`) | `python manage.py migrate` |

With the server running, open <http://127.0.0.1:8000/> to explore the API in DRF's browsable API.
`seed` deletes every supplier, order and line, then loads a fresh sample set, so you can run it as
often as you like. The tests don't use the sample data: each test creates its own.
