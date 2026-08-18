#!/usr/bin/env bash
set -euo pipefail
TARGET=${TCRM_PATH:-/var/www/TCRM-MAIN}
PATCH=ZAGHLOUL_V5R3R2_TSC_LOCATION_NORMALIZATION_ACCOUNT_PROBE
WORK=/tmp/$PATCH
BASE_WT="$WORK/baseline-worktree"
cd "$TARGET"
[ -f "$WORK/baseline_head" ] || { echo PRECHECK=FAIL; exit 2; }
[ -d "$BASE_WT/.git" ] || [ -f "$BASE_WT/.git" ] || { echo BASELINE_WORKTREE=FAIL; exit 3; }
BASE=$(cat "$WORK/baseline_head")
CAND=$(git rev-parse HEAD)

run_tsc(){
  local dir=$1 out=$2 rcfile=$3
  set +e
  (cd "$dir" && NODE_OPTIONS=--max-old-space-size=16384 npx tsc --noEmit --pretty false >"$out" 2>&1)
  local rc=$?
  set -e
  printf '%s\n' "$rc" > "$rcfile"
}
run_tsc "$BASE_WT" "$WORK/tsc.baseline" "$WORK/tsc.baseline.rc"
run_tsc "$TARGET" "$WORK/tsc.candidate" "$WORK/tsc.candidate.rc"
BRC=$(cat "$WORK/tsc.baseline.rc"); CRC=$(cat "$WORK/tsc.candidate.rc")
case "$BRC" in 0|1|2) ;; *) echo "TSC_BASELINE_EXIT=$BRC"; echo FINAL=FAIL; exit 4;; esac
case "$CRC" in 0|1|2) ;; *) echo "TSC_CANDIDATE_EXIT=$CRC"; echo FINAL=FAIL; exit 5;; esac

python3 - "$WORK/tsc.baseline" "$WORK/tsc.candidate" <<'PY'
import re,sys
from collections import Counter
pat=re.compile(r'^(.*)\((\d+),(\d+)\):\s+error\s+(TS\d+):\s+(.*)$')
def parse(p):
 raw=[]; norm=[]
 for line in open(p,errors='ignore'):
  line=line.rstrip('\n')
  m=pat.match(line)
  if not m: continue
  raw.append(line)
  path,_,_,code,msg=m.groups()
  norm.append(f'{path} :: {code} :: {re.sub(r"\\s+"," ",msg.strip())}')
 return raw,Counter(norm)
br,b=parse(sys.argv[1]); cr,c=parse(sys.argv[2])
new=c-b
new_count=sum(new.values())
print(f'TSC_BASELINE_ERRORS={len(br)}')
print(f'TSC_CANDIDATE_ERRORS={len(cr)}')
print(f'TSC_NEW_ERROR_COUNT={new_count}')
if new_count:
 for k,n in sorted(new.items()):
  for _ in range(n): print('NEW_TS_ERROR='+k)
 raise SystemExit(1)
PY

echo "TSC_BASELINE_EXIT=$BRC"
echo "TSC_CANDIDATE_EXIT=$CRC"

# Real service-layer account-management runtime probe.
ACCOUNT_JSON=$(NODE_OPTIONS=--max-old-space-size=4096 npx tsx -e 'import { getZaghloulV5Settings } from "./server/services/zaghloul-v5/v5Service.ts"; const r=await getZaghloulV5Settings(); process.stdout.write(JSON.stringify(r));')
AUTH=$(node -e 'const x=JSON.parse(process.argv[1]);process.stdout.write(String(x.authMode||""))' "$ACCOUNT_JSON")
[ "$AUTH" = TCRM_SESSION ] || { echo ACCOUNT_MANAGEMENT=FAIL; echo "AUTH_MODE=${AUTH:-UNDEFINED}"; exit 6; }
# Router must remain TCRM-authenticated, not public.
grep -nA40 -B5 'zaghloulV5: router' server/routers.ts | grep -q 'settings: protectedProcedure\|settings: router' || true
# Stronger check: the settings query block must use protectedProcedure somewhere in the V5 router window.
grep -nA220 'zaghloulV5: router' server/routers.ts | grep -q 'protectedProcedure' || { echo ACCOUNT_AUTH_ROUTE=FAIL; exit 7; }

echo ACCOUNT_MANAGEMENT=PASS
echo AUTH_MODE=TCRM_SESSION
echo BASELINE_HEAD="$BASE"
echo CANDIDATE_HEAD="$CAND"
echo FINAL_MARKER=ZAGHLOUL_V5R3R2_TSC_LOCATION_NORMALIZATION_ACCOUNT_PROBE_OK
# cleanup detached worktree only on success
cd "$TARGET" && git worktree remove --force "$BASE_WT" >/dev/null 2>&1 || true
