"""`skl <skill> ...` and `skl run <skill> ...`: validate, then hand off by run mode."""
from __future__ import annotations

from typing import Sequence

from sklcli.commands.listing import print_usage_block
from sklcli.errors import UsageError
from sklcli.output import err
from sklcli.parsing.validate import validate
from sklcli.runmode.launch import launch
from sklcli.runmode.modes import split_mode
from sklcli.store import index as index_store


def cmd_run(args: Sequence[str]) -> int:
    if not args:
        raise UsageError("usage: skl run <skill> [args...]")
    entry = index_store.get_entry(index_store.load_index(), args[0])
    mode, rest = split_mode(entry, args[1:])
    if "--help" in rest or "-h" in rest:
        print_usage_block(entry["usage_block"])
        return 0
    try:
        validate(entry, rest)
    except UsageError as e:
        err("error: %s" % e)
        if e.usage_line:
            err("usage: %s" % e.usage_line)
        return 2
    return launch(entry, rest, mode)
