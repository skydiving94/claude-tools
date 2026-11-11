#!/bin/sh
set -eu

if ! command -v python3 >/dev/null 2>&1; then
    echo "error: python3 not found" >&2
    exit 1
fi

src_dir=$(cd "$(dirname "$0")" && pwd)
bin_dir=${SKL_BIN_DIR:-$HOME/.local/bin}

# Build one executable file (a Python zipapp) from the sklcli package.
stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT
cp -R "$src_dir/sklcli" "$stage/sklcli"
find "$stage" -name __pycache__ -type d -prune -exec rm -rf {} +
printf 'import sys\n\nfrom sklcli.cli import main\n\nsys.exit(main(sys.argv[1:]))\n' > "$stage/__main__.py"

mkdir -p "$bin_dir"
python3 -m zipapp "$stage" -p "/usr/bin/env python3" -o "$bin_dir/skl"
chmod 755 "$bin_dir/skl"

echo "installed $bin_dir/skl"
echo "Add to ~/.zshrc:   source <(skl completion zsh)"
echo 'Add to ~/.bashrc:  eval "$(skl completion bash)"'
echo "Then run: skl sync"

case ":$PATH:" in
    *":$bin_dir:"*) ;;
    *) echo "note: $bin_dir is not on your PATH" ;;
esac
