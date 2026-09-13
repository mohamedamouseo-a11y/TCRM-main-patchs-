#!/usr/bin/env python3
from pathlib import Path
import os
import re
import shutil
import sys
from datetime import datetime

PATCH = "TCRM-TOS-CLIENT-BRIEF-MAPPING-V1-SENDER-R1-LIVE-BASELINE-GIT-GENERATED"
DEFAULT_REPO = "/var/www/TTCRM"
TARGET_REL = "server/services/tosIntegrationService.ts"

repo = Path(os.environ.get("TCRM_REPO", DEFAULT_REPO)).resolve()
target = repo / TARGET_REL

if not target.exists():
    print(f"PATCH={PATCH}")
    print("STATUS=ABORT")
    print(f"REASON=TARGET_NOT_FOUND:{target}")
    sys.exit(2)

text = target.read_text(encoding="utf-8")

# Idempotency check.
if (
    'const CRM_HANDOVER_BRIEF_SYNC_VERSION = "TCRM_CLIENT_HANDOVER_BRIEF_V1";' in text
    and 'function buildStructuredHandoverBrief(brief: any)' in text
    and '...(crmHandoverBrief ? { crmHandoverBrief } : {})' in text
):
    print(f"PATCH={PATCH}")
    print("STATUS=ALREADY_APPLIED")
    print(f"PROJECT_PATH={repo}")
    sys.exit(0)

required_markers = [
    "const SALES_BRIEF_FIELDS:",
    "function redactBriefText(value: unknown)",
    "function buildSalesBriefSummary(brief: any)",
    "function buildProjectPayloadFromClientProfile(profile: any, handoverBrief: any = null)",
    "const salesBrief = buildSalesBriefSummary(handoverBrief);",
]
missing = [marker for marker in required_markers if marker not in text]
if missing:
    print(f"PATCH={PATCH}")
    print("STATUS=ABORT")
    print("REASON=BASELINE_ANCHOR_MISMATCH")
    print("MISSING=" + " | ".join(missing))
    sys.exit(3)

constants_block = '''const CRM_HANDOVER_BRIEF_SYNC_VERSION = "TCRM_CLIENT_HANDOVER_BRIEF_V1";\nconst CRM_HANDOVER_BRIEF_MAX_JSON_CHARS = 45000;\nconst CRM_HANDOVER_BRIEF_MAX_FIELD_CHARS = 6000;\n\n'''

# Insert constants before SETTINGS_KEYS, which is stable across current TCRM integration versions.
settings_anchor = "const SETTINGS_KEYS = {"
if settings_anchor not in text:
    print(f"PATCH={PATCH}")
    print("STATUS=ABORT")
    print("REASON=SETTINGS_KEYS_ANCHOR_NOT_FOUND")
    sys.exit(4)
text = text.replace(settings_anchor, constants_block + settings_anchor, 1)

helper_block = r'''function buildStructuredHandoverBrief(brief: any) {
  if (!brief || typeof brief !== "object" || Array.isArray(brief)) return null;

  // Keep the structured TOS copy aligned with the already-approved Sales Brief
  // field allow-list. Contact/payment/meta identifiers are not copied as fields.
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

builder_anchor = "function buildProjectPayloadFromClientProfile(profile: any, handoverBrief: any = null) {"
text = text.replace(builder_anchor, helper_block + builder_anchor, 1)

# Add structured brief variable immediately after the existing salesBrief calculation.
sales_var_anchor = "  const salesBrief = buildSalesBriefSummary(handoverBrief);\n"
if sales_var_anchor not in text:
    print(f"PATCH={PATCH}")
    print("STATUS=ABORT")
    print("REASON=SALES_BRIEF_VAR_ANCHOR_NOT_FOUND")
    sys.exit(5)
text = text.replace(
    sales_var_anchor,
    sales_var_anchor + "  const crmHandoverBrief = buildStructuredHandoverBrief(handoverBrief);\n",
    1,
)

# Restrict payload insertion to buildProjectPayloadFromClientProfile and the first
# root-level return object. Root properties use four-space indentation; metadata
# uses deeper indentation, so this does not alter metadata behavior.
builder_start = text.find(builder_anchor)
if builder_start < 0:
    print(f"PATCH={PATCH}")
    print("STATUS=ABORT")
    print("REASON=BUILDER_NOT_FOUND_AFTER_HELPER_INSERT")
    sys.exit(6)
next_function = text.find("\nfunction ", builder_start + len(builder_anchor))
export_function = text.find("\nexport function ", builder_start + len(builder_anchor))
ends = [x for x in (next_function, export_function) if x >= 0]
builder_end = min(ends) if ends else len(text)
builder = text[builder_start:builder_end]

root_candidates = [
    "    salesBrief,\n    accountManagerBrief,\n",
    "    salesBrief,\n",
]
root_anchor = next((a for a in root_candidates if a in builder), None)
if not root_anchor:
    print(f"PATCH={PATCH}")
    print("STATUS=ABORT")
    print("REASON=ROOT_PAYLOAD_BRIEF_ANCHOR_NOT_FOUND")
    sys.exit(7)

if root_anchor == root_candidates[0]:
    root_replacement = "    salesBrief,\n    accountManagerBrief,\n    ...(crmHandoverBrief ? { crmHandoverBrief } : {}),\n"
else:
    root_replacement = "    salesBrief,\n    ...(crmHandoverBrief ? { crmHandoverBrief } : {}),\n"

builder = builder.replace(root_anchor, root_replacement, 1)
text = text[:builder_start] + builder + text[builder_end:]

# Final source-level invariants before writing.
checks = {
    "helper": 'function buildStructuredHandoverBrief(brief: any)' in text,
    "version": 'CRM_HANDOVER_BRIEF_SYNC_VERSION = "TCRM_CLIENT_HANDOVER_BRIEF_V1"' in text,
    "root_payload": '...(crmHandoverBrief ? { crmHandoverBrief } : {})' in text,
    "sales_brief_preserved": "const salesBrief = buildSalesBriefSummary(handoverBrief);" in text,
    "builder_preserved": builder_anchor in text,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    print(f"PATCH={PATCH}")
    print("STATUS=ABORT")
    print("REASON=POST_PATCH_INVARIANT_FAILED:" + ",".join(failed))
    sys.exit(8)

backup_dir = repo / "backups"
backup_dir.mkdir(parents=True, exist_ok=True)
stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = backup_dir / f"tosIntegrationService.ts.pre-client-brief-sender-r1-{stamp}.bak"
shutil.copy2(target, backup)
target.write_text(text, encoding="utf-8")

print(f"PATCH={PATCH}")
print("STATUS=APPLIED")
print(f"PROJECT_PATH={repo}")
print(f"BACKUP={backup}")
print(f"FILES_CHANGED={TARGET_REL}")
print("CRM_HANDOVER_BRIEF_ROOT_PAYLOAD=YES")
print("CRM_HANDOVER_BRIEF_SCHEMA_VERSION=TCRM_CLIENT_HANDOVER_BRIEF_V1")
print("CRM_HANDOVER_BRIEF_ALLOWLIST=SALES_BRIEF_FIELDS+accountManagerBrief")
print("CONTACT_FIELDS_ADDED_AS_STRUCTURED_FIELDS=NO")
print("PAYMENT_STATUS_ADDED_AS_STRUCTURED_FIELD=NO")
print("INTERNAL_METADATA_ADDED_AS_STRUCTURED_FIELDS=NO")
print("MAX_JSON_CHARS=45000")
print("SYNC_EXECUTED=NO")
print("DEPLOY=NOT_RUN")
print("GIT_PUSH=NO")
