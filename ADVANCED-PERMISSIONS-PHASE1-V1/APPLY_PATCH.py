#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


def write_text(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"[write] {path}")


def patch_once(path: Path, needle: str, replacement: str):
    text = path.read_text(encoding="utf-8")
    if replacement in text:
        print(f"[skip] {path}: already patched")
        return
    if needle not in text:
        raise RuntimeError(f"Patch marker not found in {path}: {needle[:120]!r}")
    path.write_text(text.replace(needle, replacement, 1), encoding="utf-8")
    print(f"[patch] {path}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 APPLY_PATCH.py /path/to/TCRM", file=sys.stderr)
        raise SystemExit(2)

    root = Path(sys.argv[1]).resolve()
    if not (root / "package.json").exists() or not (root / "server/_core/trpc.ts").exists():
        raise RuntimeError("Target does not look like the TCRM repository")

    catalog = r'''export const PERMISSION_SCOPES = [
  "all",
  "team",
  "department",
  "own",
  "assigned",
  "created_by",
  "custom",
  "none",
] as const;

export type PermissionScope = (typeof PERMISSION_SCOPES)[number];

export const PHASE1_PERMISSION_CATALOG = [
  "dashboard.view",
  "leads.view", "leads.create", "leads.edit", "leads.delete", "leads.restore", "leads.assign", "leads.reassign", "leads.export", "leads.import",
  "deals.view", "deals.create", "deals.edit", "deals.delete", "deals.export",
  "clients.view", "clients.create", "clients.edit", "clients.delete", "clients.export",
  "activities.view", "activities.create", "activities.edit", "activities.delete",
  "tasks.view", "tasks.create", "tasks.edit", "tasks.delete", "tasks.assign",
  "meetings.view", "meetings.create", "meetings.edit", "meetings.delete",
  "contracts.view", "contracts.create", "contracts.edit", "contracts.delete", "contracts.export",
  "campaigns.view", "campaigns.create", "campaigns.edit", "campaigns.delete", "campaigns.export",
  "whatsapp.view", "whatsapp.send", "whatsapp.manage",
  "messenger.view", "messenger.send", "messenger.manage",
  "files.view", "files.upload", "files.edit", "files.delete", "files.share",
  "reports.view", "reports.export",
  "users.view", "users.create", "users.edit", "users.delete", "users.assign_roles",
  "roles.view", "roles.create", "roles.edit", "roles.delete", "roles.assign_permissions",
  "settings.view", "settings.edit",
  "integrations.view", "integrations.manage",
  "notifications.view", "notifications.manage",
  "backup.view", "backup.run", "backup.restore", "backup.manage",
  "audit.view", "audit.export",
  "developer.view", "developer.manage",
] as const;

export type PermissionKey = (typeof PHASE1_PERMISSION_CATALOG)[number] | (string & {});
'''

    engine = r'''import { sql } from "drizzle-orm";
import { getDb } from "../db";
import type { PermissionKey, PermissionScope } from "./permissionCatalog";

export type PermissionUser = {
  id: number | string;
  role?: string | null;
  email?: string | null;
  teamId?: number | null;
};

export type PermissionDecision = {
  allowed: boolean;
  permission: string;
  scope: PermissionScope;
  source: "super_admin" | "user_deny" | "user_allow" | "role" | "legacy_role" | "none";
  roleIds?: number[];
};

const SCOPE_WEIGHT: Record<PermissionScope, number> = {
  none: 0,
  own: 10,
  assigned: 20,
  created_by: 30,
  team: 40,
  department: 50,
  custom: 60,
  all: 100,
};

function rows(result: any): any[] {
  if (Array.isArray(result) && Array.isArray(result[0])) return result[0];
  if (Array.isArray(result)) return result;
  return [];
}

function normalizeRole(role?: string | null) {
  return String(role ?? "").replace(/[\s_-]+/g, "").toLowerCase();
}

function normalizeEmail(email?: string | null) {
  return String(email ?? "").trim().toLowerCase();
}

export function isPermissionSuperAdmin(user?: PermissionUser | null): boolean {
  if (!user) return false;
  const role = normalizeRole(user.role);
  if (role === "superadmin") return true;

  const configured = String(process.env.PERMISSIONS_SUPER_ADMIN_EMAILS ?? "")
    .split(",")
    .map(normalizeEmail)
    .filter(Boolean);
  if (configured.includes(normalizeEmail(user.email))) return true;

  if (role === "admin" && process.env.PERMISSIONS_LEGACY_ADMIN_BYPASS !== "false") return true;
  return false;
}

function strongestScope(scopes: Array<PermissionScope | null | undefined>): PermissionScope {
  return scopes.reduce<PermissionScope>((best, item) => {
    const current = item && item in SCOPE_WEIGHT ? item : "none";
    return SCOPE_WEIGHT[current] > SCOPE_WEIGHT[best] ? current : best;
  }, "none");
}

export async function evaluatePermission(user: PermissionUser, permission: PermissionKey): Promise<PermissionDecision> {
  if (isPermissionSuperAdmin(user)) {
    return { allowed: true, permission, scope: "all", source: "super_admin" };
  }

  const db = await getDb();
  if (!db) return { allowed: false, permission, scope: "none", source: "none" };

  const userId = Number(user.id);
  if (!Number.isFinite(userId) || userId <= 0) return { allowed: false, permission, scope: "none", source: "none" };

  const overrideRows = rows(await db.execute(sql`
    SELECT upo.effect, upo.data_scope AS dataScope
    FROM user_permission_overrides upo
    JOIN permissions p ON p.id = upo.permission_id
    WHERE upo.user_id = ${userId}
      AND p.permission_key = ${String(permission)}
      AND p.is_active = 1
      AND (upo.expires_at IS NULL OR upo.expires_at > NOW())
    ORDER BY CASE WHEN upo.effect = 'deny' THEN 0 ELSE 1 END, upo.id DESC
  `));

  const deny = overrideRows.find((r: any) => String(r.effect) === "deny");
  if (deny) return { allowed: false, permission, scope: "none", source: "user_deny" };

  const allows = overrideRows.filter((r: any) => String(r.effect) === "allow");
  if (allows.length) {
    return {
      allowed: true,
      permission,
      scope: strongestScope(allows.map((r: any) => String(r.dataScope || "all") as PermissionScope)),
      source: "user_allow",
    };
  }

  const roleRows = rows(await db.execute(sql`
    SELECT r.id AS roleId, rp.effect, rp.data_scope AS dataScope
    FROM user_roles ur
    JOIN roles r ON r.id = ur.role_id AND r.is_active = 1
    JOIN role_permissions rp ON rp.role_id = r.id
    JOIN permissions p ON p.id = rp.permission_id AND p.is_active = 1
    WHERE ur.user_id = ${userId}
      AND ur.is_active = 1
      AND (ur.expires_at IS NULL OR ur.expires_at > NOW())
      AND p.permission_key = ${String(permission)}
  `));

  if (roleRows.some((r: any) => String(r.effect) === "deny")) {
    return { allowed: false, permission, scope: "none", source: "role", roleIds: roleRows.map((r: any) => Number(r.roleId)) };
  }

  const roleAllows = roleRows.filter((r: any) => String(r.effect) === "allow");
  if (roleAllows.length) {
    return {
      allowed: true,
      permission,
      scope: strongestScope(roleAllows.map((r: any) => String(r.dataScope || "all") as PermissionScope)),
      source: "role",
      roleIds: roleAllows.map((r: any) => Number(r.roleId)),
    };
  }

  const legacyRole = String(user.role ?? "").trim();
  if (legacyRole) {
    const legacyRows = rows(await db.execute(sql`
      SELECT rp.effect, rp.data_scope AS dataScope, r.id AS roleId
      FROM roles r
      JOIN role_permissions rp ON rp.role_id = r.id
      JOIN permissions p ON p.id = rp.permission_id
      WHERE r.legacy_role_key = ${legacyRole}
        AND r.is_active = 1
        AND p.is_active = 1
        AND p.permission_key = ${String(permission)}
    `));
    if (legacyRows.some((r: any) => String(r.effect) === "deny")) {
      return { allowed: false, permission, scope: "none", source: "legacy_role" };
    }
    const legacyAllows = legacyRows.filter((r: any) => String(r.effect) === "allow");
    if (legacyAllows.length) {
      return {
        allowed: true,
        permission,
        scope: strongestScope(legacyAllows.map((r: any) => String(r.dataScope || "all") as PermissionScope)),
        source: "legacy_role",
        roleIds: legacyAllows.map((r: any) => Number(r.roleId)),
      };
    }
  }

  return { allowed: false, permission, scope: "none", source: "none" };
}

export async function hasPermission(user: PermissionUser, permission: PermissionKey): Promise<boolean> {
  return (await evaluatePermission(user, permission)).allowed;
}

export async function hasAnyPermission(user: PermissionUser, permissions: PermissionKey[]): Promise<boolean> {
  for (const permission of permissions) {
    if (await hasPermission(user, permission)) return true;
  }
  return false;
}

export async function requirePermission(user: PermissionUser, permission: PermissionKey) {
  const decision = await evaluatePermission(user, permission);
  if (!decision.allowed) {
    const error: any = new Error(`Permission denied: ${permission}`);
    error.code = "PERMISSION_DENIED";
    error.permission = permission;
    error.decision = decision;
    throw error;
  }
  return decision;
}
'''

    procedure = r'''import { TRPCError } from "@trpc/server";
import type { PermissionKey } from "./permissionCatalog";
import { evaluatePermission } from "./permissionEngine";

export function permissionMiddlewareFactory(t: any, permission: PermissionKey) {
  return t.middleware(async (opts: any) => {
    const user = opts.ctx?.user;
    if (!user) throw new TRPCError({ code: "UNAUTHORIZED", message: "Authentication required" });
    const decision = await evaluatePermission(user, permission);
    if (!decision.allowed) {
      throw new TRPCError({ code: "FORBIDDEN", message: `Permission denied: ${permission}` });
    }
    return opts.next({ ctx: { ...opts.ctx, permissionDecision: decision } });
  });
}

export function anyPermissionMiddlewareFactory(t: any, permissions: PermissionKey[]) {
  return t.middleware(async (opts: any) => {
    const user = opts.ctx?.user;
    if (!user) throw new TRPCError({ code: "UNAUTHORIZED", message: "Authentication required" });
    for (const permission of permissions) {
      const decision = await evaluatePermission(user, permission);
      if (decision.allowed) return opts.next({ ctx: { ...opts.ctx, permissionDecision: decision } });
    }
    throw new TRPCError({ code: "FORBIDDEN", message: `Permission denied: ${permissions.join(" | ")}` });
  });
}
'''

    migration = r'''import { sql } from "drizzle-orm";
import { getDb } from "../server/db";
import { PHASE1_PERMISSION_CATALOG } from "../server/security/permissionCatalog";

const LEGACY_ROLES = [
  "Admin", "Developer", "SalesManager", "SalesAgent", "ColdSalesAgent", "TechnicalAccountManager",
  "ServiceAdvisor", "PartsAgent", "CrmFollowUp", "Viewer", "MediaBuyer", "AccountManager",
  "AccountManagerLead", "BusinessDeveloper", "Moderator",
];

async function main() {
  const db = await getDb();
  if (!db) throw new Error("DATABASE_URL is required");

  const statements = [
    `CREATE TABLE IF NOT EXISTS roles (
      id INT NOT NULL AUTO_INCREMENT,
      role_key VARCHAR(100) NOT NULL,
      name VARCHAR(150) NOT NULL,
      name_ar VARCHAR(150) NULL,
      description TEXT NULL,
      legacy_role_key VARCHAR(100) NULL,
      parent_role_id INT NULL,
      is_system TINYINT NOT NULL DEFAULT 0,
      is_active TINYINT NOT NULL DEFAULT 1,
      created_by INT NULL,
      updated_by INT NULL,
      created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (id),
      UNIQUE KEY uq_roles_role_key (role_key),
      UNIQUE KEY uq_roles_legacy_role_key (legacy_role_key),
      KEY idx_roles_parent (parent_role_id),
      KEY idx_roles_active (is_active)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`,
    `CREATE TABLE IF NOT EXISTS permissions (
      id INT NOT NULL AUTO_INCREMENT,
      permission_key VARCHAR(190) NOT NULL,
      module_key VARCHAR(100) NOT NULL,
      action_key VARCHAR(100) NOT NULL,
      name VARCHAR(190) NOT NULL,
      description TEXT NULL,
      is_sensitive TINYINT NOT NULL DEFAULT 0,
      is_active TINYINT NOT NULL DEFAULT 1,
      created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (id),
      UNIQUE KEY uq_permissions_key (permission_key),
      KEY idx_permissions_module (module_key),
      KEY idx_permissions_active (is_active)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`,
    `CREATE TABLE IF NOT EXISTS role_permissions (
      id INT NOT NULL AUTO_INCREMENT,
      role_id INT NOT NULL,
      permission_id INT NOT NULL,
      effect ENUM('allow','deny') NOT NULL DEFAULT 'allow',
      data_scope ENUM('all','team','department','own','assigned','created_by','custom','none') NOT NULL DEFAULT 'all',
      scope_config JSON NULL,
      created_by INT NULL,
      created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (id),
      UNIQUE KEY uq_role_permission (role_id, permission_id),
      KEY idx_role_permissions_permission (permission_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`,
    `CREATE TABLE IF NOT EXISTS user_roles (
      id INT NOT NULL AUTO_INCREMENT,
      user_id INT NOT NULL,
      role_id INT NOT NULL,
      is_primary TINYINT NOT NULL DEFAULT 0,
      is_active TINYINT NOT NULL DEFAULT 1,
      starts_at TIMESTAMP NULL,
      expires_at TIMESTAMP NULL,
      assigned_by INT NULL,
      created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (id),
      UNIQUE KEY uq_user_role (user_id, role_id),
      KEY idx_user_roles_user_active (user_id, is_active),
      KEY idx_user_roles_role (role_id),
      KEY idx_user_roles_expiry (expires_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`,
    `CREATE TABLE IF NOT EXISTS user_permission_overrides (
      id INT NOT NULL AUTO_INCREMENT,
      user_id INT NOT NULL,
      permission_id INT NOT NULL,
      effect ENUM('allow','deny') NOT NULL,
      data_scope ENUM('all','team','department','own','assigned','created_by','custom','none') NOT NULL DEFAULT 'all',
      scope_config JSON NULL,
      starts_at TIMESTAMP NULL,
      expires_at TIMESTAMP NULL,
      reason VARCHAR(500) NULL,
      created_by INT NULL,
      created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (id),
      UNIQUE KEY uq_user_permission_override (user_id, permission_id),
      KEY idx_user_overrides_user (user_id),
      KEY idx_user_overrides_expiry (expires_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`,
    `CREATE TABLE IF NOT EXISTS permission_audit_logs (
      id BIGINT NOT NULL AUTO_INCREMENT,
      actor_user_id INT NULL,
      target_user_id INT NULL,
      target_role_id INT NULL,
      action VARCHAR(100) NOT NULL,
      permission_key VARCHAR(190) NULL,
      previous_value JSON NULL,
      new_value JSON NULL,
      reason VARCHAR(500) NULL,
      metadata JSON NULL,
      created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (id),
      KEY idx_permission_audit_actor (actor_user_id),
      KEY idx_permission_audit_target_user (target_user_id),
      KEY idx_permission_audit_target_role (target_role_id),
      KEY idx_permission_audit_created (created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`,
  ];

  for (const statement of statements) await db.execute(sql.raw(statement));

  for (const key of PHASE1_PERMISSION_CATALOG) {
    const [moduleKey, ...actionParts] = String(key).split(".");
    const actionKey = actionParts.join(".") || "view";
    await db.execute(sql`
      INSERT INTO permissions (permission_key, module_key, action_key, name)
      VALUES (${String(key)}, ${moduleKey}, ${actionKey}, ${String(key)})
      ON DUPLICATE KEY UPDATE module_key = VALUES(module_key), action_key = VALUES(action_key), is_active = 1
    `);
  }

  for (const legacyRole of LEGACY_ROLES) {
    const roleKey = `legacy.${legacyRole.replace(/([a-z])([A-Z])/g, "$1_$2").toLowerCase()}`;
    await db.execute(sql`
      INSERT INTO roles (role_key, name, legacy_role_key, is_system, is_active)
      VALUES (${roleKey}, ${legacyRole}, ${legacyRole}, 1, 1)
      ON DUPLICATE KEY UPDATE name = VALUES(name), is_active = 1
    `);
  }

  await db.execute(sql.raw(`
    INSERT IGNORE INTO user_roles (user_id, role_id, is_primary, is_active)
    SELECT u.id, r.id, 1, 1
    FROM users u
    JOIN roles r ON r.legacy_role_key = u.role
    WHERE u.deletedAt IS NULL
  `));

  // Compatibility seed: Admin gets all permissions during rollout; Viewer only gets common read permissions.
  await db.execute(sql.raw(`
    INSERT IGNORE INTO role_permissions (role_id, permission_id, effect, data_scope)
    SELECT r.id, p.id, 'allow', 'all'
    FROM roles r CROSS JOIN permissions p
    WHERE r.legacy_role_key = 'Admin'
  `));
  await db.execute(sql.raw(`
    INSERT IGNORE INTO role_permissions (role_id, permission_id, effect, data_scope)
    SELECT r.id, p.id, 'allow', 'all'
    FROM roles r JOIN permissions p ON p.action_key = 'view'
    WHERE r.legacy_role_key = 'Viewer'
  `));

  console.log("Advanced permissions Phase 1 migration completed.");
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
'''

    verify = r'''import { sql } from "drizzle-orm";
import { getDb } from "../server/db";
import { PHASE1_PERMISSION_CATALOG } from "../server/security/permissionCatalog";

function rows(result: any): any[] {
  if (Array.isArray(result) && Array.isArray(result[0])) return result[0];
  if (Array.isArray(result)) return result;
  return [];
}

async function main() {
  const db = await getDb();
  if (!db) throw new Error("DATABASE_URL is required");
  const required = ["roles", "permissions", "role_permissions", "user_roles", "user_permission_overrides", "permission_audit_logs"];
  const tableRows = rows(await db.execute(sql.raw(`SELECT TABLE_NAME AS name FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE()`)));
  const names = new Set(tableRows.map((r: any) => String(r.name)));
  for (const table of required) if (!names.has(table)) throw new Error(`Missing table: ${table}`);

  const permissionRows = rows(await db.execute(sql.raw(`SELECT COUNT(*) AS count FROM permissions WHERE is_active = 1`)));
  const permissionCount = Number(permissionRows[0]?.count ?? 0);
  if (permissionCount < PHASE1_PERMISSION_CATALOG.length) throw new Error(`Permission catalog incomplete: ${permissionCount}`);

  const duplicateRows = rows(await db.execute(sql.raw(`SELECT user_id, role_id, COUNT(*) c FROM user_roles GROUP BY user_id, role_id HAVING c > 1 LIMIT 1`)));
  if (duplicateRows.length) throw new Error("Duplicate user_roles detected");

  console.log(JSON.stringify({ ok: true, tables: required.length, permissionCount }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
'''

    write_text(root / "server/security/permissionCatalog.ts", catalog)
    write_text(root / "server/security/permissionEngine.ts", engine)
    write_text(root / "server/security/permissionProcedure.ts", procedure)
    write_text(root / "scripts/apply-advanced-permissions-phase1-migration.ts", migration)
    write_text(root / "scripts/verify-advanced-permissions-phase1.ts", verify)

    package_path = root / "package.json"
    package = json.loads(package_path.read_text(encoding="utf-8"))
    scripts = package.setdefault("scripts", {})
    scripts["db:migrate:advanced-permissions-phase1"] = "tsx scripts/apply-advanced-permissions-phase1-migration.ts"
    scripts["verify:advanced-permissions-phase1"] = "tsx scripts/verify-advanced-permissions-phase1.ts"
    package_path.write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[patch] {package_path}")

    trpc_path = root / "server/_core/trpc.ts"
    import_marker = 'import { getDeveloperAccessDenialReason } from "../utils/developerAccessPolicy";'
    import_replacement = import_marker + '\nimport type { PermissionKey } from "../security/permissionCatalog";\nimport { evaluatePermission } from "../security/permissionEngine";'
    patch_once(trpc_path, import_marker, import_replacement)

    export_marker = '''export const protectedProcedure = moderatorDenyByDefault
  .use(centralMutationAudit as any)
  .use(developerAccessProtection as any)
  .use(developerDataProtection as any);'''
    export_replacement = export_marker + r'''

// ADVANCED_PERMISSIONS_PHASE1_V1
// Reusable permission guards. Existing routers remain unchanged until module integration phases.
export const permissionProcedure = (permission: PermissionKey) =>
  protectedProcedure.use(
    t.middleware(async (opts) => {
      const decision = await evaluatePermission(opts.ctx.user, permission);
      if (!decision.allowed) {
        throw new TRPCError({ code: "FORBIDDEN", message: `Permission denied: ${permission}` });
      }
      return opts.next({ ctx: { ...opts.ctx, permissionDecision: decision } as any });
    }),
  );

export const anyPermissionProcedure = (permissions: PermissionKey[]) =>
  protectedProcedure.use(
    t.middleware(async (opts) => {
      for (const permission of permissions) {
        const decision = await evaluatePermission(opts.ctx.user, permission);
        if (decision.allowed) {
          return opts.next({ ctx: { ...opts.ctx, permissionDecision: decision } as any });
        }
      }
      throw new TRPCError({ code: "FORBIDDEN", message: `Permission denied: ${permissions.join(" | ")}` });
    }),
  );'''
    patch_once(trpc_path, export_marker, export_replacement)

    print("\nPhase 1 patch applied. Next run:")
    print("  pnpm db:migrate:advanced-permissions-phase1")
    print("  pnpm verify:advanced-permissions-phase1")
    print("  pnpm check")


if __name__ == "__main__":
    main()
