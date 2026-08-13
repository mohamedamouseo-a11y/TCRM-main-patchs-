#!/usr/bin/env bash
set -Eeuo pipefail

PATCH_NAME="ZAGHLOUL_V5R2_WACRM_PARITY_COMPLETION"
FINAL_MARKER="${PATCH_NAME}_OK"
TARGET="${TCRM_PATH:-/var/www/TCRM-MAIN}"
PARITY="$TARGET/server/services/zaghloul-v5/WACRM_PARITY.json"
UPSTREAM="$TARGET/apps/zaghloul-wacrm/.wacrm-upstream-commit"
EXPECTED_UPSTREAM="6ed9191189e71d2e69d9380422f9415ecc589266"
EXPECTED_COUNT=15

[[ -d "$TARGET" ]] || { echo "ERROR=TARGET_NOT_FOUND"; exit 2; }
[[ -f "$PARITY" ]] || { echo "ERROR=PARITY_MANIFEST_MISSING"; exit 3; }
[[ -f "$UPSTREAM" ]] || { echo "ERROR=UPSTREAM_PIN_MISSING"; exit 3; }
[[ "$(tr -d '\r\n' < "$UPSTREAM")" == "$EXPECTED_UPSTREAM" ]] || { echo "ERROR=UPSTREAM_PIN_MISMATCH"; exit 3; }
[[ -f "$TARGET/apps/zaghloul-wacrm/LICENSE" ]] || { echo "ERROR=MIT_LICENSE_MISSING"; exit 3; }

node - "$PARITY" "$EXPECTED_COUNT" <<'NODE'
const fs = require('fs');
const p = process.argv[2];
const expected = Number(process.argv[3]);
const data = JSON.parse(fs.readFileSync(p, 'utf8'));
const items = Array.isArray(data) ? data : data.features;
if (!Array.isArray(items)) throw new Error('PARITY_FORMAT_INVALID');
if (items.length !== expected) throw new Error(`PARITY_COUNT_${items.length}_EXPECTED_${expected}`);
for (const item of items) {
  if (!item || item.status !== 'complete') throw new Error(`PARITY_INCOMPLETE:${item?.id || 'unknown'}`);
  if (!Array.isArray(item.evidence) || item.evidence.length === 0) throw new Error(`PARITY_NO_EVIDENCE:${item?.id || 'unknown'}`);
}
console.log(`PARITY_COMPLETE_COUNT=${items.length}`);
NODE

echo "VERIFY_GATE=READY"
echo "NEXT=RUN_VERIFY_SH"
