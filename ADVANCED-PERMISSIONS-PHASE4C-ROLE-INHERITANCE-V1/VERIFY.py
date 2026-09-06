#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

EXPECTED_HEAD = "7da712b977843ee28c2de2b49b7cc6ad94338a41"
EXPECTED_FILES = {
    "server/security/permissionAdminService.ts",
    "server/permissionsAdminRouter.ts",
    "server/security/permissionEngine.ts",
    "client/src/pages/RolesPermissions.tsx",
}

root = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TCRM-MAIN").resolve()
head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
status = subprocess.check_output(["git", "-C", str(root), "status", "--porcelain", "--untracked-files=all"], text=True)
changed = set()
untracked = []
for line in status.splitlines():
    if not line.strip():
        continue
    code = line[:2]
    path = line[3:].strip()
    if " -> " in path:
        path = path.split(" -> ", 1)[1]
    changed.add(path)
    if code == "??":
        untracked.append(path)

texts = {path: (root / path).read_text() for path in EXPECTED_FILES}
checks = {
    "baseline-head": head == EXPECTED_HEAD,
    "expected-files-only": changed == EXPECTED_FILES,
    "no-untracked-files": len(untracked) == 0,
    "admin-marker": "ADVANCED_PERMISSIONS_PHASE4C_ROLE_INHERITANCE_ADMIN" in texts["server/security/permissionAdminService.ts"],
    "router-marker": "ADVANCED_PERMISSIONS_PHASE4C_ROLE_INHERITANCE_ROUTER" in texts["server/permissionsAdminRouter.ts"],
    "engine-marker": "ADVANCED_PERMISSIONS_PHASE4C_ROLE_INHERITANCE_ENGINE" in texts["server/security/permissionEngine.ts"],
    "ui-marker": "ADVANCED_PERMISSIONS_PHASE4C_ROLE_INHERITANCE_UI" in texts["client/src/pages/RolesPermissions.tsx"],
    "parent-persisted": "parent_role_id = ${parentRoleId}" in texts["server/security/permissionAdminService.ts"],
    "cycle-guard": "Role inheritance cycle detected" in texts["server/security/permissionAdminService.ts"],
    "child-override-resolver": "resolveInheritedRoleRows" in texts["server/security/permissionEngine.ts"],
    "dynamic-inheritance": "assignedRoleIds" in texts["server/security/permissionEngine.ts"],
    "legacy-inheritance": "legacyRootIds" in texts["server/security/permissionEngine.ts"],
    "parent-ui": "Inherits permissions from" in texts["client/src/pages/RolesPermissions.tsx"],
    "no-db-migration-files": not any("migration" in path.lower() or "schema" in path.lower() for path in changed),
}

for name, passed in checks.items():
    print(f"{name}={'PASS' if passed else 'FAIL'}")

if not all(checks.values()):
    print("VERIFY=FAIL")
    raise SystemExit(1)

print("VERIFY=PASS")
