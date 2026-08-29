#!/usr/bin/env bash
set -Eeuo pipefail

TARGET="${TCRM_TARGET:-/var/www/TCRM-MAIN}"
FILE="$TARGET/client/src/components/CRMLayout.tsx"
EXPECTED_BLOB="9f9dbee77fa8a755f98d16df88c9f18bd0ff2bf8"
BACKUP_ROOT="${TEM_NAV_FIX_BACKUP_ROOT:-/var/backups/tcrm-tem-nav-fix}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR="$BACKUP_ROOT/$STAMP"

fail() { echo "ERROR=$*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || fail "missing command: $1"; }
for cmd in git python3 pnpm mkdir cp; do need "$cmd"; done

[[ -d "$TARGET/.git" ]] || fail "target is not a Git worktree: $TARGET"
[[ -f "$FILE" ]] || fail "CRMLayout.tsx missing"
cd "$TARGET"

BRANCH_BEFORE="$(git branch --show-current)"
HEAD_BEFORE="$(git rev-parse HEAD)"
echo "BRANCH_BEFORE=$BRANCH_BEFORE"
echo "HEAD_BEFORE=$HEAD_BEFORE"

# Never overwrite local edits to the target file.
git diff --quiet -- client/src/components/CRMLayout.tsx || fail "CRMLayout.tsx has local modifications; refusing to overwrite"

CURRENT_BLOB="$(git hash-object client/src/components/CRMLayout.tsx)"

# Idempotent fast-path: if already fixed, verify and stop.
if python3 - <<'PY'
from pathlib import Path
p=Path('client/src/components/CRMLayout.tsx')
s=p.read_text()
start=s.find('{/* ── Business Development collapsible group ── */}')
end=s.find('{afterMarketing.map(renderItem)}', start)
if start < 0 or end < 0:
    raise SystemExit(2)
seg=s[start:end]
if '<a key={sub.href} href={sub.href}>' not in seg and seg.count('<Link key={sub.href} href={sub.href}>') >= 2:
    raise SystemExit(0)
raise SystemExit(1)
PY
then
  echo "ALREADY_FIXED=YES"
  bash "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/VERIFY.sh"
  exit 0
fi

[[ "$CURRENT_BLOB" == "$EXPECTED_BLOB" ]] || fail "reviewed CRMLayout baseline drifted: $CURRENT_BLOB"

mkdir -p "$BACKUP_DIR/client/src/components"
chmod 0700 "$BACKUP_DIR"
cp -a client/src/components/CRMLayout.tsx "$BACKUP_DIR/client/src/components/CRMLayout.tsx"
printf '%s\n' "$BRANCH_BEFORE" > "$BACKUP_DIR/branch.txt"
printf '%s\n' "$HEAD_BEFORE" > "$BACKUP_DIR/head.txt"
printf '%s\n' "$BACKUP_DIR" > /tmp/tcrm-tem-nav-fix-last-backup

python3 - <<'PY'
from pathlib import Path
p=Path('client/src/components/CRMLayout.tsx')
s=p.read_text()
marker='{/* ── Business Development collapsible group ── */}'
start=s.find(marker)
end=s.find('{afterMarketing.map(renderItem)}', start)
if start < 0 or end < 0:
    raise SystemExit('Business Development navigation block not found')
seg=s[start:end]
open_tag='<a key={sub.href} href={sub.href}>'
close_tag='</a>'
if seg.count(open_tag) != 2:
    raise SystemExit(f'Expected exactly 2 native BD anchors, found {seg.count(open_tag)}')
if seg.count(close_tag) != 2:
    raise SystemExit(f'Expected exactly 2 native BD closing anchors, found {seg.count(close_tag)}')
seg=seg.replace(open_tag, '<Link key={sub.href} href={sub.href}>')
seg=seg.replace(close_tag, '</Link>')
p.write_text(s[:start] + seg + s[end:])
PY

# Source-level regression guard.
python3 - <<'PY'
from pathlib import Path
s=Path('client/src/components/CRMLayout.tsx').read_text()
start=s.find('{/* ── Business Development collapsible group ── */}')
end=s.find('{afterMarketing.map(renderItem)}', start)
if start < 0 or end < 0:
    raise SystemExit('BD block missing after patch')
seg=s[start:end]
if '<a key={sub.href} href={sub.href}>' in seg:
    raise SystemExit('Native BD anchor still present')
if seg.count('<Link key={sub.href} href={sub.href}>') < 2:
    raise SystemExit('Wouter BD Link wrappers missing')
if '{ href: "/tem", label: "TEM"' not in seg:
    raise SystemExit('TEM navigation entry missing')
print('BD_SPA_NAVIGATION=PASS')
PY

git diff --check
NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=3072}" pnpm build >/tmp/tcrm-tem-nav-fix-build.log 2>&1 || {
  tail -n 120 /tmp/tcrm-tem-nav-fix-build.log >&2
  cp -a "$BACKUP_DIR/client/src/components/CRMLayout.tsx" client/src/components/CRMLayout.tsx
  fail "build failed; CRMLayout restored"
}

echo "BUILD=PASS"
echo "DATABASE_CHANGED=NO"
echo "EMAIL_SENT=NO"
echo "WORKERS_CHANGED=NO"
echo "SCHEDULER_CHANGED=NO"
echo "GITHUB_PUSH=NOT_ATTEMPTED"
echo "BACKUP_DIR=$BACKUP_DIR"
echo "BRANCH_AFTER=$(git branch --show-current)"
echo "HEAD_AFTER=$(git rev-parse HEAD)"
echo "FINAL_MARKER=TCRM_TEM_NAVIGATION_LOADING_FIX_OK"
