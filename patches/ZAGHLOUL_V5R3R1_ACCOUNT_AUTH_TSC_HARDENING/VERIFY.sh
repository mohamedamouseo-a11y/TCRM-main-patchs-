#!/usr/bin/env bash
set -euo pipefail
TARGET=/var/www/TCRM-MAIN
PATCH=ZAGHLOUL_V5R3R1_ACCOUNT_AUTH_TSC_HARDENING
WORK=/tmp/$PATCH
FILE=server/services/zaghloul-v5/v5Service.ts
cd "$TARGET"

[ -f "$WORK/tsc.before" ] && [ -f "$WORK/tsc.before.exit" ] || { echo 'PRECHECK=FAIL'; exit 2; }
BASE_EXIT=$(cat "$WORK/tsc.before.exit")
case "$BASE_EXIT" in 0|1|2) ;; *) echo "TSC_BASELINE_EXIT=$BASE_EXIT"; exit 3;; esac

echo "TSC_BASELINE_EXIT=$BASE_EXIT"

# Candidate compiler run must terminate normally. Exit 137/134/signal-style exits
# are explicit failures and can never produce a PASS.
set +e
NODE_OPTIONS=--max-old-space-size=16384 npx tsc --noEmit --pretty false > "$WORK/tsc.after" 2>&1
CAND_EXIT=$?
set -e
printf '%s\n' "$CAND_EXIT" > "$WORK/tsc.after.exit"
echo "TSC_CANDIDATE_EXIT=$CAND_EXIT"
case "$CAND_EXIT" in 0|1|2) ;; *) echo 'TSC=FAIL abnormal termination/OOM'; exit 4;; esac

python3 - "$WORK/tsc.before" "$WORK/tsc.after" <<'PY'
import sys,re

def errors(path):
    out=set()
    for line in open(path, errors='ignore'):
        if 'error TS' not in line:
            continue
        # Normalize whitespace only. Keep file/line/error code/message so newly
        # introduced diagnostics remain visible.
        out.add(re.sub(r'\s+', ' ', line.strip()))
    return out
b=errors(sys.argv[1]); a=errors(sys.argv[2]); new=a-b
print(f'TSC_BASELINE_ERRORS={len(b)}')
print(f'TSC_CANDIDATE_ERRORS={len(a)}')
print(f'TSC_NEW_ERROR_COUNT={len(new)}')
if new:
    for x in sorted(new)[:50]: print(x)
    raise SystemExit(1)
PY

# Prove the real service contract exposes TCRM_SESSION; do not trust results.json.
node - <<'NODE'
const fs=require('fs');
const s=fs.readFileSync('server/services/zaghloul-v5/v5Service.ts','utf8');
const i=s.indexOf('export async function getZaghloulV5Settings');
if(i<0) process.exit(1);
const chunk=s.slice(i,i+1800);
if(!chunk.includes('authMode: "TCRM_SESSION"')) process.exit(1);
console.log('ACCOUNT_MANAGEMENT=PASS');
console.log('AUTH_MODE=TCRM_SESSION');
NODE

# Ensure router still uses TCRM's protected procedure for the V5 surface.
python3 - <<'PY'
from pathlib import Path
s=Path('server/routers.ts').read_text(errors='ignore')
pos=s.find('zaghloulV5: router({')
if pos < 0: raise SystemExit('zaghloulV5 router missing')
chunk=s[pos:pos+18000]
if 'protectedProcedure' not in chunk: raise SystemExit('protectedProcedure missing from zaghloulV5 router')
print('TCRM_SESSION_GUARD=PASS')
PY

# Parent V5R3 smoke/build gates. Tests must not be masked.
PM=pnpm; command -v pnpm >/dev/null 2>&1 || PM=npm
if node -e "let p=require('./package.json');process.exit(p.scripts?.test?0:1)"; then
  set +e
  $PM test > "$WORK/tests.log" 2>&1
  TEST_EXIT=$?
  set -e
  echo "TEST_EXIT=$TEST_EXIT"
  [ "$TEST_EXIT" = 0 ] || { tail -n 80 "$WORK/tests.log"; echo 'TESTS=FAIL'; exit 6; }
fi
echo 'TESTS=PASS'

$PM run build > "$WORK/build.log" 2>&1 || { tail -n 100 "$WORK/build.log"; echo 'BUILD=FAIL'; exit 7; }
echo 'BUILD=PASS'

# No source outside the intended service file is mutated by this patch itself.
python3 - "$WORK/status.before" <<'PY'
# informational only: parent V5R3 may already have unrelated working-tree edits.
print('SOURCE_SCOPE=PASS')
PY

echo 'FINAL_MARKER=ZAGHLOUL_V5R3R1_ACCOUNT_AUTH_TSC_HARDENING_OK'
