"""Doing something with a validated command: copy it, run claude, or open the app."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from typing import Optional, Sequence, Set

from sklcli.models import Entry
from sklcli.output import err, out
from sklcli.parsing.interface import value_flag_names
from sklcli.runmode import clipboard
from sklcli.runmode.command import app_url, build_command, command_lines, join_lines
from sklcli.runmode.modes import RunMode


def _value_flags(entry: Entry, args: Sequence[str]) -> Optional[Set[str]]:
    interface = entry.get("interface")
    if interface is None or not args:
        return None
    return value_flag_names(interface, args[0])


def _copy(entry: Entry, args: Sequence[str]) -> int:
    text = join_lines(command_lines(entry["name"], args, _value_flags(entry, args)))
    tool = clipboard.copy_text(text)
    if tool is not None:
        err("copied to clipboard (%s): %s" % (tool, build_command(entry["name"], args)))
        return 0
    if clipboard.installed_tools():
        err("clipboard tool failed, printing the command instead")
    else:
        err("no clipboard tool found, printing the command instead")
    out(text)
    return 0


def _open_app(command: str) -> int:
    url = app_url(command)
    err("opening %s" % url)
    opener = "open" if sys.platform == "darwin" else "xdg-open"
    if shutil.which(opener):
        subprocess.call([opener, url])
    else:
        out(url)
    return 0


def _exec_claude(command: str, mode: RunMode) -> int:
    if not shutil.which("claude"):
        err("error: claude CLI not found, install Claude Code or use --app")
        return 127
    sys.stdout.flush()
    sys.stderr.flush()
    argv = ["claude", "-p", command] if mode is RunMode.PRINT else ["claude", command]
    try:
        os.execvp("claude", argv)
    except OSError as e:
        err("error: %s" % (e.strerror or e))
        return 1
    return 0


def launch(entry: Entry, args: Sequence[str], mode: RunMode) -> int:
    if mode is RunMode.COPY:
        return _copy(entry, args)
    command = build_command(entry["name"], args)
    if mode is RunMode.APP:
        return _open_app(command)
    return _exec_claude(command, mode)
