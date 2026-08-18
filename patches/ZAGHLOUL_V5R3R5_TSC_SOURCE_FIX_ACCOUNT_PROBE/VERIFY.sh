#!/usr/bin/env bash
set -euo pipefail
TARGET=${TCRM_PATH:-/var/www/TCRM-MAIN}
PATCH=ZAGHLOUL_V5R3R5_TSC_SOURCE_FIX_ACCOUNT_PROBE
WORK=/tmp/$PATCH
BASE=$(cat "$WORK/baseline_head")
BASE_WT="$WORK/baseline-worktree"
TSC="$TARGET/node_modules/.bin/tsc"
TSX="$TARGET/node_modules/.bin/tsx"
cd "$TARGET"
[ -x "$TSC" ] || { echo LOCAL_TSC=FAIL; exit 2; }
[ -x "$TSX" ] || { echo LOCAL_TSX=FAIL; exit 3; }
git worktree prune >/dev/null 2>&1 || true
rm -rf "$BASE_WT"
git worktree add --detach "$BASE_WT" "$BASE" >/dev/null
ln -s "$TARGET/node_modules" "$BASE_WT/node_modules"
for f in package.json pnpm-lock.yaml package-lock.json yarn.lock; do
  if [ -f "$TARGET/$f" ] || [ -f "$BASE_WT/$f" ]; then
    cmp -s "$TARGET/$f" "$BASE_WT/$f" || { echo "DEPENDENCY_MANIFEST_MISMATCH=$f"; exit 4; }
  fi
done
echo PRECHECK=PASS
echo DEPENDENCY_MANIFEST_MISMATCH=NONE

run_tsc(){ local d=$1 o=$2 r=$3; set +e; (cd "$d" && NODE_OPTIONS=--max-old-space-size=16384 "$TSC" --noEmit --pretty false >"$o" 2>&1); rc=$?; set -e; echo "$rc" > "$r"; }
run_tsc "$BASE_WT" "$WORK/tsc.baseline" "$WORK/tsc.baseline.rc"
run_tsc "$TARGET" "$WORK/tsc.candidate" "$WORK/tsc.candidate.rc"
BRC=$(cat "$WORK/tsc.baseline.rc"); CRC=$(cat "$WORK/tsc.candidate.rc")
case "$BRC" in 0|1|2) ;; *) echo TSC_BASELINE_EXIT=$BRC; exit 5;; esac
case "$CRC" in 0|1|2) ;; *) echo TSC_CANDIDATE_EXIT=$CRC; exit 6;; esac
python3 - "$WORK/tsc.baseline" "$WORK/tsc.candidate" <<'PY'
import re,sys
from collections import Counter
pat=re.compile(r'^(.*)\((\d+),(\d+)\):\s+error\s+(TS\d+):\s+(.*)$')
def parse(p):
 raw=[]; c=Counter()
 for line in open(p,errors='ignore'):
  m=pat.match(line.rstrip())
  if not m: continue
  raw.append(m.group(0)); path,_,_,code,msg=m.groups(); msg=re.sub(r'\s+',' ',msg.strip())
  c[f'{path} :: {code} :: {msg}'] += 1
 return raw,c
br,b=parse(sys.argv[1]); cr,c=parse(sys.argv[2]); new=c-b; n=sum(new.values())
print(f'TSC_BASELINE_ERRORS={len(br)}'); print(f'TSC_CANDIDATE_ERRORS={len(cr)}'); print(f'TSC_NEW_ERROR_COUNT={n}')
for k,v in sorted(new.items()):
 for _ in range(v): print('NEW_TS_ERROR='+k)
if n: raise SystemExit(1)
PY
echo TSC_BASELINE_EXIT=$BRC
echo TSC_CANDIDATE_EXIT=$CRC

BAD='client/src/pages/zaghloul-v5/automations/[id]/logs/page.tsx'
[ ! -f "$BAD" ] || { echo MISPLACED_NEXT_PAGE=FAIL; exit 7; }
echo MISPLACED_NEXT_PAGE=ABSENT

set +e
ACCOUNT_JSON=$(timeout 20s "$TSX" -e '(async()=>{ const m=await import("./server/services/zaghloul-v5/v5Service.ts"); const r=await m.getZaghloulV5Settings(); process.stdout.write(JSON.stringify(r)); process.exit(0); })().catch(e=>{console.error(e);process.exit(1)})' 2>"$WORK/account.err")
ARC=$?
set -e
if [ "$ARC" -ne 0 ]; then echo ACCOUNT_MANAGEMENT=FAIL; echo AUTH_MODE=UNDEFINED; echo ACCOUNT_PROBE_EXIT=$ARC; cat "$WORK/account.err"; exit 8; fi
AUTH=$(node -e 'const x=JSON.parse(process.argv[1]);process.stdout.write(String(x.authMode||""))' "$ACCOUNT_JSON")
[ "$AUTH" = TCRM_SESSION ] || { echo ACCOUNT_MANAGEMENT=FAIL; echo AUTH_MODE=${AUTH:-UNDEFINED}; exit 9; }
echo ACCOUNT_MANAGEMENT=PASS
echo AUTH_MODE=TCRM_SESSION

PM=pnpm; command -v pnpm >/dev/null 2>&1 || PM=npm
$PM run build >/dev/null
echo BUILD=PASS
PROC=$(pm2 jlist | node -e "let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{let a=JSON.parse(s),p=a.find(x=>String(x.pm2_env?.pm_cwd||'').startsWith('$TARGET'));if(!p)process.exit(1);console.log(p.name)})")
pm2 reload "$PROC" --update-env >/dev/null
sleep 2
PORT=$(pm2 jlist | node -e "let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{let a=JSON.parse(s),p=a.find(x=>x.name==='$PROC');if(!p||p.pm2_env?.status!=='online')process.exit(1);console.log(p?.pm2_env?.env?.PORT||p?.pm2_env?.PORT||3001)})")
for R in /zaghloul /zaghloul-v5 /zaghloul-legacy; do C=$(curl -sS -o /dev/null -w '%{http_code}' "http://127.0.0.1:$PORT$R"); [ "$C" = 200 ] || exit 10; done
echo PM2=PASS
echo HTTP_ZAGHLOUL=200
echo HTTP_ZAGHLOUL_V5=200
echo HTTP_ZAGHLOUL_LEGACY=200
echo BASELINE_HEAD=$BASE
echo CANDIDATE_HEAD=$(git rev-parse HEAD)
echo FINAL_MARKER=ZAGHLOUL_V5R3R5_TSC_SOURCE_FIX_ACCOUNT_PROBE_OK
git worktree remove --force "$BASE_WT" >/dev/null 2>&1 || true
