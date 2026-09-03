import fs from "node:fs";
import path from "node:path";
import { sql } from "drizzle-orm";
import { getDb } from "../server/db";
import { PHASE1_PERMISSION_CATALOG } from "../server/security/permissionCatalog";

function requireFile(file: string, markers: string[]) {
  const full = path.resolve(process.cwd(), file);
  if (!fs.existsSync(full)) throw new Error(`Missing file: ${file}`);
  const text = fs.readFileSync(full, "utf8");
  for (const marker of markers) if (!text.includes(marker)) throw new Error(`Missing marker in ${file}: ${marker}`);
}

function rows(result: any): any[] {
  if (Array.isArray(result) && Array.isArray(result[0])) return result[0];
  if (Array.isArray(result)) return result;
  return [];
}

async function main() {
  requireFile("server/security/permissionAdminService.ts", ["listPermissionRoles", "replacePermissionRolePermissions", "permission_audit_logs"]);
  requireFile("server/permissionsAdminRouter.ts", ["permissionsAdminRouter", "roles.assign_permissions", "roles.delete"]);
  requireFile("client/src/pages/RolesPermissions.tsx", ["Permission Matrix", "permissionsAdmin.listRoles", "permissionsAdmin.replacePermissions"]);
  requireFile("server/routers.ts", ["permissionsAdminRouter", "permissionsAdmin: permissionsAdminRouter"]);
  requireFile("client/src/App.tsx", ["RolesPermissions", "/settings/roles-permissions"]);

  const db = await getDb();
  if (!db) throw new Error("DATABASE_URL is required for database verification");
  const tableRows = rows(await db.execute(sql.raw(`
    SELECT TABLE_NAME AS tableName FROM information_schema.TABLES
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME IN ('roles','permissions','role_permissions','user_roles','user_permission_overrides','permission_audit_logs')
  `)));
  if (tableRows.length !== 6) throw new Error(`Phase 1 permission tables missing: found ${tableRows.length}/6`);

  const countRows = rows(await db.execute(sql`SELECT COUNT(*) AS count FROM permissions WHERE is_active = 1`));
  const permissionCount = Number(countRows[0]?.count || 0);
  if (permissionCount < PHASE1_PERMISSION_CATALOG.length) throw new Error(`Permission catalog incomplete: ${permissionCount}`);

  const invalidRows = rows(await db.execute(sql.raw(`
    SELECT COUNT(*) AS count FROM role_permissions rp
    LEFT JOIN roles r ON r.id = rp.role_id
    LEFT JOIN permissions p ON p.id = rp.permission_id
    WHERE r.id IS NULL OR p.id IS NULL
  `)));
  if (Number(invalidRows[0]?.count || 0) !== 0) throw new Error("Orphan role_permissions detected");

  console.log(JSON.stringify({
    ok: true,
    phase: 2,
    tables: tableRows.length,
    permissionCount,
    ui: "/settings/roles-permissions",
    note: "Phase 2 manages roles and role_permissions only; data-scope query enforcement remains deferred to Phase 3.",
  }, null, 2));
}

main().catch(error => {
  console.error("Advanced Permissions Phase 2 verification failed:", error);
  process.exit(1);
});
