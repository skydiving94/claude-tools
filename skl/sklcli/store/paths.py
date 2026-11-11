"""Where skl keeps its data, and the limits on what it stores."""
from __future__ import annotations

import os
import re
from pathlib import Path

from sklcli.errors import SklError

NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
MAX_SKILL_BYTES = 1024 * 1024


def store_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / "skl"


def skill_folder(name: str) -> Path:
    if not NAME_RE.fullmatch(name):
        raise SklError("unsafe skill name '%s'" % name)
    return store_dir() / "skills" / name
