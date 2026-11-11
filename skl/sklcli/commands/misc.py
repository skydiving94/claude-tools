"""`skl help`, `skl completion` and the hidden `skl __complete`."""
from __future__ import annotations

import sys
from typing import Sequence

from sklcli.completion.engine import complete
from sklcli.completion.scripts import BASH_COMPLETION, ZSH_COMPLETION
from sklcli.errors import UsageError
from sklcli.help import HELP_FLAGS, command_help, help_screen
from sklcli.models import Shell
from sklcli.store import index as index_store


def cmd_help(args: Sequence[str]) -> int:
    if not args:
        sys.stdout.write(help_screen())
    elif len(args) == 1:
        sys.stdout.write(command_help("help" if args[0] in HELP_FLAGS else args[0]))
    else:
        raise UsageError("usage: skl help [<command>]")
    return 0


def cmd_completion(args: Sequence[str]) -> int:
    shells = [s.value for s in Shell]
    if len(args) != 1 or args[0] not in shells:
        raise UsageError("choose zsh or bash")
    sys.stdout.write(BASH_COMPLETION if args[0] == Shell.BASH else ZSH_COMPLETION)
    return 0


def cmd_complete(args: Sequence[str]) -> int:
    """Never fails and never prints errors: a broken completion must not disturb the prompt."""
    try:
        words = args[1:] if args and args[0] == "--" else args
        try:
            index = index_store.load_index()
        except Exception:
            index = index_store.empty_index()
        pairs = complete(index, list(words))
        sys.stdout.write("".join(c + ("\t" + d if d else "") + "\n" for c, d in pairs))
        sys.stdout.flush()
    except Exception:
        pass
    return 0
