#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('/var/www/TCRM-MAIN')
SERVICE = ROOT / 'server/services/tosIntegrationService.ts'
MARKER = 'TCRM_TOS_PHASE6_NONBLOCKING_MANAGER_RESOLUTION_V1'

if not SERVICE.exists():
    raise SystemExit('PHASE6_ERROR=MISSING_TOS_INTEGRATION_SERVICE')

text = SERVICE.read_text(encoding='utf-8')

if MARKER in text:
    print('PATCH_STATUS=ALREADY_APPLIED')
    print(f'PATCH_MARKER={MARKER}')
    raise SystemExit(0)

old = '''async function resolveStableAccountManagerTosUserId(client: any, integration: { apiUrl: string; apiKey: string }) {
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
'''

new = '''// TCRM_TOS_PHASE6_NONBLOCKING_MANAGER_RESOLUTION_V1
// Account Manager identity enrichment must never block the authoritative project/status sync.
// If a stable TOS identity is unavailable, TOS receives the project update without PM identity
// and preserves the existing Project Manager. Exact-email bootstrap remains the only auto-binding path.
async function resolveStableAccountManagerTosUserId(client: any, integration: { apiUrl: string; apiKey: string }) {
  const tcrmUserId = Number(client?.accountManagerId);
  if (!Number.isInteger(tcrmUserId) || tcrmUserId <= 0) return null;

  const existing = await getTosUserBinding(tcrmUserId);
  if (existing?.tosUserId) return existing.tosUserId;

  const rawEmail = String(client?.accountManagerEmail || "").trim().toLowerCase();
  if (!rawEmail) {
    console.warn(`[TOS Integration] Account Manager ${tcrmUserId} has no stable TOS binding; continuing project sync without PM update`);
    return null;
  }

  let directory: any[] = [];
  try {
    directory = await fetchTosTeamDirectory(integration.apiUrl, integration.apiKey);
  } catch (error: any) {
    console.warn(
      `[TOS Integration] Stable TOS identity lookup failed for Account Manager ${tcrmUserId}; continuing project sync without PM update: ${error?.message || "lookup failed"}`,
    );
    return null;
  }

  const tosUserId = uniqueTosUserIdByExactEmail(directory, rawEmail);
  if (!tosUserId) {
    console.warn(`[TOS Integration] No unique stable TOS identity for Account Manager ${tcrmUserId}; continuing project sync without PM update`);
    return null;
  }

  try {
    await saveTosUserBinding({
      tcrmUserId,
      tosUserId,
      boundEmail: rawEmail,
      verifiedAt: new Date().toISOString(),
      source: "TOS_TEAM_DIRECTORY_EXACT_EMAIL",
    });
  } catch (error: any) {
    // Identity was resolved from the authoritative TOS directory. A binding persistence
    // failure must not block this project/status delivery; a later sync can persist it.
    console.warn(
      `[TOS Integration] Stable TOS identity binding persistence failed for Account Manager ${tcrmUserId}; continuing current sync: ${error?.message || "binding save failed"}`,
    );
  }

  return tosUserId;
}
'''

count = text.count(old)
if count != 1:
    raise SystemExit(f'PHASE6_ERROR=RESOLVER_ANCHOR_COUNT_{count}')

text = text.replace(old, new, 1)
SERVICE.write_text(text, encoding='utf-8')

print('PATCH_STATUS=APPLIED_TO_WORKTREE')
print(f'PATCH_MARKER={MARKER}')
print('FILES_CHANGED=server/services/tosIntegrationService.ts')
print('UNRESOLVED_MANAGER_BEHAVIOR=CONTINUE_PROJECT_SYNC')
print('AUTO_BINDING=EXACT_EMAIL_ONLY')
print('EXISTING_PM_BEHAVIOR=PRESERVED_WHEN_NO_STABLE_ID')
