"""Reading a SKILL.md: the usage block and the frontmatter name."""
from __future__ import annotations

import re
from typing import List, Optional

_HEADING_RE = re.compile(r"^##\s+Command interface", re.IGNORECASE)
_FENCE_RE = re.compile(r"^(```|~~~)")


def normalise(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def extract_block(skill_md: str) -> Optional[str]:
    lines = normalise(skill_md).split("\n")
    start = None
    for i, line in enumerate(lines):
        if _HEADING_RE.match(line):
            start = i + 1
            break
    if start is None:
        return None
    opened = None
    body: List[str] = []
    for line in lines[start:]:
        if opened is None:
            if line.startswith("## "):
                return None
            if _FENCE_RE.match(line):
                opened = line[:3]
        elif line.startswith(opened):
            return "\n".join(body)
        else:
            body.append(line)
    return None


def frontmatter_name(skill_md: str) -> Optional[str]:
    lines = normalise(skill_md).split("\n")
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            return None
        m = re.match(r"^name:\s*(.*?)\s*$", line)
        if m:
            value = m.group(1)
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            return value or None
    return None
