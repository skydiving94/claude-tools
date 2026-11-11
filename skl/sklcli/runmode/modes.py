"""Run modes (--copy, --run, --print, --app) and how their flags are told apart from a skill's."""
from __future__ import annotations

from enum import Enum
from typing import AbstractSet, List, Optional, Sequence, Set, Tuple

from sklcli.errors import UsageError
from sklcli.models import Entry
from sklcli.parsing.interface import all_flag_names


class RunMode(Enum):
    COPY = "copy"
    RUN = "run"
    PRINT = "print"
    APP = "app"

    @property
    def flag(self) -> str:
        return "--" + self.value

    @property
    def skl_flag(self) -> str:
        """The spelling that always means skl's mode, even if a skill defines `flag`."""
        return "--skl-" + self.value


DEFAULT_MODE = RunMode.COPY
MODE_FLAGS_TEXT = ", ".join(m.flag for m in RunMode)


def skill_flag_names(entry: Entry) -> Set[str]:
    interface = entry.get("interface")
    return set(all_flag_names(interface)) if interface else set()


def match_mode_flag(arg: str, taken: AbstractSet[str]) -> Optional[RunMode]:
    """The mode `arg` selects, or None. `taken` holds the flags the skill defines itself."""
    for mode in RunMode:
        if arg == mode.skl_flag or (arg == mode.flag and mode.flag not in taken):
            return mode
    return None


def mode_flag_for(mode: RunMode, taken: AbstractSet[str]) -> str:
    """The spelling to show for `mode`: prefixed when the skill defines the plain one."""
    return mode.skl_flag if mode.flag in taken else mode.flag


def split_mode(entry: Entry, args: Sequence[str]) -> Tuple[RunMode, List[str]]:
    """Pull the mode flag out of `args`. More than one mode flag, even a repeat, is an error."""
    taken = skill_flag_names(entry)
    chosen: List[RunMode] = []
    rest: List[str] = []
    for arg in args:
        mode = match_mode_flag(arg, taken)
        if mode is None:
            rest.append(arg)
        else:
            chosen.append(mode)
    if len(chosen) > 1:
        raise UsageError("choose only one of %s" % MODE_FLAGS_TEXT)
    return (chosen[0] if chosen else DEFAULT_MODE), rest
