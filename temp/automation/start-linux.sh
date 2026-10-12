#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
python3 run.py init
python3 run.py audit
python3 run.py report
echo "打开 work/report.html；后续命令见 README.md"
