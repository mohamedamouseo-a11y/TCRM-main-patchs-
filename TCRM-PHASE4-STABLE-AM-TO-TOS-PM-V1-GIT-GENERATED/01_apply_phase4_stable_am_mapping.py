#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('/var/www/TCRM-MAIN')
SERVICE = ROOT / 'server/services/tosIntegrationService.ts'
BACKFILL = ROOT / 'scripts/backfill-tos-account-manager-bindings.ts'
MARKER = 'TCRM_TOS_PHASE4_STABLE_AM_PM_V1'

if not SERVICE.exists():
    raise SystemExit('PHASE4_ERROR=MISSING_TOS_INTEGRATION_SERVICE')

text = SERVICE.read_text(encoding='utf-8')

if MARKER in text and BACKFILL.exists():
    print('PATCH_STATUS=ALREADY_APPLIED')
    print(f'PATCH_MARKER={MARKER}')
    raise SystemExit(0)

if MARKER in text or BACKFILL.exists():
    raise SystemExit('PHASE4_ERROR=PARTIAL_STATE_DETECTED')

old_imports = '''import { inArray } from "drizzle-orm";
import { themeSettings } from "../../drizzle/schema";'''
new_imports = '''import { and, eq, inArray, isNotNull, isNull } from "drizzle-orm";
import { clients, themeSettings, users } from "../../drizzle/schema";'''
if text.count(old_imports) != 1:
    raise SystemExit(f'PHASE4_ERROR=IMPORT_ANCHOR_COUNT_{text.count(old_imports)}')
text = text.replace(old_imports, new_imports, 1)

old_prefix = 'const SYNC_KEY_PREFIX = "tos_client_sync_";'
new_prefix = '''const SYNC_KEY_PREFIX = "tos_client_sync_";
const TOS_USER_BINDING_PREFIX = "tos_user_binding_";
const STABLE_MANAGER_SYNC_VERSION = "TCRM_TOS_PHASE4_STABLE_AM_PM_V1";'''
if text.count(old_prefix) != 1:
    raise SystemExit(f'PHASE4_ERROR=PREFIX_ANCHOR_COUNT_{text.count(old_prefix)}')
text = text.replace(old_prefix, new_prefix, 1)

old_signature = 'function buildProjectPayloadFromClientProfile(profile: any, handoverBrief: any = null, options: { tosProjectId?: string | null } = {}) {'
new_signature = 'function buildProjectPayloadFromClientProfile(profile: any, handoverBrief: any = null, options: { tosProjectId?: string | null; accountManagerTosUserId?: string | null } = {}) {'
if text.count(old_signature) != 1:
    raise SystemExit(f'PHASE4_ERROR=PAYLOAD_SIGNATURE_ANCHOR_COUNT_{text.count(old_signature)}')
text = text.replace(old_signature, new_signature, 1)

project_owners_line = '  const projectOwners = normalizeTosProjectOwners(handoverBrief?.tosProjectOwners);'
project_owners_replacement = '''  const projectOwners = normalizeTosProjectOwners(handoverBrief?.tosProjectOwners);
  const accountManagerTosUserId = String(options?.accountManagerTosUserId || "").trim() || null;'''
if text.count(project_owners_line) != 1:
    raise SystemExit(f'PHASE4_ERROR=PROJECT_OWNERS_ANCHOR_COUNT_{text.count(project_owners_line)}')
text = text.replace(project_owners_line, project_owners_replacement, 1)

payload_anchor = '''    projectOwnersSyncMode: "ADD_ONLY",
    projectOwners,
    projectName,'''
payload_replacement = '''    projectOwnersSyncMode: "ADD_ONLY",
    projectOwners,
    ...(accountManagerTosUserId ? {
      projectManagerTosUserId: accountManagerTosUserId,
      accountManagerTosUserId,
    } : {}),
    projectName,'''
if text.count(payload_anchor) != 1:
    raise SystemExit(f'PHASE4_ERROR=PAYLOAD_FIELDS_ANCHOR_COUNT_{text.count(payload_anchor)}')
text = text.replace(payload_anchor, payload_replacement, 1)

metadata_anchor = '''      projectOwnersSyncMode: "ADD_ONLY",
      projectOwners,
      verificationVersion: VERIFIED_PROJECT_SYNC_VERSION,'''
metadata_replacement = '''      projectOwnersSyncMode: "ADD_ONLY",
      projectOwners,
      accountManagerTosUserId,
      managerIdentityVersion: accountManagerTosUserId ? STABLE_MANAGER_SYNC_VERSION : null,
      verificationVersion: VERIFIED_PROJECT_SYNC_VERSION,'''
if text.count(metadata_anchor) != 1:
    raise SystemExit(f'PHASE4_ERROR=METADATA_ANCHOR_COUNT_{text.count(metadata_anchor)}')
text = text.replace(metadata_anchor, metadata_replacement, 1)

helper_anchor = '\nfunction buildProjectPayloadFromClientProfile(profile: any, handoverBrief: any = null, options: { tosProjectId?: string | null; accountManagerTosUserId?: string | null } = {}) {'
helpers = r'''

type TosUserBinding = {
  tcrmUserId: number;
  tosUserId: string;
  boundEmail: string | null;
  verifiedAt: string;
  source: "TOS_TEAM_DIRECTORY_EXACT_EMAIL";
};

function tosUserBindingKey(tcrmUserId: number) {
  return `${TOS_USER_BINDING_PREFIX}${tcrmUserId}`;
}

function parseTosUserBinding(value: string | null | undefined): TosUserBinding | null {
  if (!value) return null;
  try {
    const parsed = JSON.parse(value);
    const tcrmUserId = Number(parsed?.tcrmUserId);
    const tosUserId = String(parsed?.tosUserId || "").trim();
    if (!Number.isInteger(tcrmUserId) || tcrmUserId <= 0 || !tosUserId) return null;
    return {
      tcrmUserId,
      tosUserId,
      boundEmail: String(parsed?.boundEmail || "").trim().toLowerCase() || null,
      verifiedAt: String(parsed?.verifiedAt || ""),
      source: "TOS_TEAM_DIRECTORY_EXACT_EMAIL",
    };
  } catch {
    return null;
  }
}

async function getTosUserBinding(tcrmUserId: number) {
  const settings = await getSettingsMap();
  return parseTosUserBinding(settings.get(tosUserBindingKey(tcrmUserId)));
}

async function saveTosUserBinding(binding: TosUserBinding) {
  await upsertSetting(tosUserBindingKey(binding.tcrmUserId), JSON.stringify(binding));
}

function flattenTosTeamDirectory(body: any) {
  const rows: any[] = [];
  for (const department of Array.isArray(body?.departments) ? body.departments : []) {
    for (const member of Array.isArray(department?.members) ? department.members : []) rows.push(member);
  }
  for (const member of Array.isArray(body?.projectMembers) ? body.projectMembers : []) rows.push(member);

  const byId = new Map<string, any>();
  for (const row of rows) {
    const tosUserId = String(row?.tosUserId || "").trim();
    if (!tosUserId || byId.has(tosUserId)) continue;
    byId.set(tosUserId, row);
  }
  return [...byId.values()];
}

async function fetchTosTeamDirectory(apiUrl: string, apiKey: string) {
  const url = new URL(buildOperationalUrl(apiUrl, "team-directory"));
  url.searchParams.set("includeAccountManagement", "true");
  const response = await fetch(url.toString(), {
    method: "GET",
    headers: {
      "X-API-Key": apiKey,
      "Cache-Control": "no-cache, no-store, max-age=0",
      Pragma: "no-cache",
    },
  });
  const text = await response.text();
  let body: any = null;
  try { body = text ? JSON.parse(text) : null; } catch { body = { raw: text }; }
  if (!response.ok) throw new Error(body?.message || body?.error || `TOS team-directory failed with status ${response.status}`);
  return flattenTosTeamDirectory(body);
}

function uniqueTosUserIdByExactEmail(directory: any[], emailValue: unknown) {
  const email = String(emailValue || "").trim().toLowerCase();
  if (!email) return null;
  const ids = [...new Set(directory
    .filter((row) => String(row?.email || "").trim().toLowerCase() === email)
    .map((row) => String(row?.tosUserId || "").trim())
    .filter(Boolean))];
  return ids.length === 1 ? ids[0] : null;
}

async function resolveStableAccountManagerTosUserId(client: any, integration: { apiUrl: string; apiKey: string }) {
  const tcrmUserId = Number(client?.accountManagerId);
  if (!Number.isInteger(tcrmUserId) || tcrmUserId <= 0) return null;

  const existing = await getTosUserBinding(tcrmUserId);
  if (existing?.tosUserId) return existing.tosUserId;

  const rawEmail = String(client?.accountManagerEmail || "").trim().toLowerCase();
  if (!rawEmail) {
    throw new Error(`Stable TOS identity is missing for assigned Account Manager user ${tcrmUserId}; TCRM email is empty`);
  }

  const directory = await fetchTosTeamDirectory(integration.apiUrl, integration.apiKey);
  const tosUserId = uniqueTosUserIdByExactEmail(directory, rawEmail);
  if (!tosUserId) {
    throw new Error(`Stable TOS identity could not be uniquely resolved for assigned Account Manager user ${tcrmUserId}`);
  }

  await saveTosUserBinding({
    tcrmUserId,
    tosUserId,
    boundEmail: rawEmail,
    verifiedAt: new Date().toISOString(),
    source: "TOS_TEAM_DIRECTORY_EXACT_EMAIL",
  });
  return tosUserId;
}

// TCRM_TOS_PHASE4_STABLE_AM_PM_V1
// Bootstrap is exact-email only once; after that TCRM user id -> TOS user id is persistent.
// Names are never identity keys.
export async function backfillTosAccountManagerBindings() {
  const integration = await requireTosIntegration();
  const db = await getDb();
  if (!db) throw new Error("Database is not available");

  const assigned = await db
    .select({ tcrmUserId: users.id, email: users.email })
    .from(clients)
    .innerJoin(users, eq(clients.accountManagerId, users.id))
    .where(and(isNull(clients.deletedAt), isNotNull(clients.accountManagerId)))
    .groupBy(users.id, users.email);

  const directory = await fetchTosTeamDirectory(integration.apiUrl, integration.apiKey);
  const validTosIds = new Set(directory.map((row) => String(row?.tosUserId || "").trim()).filter(Boolean));
  let existingBindings = 0;
  let createdBindings = 0;
  const unresolved: number[] = [];

  for (const row of assigned) {
    const tcrmUserId = Number(row.tcrmUserId);
    const stored = await getTosUserBinding(tcrmUserId);
    if (stored?.tosUserId && validTosIds.has(stored.tosUserId)) {
      existingBindings += 1;
      continue;
    }

    const rawEmail = String(row.email || "").trim().toLowerCase();
    const tosUserId = uniqueTosUserIdByExactEmail(directory, rawEmail);
    if (!tosUserId) {
      unresolved.push(tcrmUserId);
      continue;
    }

    await saveTosUserBinding({
      tcrmUserId,
      tosUserId,
      boundEmail: rawEmail || null,
      verifiedAt: new Date().toISOString(),
      source: "TOS_TEAM_DIRECTORY_EXACT_EMAIL",
    });
    createdBindings += 1;
  }

  return {
    assignedManagers: assigned.length,
    existingBindings,
    createdBindings,
    unresolvedCount: unresolved.length,
  };
}
'''
if text.count(helper_anchor) != 1:
    raise SystemExit(f'PHASE4_ERROR=HELPER_INSERT_ANCHOR_COUNT_{text.count(helper_anchor)}')
text = text.replace(helper_anchor, helpers + helper_anchor, 1)

send_anchor = '''    const { apiUrl, apiKey } = await requireTosIntegration();
    const profile = await getClientProfileById(clientId);
    if (!profile?.client) throw new Error("Client was not found");
    const handoverBrief = await getHandoverBrief(clientId);
    const payload = buildProjectPayloadFromClientProfile(profile, handoverBrief, { tosProjectId: attemptedTosProjectId });'''
send_replacement = '''    const { apiUrl, apiKey } = await requireTosIntegration();
    const profile = await getClientProfileById(clientId);
    if (!profile?.client) throw new Error("Client was not found");
    const handoverBrief = await getHandoverBrief(clientId);
    const accountManagerTosUserId = await resolveStableAccountManagerTosUserId(profile.client, { apiUrl, apiKey });
    const payload = buildProjectPayloadFromClientProfile(profile, handoverBrief, {
      tosProjectId: attemptedTosProjectId,
      accountManagerTosUserId,
    });'''
if text.count(send_anchor) != 1:
    raise SystemExit(f'PHASE4_ERROR=SEND_ANCHOR_COUNT_{text.count(send_anchor)}')
text = text.replace(send_anchor, send_replacement, 1)

SERVICE.write_text(text, encoding='utf-8')

BACKFILL.write_text('''import { backfillTosAccountManagerBindings } from "../server/services/tosIntegrationService";\n\nconst result = await backfillTosAccountManagerBindings();\nconsole.log(`ASSIGNED_MANAGERS=${result.assignedManagers}`);\nconsole.log(`EXISTING_BINDINGS=${result.existingBindings}`);\nconsole.log(`CREATED_BINDINGS=${result.createdBindings}`);\nconsole.log(`UNRESOLVED=${result.unresolvedCount}`);\nif (result.unresolvedCount > 0) process.exit(2);\n''', encoding='utf-8')

print('PATCH_STATUS=APPLIED_TO_WORKTREE')
print(f'PATCH_MARKER={MARKER}')
print('FILES_CHANGED=server/services/tosIntegrationService.ts,scripts/backfill-tos-account-manager-bindings.ts')
print('IDENTITY_BOOTSTRAP=EXACT_EMAIL_ONLY')
print('PERSISTENT_MAPPING=theme_settings:tos_user_binding_<tcrmUserId>')
print('PAYLOAD_FIELDS=projectManagerTosUserId,accountManagerTosUserId')
