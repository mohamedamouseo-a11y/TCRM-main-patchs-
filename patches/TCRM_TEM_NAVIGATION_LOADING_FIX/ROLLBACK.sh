#!/usr/bin/env bash
set -Eeuo pipefail

TARGET="${TCRM_TARGET:-/var/www/TCRM-MAIN}"
BACKUP_DIR="${TEM_NAV_FIX_BACKUP_DIR:-}"
if [[ -z "$BACKUP_DIR" && -f /tmp/tcrm-tem-nav-fix-last-backup ]]; then
  BACKUP_DIR="$(cat /tmp/tcrm-tem-nav-fix-last-backup)"
fi

[[ -n "$BACKUP_DIR" ]] || { echo "ERROR=Set TEM_NAV_FIX_BACKUP_DIR or apply the patch first" >&2; exit 1; }
SRC="$BACKUP_DIR/client/src/components/CRMLayout.tsx"
DST="$TARGET/client/src/components/CRMLayout.tsx"
[[ -f "$SRC" ]] || { echo "ERROR=Backup CRMLayout.tsx not found" >&2; exit 1; }
[[ -d "$TARGET/.git" ]] || { echo "ERROR=Target is not a Git worktree" >&2; exit 1; }

cp -a "$SRC" "$DST"
cd "$TARGET"
git diff --check
NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=3072}" pnpm build >/tmp/tcrm-tem-nav-fix-rollback-build.log 2>&1 || {
  tail -n 120 /tmp/tcrm-tem-nav-fix-rollback-build.log >&2
  echo "ERROR=Rollback source restored but build failed" >&2
  exit 1
}

echo "ROLLBACK_BUILD=PASS"
echo "DATABASE_CHANGED=NO"
echo "EMAIL_SENT=NO"
echo "GITHUB_PUSH=NOT_ATTEMPTED"
echo "FINAL_MARKER=TCRM_TEM_NAVIGATION_LOADING_FIX_ROLLBACK_OK"
