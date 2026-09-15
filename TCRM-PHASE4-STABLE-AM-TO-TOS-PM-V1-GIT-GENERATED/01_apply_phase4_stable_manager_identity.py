#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('/var/www/TCRM-MAIN')
SCHEMA = ROOT / 'drizzle/schema.ts'
DB = ROOT / 'server/db.ts'
SERVICE = ROOT / 'server/services/tosIntegrationService.ts'
MIGRATION = ROOT / 'scripts/apply-tcrm-tos-manager-identity-v1-migration.ts'
MARKER = 'TCRM_TOS_PHASE4_STABLE_MANAGER_ID_V1'

for path in (SCHEMA, DB, SERVICE):
    if not path.exists():
        raise SystemExit(f'PHASE4_ERROR=MISSING_{path}')

schema = SCHEMA.read_text(encoding='utf-8')
db = DB.read_text(encoding='utf-8')
service = SERVICE.read_text(encoding='utf-8')

already = (
    'tosUserId: varchar("tos_user_id", { length: 64 }).unique()' in schema
    and 'accountManagerTosUserId: users.tosUserId,' in db
    and MARKER in service
    and MIGRATION.exists()
)
if already:
    print('PATCH_STATUS=ALREADY_APPLIED')
    print(f'PATCH_MARKER={MARKER}')
    raise SystemExit(0)

partial = [
    'tosUserId: varchar("tos_user_id", { length: 64 }).unique()' in schema,
    'accountManagerTosUserId: users.tosUserId,' in db,
    MARKER in service,
    MIGRATION.exists(),
]
if any(partial):
    raise SystemExit('PHASE4_ERROR=PARTIAL_STATE_DETECTED')

# 1) Persist the cross-system identity on the TCRM user, one-to-one with a TOS User.id.
schema_anchor = '\temail: varchar({ length: 320 }),\n\tcentralEmail: varchar({ length: 320 }),'
schema_replacement = '\temail: varchar({ length: 320 }),\n\t// TCRM_TOS_PHASE4_STABLE_MANAGER_ID_V1\n\ttosUserId: varchar("tos_user_id", { length: 64 }).unique(),\n\tcentralEmail: varchar({ length: 320 }),'
if schema.count(schema_anchor) != 1:
    raise SystemExit(f'PHASE4_ERROR=USERS_SCHEMA_ANCHOR_COUNT_{schema.count(schema_anchor)}')
schema = schema.replace(schema_anchor, schema_replacement, 1)

# 2) Surface the persisted stable mapping in getClientProfileById.
db_anchor = '      accountManagerName: users.name,\n      accountManagerEmail: users.email,\n'
db_replacement = '      accountManagerName: users.name,\n      accountManagerEmail: users.email,\n      accountManagerTosUserId: users.tosUserId,\n'
if db.count(db_anchor) != 1:
    raise SystemExit(f'PHASE4_ERROR=DB_PROFILE_ANCHOR_COUNT_{db.count(db_anchor)}')
db = db.replace(db_anchor, db_replacement, 1)

# 3) Allow the sync service to persist a verified TOS id on users.tosUserId.
import_anchor = 'import { inArray } from "drizzle-orm";\nimport { themeSettings } from "../../drizzle/schema";'
import_replacement = 'import { eq, inArray } from "drizzle-orm";\nimport { themeSettings, users } from "../../drizzle/schema";'
if service.count(import_anchor) != 1:
    raise SystemExit(f'PHASE4_ERROR=SERVICE_IMPORT_ANCHOR_COUNT_{service.count(import_anchor)}')
service = service.replace(import_anchor, import_replacement, 1)

require_anchor = '''async function requireTosIntegration() {
  const settings = await getSettingsMap();
  if (settings.get(SETTINGS_KEYS.enabled) !== "1") throw new Error("TOS Integration is disabled");
  const apiUrl = normalizeApiUrl(settings.get(SETTINGS_KEYS.apiUrl) || "");
  const apiKey = decryptSecret(settings.get(SETTINGS_KEYS.apiKey));
  if (!apiKey) throw new Error("TOS API Key is missing");
  return { apiUrl, apiKey };
}
'''
helper = require_anchor + '''
// TCRM_TOS_PHASE4_STABLE_MANAGER_ID_V1
// Bind TCRM users.id -> TOS User.id once, then use the stable TOS id forever.
// Exact email is allowed only as a one-time bootstrap lookup; display-name matching is forbidden.
async function ensureStableAccountManagerTosUserId(profile: any, integration: { apiUrl: string; apiKey: string }) {
  const client = profile?.client ?? profile;
  const existing = String(client?.accountManagerTosUserId || "").trim();
  if (existing) return existing;

  const tcrmUserId = Number(client?.accountManagerId || 0);
  const email = String(client?.accountManagerEmail || "").trim().toLowerCase();
  if (!Number.isInteger(tcrmUserId) || tcrmUserId <= 0 || !email) return null;

  const directoryUrl = new URL(buildOperationalUrl(integration.apiUrl, "team-directory"));
  directoryUrl.searchParams.set("includeAccountManagement", "true");
  const response = await fetch(directoryUrl.toString(), {
    method: "GET",
    headers: {
      "X-API-Key": integration.apiKey,
      "Cache-Control": "no-cache, no-store, max-age=0",
      Pragma: "no-cache",
    },
  });
  const text = await response.text();
  let body: any = null;
  try { body = text ? JSON.parse(text) : null; } catch { body = null; }
  if (!response.ok) throw new Error(body?.message || body?.error || `TOS team-directory lookup failed with status ${response.status}`);

  const members = Array.isArray(body?.departments)
    ? body.departments.flatMap((department: any) => Array.isArray(department?.members) ? department.members : [])
    : [];
  const exactIds = Array.from(new Set(
    members
      .filter((member: any) => String(member?.email || "").trim().toLowerCase() === email)
      .map((member: any) => String(member?.tosUserId || "").trim())
      .filter(Boolean),
  ));

  if (exactIds.length !== 1) {
    throw new Error(`Stable TOS identity is not uniquely resolvable for TCRM account manager ${tcrmUserId}`);
  }

  const tosUserId = exactIds[0];
  const database = await getDb();
  if (!database) throw new Error("Database is not available");

  const [bound] = await database
    .select({ id: users.id })
    .from(users)
    .where(eq(users.tosUserId, tosUserId))
    .limit(1);
  if (bound?.id && Number(bound.id) !== tcrmUserId) {
    throw new Error(`TOS user identity ${tosUserId} is already bound to another TCRM user`);
  }

  await database.update(users).set({ tosUserId }).where(eq(users.id, tcrmUserId));
  client.accountManagerTosUserId = tosUserId;
  return tosUserId;
}
'''
if service.count(require_anchor) != 1:
    raise SystemExit(f'PHASE4_ERROR=REQUIRE_TOS_ANCHOR_COUNT_{service.count(require_anchor)}')
service = service.replace(require_anchor, helper, 1)

# 4) Put the stable TOS user id on the authoritative project payload.
manager_var_anchor = '  const accountManagerName = redactSensitiveText(client.accountManagerName);\n  const accountManagerEmail = redactSensitiveText(client.accountManagerEmail);\n'
manager_var_replacement = '  const accountManagerName = redactSensitiveText(client.accountManagerName);\n  const accountManagerEmail = redactSensitiveText(client.accountManagerEmail);\n  const accountManagerTosUserId = String(client.accountManagerTosUserId || "").trim();\n'
if service.count(manager_var_anchor) != 1:
    raise SystemExit(f'PHASE4_ERROR=MANAGER_VAR_ANCHOR_COUNT_{service.count(manager_var_anchor)}')
service = service.replace(manager_var_anchor, manager_var_replacement, 1)

payload_anchor = '    projectManagerName: accountManagerName,\n    accountManagerName,\n    accountManagerEmail,\n    projectManagerEmail: accountManagerEmail,\n'
payload_replacement = '    projectManagerTosUserId: accountManagerTosUserId || undefined,\n    accountManagerTosUserId: accountManagerTosUserId || undefined,\n    projectManagerName: accountManagerName,\n    accountManagerName,\n    accountManagerEmail,\n    projectManagerEmail: accountManagerEmail,\n'
if service.count(payload_anchor) != 1:
    raise SystemExit(f'PHASE4_ERROR=PAYLOAD_MANAGER_ANCHOR_COUNT_{service.count(payload_anchor)}')
service = service.replace(payload_anchor, payload_replacement, 1)

metadata_anchor = '      accountManagerId: client.accountManagerId ?? null,\n      accountManagerName,\n'
metadata_replacement = '      accountManagerId: client.accountManagerId ?? null,\n      accountManagerTosUserId: accountManagerTosUserId || null,\n      accountManagerName,\n'
if service.count(metadata_anchor) != 1:
    raise SystemExit(f'PHASE4_ERROR=METADATA_MANAGER_ANCHOR_COUNT_{service.count(metadata_anchor)}')
service = service.replace(metadata_anchor, metadata_replacement, 1)

# 5) Resolve/bind the stable identity before every real project delivery.
send_anchor = '''    const { apiUrl, apiKey } = await requireTosIntegration();
    const profile = await getClientProfileById(clientId);
    if (!profile?.client) throw new Error("Client was not found");
    const handoverBrief = await getHandoverBrief(clientId);
    const payload = buildProjectPayloadFromClientProfile(profile, handoverBrief, { tosProjectId: attemptedTosProjectId });
'''
send_replacement = '''    const { apiUrl, apiKey } = await requireTosIntegration();
    const profile = await getClientProfileById(clientId);
    if (!profile?.client) throw new Error("Client was not found");
    await ensureStableAccountManagerTosUserId(profile, { apiUrl, apiKey });
    const handoverBrief = await getHandoverBrief(clientId);
    const payload = buildProjectPayloadFromClientProfile(profile, handoverBrief, { tosProjectId: attemptedTosProjectId });
'''
if service.count(send_anchor) != 1:
    raise SystemExit(f'PHASE4_ERROR=SEND_ANCHOR_COUNT_{service.count(send_anchor)}')
service = service.replace(send_anchor, send_replacement, 1)

SCHEMA.write_text(schema, encoding='utf-8')
DB.write_text(db, encoding='utf-8')
SERVICE.write_text(service, encoding='utf-8')

MIGRATION.write_text('''import { config as dotenvConfig } from "dotenv";
import mysql from "mysql2/promise";

dotenvConfig({ path: process.cwd() + "/.env", override: true });

const MARKER = "TCRM_TOS_PHASE4_STABLE_MANAGER_ID_V1";
const DATABASE_URL = process.env.DATABASE_URL;
if (!DATABASE_URL) throw new Error("DATABASE_URL is required");

async function main() {
  const conn = await mysql.createConnection(DATABASE_URL);
  try {
    const [columns] = await conn.query(
      `SELECT COUNT(*) AS count FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND COLUMN_NAME = 'tos_user_id'`,
    );
    if (Number((columns as any[])[0]?.count || 0) === 0) {
      await conn.query(`ALTER TABLE users ADD COLUMN tos_user_id varchar(64) NULL`);
      console.log("ADDED_COLUMN=users.tos_user_id");
    } else {
      console.log("COLUMN_STATUS=ALREADY_EXISTS");
    }

    const [indexes] = await conn.query(
      `SELECT COUNT(*) AS count FROM information_schema.STATISTICS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND INDEX_NAME = 'uq_users_tos_user_id'`,
    );
    if (Number((indexes as any[])[0]?.count || 0) === 0) {
      await conn.query(`CREATE UNIQUE INDEX uq_users_tos_user_id ON users (tos_user_id)`);
      console.log("ADDED_INDEX=uq_users_tos_user_id");
    } else {
      console.log("INDEX_STATUS=ALREADY_EXISTS");
    }

    console.log(`MIGRATION_MARKER=${MARKER}`);
  } finally {
    await conn.end();
  }
}

main().catch((error) => {
  console.error("PHASE4_MIGRATION_FAILED", error);
  process.exit(1);
});
''', encoding='utf-8')

print('PATCH_STATUS=APPLIED_TO_WORKTREE')
print(f'PATCH_MARKER={MARKER}')
print('FILES_CHANGED=drizzle/schema.ts,server/db.ts,server/services/tosIntegrationService.ts,scripts/apply-tcrm-tos-manager-identity-v1-migration.ts')
print('IDENTITY_POLICY=TOS_USER_ID_ONLY_AFTER_ONE_TIME_EXACT_EMAIL_BOOTSTRAP')
print('DISPLAY_NAME_MATCHING=FORBIDDEN')
