# Task 9 review: exercise 01 (SPOILERS)

Reviewed: `exercises/01-purchase-orders/` and `.grader/01-purchase-orders/` at commit 319409e.
Requirements: the task-9 brief (text fence), CONTRIBUTING.md "Adding an exercise", spec sections 5 and 6.

I didn't re-run `verify` or the suite. I did two focused checks on a scratch copy (now deleted):
the browsable API renders (HTML 200 on `/api/`, both lists and both detail views; `/` redirects with 302),
`seed` can be run more than once, and I probed the filter edge cases listed under Minor 1. I also
worked out by hand the score each test produces on the starting code: 10/16 visible and 2/10 hidden
pass, so 12/26 = 46.2%, which matches the harness.

## Strengths

- **The README is a full spec.** It covers every endpoint's method, path, request and response
  example and status codes. It also has a global error table with body shapes, a field table with
  validation rules for every model, a worked money section with two examples (one of them checks
  `ROUND_HALF_UP`), and a status diagram. It says plainly that message wording isn't graded but
  status codes and `400` field keys are.
- **The README examples match the seed data under the correct code.** Supplier ids, order ids
  (PO-00002/PO-00004), `needed_by`, `created_at` offsets, `open_orders`, line id 16, and the totals
  `3558.72` and `1085.38` all match what the correct code returns. With the planted calculation bug,
  the seeded list shows `3963.12` and `1137.69`. A candidate who runs `seed` plus `runserver` and
  compares can find fix_02 without reading code. The seed also includes an empty draft order
  ("waiting for the updated quote"), so fix_06 can be reproduced by hand.
- **Every bug contradicts an explicit README statement, and a candidate can find each one by
  probing the API:**
  - fix_02: the Money worked example.
  - fix_03: the `active=false` rule.
  - fix_04: line create returns `201 Created`.
  - fix_05: `status` is read-only and ignored, stated in three places.
  - fix_06: submit "must have at least one line".
  - fix_07: "409 ... and changes nothing" and "(the order isn't changed)".
- **The bugs are realistic.** Each is a mistake real Django/DRF developers make: discount taken
  from the unit price instead of the gross, `bool("false")`, a hand-written `@action` without
  `status=201`, a missing `read_only_fields` entry, `exists` without parentheses, and save before
  the guard in `perform_update`. No comments, names or style point at them.
- **The difficulty mix is right.** Four bugs are entry-level (02 to 05), one is medium (06) and one
  is harder (07: the visible test still passes because the status code is right, so the candidate
  has to check persisted state).
- **Each fix accepts several correct approaches.** For example, fix_07 can be fixed by checking
  before saving, with `@transaction.atomic` on the hook, or with `ATOMIC_REQUESTS` (DRF's
  `set_rollback` handles it). fix_05 can be fixed with `read_only_fields`, an explicit read-only
  field, or by popping the key. The hidden tests don't depend on how a fix is written.
- **The feature stub is right.** It's a single
  `# TODO: Implement this endpoint. See "Feature to implement" in README.md.` that returns `501`.
  It gives away nothing, and the README tells the candidate the route already exists. The tests
  only check behaviour the README states: valid approve, the 409 for a draft, case-insensitive
  self-approval returning `400` with an `approver` key, the payment due date from supplier terms,
  and a missing approver. Rules whose order the README leaves open (for example, which of 400 and
  409 wins) aren't tested.
- **The tests are well built.** There are 26 in total: 16 visible and 10 hidden (38%). Each one
  builds its own data through factory fixtures, and none use the seed. Ordering tests break ties by
  id, so they don't depend on timestamp resolution. Two hidden tests guard against regressions and
  pass at the start. The hidden tests use the visible `conftest.py`, and the harness restores the
  original `tests/` before grading (`harnesslib/grading.py:35-39`), so a candidate's edits to the
  conftest can't break the hidden tests.
- **ANSWER_KEY.md is accurate.** Every location, symptom, README rule, catching test, fix and
  "caught by" count matches the patches and the tests. All seven patches touch only `purchasing/`.
  `solution.patch` is the union of the seven fixes.
- **Size and structure meet the brief.** The `purchasing/` app is 644 lines (774 including the
  project package and `manage.py`), with no tests or migrations counted. That's inside the 600–900
  range, though about 145 of those lines are the seed command. There are 3 models, 10 endpoints,
  3 query filters, several computed fields and a services module. Migrations are included, and
  `seed` is idempotent and atomic. The settings are clean and marked dev-only. LF line endings
  throughout, no stray `__pycache__` or `db.sqlite3`.
- **Ready to publish.** All names are fictional. Emails use the reserved `.example` and
  `example.com` domains. There are no real companies or products, and nothing looks lifted from a
  real assessment: purchase-order approval is a generic enterprise domain.

## Issues

### Critical

None.

### Important

None.

### Minor

1. **The reference code accepts some edge inputs that the README says must return `400`.**
   - `purchasing/filters.py:12-14`: `?active=TRUE`, `?active= true ` and `?active=` all return
     `200` because of `.strip().lower()` and the empty-string check. README.md:146 says
     "`true` ... `false` ... Any other value: `400`."
   - `purchasing/filters.py:23` and `:30`: `?status=` and `?supplier=` with an empty value are
     treated as if the parameter were left out. README.md:224-225 says "any other value returns
     `400`."
   - `purchasing/filters.py:31-33`: `str.isdigit()` accepts Unicode digits such as `²`. Then
     `int()` raises, and `?supplier=%C2%B2` returns a **500**. I confirmed this. README.md:225 says
     "anything else returns `400`."

   *Why it matters:* the README tells candidates that "wherever the code and this document
   disagree, this document is correct." A thorough candidate who probes edge cases may spend time
   "fixing" behaviour that isn't planted. No test covers these cases, so the score isn't affected.

   *Fix:* either make the README say the parameters are case-insensitive and that an empty value
   is ignored, or tighten the code to match the README. For `supplier`, use `int()` inside
   `try/except ValueError`, or `supplier.isascii() and supplier.isdigit()`.

2. **Two README examples don't hold up against the live data** (README.md:150-171 and
   `purchasing/management/commands/seed.py:97-99`).
   - The list-suppliers example shows 2 of the 6 seeded suppliers and doesn't say it's shortened.
     The orders example, by contrast, is complete.
   - `seed` deletes rows, but Django's SQLite tables use `AUTOINCREMENT`, so after a second
     `seed` the ids no longer match the README. For example, `GET /api/purchase-orders/1/` returns
     `404` (confirmed).

   *Why it matters:* a candidate comparing the API with the README may think either of these is a
   defect.

   *Fix:* add "(shortened)" or "…" to the supplier example, and note that ids in the examples are
   illustrative. Optionally, have `seed` reset `sqlite_sequence` for the three tables.

3. **The README points at the hidden-only bug fix_05 more than it needs to** (README.md:102-104,
   277-278, 351-352). The read-only rule is stated in the Order status section, and then the
   phrase "Read-only fields in the request, such as `status`, are ignored" appears again for both
   create and update. Naming `status` three times practically tells the candidate to try POSTing a
   status. That weakens one of the two bugs meant to be caught only by hidden tests. The rule does
   have to be explicit, so this is optional.

   *Fix:* keep the general rule in "Order status" and the field-table entry, and change the two
   endpoint sentences to a generic "Read-only fields in the request are ignored." Or use a
   different example field, such as `approved_by`.

4. **An unused import becomes a weak hint toward fix_04** (`purchasing/views.py:1` and `:88`).
   `status` from `rest_framework` is used only by the 501 stub. If a candidate implements the
   feature before fixing fix_04, Pylance greys out the now-unused `status` import, which hints
   that a status constant is missing somewhere. The risk is low.

   *Fix (optional):* give the starting code another natural use of `status`, or accept the
   risk as is.

5. **fix_07's label in the answer key isn't one of spec §5's bug types** (ANSWER_KEY.md:18 and
   `## fix_07`). The answer key calls it "Wrong order of operations". Spec §5 says bug types come
   from a fixed list. The bug itself is fair and backed by the README, so only the label is off.

   *Fix:* relabel it "Missing validation (the state guard runs after the write)", which fits the
   list.

6. **Small code-quality nits that may cost candidates time:**
   - `purchasing/serializers.py:46-50`: `validate_sku` strips and checks for blank values, but
     DRF's `CharField` has already done both, so a candidate may suspect a bug there.
   - `purchasing/services.py:16-21`: `to_money` sits above the "Money" section banner instead of
     under it.
   - `purchasing/serializers.py:24-25` with `services.py:51-53`: `open_orders` runs one `COUNT`
     query per supplier in the list (N+1). This is realistic, but `annotate(Count(...,
     filter=Q(...)))` would be the idiomatic way.

   *Fix:* simplify `validate_sku` to `return value.upper()`, and move `to_money` under the
   banner. The N+1 can stay, since it isn't in the README and isn't graded.

## Verdict

**Approved.** The exercise meets the brief, CONTRIBUTING and spec §5–§6. The README fully
specifies every graded behaviour, every bug is realistic, can be found from the README and isn't
given away, and the hidden tests are fair. The answer key and patches are accurate, and the
content is safe to publish. The Minor items are polish. Item 1 (README and code disagree on edge
inputs, including one latent 500) is the most worth fixing before release.
