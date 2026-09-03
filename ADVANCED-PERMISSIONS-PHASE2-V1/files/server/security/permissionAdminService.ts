import { sql } from "drizzle-orm";
import { getDb } from "../db";
import { PERMISSION_SCOPES, PHASE1_PERMISSION_CATALOG, type PermissionScope } from "./permissionCatalog";

export type RolePermissionInput = {
  permissionKey: string;
  effect: "allow" | "deny";
  dataScope: PermissionScope;
  scopeConfig?: Record<string, unknown> | null;
};

export class PermissionAdminError extends Error {
  constructor(public code: "NOT_FOUND" | "CONFLICT" | "BAD_REQUEST" | "FORBIDDEN", message: string) {
    super(message);
  }
}

function rows(result: any): any[] {
  if (Array.isArray(result) && Array.isArray(result[0])) return result[0];
  if (Array.isArray(result)) return result;
  return [];
}

function slugifyRoleKey(value: string) {
  return value.trim().toLowerCase().replace(/[^a-z0-9._-]+/g, "_").replace(/^_+|_+$/g, "");
}

function safeJson(value: unknown) {
  return value == null ? null : JSON.stringify(value);
}

async function audit(params: {
  actorUserId: number;
  targetRoleId?: number | null;
  action: string;
  permissionKey?: string | null;
  previousValue?: unknown;
  newValue?: unknown;
  reason?: string | null;
  metadata?: unknown;
}, executor?: any) {
  const db = executor ?? await getDb();
  if (!db) return;
  await db.execute(sql`
    INSERT INTO permission_audit_logs
      (actor_user_id, target_role_id, action, permission_key, previous_value, new_value, reason, metadata)
    VALUES
      (${params.actorUserId}, ${params.targetRoleId ?? null}, ${params.action}, ${params.permissionKey ?? null},
       ${safeJson(params.previousValue)}, ${safeJson(params.newValue)}, ${params.reason ?? null}, ${safeJson(params.metadata)})
  `);
}

export async function getPermissionCatalogForAdmin() {
  const db = await getDb();
  if (!db) throw new PermissionAdminError("BAD_REQUEST", "Database is unavailable");
  const data = rows(await db.execute(sql`
    SELECT id, permission_key AS permissionKey, module_key AS moduleKey, action_key AS actionKey,
           name, description, is_sensitive AS isSensitive, is_active AS isActive
    FROM permissions
    WHERE is_active = 1
    ORDER BY module_key ASC, action_key ASC, permission_key ASC
  `));
  const byKey = new Map(data.map((item: any) => [String(item.permissionKey), item]));
  const ordered = PHASE1_PERMISSION_CATALOG.map(key => byKey.get(String(key))).filter(Boolean);
  const extras = data.filter((item: any) => !PHASE1_PERMISSION_CATALOG.includes(item.permissionKey as any));
  return { scopes: [...PERMISSION_SCOPES], permissions: [...ordered, ...extras] };
}

export async function listPermissionRoles() {
  const db = await getDb();
  if (!db) throw new PermissionAdminError("BAD_REQUEST", "Database is unavailable");
  return rows(await db.execute(sql`
    SELECT r.id, r.role_key AS roleKey, r.name, r.name_ar AS nameAr, r.description,
           r.legacy_role_key AS legacyRoleKey, r.parent_role_id AS parentRoleId,
           r.is_system AS isSystem, r.is_active AS isActive,
           COUNT(DISTINCT CASE WHEN ur.is_active = 1 THEN ur.user_id END) AS userCount,
           COUNT(DISTINCT rp.permission_id) AS permissionCount,
           r.created_at AS createdAt, r.updated_at AS updatedAt
    FROM roles r
    LEFT JOIN user_roles ur ON ur.role_id = r.id
    LEFT JOIN role_permissions rp ON rp.role_id = r.id
    GROUP BY r.id
    ORDER BY r.is_system DESC, r.name ASC
  `));
}

export async function getPermissionRole(roleId: number) {
  const db = await getDb();
  if (!db) throw new PermissionAdminError("BAD_REQUEST", "Database is unavailable");
  const roleRows = rows(await db.execute(sql`
    SELECT id, role_key AS roleKey, name, name_ar AS nameAr, description,
           legacy_role_key AS legacyRoleKey, parent_role_id AS parentRoleId,
           is_system AS isSystem, is_active AS isActive, created_at AS createdAt, updated_at AS updatedAt
    FROM roles WHERE id = ${roleId} LIMIT 1
  `));
  if (!roleRows[0]) throw new PermissionAdminError("NOT_FOUND", "Role not found");
  const permissions = rows(await db.execute(sql`
    SELECT p.permission_key AS permissionKey, rp.effect, rp.data_scope AS dataScope, rp.scope_config AS scopeConfig
    FROM role_permissions rp
    JOIN permissions p ON p.id = rp.permission_id
    WHERE rp.role_id = ${roleId}
    ORDER BY p.module_key, p.action_key
  `));
  return { ...roleRows[0], permissions };
}

export async function createPermissionRole(input: {
  roleKey?: string;
  name: string;
  nameAr?: string | null;
  description?: string | null;
}, actorUserId: number) {
  const db = await getDb();
  if (!db) throw new PermissionAdminError("BAD_REQUEST", "Database is unavailable");
  const roleKey = slugifyRoleKey(input.roleKey || input.name);
  if (!roleKey || roleKey.startsWith("legacy.")) throw new PermissionAdminError("BAD_REQUEST", "Invalid role key");
  const existing = rows(await db.execute(sql`SELECT id FROM roles WHERE role_key = ${roleKey} LIMIT 1`));
  if (existing.length) throw new PermissionAdminError("CONFLICT", "Role key already exists");
  const result: any = await db.execute(sql`
    INSERT INTO roles (role_key, name, name_ar, description, is_system, is_active, created_by, updated_by)
    VALUES (${roleKey}, ${input.name.trim()}, ${input.nameAr?.trim() || null}, ${input.description?.trim() || null}, 0, 1, ${actorUserId}, ${actorUserId})
  `);
  const insertId = Number((Array.isArray(result) ? result[0] : result)?.insertId || 0);
  const role = insertId ? await getPermissionRole(insertId) : rows(await db.execute(sql`SELECT id FROM roles WHERE role_key = ${roleKey} LIMIT 1`))[0];
  const roleId = Number((role as any).id);
  await audit({ actorUserId, targetRoleId: roleId, action: "ROLE_CREATED", newValue: input });
  return getPermissionRole(roleId);
}

export async function updatePermissionRole(roleId: number, input: {
  name: string;
  nameAr?: string | null;
  description?: string | null;
}, actorUserId: number) {
  const before = await getPermissionRole(roleId);
  const db = await getDb();
  if (!db) throw new PermissionAdminError("BAD_REQUEST", "Database is unavailable");
  await db.execute(sql`
    UPDATE roles SET name = ${input.name.trim()}, name_ar = ${input.nameAr?.trim() || null},
      description = ${input.description?.trim() || null}, updated_by = ${actorUserId}
    WHERE id = ${roleId}
  `);
  const after = await getPermissionRole(roleId);
  await audit({ actorUserId, targetRoleId: roleId, action: "ROLE_UPDATED", previousValue: before, newValue: after });
  return after;
}

export async function duplicatePermissionRole(sourceRoleId: number, input: {
  roleKey?: string;
  name: string;
  nameAr?: string | null;
}, actorUserId: number) {
  const source = await getPermissionRole(sourceRoleId);
  const created = await createPermissionRole({ roleKey: input.roleKey, name: input.name, nameAr: input.nameAr, description: `Copied from ${source.name}` }, actorUserId);
  const entries: RolePermissionInput[] = (source.permissions || []).map((p: any) => ({
    permissionKey: String(p.permissionKey),
    effect: String(p.effect) === "deny" ? "deny" : "allow",
    dataScope: String(p.dataScope || "all") as PermissionScope,
    scopeConfig: p.scopeConfig ?? null,
  }));
  await replacePermissionRolePermissions(Number(created.id), entries, actorUserId, "ROLE_DUPLICATED");
  return getPermissionRole(Number(created.id));
}

export async function replacePermissionRolePermissions(roleId: number, entries: RolePermissionInput[], actorUserId: number, action = "ROLE_PERMISSIONS_REPLACED") {
  const before = await getPermissionRole(roleId);
  const allowedKeys = new Set(PHASE1_PERMISSION_CATALOG.map(String));
  const seen = new Set<string>();
  for (const entry of entries) {
    if (!allowedKeys.has(entry.permissionKey)) throw new PermissionAdminError("BAD_REQUEST", `Unknown permission: ${entry.permissionKey}`);
    if (seen.has(entry.permissionKey)) throw new PermissionAdminError("BAD_REQUEST", `Duplicate permission: ${entry.permissionKey}`);
    if (!PERMISSION_SCOPES.includes(entry.dataScope as any)) throw new PermissionAdminError("BAD_REQUEST", `Invalid scope: ${entry.dataScope}`);
    seen.add(entry.permissionKey);
  }
  const db: any = await getDb();
  if (!db) throw new PermissionAdminError("BAD_REQUEST", "Database is unavailable");
  await db.transaction(async (tx: any) => {
    await tx.execute(sql`DELETE FROM role_permissions WHERE role_id = ${roleId}`);
    for (const entry of entries) {
      await tx.execute(sql`
        INSERT INTO role_permissions (role_id, permission_id, effect, data_scope, scope_config, created_by)
        SELECT ${roleId}, p.id, ${entry.effect}, ${entry.effect === "deny" ? "none" : entry.dataScope}, ${safeJson(entry.scopeConfig)}, ${actorUserId}
        FROM permissions p
        WHERE p.permission_key = ${entry.permissionKey} AND p.is_active = 1
      `);
    }
    await audit({ actorUserId, targetRoleId: roleId, action, previousValue: before.permissions, newValue: entries }, tx);
  });
  return getPermissionRole(roleId);
}

export async function setPermissionRoleActive(roleId: number, isActive: boolean, actorUserId: number) {
  const before = await getPermissionRole(roleId);
  if (Number(before.isSystem) === 1 && !isActive) throw new PermissionAdminError("FORBIDDEN", "System roles cannot be deactivated");
  const db = await getDb();
  if (!db) throw new PermissionAdminError("BAD_REQUEST", "Database is unavailable");
  await db.execute(sql`UPDATE roles SET is_active = ${isActive ? 1 : 0}, updated_by = ${actorUserId} WHERE id = ${roleId}`);
  const after = await getPermissionRole(roleId);
  await audit({ actorUserId, targetRoleId: roleId, action: isActive ? "ROLE_ACTIVATED" : "ROLE_DEACTIVATED", previousValue: { isActive: before.isActive }, newValue: { isActive: after.isActive } });
  return after;
}

export async function deletePermissionRole(roleId: number, actorUserId: number) {
  const before = await getPermissionRole(roleId);
  if (Number(before.isSystem) === 1) throw new PermissionAdminError("FORBIDDEN", "System roles cannot be deleted");
  const db: any = await getDb();
  if (!db) throw new PermissionAdminError("BAD_REQUEST", "Database is unavailable");
  const assigned = rows(await db.execute(sql`SELECT COUNT(*) AS count FROM user_roles WHERE role_id = ${roleId} AND is_active = 1`));
  if (Number(assigned[0]?.count || 0) > 0) throw new PermissionAdminError("CONFLICT", "Role is assigned to active users and cannot be deleted");
  await db.transaction(async (tx: any) => {
    await audit({ actorUserId, targetRoleId: roleId, action: "ROLE_DELETED", previousValue: before }, tx);
    await tx.execute(sql`DELETE FROM role_permissions WHERE role_id = ${roleId}`);
    await tx.execute(sql`DELETE FROM roles WHERE id = ${roleId}`);
  });
  return { ok: true, roleId };
}
