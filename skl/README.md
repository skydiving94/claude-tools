# skl

`skl` runs command-style Claude skills from a zsh or bash prompt on macOS and Linux. A command-style skill is one whose `SKILL.md` has a `## Command interface` section with a fenced usage block. `skl` keeps a local index of those skills, tab-completes their actions and flags, rejects bad input before any model call, and hands valid input to Claude. It is one Python 3.9+ file with no third-party packages.

## Install

```
git clone https://github.com/skydiving94/claude-tools.git
cd claude-tools
./skl/install.sh
```

The script copies `skl` to `~/.local/bin` (set `SKL_BIN_DIR` to change that). Then add one line to your profile:

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
skl notes add Hello --tag x       # run; TAB completes skills, actions and flags
skl notes add Hello --print       # claude -p "/notes add Hello"
skl notes add Hello --app         # open claude.ai/new?q=... in the browser
skl doctor                        # check claude CLI, sign-in, store, roots
```

Other commands: `show <skill> [--parsed]`, `remove <skill>`, `run <skill> ...` (for a skill named like a built-in). Bad input fails with exit code 2 and no model call, for example `skl notes list --bogus` prints `error: unknown flag '--bogus'`. `--help` prints the skill's usage block. If a skill defines its own `--print` or `--app`, the skill's flag wins and `skl`'s own are `--skl-print` and `--skl-app`.

## How it finds skills

`skl sync` scans `~/.claude/skills`, then `./.claude/skills` (current directory up to the git root), then each directory in `SKL_SKILL_PATH` (colon-separated). Copies and the index live in `${XDG_DATA_HOME:-~/.local/share}/skl/`. Imported skills are never removed by `sync`.

## Limits

- Requirements a skill states only in prose (such as "also requires `--as`") are not checked locally; the skill enforces them.
- A skill whose usage block cannot be parsed is indexed as pass-through: it runs, but has no flag completion or validation.
- `--app` opens claude.ai in the browser with the command prefilled through a `claude.ai/new?q=` link. That prefill behaviour is not confirmed. You press send yourself, and the skill must exist in the account the browser is signed in to.
- Skills created in the Claude app appear only if they exist as files under `~/.claude/skills`; otherwise use `skl import`.
- `skl` has no login of its own. It uses whatever account the `claude` CLI is signed in to.
- The bash completion is written to work on macOS's bash 3.2 but has so far been tested on newer bash only.

## Tests

```
cd skl && python3 -m unittest discover -s tests -v
```
