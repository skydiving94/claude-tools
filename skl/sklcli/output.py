from __future__ import annotations

import sys


def out(line: str) -> None:
    sys.stdout.write(line + "\n")


def err(line: str) -> None:
    sys.stderr.write(line + "\n")
