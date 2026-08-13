#!/usr/bin/env bash
set -Eeuo pipefail

PATCH_NAME="ZAGHLOUL_V5R2R1_RUNTIME_PARITY_VERIFICATION"
FINAL_MARKER="${PATCH_NAME}_OK"
TARGET="${TCRM_PATH:-/var/www/TCRM-MAIN}"
WORK="/tmp/${PATCH_NAME}"
RESULT="$WORK/RUNTIME_PARITY_RESULTS.json"
EXPECTED_UPSTREAM="6ed9191189e71d2e69d9380422f9415ecc589266"

fail(){ echo "FINAL_MARKER=FAIL:$1"; exit 1; }

[[ -d "$TARGET/.git" ]] || fail TARGET_NOT_GIT_REPO
[[ -d "$WORK" ]] || fail PREFLIGHT_WORKSPACE_MISSING
[[ -f "$WORK/head.before" && -f "$WORK/tree.before" && -f "$WORK/tracked.before" ]] || fail PREFLIGHT_FINGERPRINTS_MISSING
[[ -f "$RESULT" ]] || fail RUNTIME_RESULTS_MISSING

cd "$TARGET"
HEAD_NOW="$(git rev-parse HEAD)"
HEAD_BEFORE="$(cat "$WORK/head.before")"
[[ "$HEAD_NOW" == "$HEAD_BEFORE" ]] || fail TARGET_HEAD_CHANGED

TREE_NOW="$(git status --porcelain=v1 --untracked-files=all | sha256sum | awk '{print $1}')"
TREE_BEFORE="$(cat "$WORK/tree.before")"
TRACKED_NOW="$(git ls-files -z | sort -z | xargs -0 sha256sum 2>/dev/null | sha256sum | awk '{print $1}')"
TRACKED_BEFORE="$(cat "$WORK/tracked.before")"
[[ "$TREE_NOW" == "$TREE_BEFORE" ]] || fail WORKTREE_STATE_CHANGED
[[ "$TRACKED_NOW" == "$TRACKED_BEFORE" ]] || fail TRACKED_SOURCE_CHANGED

echo "SOURCE_MUTATION=NONE"

node - "$RESULT" "$HEAD_NOW" "$EXPECTED_UPSTREAM" <<'NODE'
const fs=require('fs');
const [p,head,pin]=process.argv.slice(2);
const r=JSON.parse(fs.readFileSync(p,'utf8'));
const ids=[
'shared-inbox',
'contacts-tags-custom-fields-import-dedup',
'sales-pipelines-kanban-deals',
'broadcasts-templates-delivery-read-variables',
'automations-builder-triggers-branches-waits-tags-webhooks',
'flows-builder-buttons-branches-media',
'ai-agents-draft-auto-reply-kb-playground-handoff',
'realtime-dashboard-analytics-activity',
'team-accounts-roles-invites-ownership',
'account-management',
'public-rest-api-api-keys-scopes-rate-limits',
'outbound-event-webhooks-hmac',
'mcp-server',
'chat-actions-reactions-reply-copy',
'media-persistence-inbound-outbound'
];
function die(s){ console.error(`RESULT_SCHEMA=FAIL:${s}`); process.exit(2); }
if(r.version!==1) die('VERSION');
if(r.patch!=='ZAGHLOUL_V5R2R1_RUNTIME_PARITY_VERIFICATION') die('PATCH');
if(r.target_head!==head) die('HEAD');
if(r.upstream_pin!==pin) die('UPSTREAM');
if(r.auth_mode!=='TCRM_SESSION') die('AUTH_MODE');
if(r.second_whatsapp_sender!=='NO') die('SECOND_SENDER');
if(r.meta_external_calls!==0) die('META_EXTERNAL_CALLS');
if(r.email_external_calls!==0) die('EMAIL_EXTERNAL_CALLS');
if(r.non_loopback_webhook_calls!==0) die('NON_LOOPBACK_WEBHOOK_CALLS');
if(r.test_rows_remaining!==0) die('TEST_ROWS_REMAINING');
if(r.db_cleanup!=='PASS') die('DB_CLEANUP');
if(r.pm2_reload!=='NONE') die('PM2_RELOAD');
if(!Array.isArray(r.features)||r.features.length!==15) die('FEATURE_COUNT');
const seen=new Set(); let pass=0,fail=0; const failed=[];
for(const f of r.features){
 if(!ids.includes(f?.id)) die(`UNKNOWN_ID:${f?.id}`);
 if(seen.has(f.id)) die(`DUPLICATE_ID:${f.id}`); seen.add(f.id);
 if(!['PASS','FAIL'].includes(f.status)) die(`BAD_STATUS:${f.id}`);
 if(typeof f.runtime_entrypoint!=='string'||f.runtime_entrypoint.trim().length<3) die(`ENTRYPOINT:${f.id}`);
 if(typeof f.observed!=='string'||f.observed.trim().length<3) die(`OBSERVED:${f.id}`);
 if(!Array.isArray(f.subchecks)||f.subchecks.length===0) die(`SUBCHECKS:${f.id}`);
 if(f.status==='PASS') pass++; else { fail++; failed.push(f.id); }
}
for(const id of ids) if(!seen.has(id)) die(`MISSING_ID:${id}`);
console.log('RESULT_SCHEMA=PASS');
console.log(`AUTH_MODE=${r.auth_mode}`);
console.log(`RUNTIME_PARITY_PASS_COUNT=${pass}`);
console.log(`RUNTIME_PARITY_FAIL_COUNT=${fail}`);
console.log(`FAILED_FEATURES=${failed.length?failed.join(','):'NONE'}`);
console.log(`META_EXTERNAL_CALLS=${r.meta_external_calls}`);
console.log(`EMAIL_EXTERNAL_CALLS=${r.email_external_calls}`);
console.log(`NON_LOOPBACK_WEBHOOK_CALLS=${r.non_loopback_webhook_calls}`);
console.log(`SECOND_WHATSAPP_SENDER=${r.second_whatsapp_sender}`);
console.log(`TEST_ROWS_REMAINING=${r.test_rows_remaining}`);
console.log(`DB_CLEANUP=${r.db_cleanup}`);
console.log(`PM2_RELOAD=${r.pm2_reload}`);
if(fail!==0 || pass!==15) process.exit(3);
NODE

# Production process must remain online; verification never reloads it.
pm2 jlist > "$WORK/pm2.verify.json"
PORT="$(node - "$TARGET" "$WORK/pm2.verify.json" <<'NODE'
const fs=require('fs'),path=require('path');const t=path.resolve(process.argv[2]);const a=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));const p=a.find(x=>x?.pm2_env?.pm_cwd&&path.resolve(x.pm2_env.pm_cwd)===t);if(!p||p?.pm2_env?.status!=='online')process.exit(2);const port=p?.pm2_env?.env?.PORT??p?.pm2_env?.PORT;if(port)process.stdout.write(String(port));
NODE
)" || fail PM2_NOT_ONLINE
if [[ -z "$PORT" ]]; then
 PID="$(node - "$TARGET" "$WORK/pm2.verify.json" <<'NODE'
const fs=require('fs'),path=require('path');const t=path.resolve(process.argv[2]);const a=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));const p=a.find(x=>x?.pm2_env?.pm_cwd&&path.resolve(x.pm2_env.pm_cwd)===t);if(p?.pid)process.stdout.write(String(p.pid));
NODE
)"
 if [[ -n "$PID" ]] && command -v ss >/dev/null; then PORT="$(ss -ltnp 2>/dev/null | awk -v pid="$PID" '$0~("pid=" pid ","){split($4,a,":");print a[length(a)];exit}')"; fi
fi
[[ "$PORT" =~ ^[0-9]+$ ]] || fail PORT_NOT_FOUND
HTTP_ZAGHLOUL="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 10 "http://127.0.0.1:${PORT}/zaghloul" || true)"
echo "HTTP_ZAGHLOUL=$HTTP_ZAGHLOUL"
[[ "$HTTP_ZAGHLOUL" == "200" ]] || fail HTTP_ZAGHLOUL_NOT_200

echo "TARGET_HEAD=$HEAD_NOW"
echo "UPSTREAM_PIN=$EXPECTED_UPSTREAM"
echo "FINAL_MARKER=$FINAL_MARKER"
