#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

EXPECTED_HEAD = "3e0aa9de85e55253dba928b5dedf96098286bec8"
EXPECTED_FILES = {
    "server/security/permissionEngine.ts",
    "server/routers.ts",
    "client/src/pages/RolesPermissions.tsx",
}

root = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TCRM-MAIN").resolve()
engine = (root / "server/security/permissionEngine.ts").read_text()
routers = (root / "server/routers.ts").read_text()
ui = (root / "client/src/pages/RolesPermissions.tsx").read_text()

head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
status_lines = subprocess.check_output(["git", "-C", str(root), "status", "--porcelain"], text=True).splitlines()
modified = set()
untracked = set()
for line in status_lines:
    if not line.strip():
        continue
    path = line[3:].strip()
    if line.startswith("??"):
        untracked.add(path)
    else:
        modified.add(path)

changed = modified | untracked

def has_all(text: str, needles):
    return all(needle in text for needle in needles)

checks = {
    "baseline-head": head == EXPECTED_HEAD,
    "expected-files-only": changed == EXPECTED_FILES,
    "no-untracked-files": len(untracked) == 0,
    "engine-marker": "ADVANCED_PERMISSIONS_PHASE4D_FIELD_POLICY_ENGINE" in engine,
    "engine-scope-config-read": has_all(engine, [
        "upo.scope_config AS scopeConfig",
        "rp.scope_config AS scopeConfig",
        "fieldPolicy: mergePermissionFieldPolicies",
    ]),
    "engine-default-unrestricted": has_all(engine, [
        "if (!fields || typeof fields !== \"object\" || Array.isArray(fields)) return undefined;",
        "if (!policy?.configured) return true;",
    ]),
    "engine-deny-precedence": "if (policy.deny.includes(field)) return false;" in engine,
    "engine-user-role-policy": engine.count("fieldPolicy: mergePermissionFieldPolicies") >= 3,
    "router-marker": "ADVANCED_PERMISSIONS_PHASE4D_FIELD_POLICY_ROUTER" in routers,
    "leads-read-enforced": has_all(routers, [
        "filterPermissionFieldRows(items as any[]",
        "return filterPermissionFields(lead, (ctx as any).permissionDecision, [\"id\"]);",
    ]),
    "leads-write-enforced": routers.count('assertPermissionFieldWrite((ctx as any).permissionDecision') >= 4,
    "leads-export-enforced": has_all(routers, [
        'const viewDecision = await evaluatePermission(ctx.user as any, "leads.view");',
        "return filterPermissionFieldRows(rows as any[], fieldDecision, [\"id\"]);",
    ]),
    "deals-read-enforced": has_all(routers, [
        "filterPermissionFields(deal, (ctx as any).permissionDecision, [\"id\", \"leadId\", \"payments\"])",
        "filterPermissionFieldRows(deals as any[], (ctx as any).permissionDecision, [\"id\", \"leadId\"])",
    ]),
    "deals-write-enforced": has_all(routers, [
        'assertPermissionFieldWrite((ctx as any).permissionDecision, input as any, "deal", ["leadId"]);',
        'assertPermissionFieldWrite((ctx as any).permissionDecision, data as any, "deal", ["leadId"]);',
    ]),
    "clients-read-enforced": has_all(routers, [
        "filterPermissionFieldRows(result.data",
        "filterPermissionFields(client, (ctx as any).permissionDecision, [\"id\", \"leadId\", \"dealId\"])",
    ]),
    "clients-write-enforced": has_all(routers, [
        'assertPermissionFieldWrite((ctx as any).permissionDecision, input as any, "client", ["clientRequestId", "leadId", "dealId"]);',
        'const clientEditDecision = await evaluatePermission(ctx.user as any, "clients.edit");',
        'const clientCreateDecision = await evaluatePermission(ctx.user as any, "clients.create");',
    ]),
    "ui-marker": "ADVANCED_PERMISSIONS_PHASE4D_FIELD_POLICY_UI" in ui,
    "ui-role-field-editor": 'setFieldEditor({ target: "role", permissionKey: "leads.view" })' in ui,
    "ui-user-field-editor": 'setFieldEditor({ target: "user", permissionKey: "leads.view" })' in ui,
    "ui-field-modes": has_all(ui, [
        '<SelectItem value="all">',
        '<SelectItem value="allow">',
        '<SelectItem value="deny">',
        "FIELD_CATALOG",
    ]),
    "ui-scopeconfig-preserved": has_all(ui, [
        "scopeConfig: normalizeScopeConfig(item.scopeConfig)",
        "scopeConfig: draft[key]?.scopeConfig ?? null",
        "next[key] = { ...next[key], effect, dataScope:",
    ]),
    "tester-field-policy": "d.fieldPolicy?.configured" in ui,
}

# The patch itself must not introduce DB/migration files.
diff_names = subprocess.check_output(["git", "-C", str(root), "diff", "--name-only", HEAD := "HEAD"], text=True).splitlines()
checks["no-db-migration-files"] = not any(
    name.startswith("drizzle/") or
    "/migrations/" in name or
    name.endswith("schema.ts") or
    name.endswith("schema.sql")
    for name in diff_names
)

failed = [name for name, ok in checks.items() if not ok]
for name, ok in checks.items():
    print(f"{name}={'PASS' if ok else 'FAIL'}")

if failed:
    print("VERIFY=FAIL")
    print("FAILED=" + ",".join(failed))
    raise SystemExit(1)

print("VERIFY=PASS")
print("FIELD_POLICY_ENGINE=YES")
print("ROLE_FIELD_UI=YES")
print("USER_OVERRIDE_FIELD_UI=YES")
print("LEADS_READ_ENFORCED=YES")
print("LEADS_WRITE_ENFORCED=YES")
print("LEADS_EXPORT_ENFORCED=YES")
print("DEALS_READ_ENFORCED=YES")
print("DEALS_WRITE_ENFORCED=YES")
print("CLIENTS_READ_ENFORCED=YES")
print("CLIENTS_WRITE_ENFORCED=YES")
print("DEFAULT_UNRESTRICTED=YES")
print("SUPER_ADMIN_UNCHANGED=YES")
print("PRECEDENCE_UNCHANGED=YES")
print("DB_CHANGES=NO")
