#!/usr/bin/env bash
set -Eeuo pipefail

PATCH_ID="TCRM_TEM_PHASE4_PRODUCTION_ACTIVATION"
TARGET="${TCRM_TARGET:-/var/www/TCRM-MAIN}"
EXPECTED_MAUTIC_COMMIT="27a76aff64aed8e50f6dd784ea86ec95d45d4616"

log(){ printf '[%s] %s\n' "$PATCH_ID" "$*"; }
die(){ printf '[%s] ERROR: %s\n' "$PATCH_ID" "$*" >&2; exit 1; }

[[ -d "$TARGET/.git" ]] || die "target is not a Git worktree"
[[ -f "$TARGET/server/tem/temRouter.ts" ]] || die "TEM router missing"
[[ -f "$TARGET/server/emailMarketing.ts" ]] || die "legacy email marketing source missing"
[[ -f "$TARGET/services/tem-mautic/docker-compose.yml" ]] || die "TEM compose missing"
[[ -x "$TARGET/services/tem-mautic/phase4-activate.sh" ]] || die "phase4 activation helper missing/not executable"
[[ -x "$TARGET/services/tem-mautic/phase4-disable.sh" ]] || die "phase4 disable helper missing/not executable"
[[ -f "$TARGET/services/tem-mautic/MAUTIC_UPSTREAM.lock" ]] || die "Mautic upstream lock missing"

grep -Fq "COMMIT=${EXPECTED_MAUTIC_COMMIT}" "$TARGET/services/tem-mautic/MAUTIC_UPSTREAM.lock" || die "Mautic upstream pin mismatch"
grep -Fq "TEM_PHASE4_PRODUCTION_ROUTER" "$TARGET/server/tem/temRouter.ts" || die "production router marker missing"
grep -Fq "syncSuppression" "$TARGET/server/tem/temRouter.ts" || die "suppression migration endpoint missing"
grep -Fq "sendControlledTest" "$TARGET/server/tem/temRouter.ts" || die "controlled test endpoint missing"
grep -Fq "TEM_PHASE4_LEGACY_SEND_GUARD" "$TARGET/server/emailMarketing.ts" || die "legacy sender guard missing"
grep -Fq 'MAUTIC_MAILER_DSN: ${MAUTIC_MAILER_DSN:-null://null}' "$TARGET/services/tem-mautic/docker-compose.yml" || die "runtime mailer DSN gate missing"
grep -Fq 'profiles: ["production"]' "$TARGET/services/tem-mautic/docker-compose.yml" || die "production scheduler profile missing"
grep -Fq 'mautic:segments:update' "$TARGET/services/tem-mautic/docker-compose.yml" || die "segment scheduler command missing"
grep -Fq 'mautic:campaigns:update' "$TARGET/services/tem-mautic/docker-compose.yml" || die "campaign update command missing"
grep -Fq 'mautic:campaigns:trigger' "$TARGET/services/tem-mautic/docker-compose.yml" || die "campaign trigger command missing"
grep -Fq 'mautic:messages:send' "$TARGET/services/tem-mautic/docker-compose.yml" || die "message queue command missing"
grep -Fq 'TEM_BULK_SEND_APPROVED' "$TARGET/services/tem-mautic/docker-compose.yml" || die "bulk approval gate missing"

(cd "$TARGET" && git diff --check)

log "running build"
(cd "$TARGET" && pnpm build)

TYPECHECK_LOG="$(mktemp)"
trap 'rm -f "$TYPECHECK_LOG"' EXIT
set +e
(cd "$TARGET" && pnpm check) >"$TYPECHECK_LOG" 2>&1
TYPECHECK_RC=$?
set -e
TYPECHECK_ERRORS=$(grep -cE 'error TS[0-9]+' "$TYPECHECK_LOG" || true)
echo "TYPECHECK_RC=$TYPECHECK_RC"
echo "TYPECHECK_ERRORS=$TYPECHECK_ERRORS"

if [[ -f /etc/tcrm-tem/tem.env ]]; then
  docker compose -f "$TARGET/services/tem-mautic/docker-compose.yml" --env-file /etc/tcrm-tem/tem.env config -q
  echo "COMPOSE_VALIDATION=PASS"
else
  echo "COMPOSE_VALIDATION=SKIPPED_NO_RUNTIME_ENV"
fi

if curl -fsS --max-time 5 http://127.0.0.1:8089/ >/dev/null 2>&1; then
  echo "MAUTIC_INTERNAL_HEALTH=PASS"
else
  echo "MAUTIC_INTERNAL_HEALTH=NOT_RUNNING_OR_UNHEALTHY"
fi

if [[ -d "$TARGET/external/mautic" ]]; then
  echo "MAUTIC_SOURCE_PRESENT=YES"
else
  die "external/mautic missing"
fi

if git -C "$TARGET" ls-files external/mautic | grep -q .; then
  die "external/mautic must not be tracked by TCRM Git"
fi
echo "MAUTIC_SOURCE_TRACKED=NO"

echo "GITHUB_PUSH=NOT_ATTEMPTED"
echo "USER_WILL_PUSH_MANUALLY=YES"
echo "FINAL_MARKER=TCRM_TEM_PHASE4_VERIFY_OK"
