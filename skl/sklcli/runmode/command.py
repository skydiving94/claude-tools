"""Building the `/skill args` command: one-line for claude and the browser, multi-line to copy."""
from __future__ import annotations

import re
import urllib.parse
from typing import List, Optional, Sequence, Set

from sklcli.parsing.validate import is_flag_arg

_SAFE_ARG_RE = re.compile(r"^[A-Za-z0-9_@%+=:,./-]+$")


def quote_arg(arg: str) -> str:
    if _SAFE_ARG_RE.match(arg):
        return arg
    return '"%s"' % arg.replace("\\", "\\\\").replace('"', '\\"')


def build_command(name: str, args: Sequence[str]) -> str:
    return "/" + name + "".join(" " + quote_arg(a) for a in args)


def command_lines(name: str, args: Sequence[str], value_flags: Optional[Set[str]]) -> List[str]:
    """Split the command into lines: `/skill action`, then one line per target or flag.

    A flag keeps its value on its own line. `value_flags` lists the flags that take a value;
    None means unknown (a pass-through skill), so a flag takes the next word if it is not a flag.
    """
    first = "/" + name + (" " + quote_arg(args[0]) if args else "")
    lines = [first]
    i = 1
    while i < len(args):
        arg = args[i]
        i += 1
        if not is_flag_arg(arg):
            lines.append(quote_arg(arg))
            continue
        line = quote_arg(arg)
        flag, eq, _value = arg.partition("=")
        if not eq and i < len(args):
            if value_flags is None:
                takes_value = not is_flag_arg(args[i])
            else:
                takes_value = flag in value_flags
            if takes_value:
                line += " " + quote_arg(args[i])
                i += 1
        lines.append(line)
    return lines


def join_lines(lines: Sequence[str]) -> str:
    """Join with a trailing ' \\' on every line but the last. No trailing newline."""
    return " \\\n".join(lines)


def app_url(command: str) -> str:
    return "https://claude.ai/new?q=" + urllib.parse.quote(command, safe="")
