"""Entry point: route argv to a built-in command or to the skill run form."""
from __future__ import annotations

import sys
from typing import Sequence

from sklcli import __version__
from sklcli.commands import COMMANDS
from sklcli.commands.misc import cmd_complete
from sklcli.commands.run import cmd_run
from sklcli.errors import SklError, UsageError
from sklcli.help import HELP_FLAGS, command_help, help_screen
from sklcli.output import out


def _wants_command_help(command: str, rest: Sequence[str]) -> bool:
    # 'run <skill> ... --help' belongs to the skill; only a bare 'run --help' is run's help.
    if command == "run":
        return len(rest) == 1 and rest[0] in HELP_FLAGS
    return command != "help" and any(a in HELP_FLAGS for a in rest)


def main(argv: Sequence[str]) -> int:
    argv = list(argv)
    try:
        if argv and argv[0] == "__complete":
            return cmd_complete(argv[1:])
        if argv in (["--version"], ["-V"]):
            out("skl %s" % __version__)
            return 0
        if not argv or argv in (["--help"], ["-h"]):
            sys.stdout.write(help_screen())
            return 0
        if argv[0] in COMMANDS:
            if _wants_command_help(argv[0], argv[1:]):
                sys.stdout.write(command_help(argv[0]))
                return 0
            return COMMANDS[argv[0]](argv[1:])
        return cmd_run(argv)
    except KeyboardInterrupt:
        return 130
    except UsageError as e:
        sys.stderr.write("error: %s\n" % e)
        return 2
    except (SklError, OSError) as e:
        message = e.strerror or e if isinstance(e, OSError) and not isinstance(e, SklError) else e
        sys.stderr.write("error: %s\n" % message)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
