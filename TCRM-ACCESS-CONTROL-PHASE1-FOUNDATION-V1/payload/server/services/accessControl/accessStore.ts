import { sql } from "drizzle-orm";
import type { AccessCondition, AccessEffect, AccessScope } from "@shared/accessControl";
import { getDb } from "../../db";
import type { AccessCandidate } from "./accessDecision";

function rows(result: any): any[] {
  if (Array.isArray(result) && Array.isArray(result[0])) return result[0];
  if (Array.isArray(result)) return result;
  return [];
}

function parseConditions(value: unknown): AccessCondition[] | null {
  if (!value) return null;
  if (Array.isArray(value)) return value as AccessCondition[];
  if (typeof value === "string") {
    try {
      const parsed = JSON.parse(value);
      return Array.isArray(parsed) ? parsed : null;
    } catch {
      return null;
    }
  }
  return null;
}

export async function requireAccessControlDb() {
  const db = await getDb();
  if (!db) throw new Error("Database unavailable");
  const result = rows(await db.execute(sql`
    SELECT COUNT(*) AS count
    FROM information_schema.TABLES
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME IN (
        'access_roles','access_permissions','access_role_permissions','access_user_roles',
        'access_user_overrides','access_temporary_grants','access_decision_logs'
      )
  `));
  if (Number(result[0]?.count ?? 0) !== 7) {
    const error: any = new Error("Access Control Phase 1 migration is required");
    error.code = "ACCESS_CONTROL_NOT_READY";
    throw error;
  }
  return db;
}

export async function isAccessControlInstalled() {
  try { await requireAccessControlDb(); return true; } catch { return false; }
}

export async function listAccessCandidates(input: { userId: number; legacyRole?: string | null; permissionKey: string }): Promise<AccessCandidate[]> {
  const db = await requireAccessControlDb();

  const overrides = rows(await db.execute(sql`
    SELECT 'user_override' source, uo.id sourceId, uo.effect, uo.scope, uo.conditions_json conditionsJson
    FROM access_user_overrides uo
    JOIN access_permissions p ON p.id = uo.permission_id
    WHERE uo.user_id = ${input.userId}
      AND p.permission_key = ${input.permissionKey}
      AND (uo.expires_at IS NULL OR uo.expires_at > NOW())
  `));

  const temporary = rows(await db.execute(sql`
    SELECT 'temporary_grant' source, tg.id sourceId, 'allow' effect, tg.scope, tg.conditions_json conditionsJson
    FROM access_temporary_grants tg
    JOIN access_permissions p ON p.id = tg.permission_id
    WHERE tg.user_id = ${input.userId}
      AND p.permission_key = ${input.permissionKey}
      AND tg.starts_at <= NOW() AND tg.expires_at > NOW() AND tg.revoked_at IS NULL
  `));

  const assignedRoles = rows(await db.execute(sql`
    SELECT 'role_permission' source, rp.role_id sourceId, rp.effect, rp.scope, rp.conditions_json conditionsJson
    FROM access_user_roles ur
    JOIN access_roles r ON r.id = ur.role_id AND r.is_active = 1
    JOIN access_role_permissions rp ON rp.role_id = ur.role_id
    JOIN access_permissions p ON p.id = rp.permission_id
    WHERE ur.user_id = ${input.userId}
      AND p.permission_key = ${input.permissionKey}
      AND (ur.valid_from IS NULL OR ur.valid_from <= NOW())
      AND (ur.valid_to IS NULL OR ur.valid_to > NOW())
  `));

  const legacyBridge = input.legacyRole ? rows(await db.execute(sql`
    SELECT 'legacy_role_bridge' source, r.id sourceId, rp.effect, rp.scope, rp.conditions_json conditionsJson
    FROM access_roles r
    JOIN access_role_permissions rp ON rp.role_id = r.id
    JOIN access_permissions p ON p.id = rp.permission_id
    WHERE r.role_key = ${String(input.legacyRole)}
      AND r.is_active = 1
      AND p.permission_key = ${input.permissionKey}
      AND NOT EXISTS (
        SELECT 1 FROM access_user_roles ur2
        WHERE ur2.user_id = ${input.userId}
          AND (ur2.valid_from IS NULL OR ur2.valid_from <= NOW())
          AND (ur2.valid_to IS NULL OR ur2.valid_to > NOW())
      )
  `)) : [];

  return [...overrides, ...temporary, ...assignedRoles, ...legacyBridge].map((row: any) => ({
    source: row.source,
    sourceId: row.sourceId == null ? null : Number(row.sourceId),
    effect: String(row.effect) as AccessEffect,
    scope: String(row.scope) as AccessScope,
    conditions: parseConditions(row.conditionsJson),
  }));
}

export async function getAccessControlOverview() {
  const db = await requireAccessControlDb();
  const result = rows(await db.execute(sql`
    SELECT
      (SELECT COUNT(*) FROM access_roles WHERE is_active = 1) roles,
      (SELECT COUNT(*) FROM access_permissions) permissions,
      (SELECT COUNT(DISTINCT user_id) FROM access_user_roles WHERE valid_to IS NULL OR valid_to > NOW()) assignedUsers,
      (SELECT COUNT(*) FROM access_temporary_grants WHERE starts_at <= NOW() AND expires_at > NOW() AND revoked_at IS NULL) temporaryGrants,
      (SELECT COUNT(*) FROM access_user_overrides WHERE expires_at IS NULL OR expires_at > NOW()) userOverrides,
      (SELECT COUNT(*) FROM access_decision_logs WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR) AND effect = 'deny') deniedLast24h
  `));
  const row = result[0] ?? {};
  return Object.fromEntries(Object.entries(row).map(([key, value]) => [key, Number(value ?? 0)]));
}

export async function listAccessRoles() {
  const db = await requireAccessControlDb();
  return rows(await db.execute(sql`
    SELECT r.id, r.role_key roleKey, r.name, r.description, r.is_system isSystem, r.is_active isActive, r.version,
      COUNT(DISTINCT rp.permission_id) permissionCount, COUNT(DISTINCT ur.user_id) userCount
    FROM access_roles r
    LEFT JOIN access_role_permissions rp ON rp.role_id = r.id
    LEFT JOIN access_user_roles ur ON ur.role_id = r.id AND (ur.valid_to IS NULL OR ur.valid_to > NOW())
    GROUP BY r.id
    ORDER BY r.is_system DESC, r.name ASC
  `));
}

export async function getAccessRolePermissions(roleId: number) {
  const db = await requireAccessControlDb();
  return rows(await db.execute(sql`
    SELECT p.id permissionId, p.permission_key permissionKey, p.module, p.resource, p.action, p.risk_level riskLevel,
      rp.effect, rp.scope, rp.conditions_json conditions
    FROM access_permissions p
    LEFT JOIN access_role_permissions rp ON rp.permission_id = p.id AND rp.role_id = ${roleId}
    ORDER BY p.module, p.resource, p.action
  `));
}

export async function createAccessRole(input: { roleKey: string; name: string; description?: string | null; actorUserId: number }) {
  const db = await requireAccessControlDb();
  await db.execute(sql`
    INSERT INTO access_roles (role_key,name,description,is_system,is_active,version,created_by,created_at,updated_at)
    VALUES (${input.roleKey},${input.name},${input.description ?? null},0,1,1,${input.actorUserId},NOW(),NOW())
  `);
  const result = rows(await db.execute(sql`SELECT id, role_key roleKey, name, description, version FROM access_roles WHERE role_key=${input.roleKey} LIMIT 1`));
  return result[0] ?? null;
}

async function permissionId(permissionKey: string) {
  const db = await requireAccessControlDb();
  const result = rows(await db.execute(sql`SELECT id FROM access_permissions WHERE permission_key=${permissionKey} LIMIT 1`));
  const id = Number(result[0]?.id ?? 0);
  if (!id) throw new Error(`Unknown permission: ${permissionKey}`);
  return { db, id };
}

export async function setAccessRolePermission(input: { roleId: number; permissionKey: string; effect: AccessEffect; scope: AccessScope; conditions?: AccessCondition[] | null }) {
  const { db, id } = await permissionId(input.permissionKey);
  await db.execute(sql`
    INSERT INTO access_role_permissions (role_id,permission_id,effect,scope,conditions_json,created_at,updated_at)
    VALUES (${input.roleId},${id},${input.effect},${input.scope},${JSON.stringify(input.conditions ?? [])},NOW(),NOW())
    ON DUPLICATE KEY UPDATE effect=VALUES(effect),scope=VALUES(scope),conditions_json=VALUES(conditions_json),updated_at=NOW()
  `);
  await db.execute(sql`UPDATE access_roles SET version=version+1,updated_at=NOW() WHERE id=${input.roleId}`);
  return { success: true };
}

export async function assignAccessRole(input: { userId: number; roleId: number; actorUserId: number; validFrom?: Date | null; validTo?: Date | null }) {
  const db = await requireAccessControlDb();
  await db.execute(sql`
    INSERT INTO access_user_roles (user_id,role_id,assigned_by,valid_from,valid_to,source,created_at)
    VALUES (${input.userId},${input.roleId},${input.actorUserId},${input.validFrom ?? null},${input.validTo ?? null},'manual',NOW())
    ON DUPLICATE KEY UPDATE assigned_by=VALUES(assigned_by),valid_from=VALUES(valid_from),valid_to=VALUES(valid_to),source='manual'
  `);
  return { success: true };
}

export async function upsertAccessUserOverride(input: { userId: number; permissionKey: string; effect: AccessEffect; scope: AccessScope; conditions?: AccessCondition[] | null; reason?: string | null; expiresAt?: Date | null; actorUserId: number }) {
  const { db, id } = await permissionId(input.permissionKey);
  await db.execute(sql`
    INSERT INTO access_user_overrides (user_id,permission_id,effect,scope,conditions_json,reason,expires_at,created_by,created_at,updated_at)
    VALUES (${input.userId},${id},${input.effect},${input.scope},${JSON.stringify(input.conditions ?? [])},${input.reason ?? null},${input.expiresAt ?? null},${input.actorUserId},NOW(),NOW())
    ON DUPLICATE KEY UPDATE effect=VALUES(effect),scope=VALUES(scope),conditions_json=VALUES(conditions_json),reason=VALUES(reason),expires_at=VALUES(expires_at),created_by=VALUES(created_by),updated_at=NOW()
  `);
  return { success: true };
}

export async function createTemporaryAccessGrant(input: { userId: number; permissionKey: string; scope: AccessScope; conditions?: AccessCondition[] | null; startsAt: Date; expiresAt: Date; reason: string; actorUserId: number }) {
  const { db, id } = await permissionId(input.permissionKey);
  await db.execute(sql`
    INSERT INTO access_temporary_grants (user_id,permission_id,scope,conditions_json,starts_at,expires_at,reason,approved_by,created_by,created_at)
    VALUES (${input.userId},${id},${input.scope},${JSON.stringify(input.conditions ?? [])},${input.startsAt},${input.expiresAt},${input.reason},${input.actorUserId},${input.actorUserId},NOW())
  `);
  return { success: true };
}

export async function writeAccessDecisionLog(input: { userId: number; permissionKey: string; resourceType?: string | null; resourceId?: string | number | null; effect: AccessEffect; scope?: AccessScope | null; source: string; reason: string; matchedPolicies?: unknown }) {
  const db = await requireAccessControlDb();
  await db.execute(sql`
    INSERT INTO access_decision_logs (user_id,permission_key,resource_type,resource_id,effect,scope,source,reason,matched_policy_json,created_at)
    VALUES (${input.userId},${input.permissionKey},${input.resourceType ?? null},${input.resourceId == null ? null : String(input.resourceId)},${input.effect},${input.scope ?? null},${input.source},${input.reason},${JSON.stringify(input.matchedPolicies ?? [])},NOW())
  `);
}
