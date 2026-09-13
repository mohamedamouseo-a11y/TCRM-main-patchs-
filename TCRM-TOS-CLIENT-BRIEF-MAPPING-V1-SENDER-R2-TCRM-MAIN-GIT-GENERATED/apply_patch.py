#!/usr/bin/env python3
from pathlib import Path
import os
import shutil
import sys
from datetime import datetime

PATCH = "TCRM-TOS-CLIENT-BRIEF-MAPPING-V1-SENDER-R2-TCRM-MAIN-GIT-GENERATED"
DEFAULT_REPO = "/var/www/TCRM-MAIN"
TARGET_REL = "server/services/tosIntegrationService.ts"

repo = Path(os.environ.get("TCRM_REPO", DEFAULT_REPO)).resolve()
target = repo / TARGET_REL

print(f"PATCH={PATCH}")
print(f"PROJECT_PATH={repo}")

if repo != Path(DEFAULT_REPO).resolve():
    print("STATUS=ABORT")
    print("REASON=WRONG_PROJECT_PATH")
    sys.exit(2)

if not target.exists():
    print("STATUS=ABORT")
    print(f"REASON=TARGET_NOT_FOUND:{target}")
    sys.exit(2)

text = target.read_text(encoding="utf-8")

constants_anchor = 'const VERIFIED_PROJECT_SYNC_VERSION = "TCRM_TOS_LEAD_NAME_VERIFIED_SYNC_AM_TASKS_V3";\n'
constants_replacement = constants_anchor + '''const CRM_HANDOVER_BRIEF_SYNC_VERSION = "TCRM_CLIENT_HANDOVER_BRIEF_V1";\nconst CRM_HANDOVER_BRIEF_MAX_JSON_CHARS = 45000;\nconst CRM_HANDOVER_BRIEF_MAX_FIELD_CHARS = 6000;\n'''

helper_anchor = '''function buildSalesBriefSummary(brief: any) {\n  if (!brief) return "";\n  const usedKeys = new Set<string>();\n  const structuredParts = SALES_BRIEF_FIELDS.map(([label, keys]) => {\n    const keyList = Array.isArray(keys) ? keys : [keys];\n    keyList.forEach((key) => usedKeys.add(key));\n    return briefLine(label, valueFromBriefKeys(brief, keys));\n  }).filter(Boolean);\n\n  // Forward-safe fallback: if the sales brief form gains new fields later, sync them\n  // instead of silently sending an empty Sales Brief. Sensitive/contact/meta fields stay excluded.\n  const fallbackParts = Object.entries(brief)\n    .filter(([key, value]) => !usedKeys.has(key) && !SALES_BRIEF_NEVER_SYNC_FIELDS.has(key) && String(value ?? "").trim())\n    .map(([key, value]) => briefLine(humanizeBriefField(key), value))\n    .filter(Boolean);\n\n  return truncate([...structuredParts, ...fallbackParts].join("\\n"), 8000);\n}\n'''

# A second accepted anchor handles the same live function if the explanatory
# comment is absent, while keeping the actual implementation identical.
helper_anchor_alt = '''function buildSalesBriefSummary(brief: any) {\n  if (!brief) return "";\n  const usedKeys = new Set<string>();\n  const structuredParts = SALES_BRIEF_FIELDS.map(([label, keys]) => {\n    const keyList = Array.isArray(keys) ? keys : [keys];\n    keyList.forEach((key) => usedKeys.add(key));\n    return briefLine(label, valueFromBriefKeys(brief, keys));\n  }).filter(Boolean);\n\n  const fallbackParts = Object.entries(brief)\n    .filter(([key, value]) => !usedKeys.has(key) && !SALES_BRIEF_NEVER_SYNC_FIELDS.has(key) && String(value ?? "").trim())\n    .map(([key, value]) => briefLine(humanizeBriefField(key), value))\n    .filter(Boolean);\n\n  return truncate([...structuredParts, ...fallbackParts].join("\\n"), 8000);\n}\n'''

helper_block = r'''

function buildStructuredHandoverBrief(brief: any) {
  if (!brief || typeof brief !== "object" || Array.isArray(brief)) return null;

  // Strict allow-list based on the existing approved Sales Brief mapping.
  // Do not copy fallback fields into the structured payload: contact, payment,
  // submitter/updater metadata, timestamps and TOS owner assignments stay out.
  const orderedKeys: string[] = [];
  for (const [, keys] of SALES_BRIEF_FIELDS) {
    for (const key of (Array.isArray(keys) ? keys : [keys])) {
      if (!orderedKeys.includes(key)) orderedKeys.push(key);
    }
  }

  const result: Record<string, string> = {
    schemaVersion: CRM_HANDOVER_BRIEF_SYNC_VERSION,
  };

  const appendField = (key: string, value: unknown) => {
    const clean = truncate(redactBriefText(value), CRM_HANDOVER_BRIEF_MAX_FIELD_CHARS);
    if (!clean) return;

    const candidate = { ...result, [key]: clean };
    if (JSON.stringify(candidate).length <= CRM_HANDOVER_BRIEF_MAX_JSON_CHARS) {
      result[key] = clean;
      return;
    }

    const remaining = CRM_HANDOVER_BRIEF_MAX_JSON_CHARS - JSON.stringify(result).length - key.length - 32;
    if (remaining < 64) return;
    result[key] = truncate(clean, Math.max(1, remaining - 8));
    if (JSON.stringify(result).length > CRM_HANDOVER_BRIEF_MAX_JSON_CHARS) delete result[key];
  };

  for (const key of orderedKeys) appendField(key, brief?.[key]);
  appendField("accountManagerBrief", brief?.accountManagerBrief);

  return Object.keys(result).length > 1 ? result : null;
}
'''

vars_anchor = '''  const salesBrief = buildSalesBriefSummary(handoverBrief);\n  const accountManagerBrief = redactBriefText(handoverBrief?.accountManagerBrief);\n  const projectOwners = normalizeTosProjectOwners(handoverBrief?.tosProjectOwners);'''
vars_replacement = '''  const salesBrief = buildSalesBriefSummary(handoverBrief);\n  const accountManagerBrief = redactBriefText(handoverBrief?.accountManagerBrief);\n  const crmHandoverBrief = buildStructuredHandoverBrief(handoverBrief);\n  const projectOwners = normalizeTosProjectOwners(handoverBrief?.tosProjectOwners);'''

payload_anchor = '''    salesBrief,\n    accountManagerBrief,\n    projectManagerName: accountManagerName,'''
payload_replacement = '''    salesBrief,\n    accountManagerBrief,\n    crmHandoverBrief,\n    projectManagerName: accountManagerName,'''

metadata_anchor = '''      salesBrief,\n      accountManagerBrief,\n      businessProfile,'''
metadata_replacement = '''      salesBrief,\n      accountManagerBrief,\n      crmHandoverBriefVersion: crmHandoverBrief ? CRM_HANDOVER_BRIEF_SYNC_VERSION : null,\n      businessProfile,'''

already_applied = (
    'const CRM_HANDOVER_BRIEF_SYNC_VERSION = "TCRM_CLIENT_HANDOVER_BRIEF_V1";' in text
    and 'function buildStructuredHandoverBrief(brief: any)' in text
    and '\n    crmHandoverBrief,\n' in text
)
if already_applied:
    print("STATUS=ALREADY_APPLIED")
    print(f"FILES_CHANGED={TARGET_REL}")
    sys.exit(0)

required_markers = [
    constants_anchor.strip(),
    "const SALES_BRIEF_FIELDS:",
    "function redactBriefText(value: unknown)",
    "function buildSalesBriefSummary(brief: any)",
    "function buildProjectPayloadFromClientProfile(profile: any, handoverBrief: any = null)",
    'crmProjectId: `crm-client-${client.id}`',
    'crmClientId: String(client.id)',
    'projectOwnersSyncMode: "ADD_ONLY"',
]
missing = [marker for marker in required_markers if marker not in text]
for anchor, label in [
    (vars_anchor, "handover brief variables anchor"),
    (payload_anchor, "root payload anchor"),
    (metadata_anchor, "metadata anchor"),
]:
    if anchor not in text:
        missing.append(label)

selected_helper_anchor = helper_anchor if helper_anchor in text else helper_anchor_alt if helper_anchor_alt in text else None
if selected_helper_anchor is None:
    missing.append("buildSalesBriefSummary exact anchor")

if missing:
    print("STATUS=ABORT")
    print("REASON=BASELINE_ANCHOR_MISMATCH")
    print("MISSING=" + " | ".join(missing))
    sys.exit(3)

backup_dir = repo / "backups"
backup_dir.mkdir(parents=True, exist_ok=True)
stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = backup_dir / f"tosIntegrationService.ts.pre-client-brief-r2-{stamp}.bak"
shutil.copy2(target, backup)

patched = text
patched = patched.replace(constants_anchor, constants_replacement, 1)
patched = patched.replace(selected_helper_anchor, selected_helper_anchor + helper_block, 1)
patched = patched.replace(vars_anchor, vars_replacement, 1)
patched = patched.replace(payload_anchor, payload_replacement, 1)
patched = patched.replace(metadata_anchor, metadata_replacement, 1)

target.write_text(patched, encoding="utf-8")

print("STATUS=APPLIED")
print(f"BACKUP={backup}")
print(f"FILES_CHANGED={TARGET_REL}")
print("CRM_HANDOVER_BRIEF_ROOT_PAYLOAD=YES")
print("CRM_HANDOVER_BRIEF_SCHEMA_VERSION=TCRM_CLIENT_HANDOVER_BRIEF_V1")
print("CRM_HANDOVER_BRIEF_ALLOWLIST=SALES_BRIEF_FIELDS+accountManagerBrief")
print("CRM_HANDOVER_BRIEF_NULL_WHEN_NO_BRIEF=YES")
print("CONTACT_FIELDS_ADDED_AS_STRUCTURED_FIELDS=NO")
print("PAYMENT_STATUS_ADDED_AS_STRUCTURED_FIELD=NO")
print("INTERNAL_METADATA_ADDED_AS_STRUCTURED_FIELDS=NO")
print("MAX_JSON_CHARS=45000")
print("DATABASE_SCHEMA_CHANGED=NO")
print("SYNC_EXECUTED=NO")
print("DEPLOY=NOT_RUN")
print("GIT_PUSH=NO")
