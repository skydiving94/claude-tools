from __future__ import annotations

from typing import Optional


class SklError(Exception):
    """General failure: exit 1, printed as 'error: <msg>'."""


class UsageError(SklError):
    """Usage failure: exit 2, optionally carrying a usage line."""

    def __init__(self, msg: str, usage_line: Optional[str] = None) -> None:
        super().__init__(msg)
        self.usage_line = usage_line


class NoInterfaceError(SklError):
    """The file has no command interface block."""
