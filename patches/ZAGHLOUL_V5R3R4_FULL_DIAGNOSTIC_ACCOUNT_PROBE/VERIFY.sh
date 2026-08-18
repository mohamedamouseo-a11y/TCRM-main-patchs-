#!/usr/bin/env bash
set -euo pipefail
TARGET=${TCRM_PATH:-/var/www/TCRM-MAIN}
PATCH=ZAGHLOUL_V5R3R4_FULL_DIAGNOSTIC_ACCOUNT_PROBE
WORK=/tmp/$PATCH
BASE_WT="$WORK/baseline-worktree"
BASE=${ZAGHLOUL_V5R3_BASELINE_HEAD:-c7ca52c5bb0495400ed327601d50cf6c7a363c73}
rm -rf "$WORK"
mkdir -p "$WORK"
cd "$TARGET"
git worktree prune >/dev/null 2>&1 || true
git cat-file -e "$BASE^{commit}"
for f in package.json pnpm-lock.yaml package-lock.json yarn.lock; do
  if [ -e "$f" ] || git cat-file -e "$BASE:$f" 2>/dev/null; then
    [ -e "$f" ] && git cat-file -e "$BASE:$f" 2>/dev/null || { echo DEPENDENCY_MANIFEST_MISMATCH=$f; exit 2; }
    git show "$BASE:$f" > "$WORK/base.$(basename "$f")"
    cmp -s "$WORK/base.$(basename "$f")" "$f" || { echo DEPENDENCY_MANIFEST_MISMATCH=$f; exit 2; }
  fi
done
echo DEPENDENCY_MANIFEST_MISMATCH=NONE
[ -x "$TARGET/node_modules/.bin/tsc" ] || { echo LOCAL_TSC=FAIL; exit 3; }
git worktree add --detach "$BASE_WT" "$BASE" >/dev/null
ln -s "$TARGET/node_modules" "$BASE_WT/node_modules"
TSC="$TARGET/node_modules/.bin/tsc"
run_tsc(){
  local dir=$1 out=$2 rcfile=$3
  set +e
  (cd "$dir" && NODE_OPTIONS=--max-old-space-size=16384 "$TSC" --noEmit --pretty false >"$out" 2>&1)
  local rc=$?
  set -e
  printf '%s\n' "$rc" > "$rcfile"
}
run_tsc "$BASE_WT" "$WORK/tsc.baseline" "$WORK/tsc.baseline.rc"
run_tsc "$TARGET" "$WORK/tsc.candidate" "$WORK/tsc.candidate.rc"
BRC=$(cat "$WORK/tsc.baseline.rc"); CRC=$(cat "$WORK/tsc.candidate.rc")
case "$BRC" in 0|1|2) ;; *) echo "TSC_BASELINE_EXIT=$BRC"; echo FINAL=FAIL; exit 4;; esac
case "$CRC" in 0|1|2) ;; *) echo "TSC_CANDIDATE_EXIT=$CRC"; echo FINAL=FAIL; exit 5;; esac
python3 - "$WORK/tsc.baseline" "$WORK/tsc.candidate" "$WORK/new-ts-errors.txt" <<'PY'
import re,sys
from collections import Counter
pat=re.compile(r'^(.*)\((\d+),(\d+)\):\s+error\s+(TS\d+):\s+(.*)$')
def parse(p):
 raw=[]; norm=[]
 for line in open(p,errors='ignore'):
  m=pat.match(line.rstrip('\n'))
  if not m: continue
  raw.append(m.group(0)); path,_,_,code,msg=m.groups()
  norm.append(f'{path} :: {code} :: {re.sub(r"\\s+"," ",msg.strip())}')
 return raw,Counter(norm)
br,b=parse(sys.argv[1]); cr,c=parse(sys.argv[2]); new=c-b; n=sum(new.values())
print(f'TSC_BASELINE_ERRORS={len(br)}')
print(f'TSC_CANDIDATE_ERRORS={len(cr)}')
print(f'TSC_NEW_ERROR_COUNT={n}')
with open(sys.argv[3],'w') as f:
 for k,v in sorted(new.items()):
  for _ in range(v): f.write('NEW_TS_ERROR='+k+'\n')
PY
cat "$WORK/new-ts-errors.txt" || true
echo "TSC_BASELINE_EXIT=$BRC"
echo "TSC_CANDIDATE_EXIT=$CRC"
NEWCOUNT=$(grep -c '^NEW_TS_ERROR=' "$WORK/new-ts-errors.txt" 2>/dev/null || true)

cd "$TARGET"
set +e
ACCOUNT_JSON=$(NODE_OPTIONS=--max-old-space-size=4096 npx tsx -e 'import { getZaghloulV5Settings } from "./server/services/zaghloul-v5/v5Service.ts"; (async()=>{const r=await getZaghloulV5Settings(); process.stdout.write(JSON.stringify(r));})().catch(e=>{console.error(e);process.exit(1)});' 2>"$WORK/account.err")
ARC=$?
set -e
if [ "$ARC" -eq 0 ]; then
  AUTH=$(node -e 'const x=JSON.parse(process.argv[1]);process.stdout.write(String(x.authMode||""))' "$ACCOUNT_JSON")
else
  AUTH=""
fi
if [ "$ARC" -eq 0 ] && [ "$AUTH" = TCRM_SESSION ]; then
  echo ACCOUNT_MANAGEMENT=PASS
  echo AUTH_MODE=TCRM_SESSION
else
  echo ACCOUNT_MANAGEMENT=FAIL
  echo "AUTH_MODE=${AUTH:-UNDEFINED}"
  sed 's/^/ACCOUNT_PROBE_ERROR=/' "$WORK/account.err" || true
fi

echo BASELINE_HEAD="$BASE"
echo CANDIDATE_HEAD="$(git rev-parse HEAD)"
if [ "$NEWCOUNT" -eq 0 ] && [ "$ARC" -eq 0 ] && [ "$AUTH" = TCRM_SESSION ]; then
  echo FINAL_MARKER=ZAGHLOUL_V5R3R4_FULL_DIAGNOSTIC_ACCOUNT_PROBE_OK
else
  echo FINAL_MARKER=NOT_EMITTED
fi
git worktree remove --force "$BASE_WT" >/dev/null 2>&1 || true
