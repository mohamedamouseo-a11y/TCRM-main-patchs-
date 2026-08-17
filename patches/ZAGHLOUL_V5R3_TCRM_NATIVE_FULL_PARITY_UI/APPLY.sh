#!/usr/bin/env bash
set -euo pipefail

TARGET=/var/www/TCRM-MAIN
PATCH=ZAGHLOUL_V5R3_TCRM_NATIVE_FULL_PARITY_UI
WORK=/tmp/$PATCH
BASE_EXPECTED=c7ca52c5bb0495400ed327601d50cf6c7a363c73
UPSTREAM=6ed9191189e71d2e69d9380422f9415ecc589266

cd "$TARGET"
git rev-parse --is-inside-work-tree >/dev/null
HEAD=$(git rev-parse HEAD)

git merge-base --is-ancestor "$BASE_EXPECTED" "$HEAD" || { echo "BASELINE_GUARD=FAIL"; exit 2; }
[ -d apps/zaghloul-wacrm ] || { echo "WACRM_SOURCE=FAIL"; exit 3; }
[ -f server/services/zaghloul-v5/WACRM_PARITY.json ] || { echo "PARITY_MANIFEST=FAIL"; exit 4; }
[ -f client/src/pages/ZaghloulV5Page.tsx ] || { echo "V5_UI=FAIL"; exit 5; }
[ -f server/services/zaghloul-v5/v5Service.ts ] || { echo "V5_SERVICE=FAIL"; exit 6; }

grep -Rqs "$UPSTREAM" apps/zaghloul-wacrm server/services/zaghloul-v5 2>/dev/null || { echo "UPSTREAM_PIN=FAIL"; exit 7; }

node - <<'NODE'
const fs=require('fs');
const p='server/services/zaghloul-v5/WACRM_PARITY.json';
const a=JSON.parse(fs.readFileSync(p,'utf8'));
if(!Array.isArray(a)||a.length!==15||a.some(x=>x.status!=='complete')) process.exit(1);
NODE

rm -rf "$WORK" && mkdir -p "$WORK"
printf '%s\n' "$HEAD" > "$WORK/baseline_head"
git status --porcelain=v1 -uall > "$WORK/status.before"

# Baseline TypeScript diagnostics; verification compares candidate against this.
set +e
NODE_OPTIONS=--max-old-space-size=8192 npx tsc --noEmit --pretty false > "$WORK/tsc.before" 2>&1
TSC_EXIT=$?
set -e
printf '%s\n' "$TSC_EXIT" > "$WORK/tsc.before.exit"

echo "BASELINE_HEAD=$HEAD"
echo "PARITY_COUNT=15"
echo "PREFLIGHT=PASS"
