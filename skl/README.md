# skl

`skl` runs command-style Claude skills from a zsh or bash prompt on macOS and Linux. A command-style skill is one whose `SKILL.md` has a `## Command interface` section with a fenced usage block. `skl` keeps a local index of those skills, tab-completes their actions and flags, rejects bad input before any model call, and hands valid input to Claude. It needs Python 3.9+ and no third-party packages. The installer builds the `sklcli` package into one executable file.

## Install

```
git clone https://github.com/skydiving94/claude-tools.git
cd claude-tools
./skl/install.sh
```

The script builds `skl` from the `sklcli` package and puts it in `~/.local/bin` (set `SKL_BIN_DIR` to change that). To run from a checkout without installing, use `skl/skl`. Then add one line to your profile:

```
source <(skl completion zsh)     # ~/.zshrc
eval "$(skl completion bash)"    # ~/.bashrc
```

zsh needs `autoload -U compinit && compinit` before its line. The bash line uses `eval` because `source <(...)` does nothing in bash 3.2 (stock macOS).

## Usage

```
skl sync                          # index skills from ~/.claude/skills
skl import ./other                # add a .skill archive, a SKILL.md, or a folder
skl list                          # one line per skill: name, actions
skl notes add Hello --tag x       # copy the command to the clipboard; TAB completes skills, actions and flags
skl notes add Hello --run         # start an interactive claude session with it
skl notes add Hello --print       # claude -p "/notes add Hello"
skl notes add Hello --app         # open claude.ai/new?q=... in the browser
skl doctor                        # check claude CLI, sign-in, clipboard tool, store, roots
skl --help                        # commands, run options, environment, indexed skills
skl --version                     # skl 0.1.0
```

Other commands: `help [<command>]`, `show <skill> [--parsed]`, `remove <skill>`, `run <skill> ...` (for a skill named like a built-in). Bad input fails with exit code 2 and no model call, for example `skl notes list --bogus` prints `error: unknown flag '--bogus'`. `skl --help` (or plain `skl`) lists the commands; `skl help <command>` or `skl <command> --help` explains one. After a skill name, `--help` prints the skill's usage block. If a skill defines its own `--copy`, `--run`, `--print` or `--app`, the skill's flag wins and `skl`'s own is `--skl-copy`, `--skl-run`, `--skl-print` or `--skl-app`.

## Run modes

Give at most one mode flag; two (or the same one twice) is an error with exit code 2.

| Flag | What happens |
| --- | --- |
| `--copy` (default) | Copies the finished command to the clipboard, so you paste it into Claude yourself. |
| `--run` | Replaces `skl` with an interactive `claude` session that starts with the command. This was the default before `--copy`. |
| `--print` | Runs `claude -p` and prints the result. |
| `--app` | Opens claude.ai in the browser with the command filled in. |

`--copy` uses the first of `pbcopy`, `wl-copy`, `xclip` and `xsel` found on `PATH`, and tries the next one if a tool fails. The text goes in as is, with no shell and no trailing newline. It has the command on several lines: `/skill action`, then one line per target and per flag (a flag keeps its value), each line but the last ending in ` \`. If no tool works, the same text is printed to stdout and the exit code is still 0. `skl doctor` shows which tool would be used.

## How it finds skills

`skl sync` scans `~/.claude/skills`, then `./.claude/skills` (current directory up to the git root), then each directory in `SKL_SKILL_PATH` (colon-separated). Copies and the index live in `${XDG_DATA_HOME:-~/.local/share}/skl/`. Imported skills are never removed by `sync`.

## Limits

- Requirements a skill states only in prose (such as "also requires `--as`") are not checked locally; the skill enforces them.
- A skill whose usage block cannot be parsed is indexed as pass-through: it runs, but has no flag completion or validation.
- `--copy` needs a clipboard tool; over SSH or on a bare server there is usually none, so the command is printed instead.
- `--app` opens claude.ai in the browser with the command prefilled through a `claude.ai/new?q=` link. That prefill behaviour is not confirmed. You press send yourself, and the skill must exist in the account the browser is signed in to.
- Skills created in the Claude app appear only if they exist as files under `~/.claude/skills`; otherwise use `skl import`.
- `skl` has no login of its own. It uses whatever account the `claude` CLI is signed in to.
- The bash completion is written to work on macOS's bash 3.2 but has so far been tested on newer bash only.

## Tests

```
cd skl && python3 -m unittest discover -s tests -v
```
