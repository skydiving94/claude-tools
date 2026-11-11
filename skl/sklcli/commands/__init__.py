"""The built-in commands, by name."""
from __future__ import annotations

from typing import Callable, Dict, Sequence

from sklcli.commands.doctor import cmd_doctor
from sklcli.commands.listing import cmd_list, cmd_remove, cmd_show
from sklcli.commands.misc import cmd_completion, cmd_help
from sklcli.commands.run import cmd_run
from sklcli.commands.sync import cmd_import, cmd_sync

Command = Callable[[Sequence[str]], int]

COMMANDS: Dict[str, Command] = {
    "sync": cmd_sync, "import": cmd_import, "list": cmd_list, "show": cmd_show,
    "remove": cmd_remove, "doctor": cmd_doctor, "run": cmd_run,
    "completion": cmd_completion, "help": cmd_help,
}
