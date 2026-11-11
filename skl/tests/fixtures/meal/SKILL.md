---
name: meal-prep-cookbook-recipe
description: Fixture skill.
---
## Command interface (read first)
This skill behaves like a shell command.

```
/meal-prep-cookbook-recipe <action> [<recipe>] [options]

Actions (exactly one, required):
  add <recipe>         New recipe from pasted text or an image
  update <recipe>      Targeted change to an existing recipe
  duplicate <recipe>   Copy with customizations (--as required)
  remove <recipe>      Remove (refuses if it has derived dishes)
  list                 List recipes (nested by parent)

Global:     --commit (default: preview only)   --help | -h
Recipe options (add / update / duplicate):
  --sizes <list>   --parent <recipe>   --nutrition <label|none>
  --no-cost   --no-sauce-tray   --no-freezing   --lang <en|zh>
duplicate:  --as <new-name>   --swap "<old>=<new>"   --note "<text>"
update:     --swap "<old>=<new>"   --note "<text>"
remove:     --cascade (needs --commit)
list:       --parent <recipe>  --lang <en|zh>  --search <text>  --flat
```
