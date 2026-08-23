#!/usr/bin/env bash
set -Eeuo pipefail

PATCH_ID="TCRM_TEM_PHASE5_TRACK_AI_MIGRATION"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${TCRM_TARGET:-/var/www/TCRM-MAIN}"
MIGRATION="drizzle/migrations/20260823_tem_ai_marketing_agent.sql"
NEGATION="!/drizzle/migrations/20260823_tem_ai_marketing_agent.sql"
EXPECTED_GITIGNORE_BLOB="834799ad53a9269933798db3c4b48442fd8debec"
STATE_ROOT="${TCRM_PATCH_STATE_ROOT:-$TARGET/.tcrm_patch_state/$PATCH_ID}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR="$STATE_ROOT/$STAMP"
AUTO_ROLLBACK=0

fail() {
  local msg="$*"
  if [[ "$AUTO_ROLLBACK" == "1" && -f "$BACKUP_DIR/.gitignore" ]]; then
    cp -a "$BACKUP_DIR/.gitignore" "$TARGET/.gitignore" || true
  fi
  echo "ERROR=$msg" >&2
  exit 1
}

need() { command -v "$1" >/dev/null 2>&1 || fail "missing command: $1"; }
for cmd in git grep cp mkdir date pnpm; do need "$cmd"; done

[[ -d "$TARGET/.git" ]] || fail "target is not a Git worktree: $TARGET"
cd "$TARGET"

BRANCH_BEFORE="$(git branch --show-current)"
HEAD_BEFORE="$(git rev-parse HEAD)"
echo "BRANCH_BEFORE=$BRANCH_BEFORE"
echo "HEAD_BEFORE=$HEAD_BEFORE"

[[ -f .gitignore ]] || fail ".gitignore missing"
[[ -f "$MIGRATION" ]] || fail "Phase 5 migration missing: $MIGRATION"
[[ -f server/tem/temAiRouter.ts ]] || fail "Phase 5 TEM AI router missing"
[[ -f server/tem/temAiPolicy.ts ]] || fail "Phase 5 TEM AI policy missing"
[[ -f drizzle/schema_tem_ai.ts ]] || fail "Phase 5 TEM AI schema missing"
[[ -f scripts/apply-tem-ai-phase5-migration.ts ]] || fail "Phase 5 migration helper missing"

grep -Eq 'CREATE TABLE IF NOT EXISTS[[:space:]]+`?tem_ai_proposals`?' "$MIGRATION" || fail "tem_ai_proposals CREATE TABLE missing"
grep -Eq 'CREATE TABLE IF NOT EXISTS[[:space:]]+`?tem_ai_audit_events`?' "$MIGRATION" || fail "tem_ai_audit_events CREATE TABLE missing"
if grep -Eqi '(^|[[:space:]])(DROP|TRUNCATE)[[:space:]]+(TABLE|DATABASE)|DELETE[[:space:]]+FROM' "$MIGRATION"; then
  fail "destructive SQL detected in Phase 5 migration"
fi

grep -Fxq '*.sql' .gitignore || fail "expected broad *.sql safety rule is missing"

if grep -Fxq "$NEGATION" .gitignore; then
  echo "ALREADY_APPLIED=YES"
  bash "$PATCH_DIR/VERIFY.sh"
  exit 0
fi

CURRENT_GITIGNORE_BLOB="$(git hash-object .gitignore)"
[[ "$CURRENT_GITIGNORE_BLOB" == "$EXPECTED_GITIGNORE_BLOB" ]] || fail ".gitignore baseline mismatch: expected $EXPECTED_GITIGNORE_BLOB got $CURRENT_GITIGNORE_BLOB"

mkdir -p "$BACKUP_DIR"
chmod 0700 "$STATE_ROOT" "$BACKUP_DIR" 2>/dev/null || true
cp -a .gitignore "$BACKUP_DIR/.gitignore"
printf '%s\n' "$BRANCH_BEFORE" > "$BACKUP_DIR/branch.txt"
printf '%s\n' "$HEAD_BEFORE" > "$BACKUP_DIR/head.txt"
git status --porcelain=v1 > "$BACKUP_DIR/git-status-before.txt"
printf '%s\n' "$BACKUP_DIR" > "$STATE_ROOT/latest"
AUTO_ROLLBACK=1

cat >> .gitignore <<'EOF'

# TEM Phase 5 AI Marketing Agent migration — version this exact additive migration only
!/drizzle/migrations/20260823_tem_ai_marketing_agent.sql
EOF

[[ "$(grep -Fxc "$NEGATION" .gitignore)" == "1" ]] || fail "migration allow-rule was not added exactly once"

if git check-ignore --quiet -- "$MIGRATION"; then
  fail "Phase 5 migration is still ignored"
fi
if ! git check-ignore --quiet --no-index -- "drizzle/migrations/__tcrm_tem_phase5_probe__.sql"; then
  fail "generic SQL files are no longer ignored; blast radius is too broad"
fi

git diff --check -- .gitignore || fail ".gitignore diff check failed"

if pnpm check >/tmp/tcrm-tem-phase5-track-typecheck.log 2>&1; then
  echo "TYPECHECK=PASS"
else
  if grep -Eqi 'temAiPolicy|temAiRouter|schema_tem_ai|apply-tem-ai-phase5-migration' /tmp/tcrm-tem-phase5-track-typecheck.log; then
    tail -n 120 /tmp/tcrm-tem-phase5-track-typecheck.log >&2
    fail "TEM Phase 5 typecheck errors detected"
  fi
  echo "TYPECHECK=BASELINE_FAIL_UNRELATED"
fi

pnpm exec vitest run server/tem/temAiPolicy.test.ts >/tmp/tcrm-tem-phase5-track-tests.log 2>&1 || {
  cat /tmp/tcrm-tem-phase5-track-tests.log >&2
  fail "TEM AI policy tests failed"
}
echo "TEM_AI_POLICY_TESTS=PASS"

NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=3072}" pnpm build >/tmp/tcrm-tem-phase5-track-build.log 2>&1 || {
  tail -n 120 /tmp/tcrm-tem-phase5-track-build.log >&2
  fail "production build failed"
}
echo "BUILD=PASS"

AUTO_ROLLBACK=0

echo "MIGRATION_IGNORE_STATE=VISIBLE_TO_GIT"
echo "GENERIC_SQL_IGNORE=STILL_ENFORCED"
echo "DB_CHANGED=NO"
echo "EMAIL_SENT=NO"
echo "WORKERS_CHANGED=NO"
echo "GITHUB_PUSH=NOT_ATTEMPTED"
echo "BACKUP_DIR=$BACKUP_DIR"
echo "BRANCH_AFTER=$(git branch --show-current)"
echo "HEAD_AFTER=$(git rev-parse HEAD)"
git status --short --untracked-files=all -- .gitignore "$MIGRATION"
echo "FINAL_MARKER=TCRM_TEM_PHASE5_MIGRATION_TRACKING_READY_OK"
