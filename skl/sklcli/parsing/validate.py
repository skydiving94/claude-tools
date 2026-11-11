"""Checking user arguments against a skill's interface, before any model call."""
from __future__ import annotations

import re
from typing import NoReturn, Sequence

from sklcli.errors import UsageError
from sklcli.models import Entry
from sklcli.parsing.interface import all_flag_names, flags_for

_NEGATIVE_NUMBER_RE = re.compile(r"^-\d+(\.\d+)?$")


def is_flag_arg(arg: str) -> bool:
    return arg.startswith("-") and arg != "-" and not _NEGATIVE_NUMBER_RE.match(arg)


def validate(entry: Entry, args: Sequence[str]) -> None:
    interface = entry.get("interface")
    if interface is None:
        return
    usage = interface["usage_line"]

    def fail(msg: str) -> NoReturn:
        raise UsageError(msg, usage)

    actions = interface["actions"]
    if not args or is_flag_arg(args[0]):
        fail("missing action")
    action = args[0]
    if action not in actions:
        fail("unknown action '%s'" % action)
    targets = actions[action]["targets"]
    valid = flags_for(interface, action)
    known = all_flag_names(interface)
    positionals = 0
    i = 1
    while i < len(args):
        arg = args[i]
        i += 1
        if not is_flag_arg(arg):
            if positionals >= len(targets):
                if arg in actions:
                    fail("second action '%s'" % arg)
                fail("unexpected argument '%s'" % arg)
            positionals += 1
            continue
        name, eq, value = arg.partition("=")
        if name not in known:
            fail("unknown flag '%s'" % name)
        flag = next((f for f in valid if name in f["names"]), None)
        if flag is None:
            fail("flag '%s' is not valid for '%s'" % (name, action))
        if not flag["takes_value"]:
            if eq:
                fail("flag '%s' takes no value" % name)
            continue
        if not eq:
            # A value that is itself a known flag means the value was left out.
            if i >= len(args) or args[i] in known:
                fail("flag '%s' needs a value" % name)
            value = args[i]
            i += 1
        choices = flag["choices"]
        if choices and value not in choices:
            fail("invalid value '%s' for '%s' (choose %s)" % (value, name, ", ".join(choices)))
    for index, target in enumerate(targets):
        if target["required"] and index >= positionals:
            fail("missing %s for '%s'" % (target["name"], action))
