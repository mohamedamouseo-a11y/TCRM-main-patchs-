#!/usr/bin/env bash
set -Eeuo pipefail

PATCH_ID="TCRM_TEM_PHASE4_PRODUCTION_ACTIVATION"
TARGET="${TCRM_TARGET:-/var/www/TCRM-MAIN}"
BACKUP_DIR="${TEM_PHASE4_BACKUP_DIR:-/var/tmp/${PATCH_ID}.backup}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

EXPECTED_TEM_ROUTER="b57a9f969b57f25e4c689bad9d071909cee1ae68"
EXPECTED_EMAIL_MARKETING="df6215302141ff729cfe9b7ac83fbbe3e7653109"
EXPECTED_COMPOSE="7099bfda04af074bd78eb962203006c5ce24885e"
EXPECTED_README="6de68196e5a42103d78b99feb6fafbffbadfcb1f"
EXPECTED_MAUTIC_COMMIT="27a76aff64aed8e50f6dd784ea86ec95d45d4616"

log(){ printf '[%s] %s\n' "$PATCH_ID" "$*"; }
die(){ printf '[%s] ERROR: %s\n' "$PATCH_ID" "$*" >&2; exit 1; }
need(){ command -v "$1" >/dev/null 2>&1 || die "required command missing: $1"; }
blob(){ git -C "$TARGET" hash-object "$1"; }

need git
need python3
need pnpm
need docker
need curl
need gzip

[[ -d "$TARGET/.git" ]] || die "target is not a Git worktree: $TARGET"
[[ -f "$TARGET/server/tem/temRouter.ts" ]] || die "TEM router missing"
[[ -f "$TARGET/server/emailMarketing.ts" ]] || die "legacy email marketing source missing"
[[ -f "$TARGET/services/tem-mautic/docker-compose.yml" ]] || die "TEM compose definition missing"
[[ -f "$TARGET/services/tem-mautic/README.md" ]] || die "TEM README missing"
[[ -f "$TARGET/services/tem-mautic/MAUTIC_UPSTREAM.lock" ]] || die "Mautic provenance lock missing"
[[ -d "$TARGET/external/mautic" ]] || die "Mautic runtime source missing at external/mautic"

grep -Fq "COMMIT=${EXPECTED_MAUTIC_COMMIT}" "$TARGET/services/tem-mautic/MAUTIC_UPSTREAM.lock" || die "Mautic lock is not pinned to approved commit"

if grep -Fq "TEM_PHASE4_PRODUCTION_ROUTER" "$TARGET/server/tem/temRouter.ts"; then
  log "phase 4 markers already present; running verifier"
  exec bash "$PATCH_DIR/VERIFY.sh"
fi

[[ "$(blob server/tem/temRouter.ts)" == "$EXPECTED_TEM_ROUTER" ]] || die "TEM router baseline mismatch"
[[ "$(blob server/emailMarketing.ts)" == "$EXPECTED_EMAIL_MARKETING" ]] || die "legacy email marketing baseline mismatch"
[[ "$(blob services/tem-mautic/docker-compose.yml)" == "$EXPECTED_COMPOSE" ]] || die "TEM compose baseline mismatch"
[[ "$(blob services/tem-mautic/README.md)" == "$EXPECTED_README" ]] || die "TEM README baseline mismatch"

if [[ -n "$(git -C "$TARGET" status --porcelain)" ]]; then
  git -C "$TARGET" status --short >&2
  die "target worktree must be clean before applying patch"
fi

log "running pre-apply build"
(cd "$TARGET" && pnpm build)

TYPECHECK_BEFORE_LOG="$(mktemp)"
TYPECHECK_AFTER_LOG="$(mktemp)"
cleanup_logs(){ rm -f "$TYPECHECK_BEFORE_LOG" "$TYPECHECK_AFTER_LOG"; }
trap cleanup_logs EXIT

set +e
(cd "$TARGET" && pnpm check) >"$TYPECHECK_BEFORE_LOG" 2>&1
TYPECHECK_BEFORE_RC=$?
set -e
TYPECHECK_BEFORE_ERRORS=$(grep -cE 'error TS[0-9]+' "$TYPECHECK_BEFORE_LOG" || true)
log "pre-apply typecheck rc=$TYPECHECK_BEFORE_RC errors=$TYPECHECK_BEFORE_ERRORS"

[[ ! -e "$BACKUP_DIR" ]] || die "backup path already exists: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR/server/tem" "$BACKUP_DIR/server" "$BACKUP_DIR/services/tem-mautic"
cp -a "$TARGET/server/tem/temRouter.ts" "$BACKUP_DIR/server/tem/temRouter.ts"
cp -a "$TARGET/server/emailMarketing.ts" "$BACKUP_DIR/server/emailMarketing.ts"
cp -a "$TARGET/services/tem-mautic/docker-compose.yml" "$BACKUP_DIR/services/tem-mautic/docker-compose.yml"
cp -a "$TARGET/services/tem-mautic/README.md" "$BACKUP_DIR/services/tem-mautic/README.md"
printf '%s\n' "$EXPECTED_TEM_ROUTER" > "$BACKUP_DIR/temRouter.blob"
printf '%s\n' "$EXPECTED_EMAIL_MARKETING" > "$BACKUP_DIR/emailMarketing.blob"
printf '%s\n' "$EXPECTED_COMPOSE" > "$BACKUP_DIR/compose.blob"
printf '%s\n' "$EXPECTED_README" > "$BACKUP_DIR/readme.blob"

rollback_on_error(){
  rc=$?
  if [[ $rc -ne 0 ]]; then
    log "apply failed; restoring source backup"
    cp -a "$BACKUP_DIR/server/tem/temRouter.ts" "$TARGET/server/tem/temRouter.ts" || true
    cp -a "$BACKUP_DIR/server/emailMarketing.ts" "$TARGET/server/emailMarketing.ts" || true
    cp -a "$BACKUP_DIR/services/tem-mautic/docker-compose.yml" "$TARGET/services/tem-mautic/docker-compose.yml" || true
    cp -a "$BACKUP_DIR/services/tem-mautic/README.md" "$TARGET/services/tem-mautic/README.md" || true
    rm -f "$TARGET/services/tem-mautic/phase4-activate.sh" "$TARGET/services/tem-mautic/phase4-disable.sh" || true
  fi
  exit $rc
}
trap rollback_on_error ERR

TARGET="$TARGET" python3 <<'PY'
from pathlib import Path
import os

root = Path(os.environ["TARGET"])

def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)

# --- TEM router production controls ---
p = root / "server/tem/temRouter.ts"
s = p.read_text()

helper_anchor = "function mauticConfig() {\n"
helper_block = r'''// TEM_PHASE4_PRODUCTION_ROUTER
function readRuntimeEnvFileAt(filePath: string): Record<string, string> {
  if (!existsSync(filePath)) return {};
  try {
    return readFileSync(filePath, "utf8").split(/\r?\n/).reduce<Record<string, string>>((values, line) => {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#")) return values;
      const separator = trimmed.indexOf("=");
      if (separator <= 0) return values;
      values[trimmed.slice(0, separator).trim()] = trimmed.slice(separator + 1).trim().replace(/^(["'])(.*)\1$/, "$2");
      return values;
    }, {});
  } catch {
    return {};
  }
}

function temProductionConfig() {
  const tcrmEnv = readRuntimeEnvFile();
  const temEnvPath = process.env.TEM_MAUTIC_RUNTIME_ENV_FILE || "/etc/tcrm-tem/tem.env";
  const temEnv = readRuntimeEnvFileAt(temEnvPath);
  const value = (key: string) => String(process.env[key] ?? tcrmEnv[key] ?? temEnv[key] ?? "").trim();
  const yes = (key: string) => value(key).toUpperCase() === "YES";
  const mailerDsn = value("MAUTIC_MAILER_DSN");
  const controlledRecipient = normalizeEmail(value("TEM_CONTROLLED_TEST_RECIPIENT"));
  return {
    activationApproved: yes("TEM_PRODUCTION_ACTIVATION_APPROVED"),
    contactSyncApproved: yes("TEM_PHASE4_CONTACT_SYNC_APPROVED"),
    suppressionSyncApproved: yes("TEM_PHASE4_SUPPRESSION_SYNC_APPROVED"),
    controlledTestPassed: yes("TEM_CONTROLLED_TEST_PASSED"),
    bulkSendApproved: yes("TEM_BULK_SEND_APPROVED"),
    primaryEngine: yes("TEM_PRIMARY_EMAIL_ENGINE"),
    mailerConfigured: Boolean(mailerDsn && mailerDsn !== "null://null"),
    controlledRecipient,
    controlledRecipientConfigured: Boolean(controlledRecipient),
  };
}

function requirePhase4Approval(condition: boolean, message: string): void {
  if (!condition) throw new TRPCError({ code: "PRECONDITION_FAILED", message });
}

'''
s = replace_once(s, helper_anchor, helper_block + helper_anchor, "tem helper anchor")

sync_anchor = "export const temRouter = router({\n"
sync_block = r'''async function legacySuppressionEmails(limit: number, offset: number): Promise<string[]> {
  const db = await getDb();
  if (!db) throw new TRPCError({ code: "INTERNAL_SERVER_ERROR", message: "Database unavailable" });
  const result: any = await db.execute(sql`
    SELECT email
    FROM email_marketing_suppression_list
    WHERE email IS NOT NULL AND email <> ''
    ORDER BY id ASC
    LIMIT ${limit} OFFSET ${offset}
  `);
  return ((result?.[0] ?? []) as Array<{ email?: string }>).map((row) => normalizeEmail(row.email)).filter(Boolean);
}

async function ensureMauticContactForEmail(email: string): Promise<{ id: number; created: boolean }> {
  const lookup = await mauticRequest(`contacts?search=${encodeURIComponent(email)}&limit=10&minimal=true`);
  const candidate = collection(lookup, "contacts").find((item: any) => getContactEmail(item) === email);
  if (candidate?.id) return { id: Number(candidate.id), created: false };
  const body = await mauticRequest("contacts/new", {
    method: "POST",
    body: JSON.stringify({ email, tags: ["tcrm-legacy-suppression"], overwriteWithBlank: false }),
  });
  const created = body?.contact ?? body;
  const id = Number(created?.id ?? 0);
  if (!id) throw new TRPCError({ code: "BAD_GATEWAY", message: "Mautic did not return a contact ID for suppression migration" });
  return { id, created: true };
}

async function syncLegacySuppressionEmail(email: string) {
  const normalized = normalizeEmail(email);
  if (!normalized) return { email: null, skipped: true, reason: "invalid-email" };
  const contact = await ensureMauticContactForEmail(normalized);
  const current = await mauticRequest(`contacts/${contact.id}`);
  const entity = current?.contact ?? current;
  const alreadyDnc = Array.isArray(entity?.doNotContact) && entity.doNotContact.some((item: any) => String(item?.channel ?? "").toLowerCase() === "email");
  if (!alreadyDnc) {
    await mauticRequest(`contacts/${contact.id}/dnc/email/add`, {
      method: "POST",
      body: JSON.stringify({ reason: 3, comments: "Migrated from TCRM legacy Email Marketing suppression list" }),
    });
  }
  return { email: normalized, mauticId: contact.id, created: contact.created, alreadyDnc, dncApplied: !alreadyDnc };
}

'''
s = replace_once(s, sync_anchor, sync_block + sync_anchor, "tem sync helper anchor")

old_health = '''  health: temAccessProcedure.query(async () => {\n    await mauticRequest("contacts?limit=1&minimal=true");\n    return { ok: true, engine: "Mautic", version: "7.1.3", emailSending: "blocked", workers: "disabled" };\n  }),\n'''
new_health = '''  health: temAccessProcedure.query(async () => {\n    await mauticRequest("contacts?limit=1&minimal=true");\n    const production = temProductionConfig();\n    return {\n      ok: true,\n      engine: "Mautic",\n      version: "7.1.3",\n      emailSending: !production.mailerConfigured ? "blocked" : production.bulkSendApproved ? "production-approved" : "controlled-test-only",\n      workers: production.bulkSendApproved && production.controlledTestPassed ? "production-approved" : "disabled",\n      production: {\n        activationApproved: production.activationApproved,\n        contactSyncApproved: production.contactSyncApproved,\n        suppressionSyncApproved: production.suppressionSyncApproved,\n        controlledTestPassed: production.controlledTestPassed,\n        bulkSendApproved: production.bulkSendApproved,\n        primaryEngine: production.primaryEngine,\n        mailerConfigured: production.mailerConfigured,\n        controlledRecipientConfigured: production.controlledRecipientConfigured,\n      },\n    };\n  }),\n'''
s = replace_once(s, old_health, new_health, "tem health block")

production_anchor = "  statistics: router({\n"
production_block = r'''  production: router({
    status: temAccessProcedure.query(async () => {
      const production = temProductionConfig();
      await mauticRequest("contacts?limit=1&minimal=true");
      return {
        activationApproved: production.activationApproved,
        contactSyncApproved: production.contactSyncApproved,
        suppressionSyncApproved: production.suppressionSyncApproved,
        controlledTestPassed: production.controlledTestPassed,
        bulkSendApproved: production.bulkSendApproved,
        primaryEngine: production.primaryEngine,
        mailerConfigured: production.mailerConfigured,
        controlledRecipientConfigured: production.controlledRecipientConfigured,
      };
    }),

    syncContacts: temAccessProcedure.input(z.object({
      limit: z.number().int().min(1).max(100).default(25),
      offset: z.number().int().min(0).default(0),
      execute: z.literal(true),
    })).mutation(async ({ input }) => {
      const production = temProductionConfig();
      requirePhase4Approval(production.activationApproved, "TEM Phase 4 production activation is not approved");
      requirePhase4Approval(production.contactSyncApproved, "TEM Phase 4 contact sync is not approved");
      const contacts = await sourceContacts({ limit: input.limit, offset: input.offset });
      const results: any[] = [];
      for (const contact of contacts) {
        if (!normalizeEmail(contact?.email)) {
          results.push({ sourceId: Number(contact?.id ?? 0), skipped: true, reason: "missing-email" });
          continue;
        }
        try {
          results.push(await syncBdContact(Number(contact.id)));
        } catch (error: any) {
          results.push({ sourceId: Number(contact?.id ?? 0), error: String(error?.message ?? "sync failed").slice(0, 300) });
        }
      }
      return {
        requested: contacts.length,
        succeeded: results.filter((item) => item?.mauticId && !item?.error).length,
        failed: results.filter((item) => item?.error).length,
        skipped: results.filter((item) => item?.skipped).length,
        results,
      };
    }),

    syncSuppression: temAccessProcedure.input(z.object({
      limit: z.number().int().min(1).max(100).default(25),
      offset: z.number().int().min(0).default(0),
      execute: z.literal(true),
    })).mutation(async ({ input }) => {
      const production = temProductionConfig();
      requirePhase4Approval(production.activationApproved, "TEM Phase 4 production activation is not approved");
      requirePhase4Approval(production.suppressionSyncApproved, "TEM Phase 4 suppression sync is not approved");
      const emails = await legacySuppressionEmails(input.limit, input.offset);
      const results: any[] = [];
      for (const email of emails) {
        try {
          results.push(await syncLegacySuppressionEmail(email));
        } catch (error: any) {
          results.push({ email, error: String(error?.message ?? "suppression sync failed").slice(0, 300) });
        }
      }
      return {
        requested: emails.length,
        succeeded: results.filter((item) => item?.mauticId && !item?.error).length,
        failed: results.filter((item) => item?.error).length,
        results,
      };
    }),

    sendControlledTest: temAccessProcedure.input(z.object({
      emailId: z.number().int().positive(),
      contactId: z.number().int().positive(),
      execute: z.literal(true),
    })).mutation(async ({ input }) => {
      const production = temProductionConfig();
      requirePhase4Approval(production.activationApproved, "TEM Phase 4 production activation is not approved");
      requirePhase4Approval(production.mailerConfigured, "TEM live mail transport is not configured");
      requirePhase4Approval(production.controlledRecipientConfigured, "TEM controlled test recipient is not configured");
      requirePhase4Approval(!production.bulkSendApproved, "Controlled test endpoint is disabled after bulk sending approval");

      const [contactBody, emailBody] = await Promise.all([
        mauticRequest(`contacts/${input.contactId}`),
        mauticRequest(`emails/${input.emailId}`),
      ]);
      const contact = contactBody?.contact ?? contactBody;
      const emailEntity = emailBody?.email ?? emailBody;
      const contactEmail = getContactEmail(contact);
      requirePhase4Approval(contactEmail === production.controlledRecipient, "Controlled test contact does not match the approved recipient");
      const testName = String(emailEntity?.name ?? "");
      requirePhase4Approval(/^\s*(TEM TEST|\[TEM TEST\])/i.test(testName), "Controlled test email name must start with 'TEM TEST' or '[TEM TEST]'");

      const result = await mauticRequest(`emails/${input.emailId}/contact/${input.contactId}/send`, { method: "POST", body: JSON.stringify({}) });
      return { success: Boolean(result?.success ?? true), emailId: input.emailId, contactId: input.contactId };
    }),
  }),

'''
s = replace_once(s, production_anchor, production_block + production_anchor, "tem production router anchor")
p.write_text(s)

# --- Disable legacy campaign sending when TEM is primary ---
p = root / "server/emailMarketing.ts"
s = p.read_text()
import_anchor = 'import { sendEmail } from "./email";\n'
import_new = import_anchor + 'import { existsSync, readFileSync } from "node:fs";\n'
s = replace_once(s, import_anchor, import_new, "legacy fs import")
helper_anchor = 'export type EmailMarketingAudienceSource = "clients" | "leads" | "manual";\n'
legacy_helper = r'''// TEM_PHASE4_LEGACY_SEND_GUARD
function temRuntimeFlag(name: string): string {
  const direct = String(process.env[name] ?? "").trim();
  if (direct) return direct;
  const filePath = process.env.TEM_MAUTIC_ENV_FILE || "/etc/tcrm-tem/tcrm.env";
  if (!existsSync(filePath)) return "";
  try {
    const line = readFileSync(filePath, "utf8").split(/\r?\n/).find((entry) => entry.trim().startsWith(`${name}=`));
    if (!line) return "";
    const value = line.slice(line.indexOf("=") + 1).trim();
    return value.replace(/^(["'])(.*)\1$/, "$2");
  } catch {
    return "";
  }
}

function isYes(value: string): boolean {
  return value.trim().toUpperCase() === "YES";
}

'''
s = replace_once(s, helper_anchor, legacy_helper + helper_anchor, "legacy helper anchor")
send_anchor = 'export async function sendEmailMarketingCampaign(campaignId: number, opts: { baseUrl: string }) {\n'
send_guard = send_anchor + '''  if (isYes(temRuntimeFlag("TEM_PRIMARY_EMAIL_ENGINE")) && !isYes(temRuntimeFlag("LEGACY_EMAIL_MARKETING_SEND_OVERRIDE"))) {\n    throw new Error("Legacy Email Marketing sending is disabled because TEM is the primary marketing engine");\n  }\n'''
s = replace_once(s, send_anchor, send_guard, "legacy send anchor")
p.write_text(s)

# --- Runtime compose production profile ---
p = root / "services/tem-mautic/docker-compose.yml"
s = p.read_text()
count = s.count("      MAUTIC_MAILER_DSN: null://null")
if count != 2:
    raise SystemExit(f"compose mailer anchors: expected 2, found {count}")
s = s.replace("      MAUTIC_MAILER_DSN: null://null", "      MAUTIC_MAILER_DSN: ${MAUTIC_MAILER_DSN:-null://null}")
s = replace_once(s, '    profiles: ["workers"]\n', '    profiles: ["workers", "production"]\n', "worker profile")
vol_anchor = "\nvolumes:\n"
scheduler = r'''
  scheduler:
    profiles: ["production"]
    image: tem-mautic:7.1.3-27a76aff
    restart: unless-stopped
    depends_on:
      app:
        condition: service_healthy
    environment:
      APP_ENV: prod
      MAUTIC_MAILER_DSN: ${MAUTIC_MAILER_DSN:-null://null}
      TEM_BULK_SEND_APPROVED: ${TEM_BULK_SEND_APPROVED:-NO}
    command:
      - /bin/sh
      - -lc
      - |
        set -eu
        while true; do
          php bin/console mautic:segments:update --batch-limit=100 --max-contacts=1000
          sleep 300
          php bin/console mautic:campaigns:update --batch-limit=100 --max-contacts=1000
          sleep 300
          php bin/console mautic:campaigns:trigger --batch-limit=50 --max-events=500
          sleep 300
          php bin/console mautic:messages:send
          if [ "$${TEM_BULK_SEND_APPROVED:-NO}" = "YES" ]; then
            php bin/console mautic:broadcasts:send
          fi
          sleep 300
        done
    volumes:
      - tem_mautic_var:/var/www/html/var
      - tem_mautic_media:/var/www/html/media
      - tem_mautic_config:/var/www/html/app/config
    networks:
      - tem_internal

'''
s = replace_once(s, vol_anchor, scheduler + vol_anchor, "compose volumes anchor")
p.write_text(s)

# --- README production runbook ---
p = root / "services/tem-mautic/README.md"
s = p.read_text()
append = r'''

## Phase 4 production activation

Phase 4 keeps production sending fail-closed. `MAUTIC_MAILER_DSN` now comes only from runtime configuration and defaults to `null://null`. Use `phase4-activate.sh prepare` to stage a real provider for one controlled recipient while worker/scheduler processing remains stopped. The TEM API will only allow the controlled test when the contact email exactly matches `TEM_CONTROLLED_TEST_RECIPIENT` and the test email name begins with `TEM TEST` or `[TEM TEST]`.

Legacy suppression migration is performed through Mautic's Do-Not-Contact API and is bounded to 100 records per request. BD contact batch synchronization is likewise bounded and remains idempotent through `tem_entity_mappings` and email matching.

Only after the controlled test has been verified should runtime configuration set `TEM_CONTROLLED_TEST_PASSED=YES` and `TEM_BULK_SEND_APPROVED=YES`, then run `phase4-activate.sh enable`. The production scheduler uses Mautic's required segment/campaign/message console commands and only invokes scheduled broadcast sending when the bulk approval flag is explicitly `YES`.

When `TEM_PRIMARY_EMAIL_ENGINE=YES`, the legacy TCRM campaign sender fails closed. Historical legacy tables, tracking, unsubscribe handling and data remain available; no destructive migration is performed.
'''
if "## Phase 4 production activation" in s:
    raise SystemExit("README Phase 4 section already exists")
p.write_text(s.rstrip() + append + "\n")
PY

cat > "$TARGET/services/tem-mautic/phase4-activate.sh" <<'SH'
#!/usr/bin/env bash
set -Eeuo pipefail

MODE="${1:-status}"
TARGET="${TCRM_TARGET:-/var/www/TCRM-MAIN}"
TRACKED_DIR="$TARGET/services/tem-mautic"
RUNTIME_DIR="${TEM_RUNTIME_DIR:-/var/lib/tcrm-tem}"
TEM_ENV_FILE="${TEM_MAUTIC_RUNTIME_ENV_FILE:-/etc/tcrm-tem/tem.env}"
TCRM_ENV_FILE="${TEM_TCRM_RUNTIME_ENV_FILE:-/etc/tcrm-tem/tcrm.env}"
LIVE_COMPOSE="$RUNTIME_DIR/docker-compose.yml"
BACKUP_DIR="$RUNTIME_DIR/phase4-backup"

log(){ printf '[TEM_PHASE4] %s\n' "$*"; }
die(){ printf '[TEM_PHASE4] ERROR: %s\n' "$*" >&2; exit 1; }

[[ "$MODE" =~ ^(status|prepare|enable)$ ]] || die "usage: $0 [status|prepare|enable]"
[[ -f "$TRACKED_DIR/docker-compose.yml" ]] || die "tracked compose file missing"
[[ -f "$TEM_ENV_FILE" ]] || die "TEM runtime env missing: $TEM_ENV_FILE"
[[ -f "$TCRM_ENV_FILE" ]] || die "TCRM TEM runtime env missing: $TCRM_ENV_FILE"
mkdir -p "$RUNTIME_DIR" "$BACKUP_DIR"

read_env(){
  local key="$1" file="$2" line
  line=$(grep -m1 -E "^[[:space:]]*${key}=" "$file" 2>/dev/null || true)
  [[ -n "$line" ]] || return 0
  printf '%s' "${line#*=}" | sed -E "s/^[[:space:]]*['\"]?(.*?)['\"]?[[:space:]]*$/\1/"
}
read_any(){
  local key="$1" value
  value="$(read_env "$key" "$TCRM_ENV_FILE")"
  [[ -n "$value" ]] || value="$(read_env "$key" "$TEM_ENV_FILE")"
  printf '%s' "$value"
}
yes(){ [[ "$(read_any "$1" | tr '[:lower:]' '[:upper:]')" == "YES" ]]; }

MAILER_DSN="$(read_env MAUTIC_MAILER_DSN "$TEM_ENV_FILE")"
CONTROLLED_RECIPIENT="$(read_any TEM_CONTROLLED_TEST_RECIPIENT)"

if [[ "$MODE" == "status" ]]; then
  yes TEM_PRODUCTION_ACTIVATION_APPROVED && echo "ACTIVATION_APPROVED=YES" || echo "ACTIVATION_APPROVED=NO"
  [[ -n "$MAILER_DSN" && "$MAILER_DSN" != "null://null" ]] && echo "MAILER_CONFIGURED=YES" || echo "MAILER_CONFIGURED=NO"
  [[ "$CONTROLLED_RECIPIENT" == *@*.* ]] && echo "CONTROLLED_RECIPIENT_CONFIGURED=YES" || echo "CONTROLLED_RECIPIENT_CONFIGURED=NO"
  yes TEM_CONTROLLED_TEST_PASSED && echo "CONTROLLED_TEST_PASSED=YES" || echo "CONTROLLED_TEST_PASSED=NO"
  yes TEM_BULK_SEND_APPROVED && echo "BULK_SEND_APPROVED=YES" || echo "BULK_SEND_APPROVED=NO"
  yes TEM_PRIMARY_EMAIL_ENGINE && echo "TEM_PRIMARY_EMAIL_ENGINE=YES" || echo "TEM_PRIMARY_EMAIL_ENGINE=NO"
  exit 0
fi

yes TEM_PRODUCTION_ACTIVATION_APPROVED || die "TEM_PRODUCTION_ACTIVATION_APPROVED must be YES"
yes TEM_PRIMARY_EMAIL_ENGINE || die "TEM_PRIMARY_EMAIL_ENGINE must be YES"
[[ -n "$MAILER_DSN" && "$MAILER_DSN" != "null://null" ]] || die "MAUTIC_MAILER_DSN must be configured to a live provider"
[[ "$CONTROLLED_RECIPIENT" == *@*.* ]] || die "TEM_CONTROLLED_TEST_RECIPIENT must be configured"

if [[ -f "$LIVE_COMPOSE" && ! -f "$BACKUP_DIR/docker-compose.pre-phase4.yml" ]]; then
  cp -a "$LIVE_COMPOSE" "$BACKUP_DIR/docker-compose.pre-phase4.yml"
fi
cp -a "$TRACKED_DIR/docker-compose.yml" "$LIVE_COMPOSE"

docker compose -f "$LIVE_COMPOSE" --env-file "$TEM_ENV_FILE" config -q

if [[ "$MODE" == "prepare" ]]; then
  STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
  DB_BACKUP="$BACKUP_DIR/tem_mautic_${STAMP}.sql.gz"
  log "creating Mautic DB backup"
  docker compose -f "$LIVE_COMPOSE" --env-file "$TEM_ENV_FILE" exec -T db sh -lc 'exec mysqldump --single-transaction --quick -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"' | gzip -c > "$DB_BACKUP"
  [[ -s "$DB_BACKUP" ]] || die "Mautic DB backup is empty"

  log "stopping production worker/scheduler before controlled test"
  docker compose -f "$LIVE_COMPOSE" --env-file "$TEM_ENV_FILE" --profile production stop worker scheduler >/dev/null 2>&1 || true
  log "recreating Mautic app with configured transport"
  docker compose -f "$LIVE_COMPOSE" --env-file "$TEM_ENV_FILE" up -d db app

  for _ in $(seq 1 30); do
    if curl -fsS http://127.0.0.1:8089/ >/dev/null; then
      echo "FINAL_MARKER=TCRM_TEM_PHASE4_CONTROLLED_TEST_READY"
      exit 0
    fi
    sleep 4
  done
  die "Mautic app did not become healthy"
fi

yes TEM_CONTROLLED_TEST_PASSED || die "TEM_CONTROLLED_TEST_PASSED must be YES before production processing"
yes TEM_BULK_SEND_APPROVED || die "TEM_BULK_SEND_APPROVED must be YES before production processing"
log "starting production worker and scheduler"
docker compose -f "$LIVE_COMPOSE" --env-file "$TEM_ENV_FILE" --profile production up -d worker scheduler

docker compose -f "$LIVE_COMPOSE" --env-file "$TEM_ENV_FILE" --profile production ps
curl -fsS http://127.0.0.1:8089/ >/dev/null || die "Mautic health check failed after production enable"
echo "FINAL_MARKER=TCRM_TEM_PHASE4_PRODUCTION_ENABLED_OK"
SH

cat > "$TARGET/services/tem-mautic/phase4-disable.sh" <<'SH'
#!/usr/bin/env bash
set -Eeuo pipefail

TARGET="${TCRM_TARGET:-/var/www/TCRM-MAIN}"
RUNTIME_DIR="${TEM_RUNTIME_DIR:-/var/lib/tcrm-tem}"
TEM_ENV_FILE="${TEM_MAUTIC_RUNTIME_ENV_FILE:-/etc/tcrm-tem/tem.env}"
LIVE_COMPOSE="$RUNTIME_DIR/docker-compose.yml"
BACKUP_COMPOSE="$RUNTIME_DIR/phase4-backup/docker-compose.pre-phase4.yml"

[[ -f "$LIVE_COMPOSE" ]] || { echo "TEM runtime compose not found" >&2; exit 1; }
[[ -f "$TEM_ENV_FILE" ]] || { echo "TEM runtime env not found" >&2; exit 1; }

docker compose -f "$LIVE_COMPOSE" --env-file "$TEM_ENV_FILE" --profile production stop worker scheduler >/dev/null 2>&1 || true
if [[ -f "$BACKUP_COMPOSE" ]]; then
  cp -a "$BACKUP_COMPOSE" "$LIVE_COMPOSE"
  docker compose -f "$LIVE_COMPOSE" --env-file "$TEM_ENV_FILE" config -q
  docker compose -f "$LIVE_COMPOSE" --env-file "$TEM_ENV_FILE" up -d app
fi
curl -fsS http://127.0.0.1:8089/ >/dev/null || { echo "Mautic app health failed after disable" >&2; exit 1; }
echo "FINAL_MARKER=TCRM_TEM_PHASE4_PRODUCTION_DISABLED_OK"
SH

chmod 0755 "$TARGET/services/tem-mautic/phase4-activate.sh" "$TARGET/services/tem-mautic/phase4-disable.sh"

log "running post-apply typecheck non-regression check"
set +e
(cd "$TARGET" && pnpm check) >"$TYPECHECK_AFTER_LOG" 2>&1
TYPECHECK_AFTER_RC=$?
set -e
TYPECHECK_AFTER_ERRORS=$(grep -cE 'error TS[0-9]+' "$TYPECHECK_AFTER_LOG" || true)
log "post-apply typecheck rc=$TYPECHECK_AFTER_RC errors=$TYPECHECK_AFTER_ERRORS"
if [[ "$TYPECHECK_BEFORE_RC" -eq 0 && "$TYPECHECK_AFTER_RC" -ne 0 ]]; then
  cat "$TYPECHECK_AFTER_LOG" >&2
  die "typecheck regressed from pass to fail"
fi
if (( TYPECHECK_AFTER_ERRORS > TYPECHECK_BEFORE_ERRORS )); then
  cat "$TYPECHECK_AFTER_LOG" >&2
  die "typecheck error count increased"
fi

log "running post-apply build"
(cd "$TARGET" && pnpm build)
(cd "$TARGET" && git diff --check)

if [[ -f /etc/tcrm-tem/tem.env ]]; then
  docker compose -f "$TARGET/services/tem-mautic/docker-compose.yml" --env-file /etc/tcrm-tem/tem.env config -q
  log "compose validation passed"
else
  log "compose validation skipped: /etc/tcrm-tem/tem.env not present"
fi

allowed='^(server/tem/temRouter\.ts|server/emailMarketing\.ts|services/tem-mautic/docker-compose\.yml|services/tem-mautic/README\.md|services/tem-mautic/phase4-activate\.sh|services/tem-mautic/phase4-disable\.sh)$'
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  path="${line:3}"
  [[ "$path" =~ $allowed ]] || die "unexpected changed path: $path"
done < <(git -C "$TARGET" status --porcelain)

trap - ERR
log "patch applied; production sending remains gated until phase4-activate.sh is run with approved runtime flags"
echo "FINAL_MARKER=TCRM_TEM_PHASE4_PATCH_APPLIED_OK"
