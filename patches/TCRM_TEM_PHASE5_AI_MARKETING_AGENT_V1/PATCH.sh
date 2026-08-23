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

  cat > "$work/payload.b64" <<'TEM_PHASE5_BUNDLE'
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[... ELLIPSIZATION ...]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
TEM_PHASE5_BUNDLE
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
