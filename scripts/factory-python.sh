#!/bin/bash
# Stable process PATH for SSH and other noninteractive launchers.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BREW_BIN="$(command -v brew || true)"
if [ -z "$BREW_BIN" ]; then
  for candidate in /opt/homebrew/bin/brew /usr/local/bin/brew; do
    if [ -x "$candidate" ]; then BREW_BIN="$candidate"; break; fi
  done
fi
if [ -n "$BREW_BIN" ]; then
  BREW_PREFIX="$("$BREW_BIN" --prefix)"
  export PATH="$BREW_PREFIX/opt/ffmpeg-full/bin:$BREW_PREFIX/bin:$BREW_PREFIX/sbin:$PATH"
fi
if [ ! -x "$ROOT/.venv/bin/python" ]; then
  echo "Run scripts/setup-mac.sh on this Mac to create .venv." >&2; exit 2
fi
exec "$ROOT/.venv/bin/python" "$@"
