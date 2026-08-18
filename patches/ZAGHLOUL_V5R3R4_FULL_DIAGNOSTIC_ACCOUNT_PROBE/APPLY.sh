#!/usr/bin/env bash
set -euo pipefail
TARGET=${TCRM_PATH:-/var/www/TCRM-MAIN}
cd "$TARGET"
git rev-parse --is-inside-work-tree >/dev/null
echo PRECHECK=PASS
