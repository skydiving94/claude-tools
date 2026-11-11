"""Parsing the usage block into an Interface, and querying it."""
from __future__ import annotations

import re
from typing import Dict, List, Mapping, Optional, Set, Tuple

from sklcli.models import Action, Entry, Flag, Group, Interface, Target
from sklcli.parsing.skillmd import normalise

_ACTION_NAME_RE = re.compile(r"^[a-z][a-z0-9-]*$")
_GROUP_RE = re.compile(r"^\s*([A-Za-z][^:]*?):\s*(.*)$")
_FLAG_RE = re.compile(r"^--?[A-Za-z][A-Za-z0-9-]*$")
_CHOICE_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_TOKEN_RE = re.compile(r'"[^"]*"|\S+')


def _parse_action_line(line: str) -> Optional[Tuple[str, Action]]:
    words = line.split()
    if not words or not _ACTION_NAME_RE.fullmatch(words[0]):
        return None
    targets: List[Target] = []
    i = 1
    while i < len(words):
        w = words[i]
        required = re.match(r"^<([^<>]+)>$", w)
        optional = re.match(r"^\[<([^<>]+)>\]$", w)
        if required:
            targets.append(Target(name=required.group(1), required=True))
        elif optional:
            targets.append(Target(name=optional.group(1), required=False))
        else:
            break
        i += 1
    # description: remainder of the line after the consumed words
    rest = line.strip()
    for w in words[:i]:
        rest = rest[len(w):].lstrip() if rest.startswith(w) else rest
    return words[0], Action(targets=targets, description=rest.strip())


def _split_actions(text: str, known: Mapping[str, Action]) -> Optional[List[str]]:
    pieces = [p.strip() for p in re.split(r"[/,]", text)]
    if pieces and all(p in known for p in pieces):
        return pieces
    return None


def _label_actions(label: str, known: Mapping[str, Action]) -> Optional[List[str]]:
    if label.strip().lower() == "global":
        return None
    m = re.search(r"\(([^)]*)\)", label)
    if m:
        found = _split_actions(m.group(1), known)
        if found is not None:
            return found
    return _split_actions(label, known)


def _parse_flags(text: str) -> List[Flag]:
    text = re.sub(r"\([^)]*\)", " ", text)
    tokens = _TOKEN_RE.findall(text)
    flags: List[Flag] = []
    i = 0
    alias = False
    while i < len(tokens):
        tok = tokens[i]
        if tok == "|":
            alias = bool(flags)
        elif _FLAG_RE.match(tok):
            if alias and flags:
                flags[-1]["names"].append(tok)
            else:
                flags.append(Flag(names=[tok], takes_value=False, choices=[]))
            alias = False
            nxt = tokens[i + 1] if i + 1 < len(tokens) else ""
            if nxt.startswith("<") or nxt.startswith('"<'):
                flag = flags[-1]
                flag["takes_value"] = True
                if nxt.startswith("<") and nxt.endswith(">"):
                    parts = nxt[1:-1].split("|")
                    if len(parts) >= 2 and all(_CHOICE_RE.match(p) for p in parts):
                        flag["choices"] = parts
                i += 1
        else:
            alias = False
        i += 1
    return flags


def parse_interface(block: str) -> Optional[Interface]:
    lines = normalise(block).split("\n")
    usage_line = None
    for line in lines:
        if line.startswith("/"):
            usage_line = line.strip()
            break
    actions: Dict[str, Action] = {}
    in_section = False
    rest_start = len(lines)
    for idx, line in enumerate(lines):
        if not in_section:
            if line.startswith("Actions"):
                in_section = True
            continue
        if not line.strip() or not line[0].isspace():
            rest_start = idx
            break
        parsed = _parse_action_line(line)
        if parsed:
            actions[parsed[0]] = parsed[1]
    if not actions:
        return None
    raw_groups: List[Tuple[str, Optional[List[str]], List[str]]] = []
    current_text: Optional[List[str]] = None
    for line in lines[rest_start:]:
        m = _GROUP_RE.match(line)
        if m and "--" not in m.group(1):
            label = m.group(1).strip()
            current_text = [m.group(2)]
            raw_groups.append((label, _label_actions(label, actions), current_text))
        elif current_text is not None and line[:1].isspace() and line.strip().startswith("-"):
            current_text.append(line)
    groups = [Group(label=label, actions=acts, flags=_parse_flags("\n".join(text)))
              for label, acts, text in raw_groups]
    return Interface(usage_line=usage_line, actions=actions, groups=groups)


def flags_for(interface: Interface, action: str) -> List[Flag]:
    out: List[Flag] = []
    seen: Set[str] = set()
    for g in interface["groups"]:
        if g["actions"] is not None and action not in g["actions"]:
            continue
        for f in g["flags"]:
            if f["names"][0] not in seen:
                seen.add(f["names"][0])
                out.append(f)
    return out


def all_flag_names(interface: Interface) -> Set[str]:
    return {n for g in interface["groups"] for f in g["flags"] for n in f["names"]}


def value_flag_names(interface: Interface, action: str) -> Set[str]:
    """Every spelling of the flags that take a value, for one action."""
    return {n for f in flags_for(interface, action) if f["takes_value"] for n in f["names"]}


def describe_actions(entry: Entry) -> str:
    if entry["interface"] is None:
        return "(pass-through)"
    return ", ".join(entry["interface"]["actions"])
