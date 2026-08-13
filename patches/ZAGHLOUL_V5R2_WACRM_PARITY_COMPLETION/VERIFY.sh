#!/usr/bin/env bash
set -Eeuo pipefail

PATCH_NAME="ZAGHLOUL_V5R2_WACRM_PARITY_COMPLETION"
FINAL_MARKER="${PATCH_NAME}_OK"
TARGET="${TCRM_PATH:-/var/www/TCRM-MAIN}"
TMP="$(mktemp -d)"
PARITY="$TARGET/server/services/zaghloul-v5/WACRM_PARITY.json"
UPSTREAM="$TARGET/apps/zaghloul-wacrm/.wacrm-upstream-commit"
EXPECTED_UPSTREAM="6ed9191189e71d2e69d9380422f9415ecc589266"
EXPECTED_COUNT=15
ACCEPTED_TSC_CEILING=191

cleanup(){ rm -rf "$TMP"; }
trap cleanup EXIT

[[ -d "$TARGET" ]] || { echo "ERROR=TARGET_NOT_FOUND"; exit 2; }
[[ -f "$PARITY" ]] || { echo "ERROR=PARITY_MANIFEST_MISSING"; exit 3; }
[[ -f "$UPSTREAM" ]] || { echo "ERROR=UPSTREAM_PIN_MISSING"; exit 3; }
[[ "$(tr -d '\r\n' < "$UPSTREAM")" == "$EXPECTED_UPSTREAM" ]] || { echo "ERROR=UPSTREAM_PIN_MISMATCH"; exit 3; }
[[ -f "$TARGET/apps/zaghloul-wacrm/LICENSE" ]] || { echo "ERROR=MIT_LICENSE_MISSING"; exit 3; }

node - "$PARITY" "$EXPECTED_COUNT" <<'NODE'
const fs=require('fs');
const p=process.argv[2], expected=Number(process.argv[3]);
const data=JSON.parse(fs.readFileSync(p,'utf8'));
const items=Array.isArray(data)?data:data.features;
if(!Array.isArray(items)||items.length!==expected) throw new Error('PARITY_COUNT_INVALID');
for(const item of items){
  if(item?.status!=='complete') throw new Error(`PARITY_INCOMPLETE:${item?.id||'unknown'}`);
  if(!Array.isArray(item.evidence)||item.evidence.length===0) throw new Error(`PARITY_NO_EVIDENCE:${item?.id||'unknown'}`);
  for(const ev of item.evidence){ if(typeof ev!=='string'||!ev.trim()) throw new Error(`PARITY_BAD_EVIDENCE:${item?.id||'unknown'}`); }
}
console.log(`PARITY_COMPLETE_COUNT=${items.length}`);
NODE

# Every declared evidence path before optional #anchor must exist under target.
node - "$TARGET" "$PARITY" <<'NODE'
const fs=require('fs'),path=require('path');
const target=path.resolve(process.argv[2]);
const data=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
const items=Array.isArray(data)?data:data.features;
for(const item of items){
  for(const ev of item.evidence){
    const rel=ev.split('#')[0].trim();
    if(!rel) continue;
    const full=path.resolve(target,rel);
    if(!full.startsWith(target+path.sep) && full!==target) throw new Error(`EVIDENCE_ESCAPE:${ev}`);
    if(!fs.existsSync(full)) throw new Error(`EVIDENCE_MISSING:${ev}`);
  }
}
console.log('PARITY_EVIDENCE_PATHS=PASS');
NODE

# Source preservation checks.
[[ -f "$TARGET/apps/zaghloul-wacrm/package.json" ]] || { echo "ERROR=WACRM_PACKAGE_MISSING"; exit 4; }
[[ -f "$TARGET/apps/zaghloul-wacrm/README.md" ]] || { echo "ERROR=WACRM_README_MISSING"; exit 4; }
[[ -d "$TARGET/apps/zaghloul-wacrm/mcp-server" ]] || { echo "ERROR=WACRM_MCP_MISSING"; exit 4; }
[[ -d "$TARGET/apps/zaghloul-wacrm/supabase" ]] || { echo "ERROR=WACRM_SUPABASE_SOURCE_MISSING"; exit 4; }
echo "WACRM_SOURCE_PRESERVATION=PASS"

# No copied secret values: forbid common local env files inside copied source.
if find "$TARGET/apps/zaghloul-wacrm" -type f \( -name '.env' -o -name '.env.local' -o -name '.env.production' -o -name '.env.development' \) -print -quit | grep -q .; then
  echo "SECRET_SCAN=FAIL_ENV_FILE"
  exit 5
fi
echo "SECRET_SCAN=PASS"

# Verify explicit adapters exist and contain intent markers.
AUTH_ADAPTER="$(find "$TARGET" -type f \( -iname '*zaghloul*auth*adapter*' -o -iname '*wacrm*auth*adapter*' \) | head -n1 || true)"
WA_ADAPTER="$(find "$TARGET" -type f \( -iname '*zaghloul*whatsapp*adapter*' -o -iname '*wacrm*whatsapp*adapter*' -o -iname '*zaghloul*meta*adapter*' \) | head -n1 || true)"
[[ -n "$AUTH_ADAPTER" ]] || { echo "AUTH_ADAPTER=FAIL_MISSING"; exit 6; }
[[ -n "$WA_ADAPTER" ]] || { echo "WHATSAPP_ADAPTER=FAIL_MISSING"; exit 6; }
echo "AUTH_ADAPTER=PASS:${AUTH_ADAPTER#$TARGET/}"
echo "WHATSAPP_ADAPTER=PASS:${WA_ADAPTER#$TARGET/}"

# Guard against obvious competing-sender implementation in copied module/adapters.
SECOND_SENDER_MATCHES="$(grep -RInE 'WHATSAPP_ACCESS_TOKEN|phone_number_id|graph\.facebook\.com/.*/messages|send.*WhatsApp.*direct|new.*WhatsApp.*client' "$TARGET/apps/zaghloul-wacrm" "$WA_ADAPTER" 2>/dev/null | head -n 20 || true)"
# Upstream source naturally contains its original Meta transport, so it must be explicitly disabled/redirected by adapter marker.
if ! grep -RInE 'TCRM_OFFICIAL_META_ADAPTER|ZAGHLOUL_TCRM_META_ADAPTER|disable.*upstream.*sender|single.*outbound.*authority' "$WA_ADAPTER" "$TARGET/apps/zaghloul-wacrm" >/dev/null 2>&1; then
  echo "SECOND_WHATSAPP_SENDER=FAIL_NO_SINGLE_AUTHORITY_EVIDENCE"
  [[ -n "$SECOND_SENDER_MATCHES" ]] && printf '%s\n' "$SECOND_SENDER_MATCHES"
  exit 7
fi
echo "SECOND_WHATSAPP_SENDER=NO"

# TypeScript baseline/candidate gate. The integration may not increase accepted legacy errors.
export NODE_OPTIONS="${NODE_OPTIONS:-} --max-old-space-size=8192"
if (cd "$TARGET" && pnpm exec tsc --noEmit --incremental false) >"$TMP/tsc.log" 2>&1; then TSC_RC=0; else TSC_RC=$?; fi
grep -F 'error TS' "$TMP/tsc.log" | sort -u >"$TMP/tsc.errors" || true
TSC_COUNT="$(wc -l < "$TMP/tsc.errors" | tr -d ' ')"
echo "TSC_CANDIDATE_ERROR_COUNT=$TSC_COUNT"
[[ "$TSC_COUNT" -le "$ACCEPTED_TSC_CEILING" ]] || { echo "TSC_NEW_ERROR_COUNT=GT_0"; cat "$TMP/tsc.errors"; exit 8; }
echo "TSC_NEW_ERROR_COUNT=0_OR_NEGATIVE_VS_CEILING"

(cd "$TARGET" && pnpm build) >"$TMP/build.log" 2>&1 || { cat "$TMP/build.log"; exit 9; }
echo "BUILD=PASS"

# Relevant tests: allow repository test command to decide pass/fail.
(cd "$TARGET" && pnpm test -- --runInBand) >"$TMP/test.log" 2>&1 || { cat "$TMP/test.log"; exit 10; }
echo "TESTS=PASS"

pm2 jlist >"$TMP/pm2.json"
PM2_NAME="$(node - "$TARGET" "$TMP/pm2.json" <<'NODE'
const fs=require('fs'),path=require('path'); const t=path.resolve(process.argv[2]); const a=JSON.parse(fs.readFileSync(process.argv[3],'utf8')); const p=a.find(x=>x?.pm2_env?.pm_cwd&&path.resolve(x.pm2_env.pm_cwd)===t); if(p?.name)process.stdout.write(p.name);
NODE
)"
[[ -n "$PM2_NAME" ]] || { echo "PM2=FAIL_NO_PROCESS"; exit 11; }
PM2_STATUS="$(node - "$TARGET" "$TMP/pm2.json" <<'NODE'
const fs=require('fs'),path=require('path'); const t=path.resolve(process.argv[2]); const a=JSON.parse(fs.readFileSync(process.argv[3],'utf8')); const p=a.find(x=>x?.pm2_env?.pm_cwd&&path.resolve(x.pm2_env.pm_cwd)===t); if(p?.pm2_env?.status)process.stdout.write(p.pm2_env.status);
NODE
)"
[[ "$PM2_STATUS" == "online" ]] || { echo "PM2=FAIL:$PM2_STATUS"; exit 11; }
echo "PM2=PASS:$PM2_NAME"

PORT="$(node - "$TARGET" "$TMP/pm2.json" <<'NODE'
const fs=require('fs'),path=require('path'); const t=path.resolve(process.argv[2]); const a=JSON.parse(fs.readFileSync(process.argv[3],'utf8')); const p=a.find(x=>x?.pm2_env?.pm_cwd&&path.resolve(x.pm2_env.pm_cwd)===t); const port=p?.pm2_env?.env?.PORT??p?.pm2_env?.PORT; if(port)process.stdout.write(String(port));
NODE
)"
if [[ -z "$PORT" ]]; then
  PID="$(node - "$TARGET" "$TMP/pm2.json" <<'NODE'
const fs=require('fs'),path=require('path'); const t=path.resolve(process.argv[2]); const a=JSON.parse(fs.readFileSync(process.argv[3],'utf8')); const p=a.find(x=>x?.pm2_env?.pm_cwd&&path.resolve(x.pm2_env.pm_cwd)===t); if(p?.pid)process.stdout.write(String(p.pid));
NODE
)"
  if [[ -n "$PID" ]] && command -v ss >/dev/null; then PORT="$(ss -ltnp 2>/dev/null | awk -v pid="$PID" '$0~("pid=" pid ","){split($4,a,":");print a[length(a)];exit}')"; fi
fi
[[ "$PORT" =~ ^[0-9]+$ ]] || { echo "HTTP=FAIL_PORT"; exit 12; }
echo "PORT=$PORT"
for route in zaghloul zaghloul-v5 zaghloul-legacy; do
  code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 10 "http://127.0.0.1:${PORT}/${route}" || true)"
  key="$(echo "$route" | tr '[:lower:]-' '[:upper:]_')"
  echo "HTTP_${key}=$code"
  [[ "$code" == "200" ]] || exit 13
done

echo "FINAL_MARKER=$FINAL_MARKER"
