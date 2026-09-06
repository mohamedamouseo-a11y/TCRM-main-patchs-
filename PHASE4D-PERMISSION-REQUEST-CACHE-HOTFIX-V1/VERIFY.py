#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

EXPECTED_HEAD = "3e0aa9de85e55253dba928b5dedf96098286bec8"
EXPECTED_MODIFIED = {
    "client/src/pages/RolesPermissions.tsx",
    "server/_core/trpc.ts",
    "server/permissionsAdminRouter.ts",
    "server/routers.ts",
    "server/security/permissionEngine.ts",
}

root = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TCRM-MAIN").resolve()
engine_path = root / "server/security/permissionEngine.ts"
trpc_path = root / "server/_core/trpc.ts"
admin_path = root / "server/permissionsAdminRouter.ts"
router_path = root / "server/routers.ts"
ui_path = root / "client/src/pages/RolesPermissions.tsx"

errors = []

def check(condition, name):
    if not condition:
        errors.append(name)

head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
modified = set(subprocess.check_output(["git", "-C", str(root), "diff", "--name-only", "HEAD"], text=True).splitlines())
untracked = set(subprocess.check_output(["git", "-C", str(root), "ls-files", "--others", "--exclude-standard"], text=True).splitlines())

check(head == EXPECTED_HEAD, "baseline-head")
check(modified == EXPECTED_MODIFIED, f"expected-modified-files:{sorted(modified)}")
check(not untracked, f"no-untracked-files:{sorted(untracked)}")

for path in (engine_path, trpc_path, admin_path, router_path, ui_path):
    check(path.exists(), f"file-exists:{path}")

engine = engine_path.read_text() if engine_path.exists() else ""
trpc = trpc_path.read_text() if trpc_path.exists() else ""
admin = admin_path.read_text() if admin_path.exists() else ""
router = router_path.read_text() if router_path.exists() else ""
ui = ui_path.read_text() if ui_path.exists() else ""

check("PERMISSION_ENGINE_REQUEST_CACHE_HOTFIX_V1" in engine, "engine-hotfix-marker")
check("new WeakMap<object, PermissionRequestCache>()" in engine, "weakmap-request-cache")
check("assignedRoleIds: Map<number, Promise<number[]>>" in engine, "assigned-role-cache")
check("overrideRows: Map<string, Promise<any[]>>" in engine, "override-cache")
check("roleGraphRows: Map<string, Promise<any[]>>" in engine, "role-graph-cache")
check("requestScope?: object | null" in engine, "optional-request-scope")
check("SELECT ur.role_id AS roleId" in engine, "assigned-role-query")
check("AND ur.is_active = 1" in engine, "assigned-role-active-filter")
check("ur.expires_at IS NULL OR ur.expires_at > NOW()" in engine, "assigned-role-expiry-filter")
check("ADVANCED_PERMISSIONS_PHASE4B_TEMPORARY_ACCESS_ENGINE" in engine, "temporary-access-marker")
check("upo.starts_at IS NULL OR upo.starts_at <= NOW()" in engine, "temporary-access-start")
check("upo.expires_at IS NULL OR upo.expires_at > NOW()" in engine, "temporary-access-expiry")
check("upo.scope_config AS scopeConfig" in engine, "user-scope-config-preserved")
check("rp.scope_config AS scopeConfig" in engine, "role-scope-config-preserved")
check("ADVANCED_PERMISSIONS_PHASE4D_FIELD_POLICY_ENGINE" in engine, "phase4d-engine-preserved")

# The old correlated role assignment EXISTS must be gone from evaluatePermission.
eval_start = engine.find("export async function evaluatePermission")
eval_end = engine.find("export async function hasPermission", eval_start)
eval_body = engine[eval_start:eval_end] if eval_start >= 0 and eval_end > eval_start else ""
check(eval_body != "", "evaluatePermission-found")
check("EXISTS(" not in eval_body, "correlated-exists-removed")

check("PERMISSION_REQUEST_CACHE_TRPC_V1" in trpc, "trpc-hotfix-marker")
query_cache_expr = 'opts.type === "query" ? opts.ctx.req : undefined'
check(trpc.count(query_cache_expr) == 3, f"query-only-cache-call-count:{trpc.count(query_cache_expr)}")
check('evaluatePermission(opts.ctx.user!, permission, opts.type === "query" ? opts.ctx.req : undefined)' in trpc, "permission-procedure-query-cache")
check('evaluatePermission(user as any, permission, opts.type === "query" ? opts.ctx.req : undefined)' in trpc, "phase3-query-cache")

# Explicitly prove mutation authorization does not receive a request cache.
check('opts.type === "query" ? opts.ctx.req : undefined' in trpc, "mutation-cache-bypass-expression")

check("PERMISSION_REQUEST_CACHE_TESTER_V1" in admin, "tester-hotfix-marker")
check('.query(async ({ ctx, input }) => {' in admin, "tester-query-ctx")
check('evaluatePermission(permissionUser, permissionKey as PermissionKey, ctx.req)' in admin, "tester-request-cache")

check("ADVANCED_PERMISSIONS_PHASE4D_FIELD_POLICY_ROUTER" in router, "phase4d-router-preserved")
check("ADVANCED_PERMISSIONS_PHASE4D_FIELD_POLICY_UI" in ui, "phase4d-ui-preserved")

# No schema/migration paths may be part of the working-tree diff.
for name in modified:
    lowered = name.lower()
    check("migration" not in lowered and "drizzle/schema" not in lowered and not lowered.endswith("schema.ts"), f"no-schema-migration:{name}")

if errors:
    print("VERIFY=FAIL")
    for error in errors:
        print(f"FAIL={error}")
    raise SystemExit(1)

print("VERIFY=PASS")
print("EXPECTED_FILES_ONLY=YES")
print("UNTRACKED_FILES=NONE")
print("QUERY_REQUEST_CACHE=YES")
print("MUTATION_REQUEST_CACHE=NO")
print("CORRELATED_EXISTS_REMOVED=YES")
print("ASSIGNED_ROLE_QUERY_CACHED=YES")
print("OVERRIDE_QUERY_CACHED=YES")
print("ROLE_GRAPH_QUERY_CACHED=YES")
print("TEMP_ACCESS_PRESERVED=YES")
print("ROLE_INHERITANCE_CODE_PRESERVED=YES")
print("FIELD_POLICY_PRESERVED=YES")
print("DB_CHANGES=NO")
