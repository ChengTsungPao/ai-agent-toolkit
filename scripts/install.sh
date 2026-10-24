#!/usr/bin/env bash
# Environment bootstrap — macOS / Linux
#
#   ./scripts/install.sh              # -> report
#   ./scripts/install.sh bootstrap    # -> install missing + wire every harness found
#   ./scripts/install.sh wire codex
#
# Only hard dependency is uv; this script installs it if missing, then hands
# off to setup.py running on a pinned Python (tomllib guaranteed).
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v uv >/dev/null 2>&1; then
  echo "installing uv ..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # shellcheck disable=SC1090
  export PATH="$HOME/.local/bin:$PATH"
fi

exec uv run --python 3.12 "$REPO/scripts/setup.py" "$@"
