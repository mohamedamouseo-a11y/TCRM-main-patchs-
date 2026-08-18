#!/usr/bin/env bash
set -euo pipefail
TARGET=/var/www/TCRM-MAIN
PATCH=ZAGHLOUL_V5R3R1_ACCOUNT_AUTH_TSC_HARDENING
WORK=/tmp/$PATCH
FILE=server/services/zaghloul-v5/v5Service.ts
mkdir -p "$WORK/backups"
cd "$TARGET"

[ -f "$FILE" ] || { echo 'PRECHECK=FAIL missing v5Service.ts'; exit 2; }
cp -a "$FILE" "$WORK/backups/v5Service.ts.before"
git rev-parse HEAD > "$WORK/baseline_head"
git status --porcelain=v1 > "$WORK/status.before"

# Establish a real pre-fix TSC baseline with enough heap. 0/1/2 are normal
# TypeScript exits; OOM/signal-style exits are invalid evidence.
set +e
NODE_OPTIONS=--max-old-space-size=16384 npx tsc --noEmit --pretty false > "$WORK/tsc.before" 2>&1
TSC_BASE=$?
set -e
printf '%s\n' "$TSC_BASE" > "$WORK/tsc.before.exit"
case "$TSC_BASE" in 0|1|2) ;; *) echo "TSC_BASELINE_EXIT=$TSC_BASE"; echo 'PRECHECK=FAIL invalid/oom baseline'; exit 3;; esac

python3 - "$FILE" <<'PY'
from pathlib import Path
import sys,re
p=Path(sys.argv[1])
s=p.read_text()

# Idempotent: if the real service already exposes the canonical mode, leave it.
if 'authMode?: "TCRM_SESSION";' not in s and 'authMode: "TCRM_SESSION";' not in s:
    marker='export interface V5Settings {'
    if marker not in s:
        raise SystemExit('V5Settings interface not found')
    s=s.replace(marker, marker+'\n  authMode?: "TCRM_SESSION";', 1)

fn='export async function getZaghloulV5Settings(): Promise<V5Settings> {'
pos=s.find(fn)
if pos < 0:
    raise SystemExit('getZaghloulV5Settings not found')
ret=s.find('return {', pos)
if ret < 0:
    raise SystemExit('settings return object not found')
window=s[ret:ret+1000]
if 'authMode: "TCRM_SESSION"' not in window:
    insert=ret+len('return {')
    s=s[:insert]+'\n    authMode: "TCRM_SESSION",'+s[insert:]

p.write_text(s)
PY

# Source-level assertions: the fix must live in the real service contract.
grep -q 'authMode.*TCRM_SESSION' "$FILE"
python3 - "$FILE" <<'PY'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text()
pos=s.index('export async function getZaghloulV5Settings')
chunk=s[pos:pos+1600]
if 'authMode: "TCRM_SESSION"' not in chunk:
    raise SystemExit(1)
PY

echo 'APPLY=PASS'
echo 'SOURCE_FIX=server/services/zaghloul-v5/v5Service.ts'
echo 'AUTH_MODE=TCRM_SESSION'
