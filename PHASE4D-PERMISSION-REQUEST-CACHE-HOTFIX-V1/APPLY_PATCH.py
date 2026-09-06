#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

EXPECTED_HEAD = "3e0aa9de85e55253dba928b5dedf96098286bec8"
PHASE4D_ENGINE_MARKER = "ADVANCED_PERMISSIONS_PHASE4D_FIELD_POLICY_ENGINE"
PHASE4D_ROUTER_MARKER = "ADVANCED_PERMISSIONS_PHASE4D_FIELD_POLICY_ROUTER"
PHASE4D_UI_MARKER = "ADVANCED_PERMISSIONS_PHASE4D_FIELD_POLICY_UI"
ENGINE_MARKER = "PERMISSION_ENGINE_REQUEST_CACHE_HOTFIX_V1"
TRPC_MARKER = "PERMISSION_REQUEST_CACHE_TRPC_V1"
ADMIN_MARKER = "PERMISSION_REQUEST_CACHE_TESTER_V1"

root = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TCRM-MAIN").resolve()
engine_path = root / "server/security/permissionEngine.ts"
trpc_path = root / "server/_core/trpc.ts"
admin_path = root / "server/permissionsAdminRouter.ts"
phase4d_router_path = root / "server/routers.ts"
phase4d_ui_path = root / "client/src/pages/RolesPermissions.tsx"

for path in (engine_path, trpc_path, admin_path, phase4d_router_path, phase4d_ui_path):
    if not path.exists():
        raise SystemExit(f"Missing required project file: {path}")

head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
if head != EXPECTED_HEAD:
    raise SystemExit(f"Baseline mismatch: expected {EXPECTED_HEAD}, got {head}. No files changed.")

engine = engine_path.read_text()
trpc = trpc_path.read_text()
admin = admin_path.read_text()
phase4d_router = phase4d_router_path.read_text()
phase4d_ui = phase4d_ui_path.read_text()

if PHASE4D_ENGINE_MARKER not in engine or PHASE4D_ROUTER_MARKER not in phase4d_router or PHASE4D_UI_MARKER not in phase4d_ui:
    raise SystemExit("Phase 4D Field Permissions V1 markers are not all present. No files changed.")

if ENGINE_MARKER in engine or TRPC_MARKER in trpc or ADMIN_MARKER in admin:
    if ENGINE_MARKER in engine and TRPC_MARKER in trpc and ADMIN_MARKER in admin:
        print("PATCH_ALREADY_APPLIED=YES")
        raise SystemExit(0)
    raise SystemExit("Partial hotfix markers detected. Refusing to continue. No files changed.")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"Anchor mismatch for {label}: expected 1 match, got {count}. No files changed.")
    return text.replace(old, new, 1)


def replace_exact_count(text: str, old: str, new: str, expected: int, label: str) -> str:
    count = text.count(old)
    if count != expected:
        raise SystemExit(f"Anchor mismatch for {label}: expected {expected} matches, got {count}. No files changed.")
    return text.replace(old, new)


def replace_once_after(text: str, marker: str, old: str, new: str, label: str) -> str:
    if text.count(marker) != 1:
        raise SystemExit(f"Marker mismatch for {label}. No files changed.")
    before, after = text.split(marker, 1)
    count = after.count(old)
    if count != 1:
        raise SystemExit(f"Anchor mismatch after marker for {label}: expected 1 match, got {count}. No files changed.")
    return before + marker + after.replace(old, new, 1)

new_engine = engine
new_trpc = trpc
new_admin = admin

cache_helpers = '''// PERMISSION_ENGINE_REQUEST_CACHE_HOTFIX_V1
// Query-only request-scoped memoization. Callers pass the Express request object
// only for read/query authorization. Mutations intentionally bypass this cache.
type PermissionRequestCache = {
  assignedRoleIds: Map<number, Promise<number[]>>;
  overrideRows: Map<string, Promise<any[]>>;
  roleGraphRows: Map<string, Promise<any[]>>;
};

const permissionRequestCaches = new WeakMap<object, PermissionRequestCache>();

function getPermissionRequestCache(requestScope?: object | null): PermissionRequestCache | undefined {
  if (!requestScope || typeof requestScope !== "object") return undefined;
  let cache = permissionRequestCaches.get(requestScope);
  if (!cache) {
    cache = {
      assignedRoleIds: new Map(),
      overrideRows: new Map(),
      roleGraphRows: new Map(),
    };
    permissionRequestCaches.set(requestScope, cache);
  }
  return cache;
}

async function getOrCreateRequestCacheValue<K, V>(
  cache: Map<K, Promise<V>> | undefined,
  key: K,
  factory: () => Promise<V>,
): Promise<V> {
  if (!cache) return factory();
  const existing = cache.get(key);
  if (existing) return existing;
  const pending = factory();
  cache.set(key, pending);
  try {
    return await pending;
  } catch (error) {
    cache.delete(key);
    throw error;
  }
}

'''

new_engine = replace_once(
    new_engine,
    'export async function evaluatePermission(user: PermissionUser, permission: PermissionKey): Promise<PermissionDecision> {',
    cache_helpers + 'export async function evaluatePermission(user: PermissionUser, permission: PermissionKey, requestScope?: object | null): Promise<PermissionDecision> {',
    "request cache helpers and evaluatePermission signature",
)

old_override = '''  const overrideRows = rows(await db.execute(sql`
    SELECT upo.effect, upo.data_scope AS dataScope, upo.scope_config AS scopeConfig
    FROM user_permission_overrides upo
    JOIN permissions p ON p.id = upo.permission_id
    WHERE upo.user_id = ${userId}
      AND p.permission_key = ${String(permission)}
      AND p.is_active = 1
      -- ADVANCED_PERMISSIONS_PHASE4B_TEMPORARY_ACCESS_ENGINE
      AND (upo.starts_at IS NULL OR upo.starts_at <= NOW())
      AND (upo.expires_at IS NULL OR upo.expires_at > NOW())
    ORDER BY CASE WHEN upo.effect = 'deny' THEN 0 ELSE 1 END, upo.id DESC
  `));'''

new_override = '''  const requestCache = getPermissionRequestCache(requestScope);
  const permissionCacheKey = `${userId}:${String(permission)}`;
  const overrideRows = await getOrCreateRequestCacheValue(
    requestCache?.overrideRows,
    permissionCacheKey,
    async () => rows(await db.execute(sql`
      SELECT upo.effect, upo.data_scope AS dataScope, upo.scope_config AS scopeConfig
      FROM user_permission_overrides upo
      JOIN permissions p ON p.id = upo.permission_id
      WHERE upo.user_id = ${userId}
        AND p.permission_key = ${String(permission)}
        AND p.is_active = 1
        -- ADVANCED_PERMISSIONS_PHASE4B_TEMPORARY_ACCESS_ENGINE
        AND (upo.starts_at IS NULL OR upo.starts_at <= NOW())
        AND (upo.expires_at IS NULL OR upo.expires_at > NOW())
      ORDER BY CASE WHEN upo.effect = 'deny' THEN 0 ELSE 1 END, upo.id DESC
    `)),
  );'''

new_engine = replace_once(new_engine, old_override, new_override, "cached user override query")

old_role_graph = '''  const roleGraphRows = rows(await db.execute(sql`
    SELECT r.id AS roleId, r.parent_role_id AS parentRoleId, r.legacy_role_key AS legacyRoleKey,
           rp.effect, rp.data_scope AS dataScope, rp.scope_config AS scopeConfig,
           EXISTS(
             SELECT 1
             FROM user_roles ur
             WHERE ur.role_id = r.id
               AND ur.user_id = ${userId}
               AND ur.is_active = 1
               AND (ur.expires_at IS NULL OR ur.expires_at > NOW())
           ) AS isAssigned
    FROM roles r
    LEFT JOIN permissions p
      ON p.permission_key = ${String(permission)} AND p.is_active = 1
    LEFT JOIN role_permissions rp
      ON rp.role_id = r.id AND rp.permission_id = p.id
    WHERE r.is_active = 1
  `));

  const assignedRoleIds = roleGraphRows
    .filter((r: any) => Number(r.isAssigned) === 1)
    .map((r: any) => Number(r.roleId));'''

new_role_graph = '''  const assignedRoleIds = await getOrCreateRequestCacheValue(
    requestCache?.assignedRoleIds,
    userId,
    async () => rows(await db.execute(sql`
      SELECT ur.role_id AS roleId
      FROM user_roles ur
      WHERE ur.user_id = ${userId}
        AND ur.is_active = 1
        AND (ur.expires_at IS NULL OR ur.expires_at > NOW())
    `))
      .map((r: any) => Number(r.roleId))
      .filter((roleId: number) => Number.isFinite(roleId) && roleId > 0),
  );

  const roleGraphRows = await getOrCreateRequestCacheValue(
    requestCache?.roleGraphRows,
    String(permission),
    async () => rows(await db.execute(sql`
      SELECT r.id AS roleId, r.parent_role_id AS parentRoleId, r.legacy_role_key AS legacyRoleKey,
             rp.effect, rp.data_scope AS dataScope, rp.scope_config AS scopeConfig
      FROM roles r
      LEFT JOIN permissions p
        ON p.permission_key = ${String(permission)} AND p.is_active = 1
      LEFT JOIN role_permissions rp
        ON rp.role_id = r.id AND rp.permission_id = p.id
      WHERE r.is_active = 1
    `)),
  );'''

new_engine = replace_once(new_engine, old_role_graph, new_role_graph, "assigned-role cache and role graph cache")

# tRPC: cache only authorization for queries. Mutations intentionally receive no request scope.
new_trpc = replace_once(
    new_trpc,
    '// ADVANCED_PERMISSIONS_PHASE1_V1\n// Reusable permission guards. Existing routers remain unchanged until module integration phases.\nexport const permissionProcedure',
    '// ADVANCED_PERMISSIONS_PHASE1_V1\n// Reusable permission guards. Existing routers remain unchanged until module integration phases.\n// PERMISSION_REQUEST_CACHE_TRPC_V1\nexport const permissionProcedure',
    "trpc hotfix marker",
)
new_trpc = replace_exact_count(
    new_trpc,
    'const decision = await evaluatePermission(opts.ctx.user!, permission);',
    'const decision = await evaluatePermission(opts.ctx.user!, permission, opts.type === "query" ? opts.ctx.req : undefined);',
    2,
    "permissionProcedure and anyPermissionProcedure query cache",
)
new_trpc = replace_once(
    new_trpc,
    'const decision = await evaluatePermission(user as any, permission);',
    'const decision = await evaluatePermission(user as any, permission, opts.type === "query" ? opts.ctx.req : undefined);',
    "phase3Scope query cache",
)

# Permission Tester is a read-only query and can safely reuse its request cache.
new_admin = replace_once(
    new_admin,
    '// ADVANCED_PERMISSIONS_PHASE4A_PERMISSION_TESTER\n  testUserPermissions:',
    '// ADVANCED_PERMISSIONS_PHASE4A_PERMISSION_TESTER\n  // PERMISSION_REQUEST_CACHE_TESTER_V1\n  testUserPermissions:',
    "permission tester hotfix marker",
)
new_admin = replace_once_after(
    new_admin,
    '// PERMISSION_REQUEST_CACHE_TESTER_V1',
    '.query(async ({ input }) => {',
    '.query(async ({ ctx, input }) => {',
    "permission tester ctx",
)
new_admin = replace_once_after(
    new_admin,
    '// PERMISSION_REQUEST_CACHE_TESTER_V1',
    'const decision = await evaluatePermission(permissionUser, permissionKey as PermissionKey);',
    'const decision = await evaluatePermission(permissionUser, permissionKey as PermissionKey, ctx.req);',
    "permission tester request cache",
)

# Validate all expected new markers before writing anything.
if ENGINE_MARKER not in new_engine or TRPC_MARKER not in new_trpc or ADMIN_MARKER not in new_admin:
    raise SystemExit("Internal patch validation failed. No files changed.")
if 'EXISTS(\n             SELECT 1\n             FROM user_roles ur' in new_engine:
    raise SystemExit("Correlated user_roles EXISTS still present in evaluatePermission patch area. No files changed.")
if 'ADVANCED_PERMISSIONS_PHASE4B_TEMPORARY_ACCESS_ENGINE' not in new_engine:
    raise SystemExit("Temporary Access marker was lost. No files changed.")
if 'scope_config AS scopeConfig' not in new_engine:
    raise SystemExit("Phase 4D scope_config selection was lost. No files changed.")

engine_path.write_text(new_engine)
trpc_path.write_text(new_trpc)
admin_path.write_text(new_admin)

print("PATCH_APPLIED=YES")
print("HOTFIX_PROJECT_FILES=server/security/permissionEngine.ts,server/_core/trpc.ts,server/permissionsAdminRouter.ts")
print("MUTATION_CACHE=DISABLED")
print("DB_CHANGES=NO")
