"""Which folders `skl sync` scans for skills."""
from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional, Set, Union


def scan_roots(cwd: Union[str, Path]) -> List[Path]:
    cwd = Path(cwd).resolve()
    roots = [Path.home() / ".claude" / "skills"]
    top: Optional[Path] = None
    for d in [cwd] + list(cwd.parents):
        if (d / ".git").exists():
            top = d
            break
    if top is None:
        chain = [cwd]
    else:
        chain = [cwd]
        while chain[0] != top:
            chain.insert(0, chain[0].parent)
    roots.extend(d / ".claude" / "skills" for d in chain)
    for p in os.environ.get("SKL_SKILL_PATH", "").split(os.pathsep):
        if p:
            roots.append(Path(p))
    out: List[Path] = []
    seen: Set[str] = set()
    for r in roots:
        if r.is_dir():
            key = str(r.resolve())
            if key not in seen:
                seen.add(key)
                out.append(r)
    return out
