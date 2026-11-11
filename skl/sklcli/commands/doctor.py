"""`skl doctor`: what skl can see of the claude CLI, the clipboard, the store and the roots."""
from __future__ import annotations

import os
import shutil
import subprocess
from typing import Sequence, Tuple

from sklcli.errors import UsageError
from sklcli.output import out
from sklcli.runmode import clipboard
from sklcli.store import index as index_store
from sklcli.store.paths import store_dir
from sklcli.store.roots import scan_roots


def _claude_status(claude: str) -> Tuple[str, str]:
    version = "unknown"
    signin = "not confirmed (run `claude` once to sign in)"
    try:
        r = subprocess.run(["claude", "--version"], capture_output=True, text=True, timeout=10,
                           stdin=subprocess.DEVNULL)
        lines = r.stdout.strip().splitlines()
        if lines:
            version = lines[0]
    except (OSError, subprocess.SubprocessError, ValueError):
        pass
    try:
        r = subprocess.run(["claude", "auth", "status"], capture_output=True, timeout=10,
                           stdin=subprocess.DEVNULL)
        if r.returncode == 0:
            signin = "ok"
    except (OSError, subprocess.SubprocessError):
        pass
    return version, signin


def cmd_doctor(args: Sequence[str]) -> int:
    if args:
        raise UsageError("doctor takes no arguments")
    claude = shutil.which("claude")
    out("claude: %s" % (claude or "not found"))
    version, signin = _claude_status(claude) if claude else ("unknown", "not confirmed (run `claude` once to sign in)")
    out("version: %s" % version)
    out("sign-in: %s" % signin)
    tool = clipboard.first_tool_name()
    out("clipboard: %s" % (tool or "none (--copy prints the command instead)"))
    out("store: %s" % store_dir())
    skills = index_store.load_index()["skills"]
    passthrough = sum(1 for e in skills.values() if e.get("interface") is None)
    out("skills: %d indexed (%d pass-through)" % (len(skills), passthrough))
    roots = scan_roots(os.getcwd())
    if roots:
        out("roots:")
        for r in roots:
            out("  %s" % r)
    else:
        out("roots: none found")
    return 0 if claude else 1
