# skl: design

Date: 2026-11-11. Status: awaiting review.

## Purpose

`skl` runs command-style Claude skills from a zsh or bash prompt on macOS and Linux. A command-style skill is one whose `SKILL.md` has a `## Command interface` section with a fenced usage block (the convention from the `command-style-skills` skill). `skl` keeps a local index of those skills, tab-completes their actions and flags, rejects bad input without a model call, and hands valid input to Claude in the terminal or in the Claude app.

Success means: after `skl sync`, typing `skl meal<TAB> up<TAB> ossobuco --sw<TAB>` completes to a valid command, and pressing Enter starts Claude with `/meal-prep-cookbook-recipe update ossobuco --swap ...`.

## Repository

Public repo `skydiving94/claude-tools`, a home for several small tools. Each tool lives in its own top-level folder with its own README. The top-level README is a short table of tools.

```
claude-tools/
  README.md                 table of tools, one line each
  LICENSE                   MIT
  skl/
    README.md               install, usage, limits
    skl                     the CLI, one Python 3 file, standard library only
    completions/skl.bash
    completions/_skl        zsh
    install.sh              copies skl to ~/.local/bin and prints the profile line
    tests/                  unittest, fixtures under tests/fixtures/
  docs/superpowers/specs/   this file
```

Python 3.9 or newer (the version Apple ships with the command line tools). No third-party packages.

## Commands

```
skl sync                       index skills from Claude Code's folders
skl import <path>              add a .skill archive, a SKILL.md, or a skill folder
skl list                       indexed skills, one line each
skl show <skill> [--parsed]    print the usage block verbatim; --parsed prints what skl understood
skl remove <skill>             drop an imported skill from the store
skl doctor                     check claude CLI, sign-in, store, and index
skl completion zsh|bash        print the completion script
skl <skill> <action> [<target>] [options] [--print | --app]
```

`skl <skill> ...` is the run form. A skill named like a built-in command is reached with `skl run <skill> ...`.

## Store and index

Store: `${XDG_DATA_HOME:-~/.local/share}/skl/`.

- `skills/<name>/SKILL.md`: a copy of each indexed skill, so the index survives changes to the source folders.
- `index.json`: one entry per skill with `name`, `source` (`sync` or `import`), `source_path`, `usage_block` (verbatim), and the parsed interface.

`skl sync` scans, in order, `~/.claude/skills/**/SKILL.md` and `./.claude/skills/**/SKILL.md` (current directory up to the git root), plus any directories in `SKL_SKILL_PATH`. It keeps skills that have a `## Command interface` heading, refreshes their copies, and removes `sync` entries whose source is gone. Imported entries are never removed by `sync`. On a name clash the later source wins and `sync` prints a note.

`skl import` accepts a `.skill` zip, a `SKILL.md`, or a folder. A skill without a command interface block is refused with an error. Archive members are extracted only if their resolved path stays inside the destination.

## Parsing the command interface

The parser takes the first fenced block after the `## Command interface` heading. It is tolerant, since real blocks vary. Rules, checked against the `meal-prep-cookbook-recipe` skill:

- Usage line: the first line starting with `/`. The skill name is the frontmatter `name`, falling back to this line.
- Actions: indented lines under a line starting with `Actions`. First word is the action. Following `<x>` words are required targets and `[<x>]` words optional targets. The rest, after two or more spaces, is the description.
- Option groups: a line of the form `<label>: ...` starts a group. The label decides which actions the group applies to:
  - `Global` applies to every action.
  - a label that is an action name, or several separated by `/` or `,`, applies to those.
  - a label with a parenthesised list, such as `Recipe options (add / update / duplicate)`, applies to the listed actions.
  - any other label applies to every action.
- Indented lines that start with `-` continue the previous group.
- Flags: every `--name` or `-x` word in a group, after parenthesised notes are stripped. `--help | -h` are aliases. A flag followed by `<...>` or `"<...>"` takes a value. A value written as literals separated by `|`, such as `<en|zh>`, gives completion choices.

If the block cannot be parsed into at least one action, the skill is still indexed as pass-through: name completion and running work, validation and flag completion are off, and `skl list` marks it.

## Validation

Before any model call, `skl` checks the input against the index and mirrors the skill contract:

- `--help` or `-h` anywhere: print the usage block verbatim, exit 0.
- Missing action, unknown action, missing required target, unknown flag, flag not valid for the action, or a value-taking flag without a value: print `error: <what is wrong>` and the usage line to stderr, exit 2.

Requirements stated only in prose, such as "`duplicate` also requires `--as`", are not checked locally. The skill itself still enforces them.

## Running

The command sent to Claude is `/<skill> <args>` with the user's arguments re-quoted so values with spaces survive.

- Default: `claude "/<skill> <args>"`, an interactive session in the terminal with the command already submitted.
- `--print`: `claude -p "/<skill> <args>"`, non-interactive, output to stdout, exit code passed through.
- `--app`: open `https://claude.ai/new?q=<url-encoded command>` with `open` (macOS) or `xdg-open` (Linux). The user presses send. If neither opener exists, print the URL.

`--print` and `--app` are `skl` flags and are stripped before validation. A skill that defines its own flag with either name wins; the `skl` flag is then given as `--skl-print` or `--skl-app`.

`skl` has no login. The terminal modes use whichever account the `claude` CLI is signed in to. `--app` uses whichever account the browser is signed in to, and the skill must exist in that account.

## Completion

The completion files are thin. They call `skl __complete -- <words so far>` and offer the lines it prints. `__complete` reads `index.json` only, so it stays fast.

- Word 1: built-in commands and skill names.
- Word 2 of a skill: its actions.
- Later words: flags valid for the chosen action that are not already present, plus `--print` and `--app`. After a flag with choices, the choices. After a value-taking flag without choices, nothing (the shell falls back to file names).

zsh shows action descriptions next to candidates. bash shows names only. bash completion works with bash 3.2.

## Errors

- `claude` not on PATH: run modes other than `--app` exit 127 with an install hint. `sync`, `list`, `show`, and completion still work.
- Missing or corrupt `index.json`: commands say to run `skl sync`; completion prints nothing.
- Unknown skill: `error:` plus the closest indexed names, exit 2. No guessing.

## Testing

`python3 -m unittest` under `skl/tests`, no network and no `claude` binary:

- Parser: fixtures for the contract template and for the `meal-prep-cookbook-recipe` block (grouped options, continuation lines, parenthesised notes, value choices), plus an unparseable block.
- Validation: each error case and `--help`.
- Completion: candidates at each position via `__complete`.
- Sync and import: temporary directories, including a zip with a path-escaping member.
- Run: the built command line for each mode, with `claude` and the opener replaced by a stub on PATH.

Both completion files are loaded in a real bash and zsh once as a smoke test.

## Open points to confirm on a real machine

- Whether skills created in the Claude app appear under `~/.claude/skills` locally. `skl doctor` reports what it finds; `skl import` covers the gap.
- Whether `claude.ai/new?q=` prefills the prompt for a signed-in user. If it does not, `--app` falls back to copying the command to the clipboard and opening the app.
- No link is known that opens the desktop app directly with a prefilled prompt, so `--app` targets the browser.

## Out of scope

Homebrew formula, fish completion, Windows, a login of its own, uploading or editing skills, and syncing through the developer Skills API.
