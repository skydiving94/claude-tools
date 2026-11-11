# skl completion for bash
_skl_complete() {
  local line
  COMPREPLY=()
  while IFS= read -r line; do
    [ -n "$line" ] && COMPREPLY+=("${line%%$'\t'*}")
  done < <(skl __complete -- "${COMP_WORDS[@]:1:COMP_CWORD}" 2>/dev/null)
}
complete -o default -F _skl_complete skl
