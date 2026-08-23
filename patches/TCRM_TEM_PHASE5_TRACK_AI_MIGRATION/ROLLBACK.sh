#!/usr/bin/env bash
set -Eeuo pipefail

PATCH_ID="TCRM_TEM_PHASE5_TRACK_AI_MIGRATION"
TARGET="${TCRM_TARGET:-/var/www/TCRM-MAIN}"
STATE_ROOT="${TCRM_PATCH_STATE_ROOT:-$TARGET/.tcrm_patch_state/$PATCH_ID}"
BACKUP_DIR="${TCRM_TEM_PHASE5_TRACK_BACKUP_DIR:-}"

fail() { echo "ERROR=$*" >&2; exit 1; }
[[ -d "$TARGET/.git" ]] || fail "target is not a Git worktree: $TARGET"
cd "$TARGET"

if [[ -z "$BACKUP_DIR" && -f "$STATE_ROOT/latest" ]]; then
  BACKUP_DIR="$(cat "$STATE_ROOT/latest")"
fi
[[ -n "$BACKUP_DIR" && -f "$BACKUP_DIR/.gitignore" ]] || fail "backup not found; set TCRM_TEM_PHASE5_TRACK_BACKUP_DIR"

cp -a "$BACKUP_DIR/.gitignore" .gitignore

echo "MIGRATION_FILE_DELETED=NO"
echo "DATABASE_CHANGED=NO"
echo "TEM_PHASE5_CODE_CHANGED=NO"
echo "GITHUB_PUSH=NOT_ATTEMPTED"
echo "FINAL_MARKER=TCRM_TEM_PHASE5_MIGRATION_TRACKING_ROLLBACK_OK"
