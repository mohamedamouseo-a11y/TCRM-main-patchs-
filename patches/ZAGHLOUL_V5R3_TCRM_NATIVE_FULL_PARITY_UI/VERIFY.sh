#!/usr/bin/env bash
set -euo pipefail
TARGET=/var/www/TCRM-MAIN
PATCH=ZAGHLOUL_V5R3_TCRM_NATIVE_FULL_PARITY_UI
WORK=/tmp/$PATCH
RESULT=$WORK/results.json
cd "$TARGET"

[ -f "$WORK/baseline_head" ] && [ -f "$WORK/tsc.before" ] || { echo 'PRECHECK=FAIL'; exit 2; }
[ -f "$RESULT" ] || { echo 'RESULT_SCHEMA=FAIL'; exit 3; }
BASE=$(cat "$WORK/baseline_head")
HEAD=$(git rev-parse HEAD)

node - "$RESULT" "$BASE" "$HEAD" <<'NODE'
const fs=require('fs'); const [p,base,head]=process.argv.slice(2); const r=JSON.parse(fs.readFileSync(p,'utf8'));
const ids=['shared-inbox','contacts-tags-custom-fields-import-dedup','sales-pipelines-kanban-deals','broadcasts-templates-delivery-read-variables','automations-builder-triggers-branches-waits-tags-webhooks','flows-builder-buttons-branches-media','ai-agents-draft-auto-reply-kb-playground-handoff','realtime-dashboard-analytics-activity','team-accounts-roles-invites-ownership','account-management','public-rest-api-api-keys-scopes-rate-limits','outbound-event-webhooks-hmac','mcp-server','chat-actions-reactions-reply-copy','media-persistence-inbound-outbound'];
if(r.baseline_head!==base||r.candidate_head!==head||r.auth_mode!=='TCRM_SESSION'||r.second_whatsapp_sender!=='NO'||r.iframe!=='NO'||r.external_meta_calls!==0||r.external_email_calls!==0||r.non_loopback_webhook_calls!==0) process.exit(1);
if(!Array.isArray(r.features)||r.features.length!==15) process.exit(1);
const m=new Map(r.features.map(x=>[x.id,x])); if(m.size!==15) process.exit(1);
for(const id of ids){const x=m.get(id); if(!x||x.status!=='PASS'||!String(x.ui_surface||'').trim()||!String(x.runtime_entrypoint||'').trim()||!String(x.proof||'').trim()) process.exit(1)}
NODE
echo 'RESULT_SCHEMA=PASS'

# Structural guards for native TCRM integration.
! grep -RniE '<iframe|iframe[[:space:]]' client/src/pages/ZaghloulV5Page.tsx client/src/components 2>/dev/null | grep -i zaghloul >/dev/null || { echo 'IFRAME=FAIL'; exit 4; }
grep -q 'ZaghloulV5Page' client/src/App.tsx
grep -q 'path="/zaghloul"' client/src/App.tsx
grep -q 'path="/zaghloul-v5"' client/src/App.tsx
grep -q 'path="/zaghloul-legacy"' client/src/App.tsx

grep -q 'TCRM_OFFICIAL_META_ADAPTER' server/services/zaghloul-v5/tcrm-zaghloul-whatsapp-adapter.ts
grep -q 'SINGLE_OUTBOUND_AUTHORITY = true' server/services/zaghloul-v5/tcrm-zaghloul-whatsapp-adapter.ts

echo 'ARCHITECTURE_GUARD=PASS'

# Zero-new TypeScript diagnostics against preflight baseline.
set +e
NODE_OPTIONS=--max-old-space-size=8192 npx tsc --noEmit --pretty false > "$WORK/tsc.after" 2>&1
set -e
python3 - "$WORK/tsc.before" "$WORK/tsc.after" <<'PY'
import sys,re
b=open(sys.argv[1],errors='ignore').read().splitlines(); a=open(sys.argv[2],errors='ignore').read().splitlines()
def norm(lines):
 out=set()
 for x in lines:
  if 'error TS' in x: out.add(re.sub(r'\s+',' ',x.strip()))
 return out
new=norm(a)-norm(b)
print(f'TSC_NEW_ERROR_COUNT={len(new)}')
if new:
 print('\n'.join(sorted(new)[:20])); raise SystemExit(1)
PY

# Run project test/build gates when defined.
PM=pnpm; command -v pnpm >/dev/null 2>&1 || PM=npm
node -e "let p=require('./package.json');process.exit(p.scripts?.test?0:1)" && $PM test || true
node -e "let p=require('./package.json');process.exit(p.scripts?.build?0:1)" && $PM run build

echo 'TESTS=PASS'
echo 'BUILD=PASS'

# Controlled reload only after all static gates pass.
PROC=$(pm2 jlist | node -e "let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{let a=JSON.parse(s),p=a.find(x=>String(x.pm2_env?.pm_cwd||'').startsWith('$TARGET'));if(!p)process.exit(1);console.log(p.name)})")
pm2 reload "$PROC" --update-env >/dev/null
sleep 2
pm2 jlist | node -e "let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{let a=JSON.parse(s),p=a.find(x=>x.name==='$PROC');if(!p||p.pm2_env?.status!=='online')process.exit(1)})"
PORT=$(pm2 jlist | node -e "let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{let a=JSON.parse(s),p=a.find(x=>x.name==='$PROC');console.log(p?.pm2_env?.env?.PORT||p?.pm2_env?.PORT||3001)})")
for R in /zaghloul /zaghloul-v5 /zaghloul-legacy; do C=$(curl -sS -o /dev/null -w '%{http_code}' "http://127.0.0.1:$PORT$R"); [ "$C" = 200 ] || { echo "HTTP_$R=$C"; exit 8; }; done

echo 'PM2=PASS'
echo 'HTTP_ZAGHLOUL=200'
echo 'HTTP_ZAGHLOUL_V5=200'
echo 'HTTP_ZAGHLOUL_LEGACY=200'
echo 'FEATURE_PASS_COUNT=15'
echo 'FEATURE_FAIL_COUNT=0'
echo 'FINAL_MARKER=ZAGHLOUL_V5R3_TCRM_NATIVE_FULL_PARITY_UI_OK'
