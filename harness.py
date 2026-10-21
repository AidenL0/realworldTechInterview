"""HackerRank-style mock interview runner. Run `python harness.py --help`."""
import sys

if sys.version_info < (3, 11):
    sys.exit(f"harness.py needs Python 3.11 or newer (found {sys.version_info.major}.{sys.version_info.minor}).")

from harnesslib.cli import main

if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    sys.exit(main())
