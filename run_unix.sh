#!/usr/bin/env sh
# Run from any directory; no third-party Python packages are required.
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"
if command -v python3 >/dev/null 2>&1; then
    exec python3 main.py "$@"
elif command -v python >/dev/null 2>&1; then
    exec python main.py "$@"
else
    echo "Python 3 was not found. Install Python, then run this script again." >&2
    exit 1
fi
