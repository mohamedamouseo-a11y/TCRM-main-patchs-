#!/usr/bin/env python3
from pathlib import Path
import os
import shutil
import sys
from datetime import datetime

PATCH = "TCRM-TOS-CLIENT-BRIEF-MAPPING-V1-SENDER-GIT-GENERATED"
DEFAULT_REPO = "/var/www/TCRM-MAIN"
TARGET_REL = "server/services/tosIntegrationService.ts"

repo = Path(os.environ.get("TCRM_REPO", DEFAULT_REPO)).resolve()
target = repo / TARGET_REL

if not target.exists():
    print(f"PATCH={PATCH}")
    print("STATUS=ABORT")
    print(f"REASON=TARGET_NOT_FOUND:{target}")
    sys.exit(2)

text = target.read_text(encoding="utf-8")

version_anchor = 'const VERIFIED_PROJECT_SYNC_VERSION = "TCRM_TOS_LEAD_NAME_VERIFIED_SYNC_AM_TASKS_V3";\n'
version_replacement = version_anchor + '''const CRM_HANDOVER_BRIEF_SYNC_VERSION = "TCRM_CLIENT_HANDOVER_BRIEF_V1";\nconst CRM_HANDOVER_BRIEF_MAX_JSON_CHARS = 45000;\nconst CRM_HANDOVER_BRIEF_MAX_FIELD_CHARS = 6000;\n'''

normalize_status_anchor = '\nfunction normalizeTosProjectStatus(client: any) {'
helper_block = r'''
function buildStructuredHandoverBrief(brief: any) {
  if (!brief || typeof brief !== "object" || Array.isArray(brief)) return null;

  // Strict allow-list: only fields already approved for Sales Brief sync are
  // copied into the structured TOS brief. Contact/payment/internal metadata,
  // submitter ids/names, timestamps and TOS owner assignments stay excluded.
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

brief_vars_anchor = '''  const salesBrief = buildSalesBriefSummary(handoverBrief);\n  const accountManagerBrief = redactBriefText(handoverBrief?.accountManagerBrief);\n  const projectOwners = normalizeTosProjectOwners(handoverBrief?.tosProjectOwners);'''
brief_vars_replacement = '''  const salesBrief = buildSalesBriefSummary(handoverBrief);\n  const accountManagerBrief = redactBriefText(handoverBrief?.accountManagerBrief);\n  const crmHandoverBrief = buildStructuredHandoverBrief(handoverBrief);\n  const projectOwners = normalizeTosProjectOwners(handoverBrief?.tosProjectOwners);'''

payload_anchor = '''    salesBrief,\n    accountManagerBrief,\n    projectManagerName: accountManagerName,'''
payload_replacement = '''    salesBrief,\n    accountManagerBrief,\n    ...(crmHandoverBrief ? { crmHandoverBrief } : {}),\n    projectManagerName: accountManagerName,'''

metadata_anchor = '''      salesBrief,\n      accountManagerBrief,\n      businessProfile,'''
metadata_replacement = '''      salesBrief,\n      accountManagerBrief,\n      crmHandoverBriefVersion: crmHandoverBrief ? CRM_HANDOVER_BRIEF_SYNC_VERSION : null,\n      businessProfile,'''

already_applied = (
    'const CRM_HANDOVER_BRIEF_SYNC_VERSION = "TCRM_CLIENT_HANDOVER_BRIEF_V1";' in text
    and 'function buildStructuredHandoverBrief(brief: any)' in text
    and '...(crmHandoverBrief ? { crmHandoverBrief } : {})' in text
)
if already_applied:
    print(f"PATCH={PATCH}")
    print("STATUS=ALREADY_APPLIED")
    print(f"PROJECT_PATH={repo}")
    sys.exit(0)

missing = []
for anchor, label in [
    (version_anchor, "verified project sync version anchor"),
    (normalize_status_anchor, "normalizeTosProjectStatus anchor"),
    (brief_vars_anchor, "handover brief payload vars anchor"),
    (payload_anchor, "root payload brief anchor"),
    (metadata_anchor, "metadata brief anchor"),
]:
    if anchor not in text:
        missing.append(label)

required_existing = [
    "const SALES_BRIEF_FIELDS:",
    "function redactBriefText(value: unknown)",
    "function buildSalesBriefSummary(brief: any)",
    "function buildProjectPayloadFromClientProfile(profile: any, handoverBrief: any = null)",
    "const handoverBrief = await getHandoverBrief(clientId);",
]
for marker in required_existing:
    if marker not in text:
        missing.append(marker)

if missing:
    print(f"PATCH={PATCH}")
    print("STATUS=ABORT")
    print("REASON=BASELINE_ANCHOR_MISMATCH")
    print("MISSING=" + " | ".join(missing))
    sys.exit(3)

backup_dir = repo / "backups"
backup_dir.mkdir(parents=True, exist_ok=True)
stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = backup_dir / f"tosIntegrationService.ts.pre-client-brief-sender-{stamp}.bak"
shutil.copy2(target, backup)

patched = text
patched = patched.replace(version_anchor, version_replacement, 1)
patched = patched.replace(normalize_status_anchor, "\n" + helper_block + normalize_status_anchor, 1)
patched = patched.replace(brief_vars_anchor, brief_vars_replacement, 1)
patched = patched.replace(payload_anchor, payload_replacement, 1)
patched = patched.replace(metadata_anchor, metadata_replacement, 1)

target.write_text(patched, encoding="utf-8")

print(f"PATCH={PATCH}")
print("STATUS=APPLIED")
print(f"PROJECT_PATH={repo}")
print(f"BACKUP={backup}")
print(f"FILES_CHANGED={TARGET_REL}")
print("CRM_HANDOVER_BRIEF_ROOT_PAYLOAD=YES")
print("CRM_HANDOVER_BRIEF_SCHEMA_VERSION=TCRM_CLIENT_HANDOVER_BRIEF_V1")
print("CRM_HANDOVER_BRIEF_ALLOWLIST=SALES_BRIEF_FIELDS+accountManagerBrief")
print("CONTACT_FIELDS_INCLUDED=NO")
print("PAYMENT_FIELDS_INCLUDED=NO")
print("INTERNAL_METADATA_INCLUDED=NO")
print("MAX_JSON_CHARS=45000")
print("SYNC_EXECUTED=NO")
print("DEPLOY=NOT_RUN")
print("GIT_PUSH=NO")
