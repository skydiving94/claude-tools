# skl completion for bash
_skl_complete() {
  local name rest
  COMPREPLY=()
  while IFS=$'\t' read -r name rest; do
    if [ -n "$name" ]; then COMPREPLY+=("$name"); fi
  done < <(skl __complete -- "${COMP_WORDS[@]:1:COMP_CWORD}" 2>/dev/null)
}
complete -o default -F _skl_complete skl
