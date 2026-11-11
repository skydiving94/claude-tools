"""The on-disk index of skills: loading with validation, atomic saving, lookup."""
from __future__ import annotations

import difflib
import json
import os
import tempfile
from typing import Any, List, Optional

from sklcli.errors import SklError, UsageError
from sklcli.models import Entry, Index, Source
from sklcli.store.paths import NAME_RE, store_dir

_UNREADABLE = "index is unreadable, run 'skl sync'"


def _valid_interface(iface: Any) -> bool:
    if iface is None:
        return True
    if not isinstance(iface, dict) or not all(k in iface for k in ("usage_line", "actions", "groups")):
        return False
    if not isinstance(iface["actions"], dict) or not isinstance(iface["groups"], list):
        return False
    if not all(isinstance(a, dict) and isinstance(a.get("targets"), list)
               for a in iface["actions"].values()):
        return False
    return all(isinstance(g, dict) and isinstance(g.get("flags"), list) for g in iface["groups"])


def _valid_entry(key: Any, entry: Any) -> bool:
    return (isinstance(key, str) and NAME_RE.fullmatch(key) is not None
            and isinstance(entry, dict)
            and isinstance(entry.get("name"), str) and NAME_RE.fullmatch(entry["name"]) is not None
            and isinstance(entry.get("usage_block"), str)
            and entry.get("source") in (Source.SYNC.value, Source.IMPORT.value)
            and _valid_interface(entry.get("interface", False)))


def empty_index() -> Index:
    return Index(version=1, skills={})


def load_index(dropped: Optional[List[str]] = None) -> Index:
    """Load the index, silently dropping invalid entries.

    If a list is passed as `dropped`, the keys of dropped entries are appended to it.
    """
    path = store_dir() / "index.json"
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return empty_index()
    except (OSError, UnicodeDecodeError):
        raise SklError(_UNREADABLE)
    try:
        data = json.loads(text)
    except ValueError:
        raise SklError(_UNREADABLE)
    if not isinstance(data, dict) or not isinstance(data.get("skills"), dict):
        raise SklError(_UNREADABLE)
    good = {}
    for key, entry in data["skills"].items():
        if _valid_entry(key, entry):
            good[key] = entry
        elif dropped is not None:
            dropped.append(key)
    data["skills"] = good
    return data


def save_index(index: Index) -> None:
    d = store_dir()
    d.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".index-", suffix=".tmp", dir=str(d))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2)
            f.write("\n")
        os.replace(tmp, str(d / "index.json"))
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def get_entry(index: Index, name: str) -> Entry:
    skills = index["skills"]
    if name in skills:
        return skills[name]
    msg = "unknown skill '%s'" % name
    close = difflib.get_close_matches(name, list(skills), n=3)
    if not skills:
        msg += "\nrun 'skl sync' to index your skills"
    elif close:
        msg += "\ndid you mean: %s" % ", ".join(close)
    raise UsageError(msg)
