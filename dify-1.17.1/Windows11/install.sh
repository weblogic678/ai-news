#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
command -v python3 >/dev/null || { echo "Install Python 3.10+ first."; exit 1; }
exec python3 installer.py "${@:-install}"
