import { sql } from "drizzle-orm";
import { getDb } from "../db";
import { PERMISSION_SCOPES, PHASE1_PERMISSION_CATALOG, type PermissionScope } from "./permissionCatalog";
import { PermissionAdminError } from "./permissionAdminService";

export type UserPermissionOverrideInput = {
  permissionKey: string;
  effect: "allow" | "deny";
  dataScope: PermissionScope;
  scopeConfig?: Record<string, unknown> | null;
  startsAt?: Date | null;
  expiresAt?: Date | null;
  reason?: string | null;
};

function rows(result: any): any[] {
  if (Array.isArray(result) && Array.isArray(result[0])) return result[0];
  if (Array.isArray(result)) return result;
  return [];
}

function safeJson(value: unknown) {
  return value == null ? null : JSON.stringify(value);
}

export async function listPermissionUsers() {
  const db = await getDb();
  if (!db) throw new PermissionAdminError("BAD_REQUEST", "Database is unavailable");
  return rows(await db.execute(sql`
    SELECT u.id, u.name, u.email, u.role AS legacyRole, u.teamId,
      COUNT(DISTINCT CASE WHEN ur.is_active = 1 THEN ur.role_id END) AS roleCount,
      COUNT(DISTINCT upo.permission_id) AS overrideCount
    FROM users u
    LEFT JOIN user_roles ur ON ur.user_id = u.id AND ur.is_active = 1
    LEFT JOIN user_permission_overrides upo ON upo.user_id = u.id
      AND (upo.starts_at IS NULL OR upo.starts_at <= NOW())
      AND (upo.expires_at IS NULL OR upo.expires_at > NOW())
    WHERE u.deletedAt IS NULL
    GROUP BY u.id
    ORDER BY COALESCE(u.name, u.email), u.id
  `));
}

export async function getPermissionUserProfile(userId: number) {
  const db = await getDb();
  if (!db) throw new PermissionAdminError("BAD_REQUEST", "Database is unavailable");
  const user = rows(await db.execute(sql`
    SELECT id, name, email, role AS legacyRole, teamId
    FROM users WHERE id = ${userId} AND deletedAt IS NULL LIMIT 1
  `))[0];
  if (!user) throw new PermissionAdminError("NOT_FOUND", "User not found");

  const roles = rows(await db.execute(sql`
    SELECT r.id, r.role_key AS roleKey, r.name, r.name_ar AS nameAr,
      ur.is_primary AS isPrimary, ur.starts_at AS startsAt, ur.expires_at AS expiresAt
    FROM user_roles ur
    JOIN roles r ON r.id = ur.role_id
    WHERE ur.user_id = ${userId} AND ur.is_active = 1 AND r.is_active = 1
      AND (ur.starts_at IS NULL OR ur.starts_at <= NOW())
      AND (ur.expires_at IS NULL OR ur.expires_at > NOW())
    ORDER BY ur.is_primary DESC, r.name
  `));

  const overrides = rows(await db.execute(sql`
    SELECT p.permission_key AS permissionKey, p.module_key AS moduleKey, p.action_key AS actionKey,
      upo.effect, upo.data_scope AS dataScope, upo.scope_config AS scopeConfig,
      upo.starts_at AS startsAt, upo.expires_at AS expiresAt, upo.reason
    FROM user_permission_overrides upo
    JOIN permissions p ON p.id = upo.permission_id
    WHERE upo.user_id = ${userId}
    ORDER BY p.module_key, p.action_key
  `));

  return { ...user, roles, overrides };
}

export async function replacePermissionUserOverrides(
  userId: number,
  entries: UserPermissionOverrideInput[],
  actorUserId: number,
) {
  const before = await getPermissionUserProfile(userId);
  const allowedKeys = new Set(PHASE1_PERMISSION_CATALOG.map(String));
  const seen = new Set<string>();
  for (const entry of entries) {
    if (!allowedKeys.has(entry.permissionKey)) throw new PermissionAdminError("BAD_REQUEST", `Unknown permission: ${entry.permissionKey}`);
    if (seen.has(entry.permissionKey)) throw new PermissionAdminError("BAD_REQUEST", `Duplicate permission: ${entry.permissionKey}`);
    if (!PERMISSION_SCOPES.includes(entry.dataScope as any)) throw new PermissionAdminError("BAD_REQUEST", `Invalid scope: ${entry.dataScope}`);
    if (entry.startsAt && entry.expiresAt && entry.expiresAt <= entry.startsAt) {
      throw new PermissionAdminError("BAD_REQUEST", `Override expiry must be after start: ${entry.permissionKey}`);
    }
    seen.add(entry.permissionKey);
  }

  const db: any = await getDb();
  if (!db) throw new PermissionAdminError("BAD_REQUEST", "Database is unavailable");
  await db.transaction(async (tx: any) => {
    await tx.execute(sql`DELETE FROM user_permission_overrides WHERE user_id = ${userId}`);
    for (const entry of entries) {
      await tx.execute(sql`
        INSERT INTO user_permission_overrides
          (user_id, permission_id, effect, data_scope, scope_config, starts_at, expires_at, reason, created_by)
        SELECT ${userId}, p.id, ${entry.effect}, ${entry.effect === "deny" ? "none" : entry.dataScope},
          ${safeJson(entry.scopeConfig)}, ${entry.startsAt ?? null}, ${entry.expiresAt ?? null},
          ${entry.reason?.trim() || null}, ${actorUserId}
        FROM permissions p
        WHERE p.permission_key = ${entry.permissionKey} AND p.is_active = 1
      `);
    }
    await tx.execute(sql`
      INSERT INTO permission_audit_logs
        (actor_user_id, target_user_id, action, previous_value, new_value, metadata)
      VALUES (${actorUserId}, ${userId}, 'USER_PERMISSION_OVERRIDES_REPLACED',
        ${safeJson(before.overrides)}, ${safeJson(entries)}, ${safeJson({ source: "roles_permissions_ui" })})
    `);
  });
  return getPermissionUserProfile(userId);
}
