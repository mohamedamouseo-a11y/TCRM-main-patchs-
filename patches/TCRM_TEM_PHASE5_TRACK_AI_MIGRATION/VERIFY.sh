#!/usr/bin/env bash
set -Eeuo pipefail

PATCH_ID="TCRM_TEM_PHASE5_TRACK_AI_MIGRATION"
TARGET="${TCRM_TARGET:-/var/www/TCRM-MAIN}"
MIGRATION="drizzle/migrations/20260823_tem_ai_marketing_agent.sql"
NEGATION="!/drizzle/migrations/20260823_tem_ai_marketing_agent.sql"

fail() { echo "ERROR=$*" >&2; exit 1; }
[[ -d "$TARGET/.git" ]] || fail "target is not a Git worktree: $TARGET"
cd "$TARGET"

[[ -f .gitignore ]] || fail ".gitignore missing"
[[ -f "$MIGRATION" ]] || fail "migration missing: $MIGRATION"
[[ "$(grep -Fxc "$NEGATION" .gitignore || true)" == "1" ]] || fail "exact migration allow-rule missing or duplicated"
grep -Fxq '*.sql' .gitignore || fail "generic *.sql ignore rule missing"

grep -Eq 'CREATE TABLE IF NOT EXISTS[[:space:]]+`?tem_ai_proposals`?' "$MIGRATION" || fail "tem_ai_proposals CREATE TABLE missing"
grep -Eq 'CREATE TABLE IF NOT EXISTS[[:space:]]+`?tem_ai_audit_events`?' "$MIGRATION" || fail "tem_ai_audit_events CREATE TABLE missing"
if grep -Eqi '(^|[[:space:]])(DROP|TRUNCATE)[[:space:]]+(TABLE|DATABASE)|DELETE[[:space:]]+FROM' "$MIGRATION"; then
  fail "destructive SQL detected"
fi

if git check-ignore --quiet -- "$MIGRATION"; then
  fail "migration is still ignored"
fi
if ! git check-ignore --quiet --no-index -- "drizzle/migrations/__tcrm_tem_phase5_probe__.sql"; then
  fail "generic SQL ignore boundary was weakened"
fi

git diff --check -- .gitignore || fail ".gitignore diff check failed"

if git ls-files --error-unmatch "$MIGRATION" >/dev/null 2>&1; then
  echo "MIGRATION_GIT_STATE=TRACKED_OR_STAGED"
elif git status --porcelain --untracked-files=all -- "$MIGRATION" | grep -q .; then
  echo "MIGRATION_GIT_STATE=VISIBLE_UNTRACKED_READY_FOR_DEVELOPER_HUB"
else
  fail "migration is neither tracked/staged nor visible as an untracked file"
fi

echo "GENERIC_SQL_IGNORE=STILL_ENFORCED"
echo "DB_CHANGED=NO"
echo "EMAIL_SENT=NO"
echo "GITHUB_PUSH=NOT_ATTEMPTED"
echo "FINAL_MARKER=TCRM_TEM_PHASE5_MIGRATION_TRACKING_VERIFY_OK"
