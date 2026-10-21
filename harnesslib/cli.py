"""Argument parsing and top-level error handling for harness.py."""
from __future__ import annotations

import argparse
import sys
import traceback

from . import commands
from .config import HarnessError, Paths, get_paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="harness.py", description="HackerRank-style mock interview runner.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("setup", help="create .venv and install the pinned packages")
    sub.add_parser("list", help="show exercises and your best scores")
    start = sub.add_parser("start", help="copy an exercise into workspace/ and start the clock")
    start.add_argument("exercise_id")
    start.add_argument("--force", action="store_true", help="overwrite an attempt in progress without asking")
    start.add_argument("--no-open", action="store_true", help="don't open VS Code")
    sub.add_parser("time", help="show how much time is left")
    sub.add_parser("submit", help="grade your workspace with the visible and hidden tests")
    reset = sub.add_parser("reset", help="delete workspace/ and the current attempt")
    reset.add_argument("--force", action="store_true", help="don't ask for confirmation")
    answers = sub.add_parser("answers", help="show the answer key (after at least one submit)")
    answers.add_argument("exercise_id")
    verify = sub.add_parser("verify", help="maintainers: check an exercise is fair (numbers only)")
    verify.add_argument("exercise_id")
    return parser


def _dispatch(args: argparse.Namespace, paths: Paths) -> int:
    if args.command == "setup":
        return commands.cmd_setup(paths)
    if args.command == "list":
        return commands.cmd_list(paths)
    if args.command == "start":
        return commands.cmd_start(paths, args.exercise_id, force=args.force, no_open=args.no_open)
    if args.command == "time":
        return commands.cmd_time(paths)
    if args.command == "submit":
        return commands.cmd_submit(paths)
    if args.command == "reset":
        return commands.cmd_reset(paths, force=args.force)
    if args.command == "answers":
        return commands.cmd_answers(paths, args.exercise_id)
    if args.command == "verify":
        return commands.cmd_verify(paths, args.exercise_id)
    raise HarnessError(f"Unknown command: {args.command}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return _dispatch(args, get_paths())
    except HarnessError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    except Exception:
        traceback.print_exc()
        return 2
