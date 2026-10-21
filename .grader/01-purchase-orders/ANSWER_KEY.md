# Answer key: 01 · Purchase Orders API

Spoilers. Read this only after you've submitted at least once.

The exercise has one missing feature (`fix_01`) and six planted bugs (`fix_02` to `fix_07`). Each
patch in `fixes/` applies on its own to the starting code with `git apply`; `solution.patch` applies
all of them. Test paths are relative to `tests/`; hidden tests live in `tests/hidden/` at grading
time.

| Fix | Kind | Where | Difficulty | Caught by |
|---|---|---|---|---|
| `fix_01` | Missing feature | `purchasing/views.py` `approve` (+ serializer and service) | Feature | 2 visible, 3 hidden |
| `fix_02` | Calculation error | `purchasing/services.py` `line_total` | Entry | 1 visible, 1 hidden |
| `fix_03` | Filtering error | `purchasing/filters.py` `filter_suppliers` | Entry | 1 visible |
| `fix_04` | Wrong status code | `purchasing/views.py` `PurchaseOrderViewSet.lines` | Entry | 1 visible |
| `fix_05` | Serializer field mistake | `purchasing/serializers.py` `PurchaseOrderSerializer.Meta` | Entry | 2 hidden only |
| `fix_06` | Missing validation | `purchasing/services.py` `submit_order` | Medium | 1 visible, 1 hidden |
| `fix_07` | Wrong order of operations | `purchasing/views.py` `PurchaseOrderViewSet.perform_update` | Harder | 1 hidden only |

---

## fix_01: approve endpoint (the feature)

- **Location:** `purchasing/views.py`, `PurchaseOrderViewSet.approve` (the stub returned `501`).
  The reference solution also adds `ApproveSerializer` to `purchasing/serializers.py` and
  `approve_order` plus a `same_person` helper to `purchasing/services.py`.
- **Spec:** README, "Feature to implement".
- **Tests:**
  - Visible: `test_approvals.py::test_approve_submitted_order`,
    `test_approvals.py::test_approve_draft_order_returns_409`.
  - Hidden: `hidden/test_hidden_approvals.py::test_requester_cannot_approve_own_order`,
    `hidden/test_hidden_approvals.py::test_approve_sets_payment_due_date_from_supplier_terms`,
    `hidden/test_hidden_approvals.py::test_approve_without_approver_returns_400`.
- **Reference implementation:**
  1. `ApproveSerializer` has a single `approver = serializers.CharField(max_length=80)`. DRF's
     `CharField` is required, rejects blank strings and trims surrounding whitespace by default, so
     a missing, blank or too-long approver becomes a `400` with an `approver` key.
  2. The action is declared with `@action(detail=True, methods=["post"],
     serializer_class=ApproveSerializer)`, so `self.get_serializer(...)` validates the body and the
     browsable API shows the right form.
  3. `services.approve_order(order, approver)` runs in a transaction. It calls
     `ensure_status(order, SUBMITTED, ...)`, which raises the app's `Conflict` exception (`409`)
     for any other status. It then compares the approver with `requested_by` using
     `strip().casefold()` on both sides and raises a DRF `ValidationError({"approver": [...]})`
     (`400`) on a match. Only then does it set `status="approved"`, `approved_by` and
     `approved_at=timezone.now()` and save, so a rejected request changes nothing.
  4. The view returns `self.order_response(order)`: the full representation with `200`.
     `payment_due_date` was already computed by the serializer from `approved_at` and the
     supplier's `payment_terms_days`, so it fills in automatically.
- **Skill:** building a DRF custom action end to end: request validation, a business rule in a
  service layer, and choosing between `400` (bad input) and `409` (wrong state).

## fix_02: discount taken from one unit instead of the whole line

- **Location:** `purchasing/services.py`, `line_total`.
- **Symptom:** the discount is computed as `unit_price × discount_percent / 100`, i.e. the discount
  on a single unit. Any line with a quantity above 1 and a discount is overpriced: 4 × `25.00` at
  10% shows `"97.50"` instead of `"90.00"`. Every `line_total` and order `total` (detail, list,
  add-line response) is affected.
- **README rule broken:** "Money": `line_total` is the gross amount (`quantity × unit_price`) minus
  `discount_percent` percent **of the gross amount**, with the worked example 4 × `25.00` at 10% =
  `"90.00"`.
- **Tests:** visible `test_purchase_orders.py::test_order_detail_includes_discounted_line_totals`;
  hidden `hidden/test_hidden_purchase_orders.py::test_list_total_rounds_discounted_lines_half_up`
  (also checks `ROUND_HALF_UP`: 9.225 rounds to `9.23`, so a float-based fix fails it).
- **Fix:** `discount = gross * line.discount_percent / 100`.
- **Skill:** checking a calculation against the spec's formula and worked examples; `Decimal`
  money arithmetic.

## fix_03: `?active=false` returns active suppliers

- **Location:** `purchasing/filters.py`, `filter_suppliers`.
- **Symptom:** the filter uses `is_active=bool(active)`. Any non-empty string is truthy, so
  `bool("false")` is `True` and `?active=false` returns the *active* suppliers.
- **README rule broken:** "1. List suppliers": `false` returns only inactive suppliers.
- **Tests:** visible `test_suppliers.py::test_list_suppliers_filtered_by_inactive`.
- **Fix:** `return queryset.filter(is_active=active == "true")` (the value is already normalised
  and validated to `"true"` or `"false"` just above).
- **Skill:** parsing query parameters; Python string truthiness.

## fix_04: adding a line returns 200 instead of 201

- **Location:** `purchasing/views.py`, `PurchaseOrderViewSet.lines`.
- **Symptom:** the custom action builds `Response(data)` without a status, so DRF's default `200 OK`
  is returned for a newly created line.
- **README rule broken:** "8. Add a line to an order": response `201 Created`.
- **Tests:** visible `test_order_lines.py::test_add_line_returns_201`.
- **Fix:** `return Response(self.get_serializer(line).data, status=status.HTTP_201_CREATED)`.
- **Skill:** correct status codes on custom `@action` endpoints (`CreateModelMixin` sets 201 for
  you; hand-written actions don't).

## fix_05: `status` is writable on create and update

- **Location:** `purchasing/serializers.py`, `PurchaseOrderSerializer.Meta.read_only_fields`.
- **Symptom:** `"status"` is missing from `read_only_fields`, so the model field becomes a writable
  `ChoiceField`. A client can create an order that is already `approved`, or `PATCH` a draft to
  `submitted`/`approved`, skipping the submit and approve rules (no lines check, no approver, no
  self-approval check).
- **README rule broken:** "Order status": `status` changes only through the submit and approve
  endpoints and is ignored in create/update bodies; "5. Create a purchase order" and "7. Update a
  purchase order" repeat that read-only fields such as `status` are ignored.
- **Tests (hidden only):**
  `hidden/test_hidden_purchase_orders.py::test_create_order_ignores_status_in_body`,
  `hidden/test_hidden_purchase_orders.py::test_update_draft_order_ignores_status_in_body`.
- **Fix:** add `"status"` back to `read_only_fields`.
- **Skill:** serializer field configuration (`read_only_fields`) and guarding against
  mass assignment; testing what the README says should be *ignored*, which visible tests rarely
  cover.

## fix_06: orders with no lines can be submitted

- **Location:** `purchasing/services.py`, `submit_order`.
- **Symptom:** the guard reads `if not order.lines.exists:` without parentheses. `exists` is a
  bound method, which is always truthy, so `not ...` is always `False` and the check never fires.
  Empty orders are submitted with `200`.
- **README rule broken:** "9. Submit an order": an order must have at least one line;
  otherwise `400` and the order stays a draft.
- **Tests:** visible `test_purchase_orders.py::test_submit_order_without_lines_returns_400`;
  hidden `hidden/test_hidden_purchase_orders.py::test_submit_without_lines_keeps_order_in_draft`.
- **Fix:** `if not order.lines.exists():`.
- **Skill:** reading Python precisely (referencing a method vs. calling it); reproducing a
  validation rule with a request before trusting the code.

## fix_07: a rejected update is still saved

- **Location:** `purchasing/views.py`, `PurchaseOrderViewSet.perform_update`.
- **Symptom:** the hook calls `serializer.save()` first and checks the status afterwards. The
  response is the expected `409`, so the visible test
  `test_purchase_orders.py::test_update_submitted_order_returns_409` passes, but the new
  `notes`/`requested_by`/`needed_by`/`supplier` values have already been written to the database.
  There's no `ATOMIC_REQUESTS`, so nothing rolls the write back.
- **README rule broken:** "Order status": a request that isn't allowed in the order's current
  status returns `409 Conflict` **and changes nothing**; "7. Update a purchase order": `409` if the
  order isn't a draft (the order isn't changed).
- **Tests (hidden only):**
  `hidden/test_hidden_purchase_orders.py::test_rejected_update_leaves_submitted_order_unchanged`.
- **Fix:** check first, then save:

  ```python
  def perform_update(self, serializer):
      services.ensure_draft(serializer.instance, "Only draft orders can be edited.")
      serializer.save()
  ```
- **Skill:** ordering side effects correctly in DRF hooks, and verifying persisted state rather
  than only the status code.
