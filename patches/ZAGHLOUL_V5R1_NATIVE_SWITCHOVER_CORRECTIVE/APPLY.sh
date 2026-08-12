#!/usr/bin/env bash
set -Eeuo pipefail

PATCH_NAME="ZAGHLOUL_V5R1_NATIVE_SWITCHOVER_CORRECTIVE"
FINAL_MARKER="${PATCH_NAME}_OK"
TARGET="${TCRM_PATH:-/var/www/TCRM-MAIN}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_REL="client/src/App.tsx"
V5_REL="client/src/pages/ZaghloulV5Page.tsx"
EXPECTED_APP_BLOB="d9d9b2bf8c48c565888798055e5f2b244a9e30c0"
EXPECTED_V5_BLOB="d3a11a1f199ae0a3d9558ba5784d6661a92a3540"
TMP="$(mktemp -d)"
MUTATED=0
PM2_RELOADED=0
PM2_NAME=""

cleanup() { rm -rf "$TMP"; }
rollback() {
  local rc=$?
  trap - ERR
  if [[ "$MUTATED" == "1" ]]; then
    echo "ROLLBACK=START"
    cp -f "$TMP/App.tsx" "$TARGET/$APP_REL" || true
    cp -f "$TMP/ZaghloulV5Page.tsx" "$TARGET/$V5_REL" || true
    (cd "$TARGET" && pnpm build >/dev/null 2>&1) || true
    if [[ "$PM2_RELOADED" == "1" && -n "$PM2_NAME" ]]; then
      pm2 reload "$PM2_NAME" >/dev/null 2>&1 || true
    fi
    echo "ROLLBACK=DONE"
  fi
  cleanup
  echo "FINAL_MARKER=${PATCH_NAME}_FAILED"
  exit "$rc"
}
trap rollback ERR
trap cleanup EXIT

[[ -d "$TARGET" ]] || { echo "ERROR=TARGET_NOT_FOUND:$TARGET"; exit 2; }
[[ -f "$TARGET/$APP_REL" ]] || { echo "ERROR=MISSING:$APP_REL"; exit 2; }
[[ -f "$TARGET/$V5_REL" ]] || { echo "ERROR=MISSING:$V5_REL"; exit 2; }
[[ -f "$PATCH_DIR/App.routes.patch" ]] || { echo "ERROR=MISSING_PATCH"; exit 2; }
[[ -f "$PATCH_DIR/files/$V5_REL" ]] || { echo "ERROR=MISSING_V5_PAYLOAD"; exit 2; }
command -v git >/dev/null
command -v pnpm >/dev/null
command -v pm2 >/dev/null
command -v curl >/dev/null

CURRENT_APP_BLOB="$(cd "$TARGET" && git hash-object "$APP_REL")"
CURRENT_V5_BLOB="$(cd "$TARGET" && git hash-object "$V5_REL")"
[[ "$CURRENT_APP_BLOB" == "$EXPECTED_APP_BLOB" ]] || { echo "BASELINE_GUARD=FAIL_APP:$CURRENT_APP_BLOB"; exit 3; }
[[ "$CURRENT_V5_BLOB" == "$EXPECTED_V5_BLOB" ]] || { echo "BASELINE_GUARD=FAIL_V5:$CURRENT_V5_BLOB"; exit 3; }
echo "BASELINE_GUARD=PASS"

cp -f "$TARGET/$APP_REL" "$TMP/App.tsx"
cp -f "$TARGET/$V5_REL" "$TMP/ZaghloulV5Page.tsx"

set +e
(cd "$TARGET" && pnpm check) >"$TMP/tsc-baseline.log" 2>&1
TSC_BASELINE_RC=$?
set -e
grep -F "error TS" "$TMP/tsc-baseline.log" | sed 's#^[^:]*/##' | sort -u >"$TMP/tsc-baseline.errors" || true
TSC_BASELINE_ERROR_COUNT="$(wc -l < "$TMP/tsc-baseline.errors" | tr -d ' ')"
echo "TSC_BASELINE_ERROR_COUNT=$TSC_BASELINE_ERROR_COUNT"

(cd "$TARGET" && git apply --check "$PATCH_DIR/App.routes.patch")
(cd "$TARGET" && git apply "$PATCH_DIR/App.routes.patch")
cp -f "$PATCH_DIR/files/$V5_REL" "$TARGET/$V5_REL"
MUTATED=1

grep -q 'import ZaghloulV5Page from "./pages/ZaghloulV5Page";' "$TARGET/$APP_REL"
grep -q '<Route path="/zaghloul" component={ZaghloulV5Page} />' "$TARGET/$APP_REL"
grep -q '<Route path="/zaghloul-v5" component={ZaghloulV5Page} />' "$TARGET/$APP_REL"
grep -q '<Route path="/zaghloul-legacy" component={ZaghloulAgentPage} />' "$TARGET/$APP_REL"
grep -q 'trpc.zaghloulV5.inbox.list.useQuery' "$TARGET/$V5_REL"
grep -q 'trpc.zaghloulV5.contacts.list.useQuery' "$TARGET/$V5_REL"
grep -q 'trpc.zaghloulV5.pipelines.list.useQuery' "$TARGET/$V5_REL"
grep -q 'trpc.zaghloulV5.automations.list.useQuery' "$TARGET/$V5_REL"
echo "STATIC_VERIFY=PASS"

set +e
(cd "$TARGET" && pnpm check) >"$TMP/tsc-candidate.log" 2>&1
TSC_CANDIDATE_RC=$?
set -e
grep -F "error TS" "$TMP/tsc-candidate.log" | sed 's#^[^:]*/##' | sort -u >"$TMP/tsc-candidate.errors" || true
TSC_CANDIDATE_ERROR_COUNT="$(wc -l < "$TMP/tsc-candidate.errors" | tr -d ' ')"
comm -13 "$TMP/tsc-baseline.errors" "$TMP/tsc-candidate.errors" >"$TMP/tsc-new.errors" || true
TSC_NEW_ERROR_COUNT="$(wc -l < "$TMP/tsc-new.errors" | tr -d ' ')"
echo "TSC_CANDIDATE_ERROR_COUNT=$TSC_CANDIDATE_ERROR_COUNT"
echo "TSC_NEW_ERROR_COUNT=$TSC_NEW_ERROR_COUNT"
if [[ "$TSC_NEW_ERROR_COUNT" != "0" ]]; then
  cat "$TMP/tsc-new.errors"
  false
fi

(cd "$TARGET" && pnpm build)
echo "BUILD=PASS"

pm2 jlist >"$TMP/pm2.json"
PM2_NAME="$(node - "$TARGET" "$TMP/pm2.json" <<'NODE'
const fs=require('fs'),path=require('path');
const target=path.resolve(process.argv[2]);
const list=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
const p=list.find(x => x?.pm2_env?.pm_cwd && path.resolve(x.pm2_env.pm_cwd)===target);
if (p?.name) process.stdout.write(p.name);
NODE
)"
[[ -n "$PM2_NAME" ]] || { echo "PM2=FAIL_NO_PROCESS_FOR_TARGET"; false; }
pm2 reload "$PM2_NAME"
PM2_RELOADED=1
echo "PM2=PASS:$PM2_NAME"

pm2 jlist >"$TMP/pm2-after.json"
PORT="$(node - "$TARGET" "$TMP/pm2-after.json" <<'NODE'
const fs=require('fs'),path=require('path');
const target=path.resolve(process.argv[2]);
const list=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
const p=list.find(x => x?.pm2_env?.pm_cwd && path.resolve(x.pm2_env.pm_cwd)===target);
const port=p?.pm2_env?.env?.PORT ?? p?.pm2_env?.PORT;
if (port) process.stdout.write(String(port));
NODE
)"

if [[ -z "$PORT" ]]; then
  PID="$(node - "$TARGET" "$TMP/pm2-after.json" <<'NODE'
const fs=require('fs'),path=require('path');
const target=path.resolve(process.argv[2]);
const list=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
const p=list.find(x => x?.pm2_env?.pm_cwd && path.resolve(x.pm2_env.pm_cwd)===target);
if (p?.pid) process.stdout.write(String(p.pid));
NODE
)"
  if [[ -n "$PID" ]] && command -v ss >/dev/null; then
    PORT="$(ss -ltnp 2>/dev/null | awk -v pid="$PID" '$0 ~ ("pid=" pid ",") {split($4,a,":"); print a[length(a)]; exit}')"
  fi
fi
[[ "$PORT" =~ ^[0-9]+$ ]] || { echo "HTTP=FAIL_PORT_NOT_DISCOVERED"; false; }

HTTP_OK=0
for _ in $(seq 1 30); do
  if curl -fsS --max-time 5 "http://127.0.0.1:${PORT}/zaghloul" >/dev/null && \
     curl -fsS --max-time 5 "http://127.0.0.1:${PORT}/zaghloul-v5" >/dev/null && \
     curl -fsS --max-time 5 "http://127.0.0.1:${PORT}/zaghloul-legacy" >/dev/null; then
    HTTP_OK=1
    break
  fi
  sleep 2
done
[[ "$HTTP_OK" == "1" ]] || { echo "HTTP=FAIL:$PORT"; false; }
echo "HTTP_ZAGHLOUL=200"
echo "HTTP_ZAGHLOUL_V5=200"
echo "HTTP_ZAGHLOUL_LEGACY=200"

echo "PATCH=$PATCH_NAME"
echo "TSC_BASELINE_RC=$TSC_BASELINE_RC"
echo "TSC_CANDIDATE_RC=$TSC_CANDIDATE_RC"
echo "FINAL_MARKER=$FINAL_MARKER"
MUTATED=0
cleanup
trap - ERR EXIT
