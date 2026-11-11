"""Help text. The command table drives the help screen, per-command help and completion."""
from __future__ import annotations

from typing import List, NamedTuple, Tuple

from sklcli import __version__
from sklcli.errors import UsageError
from sklcli.parsing.interface import describe_actions
from sklcli.runmode.modes import RunMode
from sklcli.store import index as index_store


class CommandHelp(NamedTuple):
    name: str
    usage: str
    summary: str
    description: str


RUN_OPTION_LINES: Tuple[Tuple[RunMode, str], ...] = (
    (RunMode.COPY, "Copy the command to the clipboard (the default)"),
    (RunMode.RUN, "Start an interactive claude session with the command"),
    (RunMode.PRINT, "Run non-interactively (claude -p) and print the result"),
    (RunMode.APP, "Open claude.ai in the browser with the command filled in"),
)


def _run_options(indent: str) -> str:
    return "\n".join("%s%-12s %s" % (indent, m.flag, text) for m, text in RUN_OPTION_LINES)


COMMANDS_HELP: Tuple[CommandHelp, ...] = (
    CommandHelp("sync", "sync", "Index skills from Claude Code's skill folders",
                "Scans the skill folders and refreshes the index. Imported skills are kept."),
    CommandHelp("import", "import <path>", "Add a .skill archive, a SKILL.md, or a skill folder",
                "Copies a skill that has a command interface block into the store and indexes it."),
    CommandHelp("list", "list", "List indexed skills and their actions",
                "Prints one line per indexed skill: its name and actions."),
    CommandHelp("show", "show <skill> [--parsed]", "Print a skill's usage block",
                "Prints the skill's usage block verbatim.\n\n"
                "Options:\n  --parsed   Print what skl understood of the usage block, as JSON"),
    CommandHelp("remove", "remove <skill>", "Drop a skill from the index",
                "Removes the skill and its stored copy from the index."),
    CommandHelp("doctor", "doctor", "Check the claude CLI, sign-in, clipboard and the index",
                "Reports whether the claude CLI is found and signed in, which clipboard tool "
                "--copy would use, and the state of the store, roots and index."),
    CommandHelp("completion", "completion <zsh|bash>", "Print the shell completion script",
                "Prints the completion script for your shell. Load it from your profile."),
    CommandHelp("run", "run <skill> [args]", "Run a skill whose name matches a command",
                "Runs a skill by name, for a skill named like a built-in command.\n\n"
                "Options (give at most one; --copy is the default):\n" + _run_options("  ")),
    CommandHelp("help", "help [<command>]", "Show this help, or help for one command",
                "Shows the command list, or the usage and description of one command."),
)
BUILTINS: Tuple[str, ...] = tuple(c.name for c in COMMANDS_HELP)
HELP_HINT = "run 'skl help' to see the commands"
HELP_FLAGS = ("--help", "-h")


def help_screen() -> str:
    try:
        skills = index_store.load_index()["skills"]
    except Exception:
        skills = {}
    mode_choice = " | ".join(m.flag for m in RunMode)
    lines: List[str] = [
        "skl %s - run command-style Claude skills from your shell" % __version__, "",
        "Usage:", "  skl <command> [args]",
        "  skl <skill> <action> [<target>] [options] [%s]" % mode_choice, "", "Commands:"]
    lines += ["  %-23s %s" % (c.usage, c.summary) for c in COMMANDS_HELP]
    lines += ["", "Run options (give at most one):", _run_options("  "),
              "  --help, -h   Show help (after a skill name: that skill's usage block)",
              "  --version    Show the version", "",
              "Environment:",
              "  SKL_SKILL_PATH   Extra skill folders to scan (separated like PATH)",
              "  XDG_DATA_HOME    Where skl keeps its index (default ~/.local/share)", "",
              "Indexed skills:"]
    if skills:
        width = max(len(n) for n in skills) + 3
        for name in sorted(skills):
            try:
                lines.append("  %s%s" % (name.ljust(width), describe_actions(skills[name])))
            except Exception:
                lines.append("  %s" % name)
    else:
        lines.append("  none indexed, run 'skl sync'")
    return "\n".join(lines) + "\n"


def command_help(name: str) -> str:
    for c in COMMANDS_HELP:
        if c.name == name:
            return "usage: skl %s\n\n%s\n" % (c.usage, c.description)
    raise UsageError("unknown command '%s'\n%s" % (name, HELP_HINT))
