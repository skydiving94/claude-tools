"""Putting text on the system clipboard through whichever command-line tool is installed."""
from __future__ import annotations

import shutil
import subprocess
from typing import List, NamedTuple, Optional, Tuple


class ClipboardTool(NamedTuple):
    name: str
    args: Tuple[str, ...]


# Tried in this order: macOS first, then Wayland, then X11.
CANDIDATES: Tuple[ClipboardTool, ...] = (
    ClipboardTool("pbcopy", ()),
    ClipboardTool("wl-copy", ()),
    ClipboardTool("xclip", ("-selection", "clipboard")),
    ClipboardTool("xsel", ("--clipboard", "--input")),
)
_TIMEOUT_SECONDS = 5


def installed_tools() -> List[ClipboardTool]:
    return [t for t in CANDIDATES if shutil.which(t.name)]


def _run_tool(tool: ClipboardTool, text: str) -> bool:
    path = shutil.which(tool.name)
    if path is None:
        return False
    try:
        # No shell. Output goes to /dev/null so xclip, xsel and wl-copy, which keep a
        # background process alive to serve the clipboard, cannot hold this call open.
        result = subprocess.run([path, *tool.args], input=text.encode("utf-8"),
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                timeout=_TIMEOUT_SECONDS)
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def copy_text(text: str) -> Optional[str]:
    """Copy `text` as is, with nothing appended. Return the tool's name, or None on failure.

    A tool that is installed but fails is skipped and the next one is tried.
    """
    for tool in installed_tools():
        if _run_tool(tool, text):
            return tool.name
    return None


def first_tool_name() -> Optional[str]:
    tools = installed_tools()
    return tools[0].name if tools else None
