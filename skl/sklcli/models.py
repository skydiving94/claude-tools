"""Data shapes shared across skl. Entries are stored as JSON, so these are TypedDicts."""
from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, TypedDict


class Source(str, Enum):
    """Where an indexed skill came from. A str subclass so it round-trips through JSON."""

    SYNC = "sync"
    IMPORT = "import"


class Shell(str, Enum):
    ZSH = "zsh"
    BASH = "bash"


class Target(TypedDict):
    name: str
    required: bool


class Action(TypedDict):
    targets: List[Target]
    description: str


class Flag(TypedDict):
    names: List[str]
    takes_value: bool
    choices: List[str]


class Group(TypedDict):
    label: str
    actions: Optional[List[str]]
    flags: List[Flag]


class Interface(TypedDict):
    usage_line: Optional[str]
    actions: Dict[str, Action]
    groups: List[Group]


class Entry(TypedDict):
    name: str
    source: str
    source_path: str
    usage_block: str
    interface: Optional[Interface]


class Index(TypedDict):
    version: int
    skills: Dict[str, Entry]
