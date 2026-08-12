#!/usr/bin/env bash
set -Eeuo pipefail

PATCH_NAME="ZAGHLOUL_V5R1R1_POST_APPLY_RECONCILIATION"
FINAL_MARKER="${PATCH_NAME}_OK"
TARGET="${TCRM_PATH:-/var/www/TCRM-MAIN}"
APP_REL="client/src/App.tsx"
V5_REL="client/src/pages/ZaghloulV5Page.tsx"
EXPECTED_APP_BLOB="242bd67ff1766f00decf66d7a91fcb2c83552856"
EXPECTED_V5_BLOB="a7b7d15671c9f8a6fed17608d8b07adad62920b8"
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

APP_BLOB="$(cd "$TARGET" && git hash-object "$APP_REL")"
V5_BLOB="$(cd "$TARGET" && git hash-object "$V5_REL")"
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

if (cd "$TARGET" && pnpm exec tsc --noEmit --incremental false) >"$TMP/tsc.log" 2>&1; then
  TSC_RC=0
else
  TSC_RC=$?
fi
TSC_ERROR_COUNT="$(grep -c 'error TS' "$TMP/tsc.log" || true)"
echo "TSC_CLEAN_ERROR_COUNT=$TSC_ERROR_COUNT"
[[ "$TSC_RC" == "0" && "$TSC_ERROR_COUNT" == "0" ]] || { cat "$TMP/tsc.log"; exit 4; }

(cd "$TARGET" && pnpm build) >"$TMP/build.log" 2>&1 || { cat "$TMP/build.log"; exit 5; }
echo "BUILD=PASS"

pm2 jlist >"$TMP/pm2.json"
PM2_NAME="$(node - "$TARGET" "$TMP/pm2.json" <<'NODE'
const fs=require('fs'),path=require('path');
const target=path.resolve(process.argv[2]);
const list=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
const p=list.find(x=>x?.pm2_env?.pm_cwd && path.resolve(x.pm2_env.pm_cwd)===target);
if(p?.name) process.stdout.write(p.name);
NODE
)"
[[ -n "$PM2_NAME" ]] || { echo "PM2=FAIL_NO_PROCESS"; exit 6; }
PM2_STATUS="$(node - "$TARGET" "$TMP/pm2.json" <<'NODE'
const fs=require('fs'),path=require('path');
const target=path.resolve(process.argv[2]);
const list=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
const p=list.find(x=>x?.pm2_env?.pm_cwd && path.resolve(x.pm2_env.pm_cwd)===target);
if(p?.pm2_env?.status) process.stdout.write(String(p.pm2_env.status));
NODE
)"
[[ "$PM2_STATUS" == "online" ]] || { echo "PM2=FAIL:$PM2_NAME:$PM2_STATUS"; exit 6; }
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
[[ "$PORT" =~ ^[0-9]+$ ]] || { echo "HTTP=FAIL_PORT_NOT_FOUND"; exit 7; }

echo "PORT=$PORT"
for route in zaghloul zaghloul-v5 zaghloul-legacy; do
  code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 10 "http://127.0.0.1:${PORT}/${route}" || true)"
  key="$(echo "$route" | tr '[:lower:]-' '[:upper:]_')"
  echo "HTTP_${key}=$code"
  [[ "$code" == "200" ]] || exit 8
done

echo "SOURCE_MUTATION=NONE"
echo "FINAL_MARKER=$FINAL_MARKER"
