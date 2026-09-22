#!/bin/bash
# Run on the execution Mac. System/package changes require explicit flags.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PROFILE=headless
INSTALL_SYSTEM=false
INSTALL_BROWSER=false
for arg in "$@"; do
  case "$arg" in
    --desktop) PROFILE=desktop ;;
    --install-system) INSTALL_SYSTEM=true ;;
    --install-browser-tools) INSTALL_BROWSER=true ;;
    *) echo "Usage: bash scripts/setup-mac.sh [--desktop] [--install-system] [--install-browser-tools]" >&2; exit 2 ;;
  esac
done
if [ "$(uname -s)" != Darwin ]; then
  echo "This installer is for macOS." >&2; exit 2
fi
if ! command -v brew >/dev/null; then
  for candidate in /opt/homebrew/bin/brew /usr/local/bin/brew; do
    if [ -x "$candidate" ]; then export PATH="$(dirname "$candidate"):$PATH"; break; fi
  done
fi
if [ "$INSTALL_SYSTEM" = true ]; then
  command -v brew >/dev/null || { echo "Install Homebrew from https://brew.sh, then rerun." >&2; exit 2; }
  brew install python git node gh jq
  if [ "$PROFILE" = desktop ]; then brew install ffmpeg-full; fi
fi
if command -v brew >/dev/null; then
  BREW_PREFIX="$(brew --prefix)"
  export PATH="$BREW_PREFIX/bin:$BREW_PREFIX/sbin:$PATH"
  if [ "$PROFILE" = desktop ] && [ -x "$BREW_PREFIX/opt/ffmpeg-full/bin/ffmpeg" ]; then
    export PATH="$BREW_PREFIX/opt/ffmpeg-full/bin:$PATH"
  fi
fi
command -v python3 >/dev/null || { echo "Install Python 3.10 or newer." >&2; exit 2; }
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 2)'
if [ ! -d "$ROOT/.venv" ]; then python3 -m venv "$ROOT/.venv"; fi
"$ROOT/.venv/bin/python" -m pip install -r "$ROOT/jev-gate/requirements.txt" -r "$ROOT/requirements-dev.txt"
if [ "$INSTALL_BROWSER" = true ]; then
  npm install -g @vercel/before-and-after agent-browser
fi
"$ROOT/.venv/bin/python" "$ROOT/scripts/factory_doctor.py" --profile "$PROFILE"
echo "Automated checks complete. Follow docs/mac-mini-setup.md for manual acceptance checks."
