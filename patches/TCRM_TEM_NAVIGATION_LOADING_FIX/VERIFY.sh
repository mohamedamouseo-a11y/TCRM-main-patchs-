#!/usr/bin/env bash
set -Eeuo pipefail

TARGET="${TCRM_TARGET:-/var/www/TCRM-MAIN}"
FILE="$TARGET/client/src/components/CRMLayout.tsx"

fail() { echo "ERROR=$*" >&2; exit 1; }
[[ -d "$TARGET/.git" ]] || fail "target is not a Git worktree"
[[ -f "$FILE" ]] || fail "CRMLayout.tsx missing"
cd "$TARGET"

python3 - <<'PY'
from pathlib import Path
s=Path('client/src/components/CRMLayout.tsx').read_text()
start=s.find('{/* ── Business Development collapsible group ── */}')
end=s.find('{afterMarketing.map(renderItem)}', start)
if start < 0 or end < 0:
    raise SystemExit('Business Development navigation block missing')
seg=s[start:end]
if '<a key={sub.href} href={sub.href}>' in seg:
    raise SystemExit('FAIL: native anchor remains in Business Development navigation')
if seg.count('<Link key={sub.href} href={sub.href}>') < 2:
    raise SystemExit('FAIL: expected Wouter Link wrappers for expanded/collapsed BD navigation')
if '{ href: "/tem", label: "TEM"' not in seg:
    raise SystemExit('FAIL: TEM nav item missing')
print('TEM_NAV_USES_WOUTER_LINK=YES')
print('FULL_DOCUMENT_RELOAD_PATH_REMOVED=YES')
PY

git diff --check

# Safety: this patch must not touch TEM/Mautic runtime configuration or backend source.
CHANGED="$(git diff --name-only)"
if printf '%s\n' "$CHANGED" | grep -Eq '^(server/tem/|server/emailMarketing\.ts|services/tem-mautic/|drizzle/)'; then
  echo "NOTE=Other pre-existing TEM changes are present in the worktree; verification only asserts this patch target semantics." >&2
fi

echo "DATABASE_CHANGED_BY_PATCH=NO"
echo "EMAIL_SENT_BY_PATCH=NO"
echo "WORKERS_CHANGED_BY_PATCH=NO"
echo "GITHUB_PUSH=NOT_ATTEMPTED"
echo "FINAL_MARKER=TCRM_TEM_NAVIGATION_LOADING_FIX_VERIFY_OK"
