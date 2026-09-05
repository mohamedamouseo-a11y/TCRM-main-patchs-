#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TCRM-MAIN").resolve()
router = (root / "server/permissionsAdminRouter.ts").read_text(encoding="utf-8")
ui = (root / "client/src/pages/RolesPermissions.tsx").read_text(encoding="utf-8")

checks = {
    "server-marker": "ADVANCED_PERMISSIONS_PHASE4A_PERMISSION_TESTER" in router,
    "tester-endpoint": "testUserPermissions: permissionProcedure(\"roles.view\")" in router,
    "uses-effective-engine": "evaluatePermission(permissionUser" in router,
    "catalog-validation": "Unknown permission:" in router and "PHASE1_PERMISSION_CATALOG" in router,
    "why-reason": "permissionDecisionReason" in router and "Denied by User Override" in router,
    "ui-marker": "ADVANCED_PERMISSIONS_PHASE4A_PERMISSION_TESTER_UI" in ui,
    "tester-tab": 'setTab("tester")' in ui and 'Permission Tester' in ui,
    "tester-query": "permissionsAdmin.testUserPermissions.useQuery" in ui,
    "user-selection": "visibleTesterUsers" in ui,
    "effective-result": "Effective Result & Why" in ui,
    "summary": "testerQuery.data.summary.allowed" in ui and "testerQuery.data.summary.denied" in ui,
}

try:
    diff_names = subprocess.check_output(
        ["git", "-C", str(root), "diff", "--name-only"], text=True
    ).splitlines()
    untracked = subprocess.check_output(
        ["git", "-C", str(root), "ls-files", "--others", "--exclude-standard"], text=True
    ).splitlines()
except Exception as exc:
    raise SystemExit(f"Unable to inspect working tree: {exc}")

expected = {
    "server/permissionsAdminRouter.ts",
    "client/src/pages/RolesPermissions.tsx",
}
only_expected = set(diff_names) == expected
no_untracked = len(untracked) == 0

for name, ok in checks.items():
    print(f"{name}={'PASS' if ok else 'FAIL'}")
print(f"MODIFIED_FILES={','.join(diff_names) if diff_names else 'NONE'}")
print(f"UNTRACKED_FILES={','.join(untracked) if untracked else 'NONE'}")
print(f"EXPECTED_FILES_ONLY={'YES' if only_expected else 'NO'}")
print(f"NO_UNTRACKED={'YES' if no_untracked else 'NO'}")

ok = all(checks.values()) and only_expected and no_untracked
print(f"VERIFY={'PASS' if ok else 'FAIL'}")
raise SystemExit(0 if ok else 1)
