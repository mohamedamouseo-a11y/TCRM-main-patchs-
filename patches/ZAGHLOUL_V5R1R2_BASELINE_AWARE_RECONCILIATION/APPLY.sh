#!/usr/bin/env bash
set -Eeuo pipefail

PATCH_NAME="ZAGHLOUL_V5R1R2_BASELINE_AWARE_RECONCILIATION"
FINAL_MARKER="${PATCH_NAME}_OK"
TARGET="${TCRM_PATH:-/var/www/TCRM-MAIN}"
APP_REL="client/src/App.tsx"
V5_REL="client/src/pages/ZaghloulV5Page.tsx"
EXPECTED_APP_BLOB="242bd67ff1766f00decf66d7a91fcb2c83552856"
EXPECTED_V5_BLOB="a7b7d15671c9f8a6fed17608d8b07adad62920b8"
ACCEPTED_TSC_CEILING=191
NODE_HEAP_MB="${TSC_NODE_HEAP_MB:-6144}"
TMP="$(mktemp -d)"

cleanup(){ rm -rf "$TMP"; }
trap cleanup EXIT

[[ -d "$TARGET" ]] || { echo "RECONCILIATION_GUARD=FAIL_TARGET"; exit 2; }
[[ -f "$TARGET/$APP_REL" ]] || { echo "RECONCILIATION_GUARD=FAIL_MISSING_APP"; exit 2; }
[[ -f "$TARGET/$V5_REL" ]] || { echo "RECONCILIATION_GUARD=FAIL_MISSING_V5"; exit 2; }
command -v git >/dev/null
command -v pnpm >/dev/null
command -v pm2 >/dev/null
command -v curl >/dev/null
command -v node >/dev/null

hash_file(){ (cd "$TARGET" && git hash-object "$1"); }
normalize_tsc(){
  grep -F 'error TS' "$1" | sed -E 's/\x1B\[[0-9;]*[mK]//g' | sed "s#${TARGET}/##g" | sort -u || true
}
count_scope_errors(){
  local file="$1" pattern="$2"
  grep -F "$pattern" "$file" | grep -F 'error TS' | wc -l | tr -d ' ' || true
}
run_tsc(){
  local out="$1"
  local rc=0
  if (cd "$TARGET" && NODE_OPTIONS="--max-old-space-size=${NODE_HEAP_MB}" pnpm exec tsc --noEmit --incremental false) >"$out" 2>&1; then
    rc=0
  else
    rc=$?
  fi
  echo "$rc"
}

APP_BLOB="$(hash_file "$APP_REL")"
V5_BLOB="$(hash_file "$V5_REL")"
echo "APP_BLOB=$APP_BLOB"
echo "V5_BLOB=$V5_BLOB"
[[ "$APP_BLOB" == "$EXPECTED_APP_BLOB" ]] || { echo "RECONCILIATION_GUARD=FAIL_APP_BLOB"; exit 3; }
[[ "$V5_BLOB" == "$EXPECTED_V5_BLOB" ]] || { echo "RECONCILIATION_GUARD=FAIL_V5_BLOB"; exit 3; }
echo "RECONCILIATION_GUARD=PASS"

APP="$TARGET/$APP_REL"
V5="$TARGET/$V5_REL"
grep -Fq 'import ZaghloulV5Page from "./pages/ZaghloulV5Page";' "$APP"
grep -Fq '<Route path="/zaghloul" component={ZaghloulV5Page} />' "$APP"
grep -Fq '<Route path="/zaghloul-v5" component={ZaghloulV5Page} />' "$APP"
grep -Fq '<Route path="/zaghloul-legacy" component={ZaghloulAgentPage} />' "$APP"
[[ "$(head -n 1 "$V5")" == '// @ts-nocheck' ]]
grep -Fq 'trpc.zaghloulV5.inbox.list.useQuery' "$V5"
grep -Fq 'trpc.zaghloulV5.contacts.list.useQuery' "$V5"
grep -Fq 'trpc.zaghloulV5.pipelines.list.useQuery' "$V5"
grep -Fq 'trpc.zaghloulV5.deals.list.useQuery' "$V5"
grep -Fq 'trpc.zaghloulV5.automations.list.useQuery' "$V5"
echo "STATIC_VERIFY=PASS"

TSC_BASELINE_RC="$(run_tsc "$TMP/tsc-baseline.log")"
normalize_tsc "$TMP/tsc-baseline.log" >"$TMP/tsc-baseline.errors"
TSC_BASELINE_ERROR_COUNT="$(wc -l < "$TMP/tsc-baseline.errors" | tr -d ' ')"
APP_SCOPE_BASELINE_ERROR_COUNT="$(grep -F "$APP_REL" "$TMP/tsc-baseline.errors" | wc -l | tr -d ' ' || true)"
V5_SCOPE_BASELINE_ERROR_COUNT="$(grep -F "$V5_REL" "$TMP/tsc-baseline.errors" | wc -l | tr -d ' ' || true)"
echo "TSC_BASELINE_RC=$TSC_BASELINE_RC"
echo "TSC_BASELINE_ERROR_COUNT=$TSC_BASELINE_ERROR_COUNT"
echo "APP_SCOPE_BASELINE_ERROR_COUNT=$APP_SCOPE_BASELINE_ERROR_COUNT"
echo "V5_SCOPE_BASELINE_ERROR_COUNT=$V5_SCOPE_BASELINE_ERROR_COUNT"
[[ "$TSC_BASELINE_ERROR_COUNT" -le "$ACCEPTED_TSC_CEILING" ]] || { echo "TSC_BASELINE_GUARD=FAIL_ABOVE_${ACCEPTED_TSC_CEILING}"; exit 4; }
[[ "$APP_SCOPE_BASELINE_ERROR_COUNT" == "0" ]] || { echo "PATCH_SCOPE_GUARD=FAIL_APP"; exit 4; }
[[ "$V5_SCOPE_BASELINE_ERROR_COUNT" == "0" ]] || { echo "PATCH_SCOPE_GUARD=FAIL_V5"; exit 4; }
echo "TSC_BASELINE_GUARD=PASS"
echo "PATCH_SCOPE_GUARD=PASS"

(cd "$TARGET" && pnpm build) >"$TMP/build.log" 2>&1 || { cat "$TMP/build.log"; exit 5; }
echo "BUILD=PASS"

APP_BLOB_AFTER_BUILD="$(hash_file "$APP_REL")"
V5_BLOB_AFTER_BUILD="$(hash_file "$V5_REL")"
[[ "$APP_BLOB_AFTER_BUILD" == "$EXPECTED_APP_BLOB" ]] || { echo "POST_BUILD_SOURCE_GUARD=FAIL_APP"; exit 5; }
[[ "$V5_BLOB_AFTER_BUILD" == "$EXPECTED_V5_BLOB" ]] || { echo "POST_BUILD_SOURCE_GUARD=FAIL_V5"; exit 5; }
echo "POST_BUILD_SOURCE_GUARD=PASS"

TSC_CANDIDATE_RC="$(run_tsc "$TMP/tsc-candidate.log")"
normalize_tsc "$TMP/tsc-candidate.log" >"$TMP/tsc-candidate.errors"
TSC_CANDIDATE_ERROR_COUNT="$(wc -l < "$TMP/tsc-candidate.errors" | tr -d ' ')"
APP_SCOPE_CANDIDATE_ERROR_COUNT="$(grep -F "$APP_REL" "$TMP/tsc-candidate.errors" | wc -l | tr -d ' ' || true)"
V5_SCOPE_CANDIDATE_ERROR_COUNT="$(grep -F "$V5_REL" "$TMP/tsc-candidate.errors" | wc -l | tr -d ' ' || true)"
comm -13 "$TMP/tsc-baseline.errors" "$TMP/tsc-candidate.errors" >"$TMP/tsc-new.errors" || true
TSC_NEW_ERROR_COUNT="$(wc -l < "$TMP/tsc-new.errors" | tr -d ' ')"
echo "TSC_CANDIDATE_RC=$TSC_CANDIDATE_RC"
echo "TSC_CANDIDATE_ERROR_COUNT=$TSC_CANDIDATE_ERROR_COUNT"
echo "APP_SCOPE_CANDIDATE_ERROR_COUNT=$APP_SCOPE_CANDIDATE_ERROR_COUNT"
echo "V5_SCOPE_CANDIDATE_ERROR_COUNT=$V5_SCOPE_CANDIDATE_ERROR_COUNT"
echo "TSC_NEW_ERROR_COUNT=$TSC_NEW_ERROR_COUNT"
[[ "$APP_SCOPE_CANDIDATE_ERROR_COUNT" == "0" ]] || { echo "PATCH_SCOPE_CANDIDATE_GUARD=FAIL_APP"; exit 6; }
[[ "$V5_SCOPE_CANDIDATE_ERROR_COUNT" == "0" ]] || { echo "PATCH_SCOPE_CANDIDATE_GUARD=FAIL_V5"; exit 6; }
[[ "$TSC_NEW_ERROR_COUNT" == "0" ]] || { cat "$TMP/tsc-new.errors"; echo "TSC_DELTA_GUARD=FAIL"; exit 6; }
[[ "$TSC_CANDIDATE_ERROR_COUNT" -le "$ACCEPTED_TSC_CEILING" ]] || { echo "TSC_CANDIDATE_GUARD=FAIL_ABOVE_${ACCEPTED_TSC_CEILING}"; exit 6; }
echo "TSC_DELTA_GUARD=PASS"

pm2 jlist >"$TMP/pm2.json"
PM2_NAME="$(node - "$TARGET" "$TMP/pm2.json" <<'NODE'
const fs=require('fs'),path=require('path');
const target=path.resolve(process.argv[2]);
const list=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
const p=list.find(x=>x?.pm2_env?.pm_cwd && path.resolve(x.pm2_env.pm_cwd)===target);
if(p?.name) process.stdout.write(p.name);
NODE
)"
PM2_STATUS="$(node - "$TARGET" "$TMP/pm2.json" <<'NODE'
const fs=require('fs'),path=require('path');
const target=path.resolve(process.argv[2]);
const list=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
const p=list.find(x=>x?.pm2_env?.pm_cwd && path.resolve(x.pm2_env.pm_cwd)===target);
if(p?.pm2_env?.status) process.stdout.write(String(p.pm2_env.status));
NODE
)"
[[ -n "$PM2_NAME" && "$PM2_STATUS" == "online" ]] || { echo "PM2=FAIL:${PM2_NAME:-none}:${PM2_STATUS:-unknown}"; exit 7; }
echo "PM2=PASS:$PM2_NAME"

PORT="$(node - "$TARGET" "$TMP/pm2.json" <<'NODE'
const fs=require('fs'),path=require('path');
const target=path.resolve(process.argv[2]);
const list=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
const p=list.find(x=>x?.pm2_env?.pm_cwd && path.resolve(x.pm2_env.pm_cwd)===target);
const port=p?.pm2_env?.env?.PORT ?? p?.pm2_env?.PORT;
if(port) process.stdout.write(String(port));
NODE
)"
if [[ -z "$PORT" ]]; then
  PID="$(node - "$TARGET" "$TMP/pm2.json" <<'NODE'
const fs=require('fs'),path=require('path');
const target=path.resolve(process.argv[2]);
const list=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
const p=list.find(x=>x?.pm2_env?.pm_cwd && path.resolve(x.pm2_env.pm_cwd)===target);
if(p?.pid) process.stdout.write(String(p.pid));
NODE
)"
  if [[ -n "$PID" ]] && command -v ss >/dev/null; then
    PORT="$(ss -ltnp 2>/dev/null | awk -v pid="$PID" '$0 ~ ("pid=" pid ",") {split($4,a,":"); print a[length(a)]; exit}')"
  fi
fi
[[ "$PORT" =~ ^[0-9]+$ ]] || { echo "HTTP=FAIL_PORT_NOT_FOUND"; exit 8; }
echo "PORT=$PORT"

for route in zaghloul zaghloul-v5 zaghloul-legacy; do
  code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 10 "http://127.0.0.1:${PORT}/${route}" || true)"
  key="$(echo "$route" | tr '[:lower:]-' '[:upper:]_')"
  echo "HTTP_${key}=$code"
  [[ "$code" == "200" ]] || exit 8
done

echo "SOURCE_MUTATION=NONE"
echo "PM2_RELOAD=NONE"
echo "FINAL_MARKER=$FINAL_MARKER"
