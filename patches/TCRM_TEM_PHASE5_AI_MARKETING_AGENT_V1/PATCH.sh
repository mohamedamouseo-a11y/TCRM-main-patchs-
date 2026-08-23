#!/usr/bin/env bash
set -Eeuo pipefail

MODE="${1:-apply}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${TCRM_TARGET:-/var/www/TCRM-MAIN}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_ROOT="${TEM_PHASE5_BACKUP_ROOT:-/var/backups/tcrm-tem-phase5}"
BACKUP_DIR="$BACKUP_ROOT/$STAMP"
ARCHIVE_SHA256="a89410ee4f7cb2970afcf3bce249629fdc721c1e4a81cc52522d90409c99777b"

AUTO_ROLLBACK_ACTIVE=0
ACTIVE_BACKUP_DIR=""
fail() {
  local message="$*"
  if [[ "$AUTO_ROLLBACK_ACTIVE" == "1" && -n "$ACTIVE_BACKUP_DIR" && -d "$ACTIVE_BACKUP_DIR" ]]; then
    set +e
    TEM_PHASE5_BACKUP_DIR="$ACTIVE_BACKUP_DIR" "$PATCH_DIR/PATCH.sh" rollback >/tmp/tcrm-tem-phase5-auto-rollback.log 2>&1
    cat /tmp/tcrm-tem-phase5-auto-rollback.log >&2
    set -e
  fi
  echo "ERROR=$message" >&2
  exit 1
}
need() { command -v "$1" >/dev/null 2>&1 || fail "missing command: $1"; }

verify_mode() {
  cd "$TARGET"
  local missing=0
  for f in \
    server/tem/temAiPolicy.ts \
    server/tem/temAiRouter.ts \
    server/tem/temAiPolicy.test.ts \
    client/src/pages/BD/TEMAIAgent.tsx \
    drizzle/schema_tem_ai.ts \
    drizzle/migrations/20260823_tem_ai_marketing_agent.sql \
    scripts/apply-tem-ai-phase5-migration.ts
  do
    [[ -f "$f" ]] || { echo "VERIFY_FAIL=missing $f" >&2; missing=1; }
  done
  [[ "$missing" == "0" ]] || exit 1
  grep -q 'ai: temAiRouter' server/tem/temRouter.ts || fail "TEM AI router not registered"
  grep -q '<TEMAIAgent />' client/src/pages/BD/TEMCenter.tsx || fail "TEM AI UI not registered"
  grep -q 'APPROVE TEM AI PROPOSAL' server/tem/temAiPolicy.ts || fail "approval gate missing"
  grep -q 'CREATE TEM DRAFTS' server/tem/temAiPolicy.ts || fail "materialization gate missing"
  grep -q 'TEM_AI_DRAFT_MATERIALIZATION_ENABLED' server/tem/temAiRouter.ts || fail "runtime materialization gate missing"
  if grep -Eq '\bsendEmail\s*\(|/send\b|messenger:consume|mautic:campaigns:trigger|isPublished[[:space:]]*:[[:space:]]*(true|1)' server/tem/temAiRouter.ts; then
    fail "forbidden send/publish/worker capability detected"
  fi
  pnpm exec vitest run server/tem/temAiPolicy.test.ts >/tmp/tcrm-tem-phase5-verify-tests.log 2>&1 || {
    cat /tmp/tcrm-tem-phase5-verify-tests.log >&2
    fail "TEM AI policy tests failed"
  }
  if [[ -n "${DATABASE_URL:-}" ]]; then
    local out
    out="$(pnpm exec tsx scripts/apply-tem-ai-phase5-migration.ts 2>&1 || true)"
    printf '%s\n' "$out"
    grep -q 'TEM_AI_PROPOSALS_PRESENT=YES' <<<"$out" || fail "tem_ai_proposals missing"
    grep -q 'TEM_AI_AUDIT_PRESENT=YES' <<<"$out" || fail "tem_ai_audit_events missing"
  else
    echo "DB_VERIFY=SKIPPED_NO_DATABASE_URL"
  fi
  for runtime_file in /etc/tcrm-tem/tcrm.env /etc/tcrm-tem/tem.env; do
    if [[ -f "$runtime_file" ]] && grep -Eq '^[[:space:]]*TEM_PRODUCTION_ACTIVATION_APPROVED[[:space:]]*=[[:space:]]*(YES|TRUE|1|ON)[[:space:]]*$' "$runtime_file"; then
      fail "production sending is active; Phase 5 expects the pending Phase 4 final-test boundary"
    fi
  done
  echo "AI_SEND_CAPABILITY=NONE"
  echo "HUMAN_APPROVAL_REQUIRED=YES"
  echo "FINAL_MARKER=TCRM_TEM_PHASE5_VERIFY_OK"
}

rollback_mode() {
  local backup="${TEM_PHASE5_BACKUP_DIR:-}"
  if [[ -z "$backup" && -f /tmp/tcrm-tem-phase5-last-backup ]]; then backup="$(cat /tmp/tcrm-tem-phase5-last-backup)"; fi
  [[ -n "$backup" && -d "$backup" ]] || fail "Set TEM_PHASE5_BACKUP_DIR to the APPLY backup directory"
  cd "$TARGET"
  for path in \
    server/tem/temRouter.ts \
    client/src/pages/BD/TEMCenter.tsx \
    server/tem/temAiPolicy.ts \
    server/tem/temAiRouter.ts \
    server/tem/temAiPolicy.test.ts \
    client/src/pages/BD/TEMAIAgent.tsx \
    drizzle/schema_tem_ai.ts \
    drizzle/migrations/20260823_tem_ai_marketing_agent.sql \
    scripts/apply-tem-ai-phase5-migration.ts
  do
    if [[ -e "$backup/$path" ]]; then
      mkdir -p "$(dirname "$path")"
      cp -a "$backup/$path" "$path"
    elif [[ "$path" != "server/tem/temRouter.ts" && "$path" != "client/src/pages/BD/TEMCenter.tsx" ]]; then
      rm -f "$path"
    fi
  done
  echo "DB_TABLES_DROPPED=NO"
  echo "NOTE=additive TEM AI tables are intentionally preserved"
  echo "GITHUB_PUSH=NOT_ATTEMPTED"
  echo "FINAL_MARKER=TCRM_TEM_PHASE5_ROLLBACK_FILES_OK"
}

apply_mode() {
  for cmd in git pnpm node python3 cp mkdir grep sha256sum tar base64; do need "$cmd"; done
  [[ -d "$TARGET/.git" ]] || fail "target is not a Git worktree: $TARGET"
  cd "$TARGET"

  local branch_before head_before
  branch_before="$(git branch --show-current)"
  head_before="$(git rev-parse HEAD)"
  echo "BRANCH_BEFORE=$branch_before"
  echo "HEAD_BEFORE=$head_before"

  [[ -f server/tem/temRouter.ts ]] || fail "TEM router missing"
  [[ -f client/src/pages/BD/TEMCenter.tsx ]] || fail "TEM Center missing"
  [[ -f server/emailMarketing.ts ]] || fail "legacy Email Marketing guard missing"
  [[ -f services/tem-mautic/phase4-activate.sh ]] || fail "Phase 4 activation helper missing"
  [[ -f services/tem-mautic/phase4-disable.sh ]] || fail "Phase 4 disable helper missing"
  grep -q 'TEM_PRIMARY_EMAIL_ENGINE' server/emailMarketing.ts || fail "Phase 4 legacy sender guard missing"
  grep -q 'TEM_PRODUCTION_ACTIVATION_APPROVED' server/tem/temRouter.ts || fail "Phase 4 production gate missing"

  for runtime_file in /etc/tcrm-tem/tcrm.env /etc/tcrm-tem/tem.env; do
    if [[ -f "$runtime_file" ]] && grep -Eq '^[[:space:]]*TEM_PRODUCTION_ACTIVATION_APPROVED[[:space:]]*=[[:space:]]*(YES|TRUE|1|ON)[[:space:]]*$' "$runtime_file"; then
      fail "Phase 5 expects production sending activation to remain disabled until the user's final Phase 4 test"
    fi
  done

  NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=3072}" pnpm build >/tmp/tcrm-tem-phase5-prebuild.log 2>&1 || {
    tail -n 100 /tmp/tcrm-tem-phase5-prebuild.log >&2
    fail "pre-build failed; no Phase 5 mutation performed"
  }
  echo "PREBUILD=PASS"

  mkdir -p "$BACKUP_DIR"
  chmod 0700 "$BACKUP_DIR"
  printf '%s\n' "$branch_before" > "$BACKUP_DIR/branch.txt"
  printf '%s\n' "$head_before" > "$BACKUP_DIR/head.txt"
  git status --porcelain=v1 > "$BACKUP_DIR/git-status-before.txt"

  for path in server/tem/temRouter.ts client/src/pages/BD/TEMCenter.tsx; do
    mkdir -p "$BACKUP_DIR/$(dirname "$path")"
    cp -a "$path" "$BACKUP_DIR/$path"
  done
  for path in \
    server/tem/temAiPolicy.ts \
    server/tem/temAiRouter.ts \
    server/tem/temAiPolicy.test.ts \
    client/src/pages/BD/TEMAIAgent.tsx \
    drizzle/schema_tem_ai.ts \
    drizzle/migrations/20260823_tem_ai_marketing_agent.sql \
    scripts/apply-tem-ai-phase5-migration.ts
  do
    if [[ -e "$path" ]]; then
      mkdir -p "$BACKUP_DIR/$(dirname "$path")"
      cp -a "$path" "$BACKUP_DIR/$path"
    fi
  done
  echo "$BACKUP_DIR" > /tmp/tcrm-tem-phase5-last-backup
  ACTIVE_BACKUP_DIR="$BACKUP_DIR"
  AUTO_ROLLBACK_ACTIVE=1

  local work archive
  work="$(mktemp -d /tmp/tcrm-tem-phase5.XXXXXX)"
  archive="$work/payload.tar.gz"
  trap 'rm -rf "$work"' RETURN

  cat "$PATCH_DIR"/payload.b64.part* > "$work/payload.b64"
  base64 -d "$work/payload.b64" > "$archive"
  echo "$ARCHIVE_SHA256  $archive" | sha256sum -c - >/dev/null || fail "embedded Phase 5 payload checksum mismatch"
  mkdir -p "$work/payload"
  tar -xzf "$archive" -C "$work/payload"

  rollback_on_failure() {
    local rc="$?"
    set +e
    TEM_PHASE5_BACKUP_DIR="$BACKUP_DIR" "$PATCH_DIR/PATCH.sh" rollback >/tmp/tcrm-tem-phase5-auto-rollback.log 2>&1
    cat /tmp/tcrm-tem-phase5-auto-rollback.log >&2
    rm -rf "$work"
    exit "$rc"
  }
  trap rollback_on_failure ERR

  for path in \
    server/tem/temAiPolicy.ts \
    server/tem/temAiRouter.ts \
    server/tem/temAiPolicy.test.ts \
    client/src/pages/BD/TEMAIAgent.tsx \
    drizzle/schema_tem_ai.ts \
    drizzle/migrations/20260823_tem_ai_marketing_agent.sql \
    scripts/apply-tem-ai-phase5-migration.ts
  do
    [[ -f "$work/payload/$path" ]] || fail "embedded payload missing: $path"
    mkdir -p "$(dirname "$path")"
    cp "$work/payload/$path" "$path"
  done

  python3 - <<'PY'
from pathlib import Path
import re

router_path = Path("server/tem/temRouter.ts")
s = router_path.read_text()
if 'from "./temAiRouter"' not in s:
    anchor = 'const MAUTIC_DEFAULT_BASE_URL'
    if anchor not in s:
        raise SystemExit("TEM router import anchor not found")
    s = s.replace(anchor, 'import { temAiRouter } from "./temAiRouter";\n\n' + anchor, 1)
if "ai: temAiRouter" not in s:
    anchor = "export const temRouter = router({"
    if anchor not in s:
        raise SystemExit("TEM router registration anchor not found")
    s = s.replace(anchor, anchor + "\n  ai: temAiRouter,", 1)
router_path.write_text(s)

ui_path = Path("client/src/pages/BD/TEMCenter.tsx")
u = ui_path.read_text()
if 'TEMAIAgent' not in u.split("function numberFmt", 1)[0]:
    anchor = 'import { Activity,'
    idx = u.find(anchor)
    if idx < 0:
        raise SystemExit("TEM UI import anchor not found")
    line_end = u.find("\n", idx)
    if line_end < 0:
        raise SystemExit("TEM UI import line end not found")
    u = u[:line_end+1] + 'import TEMAIAgent from "./TEMAIAgent";\n' + u[line_end+1:]
if 'value="ai"' not in u:
    match = re.search(r'(<TabsTrigger\s+value="automation"[\s\S]*?</TabsTrigger>)', u)
    if not match:
        raise SystemExit("TEM AI tab trigger anchor not found")
    trigger = '\n            <TabsTrigger value="ai">{isRTL ? "وكيل التسويق AI" : "AI Marketing Agent"}</TabsTrigger>'
    u = u[:match.end()] + trigger + u[match.end():]
if '<TEMAIAgent />' not in u:
    anchor = '<TabsContent value="statistics">'
    idx = u.find(anchor)
    if idx < 0:
        raise SystemExit("TEM AI tab content anchor not found")
    u = u[:idx] + '          <TabsContent value="ai"><TEMAIAgent /></TabsContent>\n\n' + u[idx:]
ui_path.write_text(u)
PY

  if grep -Eq '\bsendEmail\s*\(|/send\b|messenger:consume|mautic:campaigns:trigger|isPublished[[:space:]]*:[[:space:]]*(true|1)' server/tem/temAiRouter.ts; then
    fail "Phase 5 safety guard detected forbidden send/publish/worker capability"
  fi

  pnpm exec vitest run server/tem/temAiPolicy.test.ts >/tmp/tcrm-tem-phase5-tests.log 2>&1 || {
    cat /tmp/tcrm-tem-phase5-tests.log >&2
    fail "TEM AI policy tests failed"
  }
  echo "TEM_AI_POLICY_TESTS=PASS"

  NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=3072}" pnpm build >/tmp/tcrm-tem-phase5-build.log 2>&1 || {
    tail -n 120 /tmp/tcrm-tem-phase5-build.log >&2
    fail "post-patch build failed"
  }
  echo "BUILD=PASS"

  if [[ "${TEM_PHASE5_APPLY_DB:-NO}" == "YES" ]]; then
    [[ "${TCRM_DB_BACKUP_VERIFIED:-NO}" == "YES" ]] || fail "TCRM_DB_BACKUP_VERIFIED=YES is required before Phase 5 DB migration"
    pnpm exec tsx scripts/apply-tem-ai-phase5-migration.ts --apply
    echo "DB_MIGRATION=APPLIED"
  else
    fail "DB migration approval missing. Re-run with TCRM_DB_BACKUP_VERIFIED=YES TEM_PHASE5_APPLY_DB=YES"
  fi

  git diff --check
  AUTO_ROLLBACK_ACTIVE=0
  trap - ERR
  rm -rf "$work"
  echo "BACKUP_DIR=$BACKUP_DIR"
  echo "BRANCH_AFTER=$(git branch --show-current)"
  echo "HEAD_AFTER=$(git rev-parse HEAD)"
  echo "GITHUB_PUSH=NOT_ATTEMPTED"
  echo "REAL_EMAIL_SEND=BLOCKED_BY_PHASE5"
  echo "AI_SEND_CAPABILITY=NONE"
  echo "HUMAN_APPROVAL_REQUIRED=YES"
  echo "FINAL_MARKER=TCRM_TEM_PHASE5_AI_MARKETING_AGENT_V1_OK"
}

case "$MODE" in
  apply) apply_mode ;;
  verify) verify_mode ;;
  rollback) rollback_mode ;;
  *) fail "usage: $0 [apply|verify|rollback]" ;;
esac
