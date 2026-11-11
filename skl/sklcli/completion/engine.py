"""Tab-completion candidates, computed from the index alone so it stays fast."""
from __future__ import annotations

from typing import List, Mapping, Sequence, Tuple

from sklcli.help import BUILTINS
from sklcli.models import Entry, Index, Shell
from sklcli.parsing.interface import all_flag_names, flags_for
from sklcli.runmode.modes import RunMode, match_mode_flag, mode_flag_for

Candidates = List[Tuple[str, str]]


def _filter(prefix: str, pairs: Sequence[Tuple[str, str]]) -> Candidates:
    return [(c, d) for c, d in pairs if c.startswith(prefix)]


def _mode_flag_candidates(taken: Sequence[str], earlier: Sequence[str]) -> List[str]:
    """Mode flags to offer: none once one is already on the line, since only one is allowed."""
    if any(match_mode_flag(w, set(taken)) for w in earlier):
        return []
    return [mode_flag_for(m, set(taken)) for m in RunMode]


def _skill_line(entry: Entry, words: Sequence[str]) -> Candidates:
    cur = words[-1]
    interface = entry.get("interface")
    taken = sorted(all_flag_names(interface)) if interface else []
    if len(words) == 1:
        if interface is None:
            return _filter(cur, [("--help", "")] + [(m.flag, "") for m in RunMode])
        return _filter(cur, [(n, a.get("description", "")) for n, a in interface["actions"].items()])
    if interface is None or words[0] not in interface["actions"]:
        return []
    flags = flags_for(interface, words[0])
    if len(words) >= 3:
        prev = words[-2]
        for f in flags:
            if prev in f["names"] and f["takes_value"]:
                return _filter(cur, [(ch, "") for ch in f.get("choices", [])])
    earlier = set(words[1:-1])
    out = [(f["names"][0], "") for f in flags if not earlier.intersection(f["names"])]
    out += [(x, "") for x in _mode_flag_candidates(taken, list(earlier)) if x not in earlier]
    return _filter(cur, out)


def complete(index: Index, words: Sequence[str]) -> Candidates:
    skills: Mapping[str, Entry] = index.get("skills", {})
    if not words:
        return []
    cur = words[-1]
    if len(words) == 1:
        return _filter(cur, [(b, "") for b in BUILTINS] + [(n, "") for n in sorted(skills)])
    first = words[0]
    if first == "help":
        return _filter(cur, [(b, "") for b in BUILTINS]) if len(words) == 2 else []
    if first in ("show", "remove", "run") and len(words) == 2:
        return _filter(cur, [(n, "") for n in sorted(skills)])
    if first == "completion":
        return _filter(cur, [(s.value, "") for s in Shell]) if len(words) == 2 else []
    if first == "run":
        first, words = words[1], words[1:]
        if first not in skills:
            return []
        return _skill_line(skills[first], words[1:])
    if first in BUILTINS:
        return []
    if first in skills:
        return _skill_line(skills[first], words[1:])
    return []
