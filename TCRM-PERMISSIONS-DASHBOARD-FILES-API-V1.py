#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('/var/www/TCRM-MAIN')
BASELINE = 'f1c591da9586994764147364965e757524ae3d89'
PATCH = 'TCRM-PERMISSIONS-DASHBOARD-FILES-API-V1'


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.exists():
        raise SystemExit(f'MISSING_FILE={rel}')
    return path.read_text(encoding='utf-8')


def write(rel: str, content: str):
    path = ROOT / rel
    before = path.read_text(encoding='utf-8')
    if before == content:
        print(f'SKIP={rel}:already_current')
        return
    path.write_text(content, encoding='utf-8')
    print(f'UPDATED={rel}')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'ANCHOR_ERROR={label}:expected=1:actual={count}')
    return text.replace(old, new, 1)


# ---------------------------------------------------------------------------
# 1) Central API permission selection for Dashboard + CRM File Storage.
#    Existing row/context file authorization remains untouched and additive.
# ---------------------------------------------------------------------------
rel = 'server/security/corePermissionPolicy.ts'
text = read(rel)

if '// TCRM_PERMISSIONS_DASHBOARD_FILES_API_V1' not in text:
    text = replace_once(
        text,
        '// TCRM_PERMISSIONS_OPERATIONAL_MODULES_V2\n',
        '// TCRM_PERMISSIONS_OPERATIONAL_MODULES_V2\n// TCRM_PERMISSIONS_DASHBOARD_FILES_API_V1\n',
        'policy_marker',
    )

old = '''export function resolveCorePermissionKey(path: string, type: ProcedureType): PermissionKey | null {\n  const module = moduleFromPath(path);\n  if (!module) return null;\n\n  const operation = operationFromPath(path);\n'''
new = '''export function resolveCorePermissionKey(path: string, type: ProcedureType): PermissionKey | null {\n  const root = String(path || "").split(".").filter(Boolean)[0] || "";\n  const operation = operationFromPath(path);\n\n  // TCRM_PERMISSIONS_DASHBOARD_FILES_API_V1\n  // Dashboard currently exposes read-only protected queries. Preserve any future\n  // write route as explicitly unmapped until a write permission is catalogued.\n  if (root === "dashboard") {\n    if (type === "query" || type === "subscription") return "dashboard.view";\n    return null;\n  }\n\n  // CRM File Storage has its own action vocabulary, so map it explicitly instead\n  // of allowing the generic CRUD mapper to invent non-catalog keys such as\n  // files.create/files.restore. Existing file row/context checks remain additive.\n  if (root === "fileStorage") {\n    if (type === "query" || type === "subscription") {\n      if (operation === "sharelinks") return "files.share";\n      return "files.view";\n    }\n\n    if (operation === "upload") return "files.upload";\n    if (operation === "softdelete" || operation === "discardpending") return "files.delete";\n    if (operation === "createpublicviewonlysharelink" || operation === "revokepublicviewonlysharelink") return "files.share";\n\n    // update / restore / replace and any future protected file mutation are\n    // fail-closed behind files.edit rather than falling through unguarded.\n    return "files.edit";\n  }\n\n  const module = moduleFromPath(path);\n  if (!module) return null;\n'''
text = replace_once(text, old, new, 'dashboard_files_policy')
write(rel, text)


# ---------------------------------------------------------------------------
# 2) Focused resolver tests using the actual production route names.
# ---------------------------------------------------------------------------
rel = 'server/security/corePermissionPolicy.test.ts'
test = read(rel)

insert_before = '''  it("does not hijack sales contract handover", () => {\n'''
new_tests = '''  it("maps dashboard reads to dashboard.view without inventing dashboard writes", () => {\n    expect(resolveCorePermissionKey("dashboard.salesFunnel", "query")).toBe("dashboard.view");\n    expect(resolveCorePermissionKey("dashboard.taskSla", "query")).toBe("dashboard.view");\n    expect(resolveCorePermissionKey("dashboard.agentStats", "query")).toBe("dashboard.view");\n    expect(resolveCorePermissionKey("dashboard.teamStats", "query")).toBe("dashboard.view");\n    expect(resolveCorePermissionKey("dashboard.update", "mutation")).toBeNull();\n  });\n\n  it("maps CRM file storage operations to the files permission catalog", () => {\n    expect(resolveCorePermissionKey("fileStorage.list", "query")).toBe("files.view");\n    expect(resolveCorePermissionKey("fileStorage.contractFilesByClient", "query")).toBe("files.view");\n    expect(resolveCorePermissionKey("fileStorage.auditLogs", "query")).toBe("files.view");\n    expect(resolveCorePermissionKey("fileStorage.upload", "mutation")).toBe("files.upload");\n    expect(resolveCorePermissionKey("fileStorage.update", "mutation")).toBe("files.edit");\n    expect(resolveCorePermissionKey("fileStorage.restore", "mutation")).toBe("files.edit");\n    expect(resolveCorePermissionKey("fileStorage.replace", "mutation")).toBe("files.edit");\n    expect(resolveCorePermissionKey("fileStorage.softDelete", "mutation")).toBe("files.delete");\n    expect(resolveCorePermissionKey("fileStorage.discardPending", "mutation")).toBe("files.delete");\n    expect(resolveCorePermissionKey("fileStorage.shareLinks", "query")).toBe("files.share");\n    expect(resolveCorePermissionKey("fileStorage.createPublicViewOnlyShareLink", "mutation")).toBe("files.share");\n    expect(resolveCorePermissionKey("fileStorage.revokePublicViewOnlyShareLink", "mutation")).toBe("files.share");\n  });\n\n'''
if 'maps CRM file storage operations to the files permission catalog' not in test:
    test = replace_once(test, insert_before, new_tests + insert_before, 'policy_tests')
write(rel, test)


# ---------------------------------------------------------------------------
# 3) Static post-apply checks. No DB/schema/data changes.
# ---------------------------------------------------------------------------
checks = {
    'server/security/corePermissionPolicy.ts': [
        'TCRM_PERMISSIONS_DASHBOARD_FILES_API_V1',
        'if (root === "dashboard")',
        'return "dashboard.view";',
        'if (root === "fileStorage")',
        'return "files.upload";',
        'return "files.delete";',
        'return "files.share";',
        'return "files.edit";',
    ],
    'server/security/corePermissionPolicy.test.ts': [
        'dashboard.salesFunnel',
        'fileStorage.contractFilesByClient',
        'fileStorage.createPublicViewOnlyShareLink',
        'fileStorage.revokePublicViewOnlyShareLink',
    ],
}
for rel, needles in checks.items():
    data = read(rel)
    missing = [needle for needle in needles if needle not in data]
    if missing:
        raise SystemExit(f'POSTCHECK_FAILED={rel}:{missing}')

print(f'PATCH={PATCH}')
print(f'BASELINE={BASELINE}')
print('MODULES=dashboard,files')
print('DASHBOARD_PERMISSION=dashboard.view')
print('FILES_PERMISSIONS=files.view,files.upload,files.edit,files.delete,files.share')
print('EXISTING_FILE_CONTEXT_AUTH_PRESERVED=YES')
print('DB_SCHEMA_CHANGED=NO')
print('DATA_CHANGED=NO')
print('FILES_CHANGED=server/security/corePermissionPolicy.ts,server/security/corePermissionPolicy.test.ts')
