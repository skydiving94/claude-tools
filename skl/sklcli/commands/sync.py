"""`skl sync` and `skl import`."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence, Set

from sklcli.errors import NoInterfaceError, SklError, UsageError
from sklcli.models import Source
from sklcli.output import out
from sklcli.store import entries
from sklcli.store import index as index_store
from sklcli.store.paths import MAX_SKILL_BYTES
from sklcli.store.roots import scan_roots


def cmd_sync(args: Sequence[str]) -> int:
    if args:
        raise UsageError("sync takes no arguments")
    dropped: list = []
    try:
        index = index_store.load_index(dropped)
    except SklError:
        sys.stderr.write("note: index was unreadable, rebuilding it\n")
        index = index_store.empty_index()
    for key in dropped:
        out("note: dropped invalid index entry %s" % key)
    skills = index["skills"]
    seen: Set[str] = set()
    for root in scan_roots(Path.cwd()):
        for path in sorted(root.rglob("SKILL.md")):
            if path.is_file():
                _sync_one(path, skills, seen)
    for name in sorted(skills):
        if skills[name].get("source") == Source.SYNC and name not in seen:
            del skills[name]
            entries.drop_store(name)
            out("removed %s" % name)
    index_store.save_index(index)
    out("%d skills indexed" % len(skills))
    return 0


def _sync_one(path: Path, skills: dict, seen: Set[str]) -> None:
    try:
        with open(str(path), "rb") as f:
            data = f.read(MAX_SKILL_BYTES + 1)
        if len(data) > MAX_SKILL_BYTES:
            sys.stderr.write("skipped %s: too large\n" % path)
            return
        entry = entries.entry_from_bytes(data, path.parent.name, Source.SYNC, path)
    except NoInterfaceError:
        return
    except SklError as e:
        sys.stderr.write("skipped %s: %s\n" % (path, e))
        return
    except OSError as e:
        sys.stderr.write("skipped %s: %s\n" % (path, e.strerror or e))
        return
    name = entry["name"]
    old = skills.get(name)
    if old is not None and old.get("source") == Source.IMPORT and name not in seen:
        out("note: %s ignored, imported %s kept" % (path, name))
        return
    if old is not None and name in seen:
        out("note: %s from %s replaces %s" % (name, path, old.get("source_path")))
    entries.write_store(name, data)
    skills[name] = entry
    seen.add(name)
    n = len(entry["interface"]["actions"]) if entry["interface"] else None
    out("indexed %s (%s)" % (name, "pass-through" if n is None else "%d actions" % n))


def cmd_import(args: Sequence[str]) -> int:
    if len(args) != 1:
        raise UsageError("usage: skl import <path>")
    p = Path(args[0])
    data, fallback = entries.read_skill_source(p)
    entry = entries.entry_from_bytes(data, fallback, Source.IMPORT, p.resolve())
    index = index_store.load_index()
    entries.write_store(entry["name"], data)
    index["skills"][entry["name"]] = entry
    index_store.save_index(index)
    out("imported %s" % entry["name"])
    return 0
