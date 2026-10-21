# Contributing

Thanks for helping people practice for real-world coding assessments. Contributions of every size
are welcome: bug reports, harness fixes, docs, and especially new exercises.

## Ground rules

- **Exercises must be original.** Never reproduce a real assessment question, including one you
  saw in your own interview. Those questions are usually confidential under the candidate
  agreement. Invent your own domain and bugs.
- **No spoilers outside `.grader/`.** Don't put hidden tests, answer keys or fixes in issue titles,
  pull request titles or descriptions, or discussions.
- **No affiliation claims.** This project is not affiliated with HackerRank or any employer. Don't
  add their logos or text copied from their sites.
- **License.** By contributing, you agree your contribution is licensed under the project's
  license, the GNU Affero General Public License v3.0 or later.

## Development setup

```
python harness.py setup             # macOS / Linux: python3 harness.py setup
.venv/Scripts/python -m pytest      # Windows
.venv/bin/python -m pytest          # macOS / Linux
```

The harness (`harness.py` and `harnesslib/`) uses only the Python standard library and supports
Python 3.11+. Keep it that way. Every harness change needs tests in `harness_tests/` (write them
first), and CI must pass on Windows, macOS and Linux.

## Adding an exercise

An exercise is two folders:

```
exercises/<NN>-<slug>/   what the candidate gets: README.md, exercise.json, pytest.ini, app code, tests/
.grader/<NN>-<slug>/     hidden_tests/, expected.json, ANSWER_KEY.md, fixes/fix_NN.patch, solution.patch
```

Exercises currently need a pytest test suite. The reference stack is Django + Django REST
Framework. Supporting other test runners would be a welcome harness change.

### exercise.json

```json
{
  "id": "02",
  "title": "Library Loans API",
  "time_limit_minutes": 90,
  "setup_commands": [["manage.py", "migrate"], ["manage.py", "seed"]],
  "check_command": ["manage.py", "check"]
}
```

Each command runs as `<venv python> <args...>` inside the candidate's workspace. `setup_commands`
can be empty. `check_command` is optional; when no tests can run, `submit` shows its output.

### What makes a good exercise

- **The README is the whole spec:** every endpoint with its request and response examples,
  status codes and validation rules, plus one "Feature to implement" section. It never hints at
  the bugs.
- **Defects:** 5–6 planted bugs plus one missing feature.
  - Each bug breaks something the README states explicitly.
  - Use natural-looking code: no giveaway comments or suspicious names.
  - Bugs live in app code, never in tests, and no fix may depend on another.
  - Most bugs should be entry-level; 1–2 can be harder.
- **The app starts cleanly:** `check`, migrations and `seed` succeed. A bug may cause a 500 on a
  specific request, but not an import error.
- **Tests:**
  - 20–30 in total, about 60% visible (`tests/test_*.py`) and 40% hidden
    (`.grader/<NN>-<slug>/hidden_tests/test_hidden_*.py`, so basenames stay unique).
  - Every bug and the feature are covered by at least one test.
  - At least one bug is caught *only* by hidden tests.
  - Each test builds its own data; none rely on `seed`.
- **The starting score is 30–50%.**
- **Files use LF line endings.**

### Recommended method (it guarantees the patches apply)

1. In a scratch git repo, build the **correct** app with every test: visible tests in `tests/`,
   hidden tests in `tests/hidden/`. All tests pass. Commit `correct`.
2. Remove the feature and leave a stub that points to the README section. Commit.
3. Plant each bug in its own commit. Keep every planted change at least 7 lines away from the other
   planted changes in the same file.
4. From the scratch repo root, for each commit `C` after `correct`, run
   `git diff --output=fix_NN.patch C C~1`. Then run
   `git diff --output=solution.patch HEAD <correct-sha>`. (Don't use `>`: Windows PowerShell 5.1
   writes UTF-16.)
5. Export the files:
   - `HEAD` without `tests/hidden/` goes to `exercises/<NN>-<slug>/`.
   - `tests/hidden/*` goes to `.grader/<NN>-<slug>/hidden_tests/`.
   - Write `expected.json` as `{"visible": V, "hidden": H}`, counting with `pytest --collect-only -q`.
   - Write `ANSWER_KEY.md`. For each fix, give its location, the symptom, the README rule it
     breaks, the tests that catch it, the fix, and the skill it tests.

### Check it

`python harness.py verify <NN>` must print `Result: N/N checks passed`. It prints only numbers and
`fix_NN` labels, so it's safe to paste into a pull request.

## Pull request checklist

- [ ] Harness tests pass locally.
- [ ] For exercises: `python harness.py verify <NN>` passes, and the exercise is original.
- [ ] No spoilers in the pull request title or description.
