#!/usr/bin/env bash
set -Eeuo pipefail

PATCH_ID="TCRM_TEM_PHASE4_PRODUCTION_ACTIVATION"
TARGET="${TCRM_TARGET:-/var/www/TCRM-MAIN}"
BACKUP_DIR="${TEM_PHASE4_BACKUP_DIR:-/var/tmp/${PATCH_ID}.backup}"

log(){ printf '[%s] %s\n' "$PATCH_ID" "$*"; }
die(){ printf '[%s] ERROR: %s\n' "$PATCH_ID" "$*" >&2; exit 1; }

[[ -d "$TARGET/.git" ]] || die "target is not a Git worktree"
[[ -d "$BACKUP_DIR" ]] || die "backup not found: $BACKUP_DIR"
[[ -f "$BACKUP_DIR/server/tem/temRouter.ts" ]] || die "TEM router backup missing"
[[ -f "$BACKUP_DIR/server/emailMarketing.ts" ]] || die "legacy email marketing backup missing"
[[ -f "$BACKUP_DIR/services/tem-mautic/docker-compose.yml" ]] || die "compose backup missing"
[[ -f "$BACKUP_DIR/services/tem-mautic/README.md" ]] || die "README backup missing"

if [[ -x "$TARGET/services/tem-mautic/phase4-disable.sh" && -f /etc/tcrm-tem/tem.env ]]; then
  log "stopping Phase 4 worker/scheduler before source rollback"
  bash "$TARGET/services/tem-mautic/phase4-disable.sh" || die "runtime disable failed; source rollback aborted"
fi

cp -a "$BACKUP_DIR/server/tem/temRouter.ts" "$TARGET/server/tem/temRouter.ts"
cp -a "$BACKUP_DIR/server/emailMarketing.ts" "$TARGET/server/emailMarketing.ts"
cp -a "$BACKUP_DIR/services/tem-mautic/docker-compose.yml" "$TARGET/services/tem-mautic/docker-compose.yml"
cp -a "$BACKUP_DIR/services/tem-mautic/README.md" "$TARGET/services/tem-mautic/README.md"
rm -f "$TARGET/services/tem-mautic/phase4-activate.sh" "$TARGET/services/tem-mautic/phase4-disable.sh"

[[ "$(git -C "$TARGET" hash-object server/tem/temRouter.ts)" == "$(cat "$BACKUP_DIR/temRouter.blob")" ]] || die "TEM router restore hash mismatch"
[[ "$(git -C "$TARGET" hash-object server/emailMarketing.ts)" == "$(cat "$BACKUP_DIR/emailMarketing.blob")" ]] || die "email marketing restore hash mismatch"
[[ "$(git -C "$TARGET" hash-object services/tem-mautic/docker-compose.yml)" == "$(cat "$BACKUP_DIR/compose.blob")" ]] || die "compose restore hash mismatch"
[[ "$(git -C "$TARGET" hash-object services/tem-mautic/README.md)" == "$(cat "$BACKUP_DIR/readme.blob")" ]] || die "README restore hash mismatch"

(cd "$TARGET" && git diff --check)
log "running rollback build"
(cd "$TARGET" && pnpm build)

if curl -fsS --max-time 5 http://127.0.0.1:8089/ >/dev/null 2>&1; then
  echo "MAUTIC_INTERNAL_HEALTH=PASS"
else
  echo "MAUTIC_INTERNAL_HEALTH=NOT_RUNNING_OR_UNHEALTHY"
fi

echo "DB_DESTRUCTIVE_ROLLBACK=NOT_REQUIRED"
echo "GITHUB_PUSH=NOT_ATTEMPTED"
echo "FINAL_MARKER=TCRM_TEM_PHASE4_ROLLBACK_OK"
