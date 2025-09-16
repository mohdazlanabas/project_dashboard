#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_PY="$SCRIPT_DIR/../venv/bin/python"

if [[ ! -x "$VENV_PY" ]]; then
  echo "Virtualenv Python not found at: $VENV_PY" >&2
  exit 1
fi

exec "$VENV_PY" manage.py migrate "$@"

