# Real-world tech interview practice

Free, open-source practice for "real-world" project questions, the kind of HackerRank-style
task used in many entry-level software engineering assessments. You get a small app with planted
bugs and one missing feature, then fix it against the clock. Your score comes from visible tests
plus hidden tests you never see.

> This project is not affiliated with or endorsed by HackerRank or any employer. Every exercise
> is original and is not a copy of any real assessment question.

## Before you start

- **Python 3.11 or newer.** On macOS and Linux the command is `python3`, so type `python3`
  wherever this guide says `python`. Debian and Ubuntu also need the `python3-venv` package.
- **git.**
- **VS Code** with the `code` command on your PATH. This is optional: without it, open
  `workspace/` yourself.

## One-time setup

```
python harness.py setup
```

## The practice loop

Run these from this folder (the project root), not from `workspace/`. Only `submit` and `time`
are meant to be run from inside `workspace/`, via `python ../harness.py` or the VS Code tasks.
Running `start` or `reset` from a terminal inside `workspace/` fails on Windows, because the
folder can't be emptied while the terminal is in it.

| Step | Command |
|---|---|
| See exercises and your best scores | `python harness.py list` |
| Start an exercise (copies it into `workspace/`, starts the clock, opens VS Code) | `python harness.py start 01` |
| Check the time | `python harness.py time` |
| Grade your work with visible and hidden tests | `python harness.py submit` |
| See the answer key (after at least one submit) | `python harness.py answers 01` |
| Throw your work away and start fresh | `python harness.py reset` |

Inside VS Code:

- **Read `README.md` first.** It is the spec. A bug is anywhere the app disagrees with it.
- **Run the visible tests:** `pytest tests -q` in the terminal, or **Terminal → Run Task → Run Tests**.
- **Submit or check the time** with the **Submit** and **Time Left** tasks, or with `python ../harness.py submit`.
- **Try the API by hand:** run `python manage.py runserver` (or the **Run Server** task) and open
  `http://127.0.0.1:8000/` for DRF's browsable API.
- **Review your changes** with `git diff` (your starting point is the `baseline` commit).

## How scoring works

- Score = tests passed ÷ total tests (visible + hidden), with every test counting the same.
- Grading uses the original tests. Editing or deleting tests in `workspace/` doesn't change your score.
- Hidden tests are reported as a count only, as on HackerRank.
- The timer doesn't cut you off. Submits after the limit are marked **OVERTIME** in your history.
- You can submit as often as you like. Every submit is logged in `.state/history.json`.

## Tips for HackerRank-style tasks

1. Read the whole README before you open any code. List every rule it states.
2. Run the visible tests, then group the failures by endpoint.
3. Reproduce a bug before you fix it, with a failing test or a request in the browsable API.
4. Fix one thing at a time, rerun the tests, and check `git diff`.
5. Hidden tests check the README's rules too. Test the edge cases the visible tests skip.
6. Submit early, then keep improving. Don't leave the missing feature for the last five minutes.

## Don't peek

`exercises/` holds the starting code and `.grader/` holds the hidden tests and answers. Both are
plain files, so it works on the honor system: practice in `workspace/` only, and open the answers
with `python harness.py answers <id>` after you submit.

## Contributing

New exercises, fixes and docs are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) to set up a
dev environment, write an exercise, and check it with `python harness.py verify <id>`.

## License

Copyright (C) 2026 the Real-World Tech Interview Practice contributors.

Licensed under the [GNU Affero General Public License v3.0 or later](LICENSE). You may use,
share and modify this project. If you distribute a modified version, or let people use one over a
network (for example, as a hosted practice site), you must publish its source code under the same
license.
