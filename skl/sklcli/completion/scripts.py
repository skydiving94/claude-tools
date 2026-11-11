"""The shell completion scripts printed by `skl completion`. They only call `skl __complete`."""

BASH_COMPLETION = """\
# skl completion for bash
_skl_complete() {
  local name rest
  COMPREPLY=()
  while IFS=$'\\t' read -r name rest; do
    if [ -n "$name" ]; then COMPREPLY+=("$name"); fi
  done < <(skl __complete -- "${COMP_WORDS[@]:1:COMP_CWORD}" 2>/dev/null)
}
complete -o default -F _skl_complete skl
"""

ZSH_COMPLETION = """\
#compdef skl
_skl() {
  local -a out cands
  local line name desc
  out=("${(@f)$(skl __complete -- "${(@)words[2,CURRENT]}" 2>/dev/null)}")
  for line in $out; do
    [[ -z $line ]] && continue
    name=${line%%$'\\t'*}
    desc=""
    [[ $line == *$'\\t'* ]] && desc=${line#*$'\\t'}
    name=${name//:/\\\\:}
    if [[ -n $desc ]]; then cands+=("$name:$desc"); else cands+=("$name"); fi
  done
  if (( ${#cands} )); then _describe -t skl 'skl' cands; else _files; fi
}
if [[ $funcstack[1] == _skl ]]; then _skl "$@"; else compdef _skl skl; fi
"""
