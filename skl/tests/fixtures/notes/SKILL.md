---
name: notes
description: Fixture skill.
---
## Command interface (read first)

```
/notes <action> [<target>] [options]

Actions (exactly one, required):
  add <title>       Create a note
  show [<title>]    Show one note or the latest
  list              List notes
Global:  --commit (default: preview only)   --help | -h
Per-action options:
  add:   --tag <value>  --no-index
  list:  --format <short|long>
```

## 1. Body
Not part of the interface.
