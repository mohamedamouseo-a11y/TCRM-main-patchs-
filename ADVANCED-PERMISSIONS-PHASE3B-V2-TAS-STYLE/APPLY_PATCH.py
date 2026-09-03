#!/usr/bin/env python3
from pathlib import Path
import shutil, subprocess, sys, time

ROOT = Path(__file__).resolve().parent
TARGET = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TCRM-MAIN").resolve()
REPO_ROOT = ROOT.parent
V1 = REPO_ROOT / "ADVANCED-PERMISSIONS-PHASE3B-V1" / "APPLY_PATCH.py"
FILES = ROOT / "files"
BACKUP = TARGET / ".patch-backups" / f"advanced-permissions-phase3b-v2-{int(time.time())}"

if not V1.exists():
    raise SystemExit(f"Missing Phase3B V1 applier: {V1}")

# Apply reviewed Phase3B backend enforcement first.
subprocess.run([sys.executable, str(V1), str(TARGET)], check=True)

required = [
    TARGET / "server/permissionsAdminRouter.ts",
    TARGET / "server/security/permissionAdminService.ts",
    TARGET / "server/roleUtils.ts",
    TARGET / "client/src/lib/roles.ts",
    TARGET / "scripts/apply-advanced-permissions-phase1-migration.ts",
]
for p in required:
    if not p.exists():
        raise SystemExit(f"Missing required file: {p}")

BACKUP.mkdir(parents=True, exist_ok=True)
for rel in [
    "server/permissionsAdminRouter.ts",
    "server/security/permissionAdminService.ts",
    "server/roleUtils.ts",
    "client/src/lib/roles.ts",
    "scripts/apply-advanced-permissions-phase1-migration.ts",
]:
    src = TARGET / rel
    dst = BACKUP / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

# Replace active role catalogs; legacy compatibility remains inside the files.
for rel in ["server/roleUtils.ts", "client/src/lib/roles.ts", "server/security/permissionUserOverrideAdmin.ts"]:
    src = FILES / rel
    dst = TARGET / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

# Future installs: do not seed automotive-only roles into TCRM RBAC.
migration_path = TARGET / "scripts/apply-advanced-permissions-phase1-migration.ts"
migration = migration_path.read_text()
migration = migration.replace('  "ServiceAdvisor", "PartsAgent", "CrmFollowUp", "Viewer", "MediaBuyer", "AccountManager",\n', '  "Viewer", "MediaBuyer", "AccountManager",\n')
if "ServiceAdvisor\", \"PartsAgent\", \"CrmFollowUp" in migration.split("const LEGACY_ROLES", 1)[1].split("];", 1)[0]:
    raise SystemExit("Could not remove automotive-only roles from Phase1 LEGACY_ROLES")
migration_path.write_text(migration)

# Hide any previously seeded automotive system roles from the RBAC admin list without deleting DB rows.
service_path = TARGET / "server/security/permissionAdminService.ts"
service = service_path.read_text()
needle = "    FROM roles r\n    LEFT JOIN user_roles ur ON ur.role_id = r.id\n    LEFT JOIN role_permissions rp ON rp.role_id = r.id\n    GROUP BY r.id\n"
replacement = "    FROM roles r\n    LEFT JOIN user_roles ur ON ur.role_id = r.id\n    LEFT JOIN role_permissions rp ON rp.role_id = r.id\n    WHERE COALESCE(r.legacy_role_key, '') NOT IN ('ServiceAdvisor','PartsAgent','CrmFollowUp')\n    GROUP BY r.id\n"
if replacement not in service:
    if needle not in service:
        raise SystemExit("permissionAdminService role-list anchor changed")
    service = service.replace(needle, replacement, 1)
service_path.write_text(service)

# Add user-override admin API routes.
router_path = TARGET / "server/permissionsAdminRouter.ts"
r = router_path.read_text()
if 'permissionUserOverrideAdmin' not in r:
    import_anchor = '} from "./security/permissionAdminService";\n'
    extra = '''} from "./security/permissionAdminService";\nimport {\n  getPermissionUserProfile,\n  listPermissionUsers,\n  replacePermissionUserOverrides,\n} from "./security/permissionUserOverrideAdmin";\n'''
    if import_anchor not in r:
        raise SystemExit("permissionsAdminRouter import anchor changed")
    r = r.replace(import_anchor, extra, 1)

if "listUsersForPermissions:" not in r:
    anchor = '  listRoles: permissionProcedure("roles.view").query(async () => listPermissionRoles()),\n'
    block = anchor + '''  // ADVANCED_PERMISSIONS_PHASE3B_V2_USER_OVERRIDES\n  listUsersForPermissions: permissionProcedure("users.view").query(async () => listPermissionUsers()),\n  getUserPermissionProfile: permissionProcedure("roles.view")\n    .input(z.object({ userId: z.number().int().positive() }))\n    .query(async ({ input }) => getPermissionUserProfile(input.userId)),\n  replaceUserOverrides: permissionProcedure("roles.assign_permissions")\n    .input(z.object({\n      userId: z.number().int().positive(),\n      entries: z.array(z.object({\n        permissionKey: z.string().min(3).max(190),\n        effect: z.enum(["allow", "deny"]),\n        dataScope: z.enum(PERMISSION_SCOPES),\n        scopeConfig: z.record(z.string(), z.unknown()).optional().nullable(),\n        startsAt: z.date().optional().nullable(),\n        expiresAt: z.date().optional().nullable(),\n        reason: z.string().trim().max(500).optional().nullable(),\n      })).max(250),\n    }))\n    .mutation(async ({ ctx, input }) => {\n      try { return await replacePermissionUserOverrides(input.userId, input.entries as any, actorId(ctx)); } catch (error) { return mapError(error); }\n    }),\n'''
    if anchor not in r:
        raise SystemExit("permissionsAdminRouter listRoles anchor changed")
    r = r.replace(anchor, block, 1)
router_path.write_text(r)

print("Phase 3B V2 backend/role cleanup applied.")
print(f"Backup: {BACKUP}")
print("IMPORTANT: follow README UI step to implement TAS-style Basic/Advanced matrix + User Overrides tab.")
