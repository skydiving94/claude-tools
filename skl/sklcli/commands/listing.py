"""`skl list`, `skl show` and `skl remove`."""
from __future__ import annotations

import json
import sys
from typing import Sequence

from sklcli.errors import UsageError
from sklcli.models import Source
from sklcli.output import out
from sklcli.parsing.interface import describe_actions
from sklcli.store import entries
from sklcli.store import index as index_store


def cmd_list(args: Sequence[str]) -> int:
    if args:
        raise UsageError("list takes no arguments")
    skills = index_store.load_index()["skills"]
    if not skills:
        out("no skills indexed, run 'skl sync'")
        return 0
    for name in sorted(skills):
        out("%s\t%s" % (name, describe_actions(skills[name])))
    return 0


def print_usage_block(usage_block: str) -> None:
    sys.stdout.write(usage_block)
    if not usage_block.endswith("\n"):
        sys.stdout.write("\n")


def cmd_show(args: Sequence[str]) -> int:
    parsed = "--parsed" in args
    rest = [a for a in args if a != "--parsed"]
    if len(rest) != 1:
        raise UsageError("usage: skl show <skill> [--parsed]")
    entry = index_store.get_entry(index_store.load_index(), rest[0])
    if parsed:
        out(json.dumps(entry["interface"], indent=2))
    else:
        print_usage_block(entry["usage_block"])
    return 0


def cmd_remove(args: Sequence[str]) -> int:
    if len(args) != 1:
        raise UsageError("usage: skl remove <skill>")
    index = index_store.load_index()
    entry = index_store.get_entry(index, args[0])
    name = entry["name"] if entry.get("name") in index["skills"] else args[0]
    del index["skills"][name]
    entries.drop_store(name)
    index_store.save_index(index)
    out("removed %s" % name)
    if entry.get("source") == Source.SYNC:
        out("note: 'skl sync' will add it back while the source exists")
    return 0
