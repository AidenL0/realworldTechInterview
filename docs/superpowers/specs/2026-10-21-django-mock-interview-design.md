# Django Mock Interview Practice — Design

- **Date:** 2026-10-21
- **Status:** Design approved in conversation; spec awaiting review

## 1. Goal

Rehearse HackerRank "real-world" project questions, like those used in many companies'
entry-level SWE assessments: a small Django REST Framework (DRF) app with planted bugs and one missing feature,
scored by visible + hidden tests under a time limit, worked on locally in VS Code.

### What the user said
- Practice fixing bugs in mock apps that simulate real-world problems, as on HackerRank.
- Stack: Python / Django. Target format: JSON REST API endpoints, with both bug fixing and a
  missing feature (a common HackerRank project-question format).
- Use local VS Code as the IDE.
- First build: one full-length mock plus a reusable harness.
- The exercise must be built without spoiling it (authored by a background agent).

### Assumptions
- A time limit of 90 minutes matches a typical HackerRank project question.
- Equal-weight tests are a close enough stand-in for HackerRank scoring.
- A soft timer (record overtime, don't cut off) is more useful for practice than auto-submit.

### Success criteria
- After a one-time `setup`, `start 01` opens a ready-to-work VS Code workspace in under a minute.
- Visible tests run from the VS Code terminal or a VS Code task.
- `submit` prints a HackerRank-style score with visible/hidden breakdown and elapsed time.
- The untouched exercise scores 30–50%; the reference solution scores 100%.
- The user sees no bug details unless they explicitly unlock the answer key after submitting.

## 2. Scope

**In:** `harness.py`, exercise `01`, its grader assets, harness tests, a root README, and the
open-source files from §12 (license, contributing guide, CI, spoiler notice).

**Out (for now):** more exercises, short drills, Docker, hard timer / auto-submit, weighted
tests, other stacks. The harness is stack-agnostic so these can be added later without changes.

## 3. Layout

```
realworldTechInterview/
  harness.py                  # CLI, Python stdlib only
  requirements.txt            # pinned: Django, djangorestframework, pytest, pytest-django
  README.md                   # how to practice
  .gitignore                  # .venv/, workspace/, .state/, __pycache__/, *.pyc, db.sqlite3
  harness_tests/              # tests for the harness itself
    fixtures/00-sample/       # tiny non-Django exercise used only by harness tests
  exercises/01-<slug>/        # pristine starting copy (user never opens this)
  .grader/01-<slug>/          # hidden tests, answer key, fix patches
  workspace/                  # created by `start`; the only folder the user opens
  .state/                     # attempt.json, history.json
  .venv/
  docs/superpowers/specs/
```

`<slug>` is a short name for the exercise's business domain, chosen by the build agent and
not disclosed before the user starts the exercise. The root repo ignores `workspace/`, which
has its own git repo.

## 4. Component: `harness.py`

**Constraints:** Python stdlib only; runs on system Python 3.11+; Windows is the primary
platform (venv Python is `.venv/Scripts/python.exe` on Windows, `.venv/bin/python` elsewhere).
The project root defaults to the script's directory and can be overridden with the
`HARNESS_ROOT` environment variable. The venv interpreter can be overridden with
`HARNESS_PYTHON`. Both overrides exist for the harness tests. Child Python processes run with
`PYTHONUTF8=1`, and their output is decoded as UTF-8, so non-ASCII text survives Windows pipes.

**Exit codes:** `0` success, `1` user error (unknown id, no attempt, venv missing, declined
prompt), `2` unexpected internal error.

### Commands

| Command | Behavior |
|---|---|
| `setup` | Create `.venv` if missing; `pip install -r requirements.txt`. Idempotent. |
| `list` | For each `exercises/*/exercise.json`: id, title, time limit, best score from history (`—` if none), and `IN PROGRESS` marker. |
| `start <id> [--force] [--no-open]` | See *start* below. |
| `time` | Elapsed / limit / remaining, or `OVERTIME by Xm Ys`. |
| `submit` | See *submit* below. |
| `reset [--force]` | Confirm, then delete `workspace/` and `.state/attempt.json`. History is kept. |
| `answers <id>` | Requires ≥1 history entry for `<id>`; confirms (`This shows every bug and fix. Continue? [y/N]`); prints `ANSWER_KEY.md` and the paths of the fix patches. |
| `verify <id>` | Maintainer check for exercise quality (§7). Prints numbers only. |

### `start <id>`
1. Fail with exit 1 if `.venv` is missing ("Run `python harness.py setup` first") or `<id>`
   is unknown (list valid ids).
2. If an attempt is in progress, prompt `Attempt for <id> in progress. Overwrite? [y/N]`
   unless `--force`.
3. Delete `workspace/`; copy `exercises/<id>/` into it, skipping `__pycache__` and
   `db.sqlite3`.
4. Generate `workspace/.vscode/settings.json` (`python.defaultInterpreterPath` = absolute venv
   Python, `python.testing.pytestEnabled: true`) and `workspace/.vscode/tasks.json` (a
   `Run Tests` task in the default test group, `Submit` and `Time Left` tasks that call the
   harness, and a `Run Server` task when the exercise has `manage.py`). These are generated,
   not stored in the template, because the interpreter path is machine-specific.
5. Write `workspace/.gitignore` (`__pycache__/`, `*.pyc`, `db.sqlite3`, `.vscode/`); then
   `git init`, `git add -A`, and commit `baseline` using
   `git -c user.name=practice -c user.email=practice@localhost`.
6. Run each entry of `exercise.json`'s `setup_commands` in `workspace/` with the venv Python
   (for exercise 01: `manage.py migrate` and `manage.py seed`). On failure, print the output
   and exit 1.
7. Write `.state/attempt.json`: `exercise_id`, `started_at` (UTC ISO 8601),
   `time_limit_minutes`.
8. Unless `--no-open`, run `code <workspace>` if `code` is on PATH; otherwise print the path.
9. Print the time limit and a short "read README.md first" hint.

### `submit`
1. Fail with exit 1 if no attempt is in progress.
2. In a `tempfile.TemporaryDirectory`, copy `workspace/` excluding `.git`, `__pycache__`,
   `db.sqlite3`, `.vscode`.
3. Replace `tests/` with the original `exercises/<id>/tests/`, so edits to visible tests
   can't affect the score. Copy `.grader/<id>/hidden_tests/*` into `tests/hidden/`.
4. Run `<venv python> -m pytest tests -q -p no:cacheprovider --continue-on-collection-errors
   --junitxml=<tmp>/report.xml` in the temp directory with a 120-second timeout. Only `tests/`
   is collected, so test files added elsewhere in the workspace don't count. A test file that
   fails to import doesn't stop the other files from running.
5. Parse the JUnit XML. A test case passes only if it has no `failure`, `error`, or
   `skipped` child. Test cases whose classname contains `tests.hidden` are hidden; all others
   are visible.
6. **Denominators come from `.grader/<id>/expected.json`** (`{"visible": N, "hidden": M}`).
   Any expected test that did not report counts as failed. This stops collection errors from
   inflating the percentage.
7. Score = passed ÷ (N + M), shown to one decimal place. Output:
   ```
   01 · <title>
   Visible  9/14   Hidden  3/8
   Score    12/22  (54.5%)
   Time     72m 10s / 90m
   ```
   Failing visible tests are listed by node id. Hidden tests are shown as a count only.
   Raw pytest output is **never** printed, because it would reveal hidden test code.
8. On timeout: score 0, message `Tests timed out after 120s (infinite loop?)`.
9. If no test ran at all (startup or collection failure), score 0. If `exercise.json`
   defines `check_command`, run it in the temp directory and show its output. Either way,
   add a hint to run `pytest` in the workspace to see visible-test errors.
10. Append to `.state/history.json`: `exercise_id`, `submitted_at`, `visible_passed`,
    `visible_total`, `hidden_passed`, `hidden_total`, `score_pct`, `elapsed_seconds`,
    `overtime` (bool). Overtime submits print `OVERTIME` next to the time.

### Platform details
- Deleting `workspace/.git` on Windows hits read-only files: `shutil.rmtree` uses an error
  handler that clears the read-only bit and retries. If a file is still locked (VS Code or a
  terminal has it open), the harness exits 1 with a message to close them, not a traceback.
- `.gitattributes` enforces LF line endings so fix patches apply on Windows.
- All paths use `pathlib`; subprocesses get argument lists, never shell strings.

## 5. Component: Exercise `01`

**Stack:** Django 5.x + DRF 3.x, SQLite, pytest + pytest-django. The build agent pins exact
current stable versions compatible with Python 3.13 in `requirements.txt`.

**App:** one Django project, one DRF app, about 3 related models, serializers, views or
viewsets, URL routes, and a small business-logic module. 600–900 lines of app code, not
counting tests and migrations. 6–10 endpoints, including list/detail/create/update, at least
one query-parameter filter, and at least one computed field or business rule. A `seed`
management command loads realistic sample data for `runserver` and the browsable API.

**Files:**
- `README.md` — HackerRank-style problem statement: overview, data model fields, every
  endpoint (method, path, request body, response example, status codes), validation rules,
  and the spec for the missing feature. An "Environment" section explains running tests,
  `runserver`, and `seed`. It never lists or hints at bugs.
- `exercise.json` — `{"id": "01", "title": "<domain title>", "time_limit_minutes": 90,
  "setup_commands": [["manage.py", "migrate"], ["manage.py", "seed"]],
  "check_command": ["manage.py", "check"]}`. Each command is run as
  `<venv python> <args...>`. `setup_commands` is required (may be empty); `check_command`
  is optional.
- `pytest.ini` — sets `DJANGO_SETTINGS_MODULE` and test discovery.
- `tests/` — visible tests.

**Planted defects: 5–6 bugs + 1 missing feature.**
- Bug types come from this list: wrong status codes, filtering/ordering errors, missing
  validation, calculation or off-by-one errors, querysets returning the wrong records,
  serializer field mistakes (such as wrong read-only/required settings), routing mistakes.
- Difficulty: most are entry-level; 1–2 are harder (span files or are subtle).
- Every bug breaks something the README explicitly states. No trick puzzles.
- No giveaways: no `# BUG`/`TODO` comments near bugs, no suspicious names, and code style
  consistent with the rest of the app.
- Bugs are in app code only, never in tests. No fix depends on another fix.
- The app starts cleanly: `manage.py check`, `migrate`, and `seed` succeed. A bug may cause
  a 500 on a specific request, but not an import-time crash.
- The missing feature is announced in the README. The code may contain a stub with a
  `TODO` pointing to that README section, as HackerRank does.

**Tests:** pytest-django with DRF's `APIClient`. Each test creates its own data and never
relies on `seed`. 20–30 tests in total, roughly 60% visible and 40% hidden by count.
- Every bug and the feature are covered by at least one test.
- At least one bug is covered **only** by hidden tests.
- The feature is covered by both visible and hidden tests.
- The untouched exercise scores 30–50% overall.

## 6. Component: Grader assets (`.grader/01-<slug>/`)

- `hidden_tests/` — test files plus whatever `__init__.py`/`conftest.py` is needed to import
  them from `tests/hidden/`.
- `expected.json` — `{"visible": N, "hidden": M}`, the number of test cases in each set.
- `ANSWER_KEY.md` — for each bug: number, location (file and function), symptom, the README
  rule it breaks, the tests that catch it (visible/hidden), the fix, and the skill it was
  testing. For the feature: an explanation of the reference implementation.
- `fixes/fix_01.patch` … `fix_NN.patch` — one unified diff per bug and one for the feature,
  relative to the exercise root and applicable with `git apply`.
- `solution.patch` — all fixes combined.

## 7. Verification (`harness.py verify <id>`)

Runs each check in a temporary copy of the exercise and prints numbers only, labeling fixes
as `fix_01`, `fix_02`, … with no descriptions.

1. **Clean start:** `check_command` (if defined) and every `setup_commands` entry succeed;
   the starting score is in 30–50%.
2. **Full solution:** applying `solution.patch` scores 100%.
3. **Independent fixes:** applying each `fix_NN.patch` on its own to a fresh copy turns at
   least one failing test into a pass and breaks no test that was passing.
4. **Hidden-only bug:** at least one fix flips only hidden tests.
5. **Counts:** `expected.json` matches the test cases actually collected.

The build agent must get every check passing before handing the exercise back.

## 8. Harness tests (`harness_tests/`)

Written test-first with pytest, run with the venv Python.

- **Unit:** JUnit parsing (pass/fail/error/skipped; visible vs hidden classification), scoring
  with missing tests counted as failures, time formatting, overtime detection.
- **Integration:** `harness_tests/fixtures/sample_root/` holds a tiny synthetic project root
  with `exercises/00-sample/` (plain Python, no Django, two bugs with one of them caught only
  by hidden tests, empty `setup_commands`, `check_command` = `["-c", "import calc"]`) and
  `.grader/00-sample/` (hidden tests, `expected.json`, `ANSWER_KEY.md`, `fixes/fix_01.patch`,
  `fixes/fix_02.patch`, `solution.patch`). This lets every `verify` check pass on the sample. Tests copy it to a temp dir, point
  `HARNESS_ROOT` at it with the real `.venv` Python, and run `start --no-open` → `submit` →
  fix → `submit` = 100% → `reset`.
  Deleting a visible test in the workspace leaves the score unchanged. `answers` is refused
  before any submit.
- **End-to-end on exercise 01:** run by the build agent as part of acceptance: `setup` →
  `start 01 --no-open` → `submit` → `git apply` `solution.patch` in the workspace → `submit`
  = 100% → `reset`. Numbers only are reported.

## 9. Spoiler protection

- The harness, harness tests, the sample fixture, and the root README are written in the main
  session; none of them contain exercise 01 content.
- Exercise 01 (app, README, visible tests) and all of `.grader/01-<slug>/` are written by a
  background agent. Its report to the main session holds only numbers, file counts, and check
  results: no domain description, bug descriptions, or test names.
- The main session never reads or prints exercise 01 or `.grader/` contents in chat.

## 10. Root README

How to practice: `setup`, `start`, the work loop (read the exercise README, run visible tests,
`git diff`, check `time`), `submit`, `answers`, `reset`, plus HackerRank tips (read the spec
before the code, reproduce with a test or curl before fixing, re-run tests after each fix,
submit early and often).

## 11. Decisions

| Decision | Choice | Over |
|---|---|---|
| Overall approach | Runner + hidden grader folder | git solution branch; Docker |
| Timer | Soft limit, overtime recorded | Hard cut-off / auto-submit |
| Scoring | Equal-weight tests, fixed denominators | Weighted tests |
| Answer key | Locked until ≥1 submit, then confirm | Always available |
| Harness scope | Stack-agnostic (`setup_commands`) | Django-specific |
| Exercise authoring | Background agent, numbers-only report | Authored in main chat |
| License | AGPL-3.0-or-later | MIT, Apache-2.0, GPL-3.0 |
| Hidden tests in the public repo | Plain files, honor system | Packed archives |

## 12. Open-source readiness

The project will be published as a free, public practice resource. Its modifications should
stay open, including versions offered as hosted websites.

- **License:** AGPL-3.0-or-later. `LICENSE` holds the official, unmodified text from
  gnu.org. The README's License section names the license and the copyright holder
  ("the Real-World Tech Interview Practice contributors").
- **Spoilers:** `.grader/` stays plain text so contributors can review hidden tests in pull
  requests. A `.grader/README.md` warns visitors browsing GitHub that the folder contains
  spoilers. The root README asks practicers not to open it.
- **Originality:** every exercise is invented for this project. Contributors must never
  reproduce real assessment questions, which are usually confidential under candidate
  agreements. This applies to exercise 01 as well.
- **No affiliation:** the README states that the project is not affiliated with or endorsed by
  HackerRank or any employer. It mentions no specific company's assessment.
- **CONTRIBUTING.md:** covers development setup, the stdlib-only and Python 3.11+ rules for the
  harness, the exercise format, the rules for planted defects and tests (§5–§6), the
  scratch-repo method for making patches, the `verify` gate, and a pull request checklist.
  Contributions are licensed under the project license (inbound = outbound).
- **CI:** a GitHub Actions workflow runs on every push to `main` and on every pull request. It
  uses a matrix of Ubuntu, Windows, and macOS × Python 3.11 and 3.13. Each job runs
  `harness.py setup`, the harness tests, and `harness.py verify` for every exercise.
- **Default branch:** `main`.
