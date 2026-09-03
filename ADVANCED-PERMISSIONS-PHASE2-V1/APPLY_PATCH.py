#!/usr/bin/env python3
from pathlib import Path
import shutil
import sys
import time

PATCH_ROOT = Path(__file__).resolve().parent
FILES_ROOT = PATCH_ROOT / "files"
MARKER = "ADVANCED_PERMISSIONS_PHASE2_V1"

NEW_FILES = [
    "server/security/permissionAdminService.ts",
    "server/permissionsAdminRouter.ts",
    "client/src/pages/RolesPermissions.tsx",
    "scripts/verify-advanced-permissions-phase2.ts",
]


def die(message: str):
    print(f"[Phase2] ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: Path) -> str:
    if not path.exists():
        die(f"Missing expected TCRM file: {path}")
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def backup(path: Path, backup_root: Path, project: Path):
    if not path.exists():
        return
    rel = path.relative_to(project)
    dest = backup_root / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dest)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        die(f"Expected exactly one marker for {label}; found {count}. Refusing blind patch.")
    return text.replace(old, new, 1)


def main():
    project = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    required = [
        project / "package.json",
        project / "server/_core/trpc.ts",
        project / "server/security/permissionCatalog.ts",
        project / "server/security/permissionEngine.ts",
        project / "server/routers.ts",
        project / "client/src/App.tsx",
        project / "client/src/components/CRMLayout.tsx",
        project / "client/src/lib/i18n.ts",
    ]
    for p in required:
        if not p.exists():
            die(f"Not a compatible TCRM checkout; missing {p.relative_to(project)}")

    phase1 = read(project / "server/security/permissionCatalog.ts")
    if "PHASE1_PERMISSION_CATALOG" not in phase1 or "roles.assign_permissions" not in phase1:
        die("Advanced Permissions Phase 1 is not present. Apply Phase 1 first.")
    trpc = read(project / "server/_core/trpc.ts")
    if "export const permissionProcedure" not in trpc:
        die("Phase 1 permissionProcedure is missing. Apply Phase 1 first.")

    backup_root = project / ".patch-backups" / f"advanced-permissions-phase2-{int(time.time())}"
    modified = [
        project / "server/routers.ts",
        project / "client/src/App.tsx",
        project / "client/src/components/CRMLayout.tsx",
        project / "client/src/lib/i18n.ts",
    ]
    for p in modified + [project / rel for rel in NEW_FILES]:
        backup(p, backup_root, project)

    for rel in NEW_FILES:
        source = FILES_ROOT / rel
        if not source.exists():
            die(f"Patch package is incomplete: missing files/{rel}")
        target = project / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        print(f"[Phase2] installed {rel}")

    # server/routers.ts: import and register the new router.
    path = project / "server/routers.ts"
    text = read(path)
    if 'import { permissionsAdminRouter } from "./permissionsAdminRouter";' not in text:
        anchor = 'import { protectedProcedure, publicProcedure, router } from "./_core/trpc";'
        text = replace_once(text, anchor, 'import { permissionsAdminRouter } from "./permissionsAdminRouter";\n' + anchor, "server router import")
    if "permissionsAdmin: permissionsAdminRouter" not in text:
        anchor = "export const appRouter = router({\n"
        text = replace_once(text, anchor, anchor + f"  // {MARKER}\n  permissionsAdmin: permissionsAdminRouter,\n", "appRouter registration")
    write(path, text)

    # client/src/App.tsx: page import and route.
    path = project / "client/src/App.tsx"
    text = read(path)
    if 'import RolesPermissions from "./pages/RolesPermissions";' not in text:
        anchor = 'import AdminSettings from "./pages/AdminSettings";'
        text = replace_once(text, anchor, anchor + '\nimport RolesPermissions from "./pages/RolesPermissions";', "RolesPermissions import")
    if 'path="/settings/roles-permissions"' not in text:
        anchor = '      <Route path="/settings" component={AdminSettings} />'
        text = replace_once(text, anchor, '      <Route path="/settings/roles-permissions" component={RolesPermissions} />\n' + anchor, "RolesPermissions route")
    write(path, text)

    # CRMLayout: Admin-only navigation entry next to Settings. This is a UI hint only;
    # server authorization remains authoritative.
    path = project / "client/src/components/CRMLayout.tsx"
    text = read(path)
    if "Shield," not in text:
        text = replace_once(text, "  Settings,\n", "  Settings,\n  Shield,\n", "Shield icon import")
    if 'href: "/settings/roles-permissions"' not in text:
        settings_block = '''    {\n      href: "/settings",\n      labelKey: "settings",\n      icon: <Settings size={18} />,\n      roles: ["Admin", "SalesManager", "SalesAgent", "ColdSalesAgent", "ServiceAdvisor", "PartsAgent", "CrmFollowUp", "MediaBuyer"],\n    },'''
        role_block = '''    {\n      href: "/settings/roles-permissions",\n      labelKey: "rolesPermissions",\n      icon: <Shield size={18} />,\n      roles: ["Admin"],\n    },\n'''
        text = replace_once(text, settings_block, role_block + settings_block, "Roles & Permissions navigation")
    write(path, text)

    # Translation key used by sidebar.
    path = project / "client/src/lib/i18n.ts"
    text = read(path)
    if 'rolesPermissions: "الأدوار والصلاحيات"' not in text:
        text = replace_once(text, '    settings: "الإعدادات",', '    settings: "الإعدادات",\n    rolesPermissions: "الأدوار والصلاحيات",', "Arabic rolesPermissions translation")
    if 'rolesPermissions: "Roles & Permissions"' not in text:
        english_anchor = '    settings: "Settings",'
        text = replace_once(text, english_anchor, english_anchor + '\n    rolesPermissions: "Roles & Permissions",', "English rolesPermissions translation")
    write(path, text)

    print("\n[Phase2] Patch applied successfully.")
    print(f"[Phase2] Backup: {backup_root}")
    print("[Phase2] No database migration was executed and no git command was run.")
    print("\nRun verification:")
    print("  pnpm exec tsx scripts/verify-advanced-permissions-phase2.ts")
    print("  pnpm check")
    print("  pnpm build")
    print("  pnpm test")
    print("\nManual smoke test:")
    print("  1. Login as Admin/Super Admin")
    print("  2. Open /settings/roles-permissions")
    print("  3. Create a custom role, change matrix entries/scopes, save, reload")
    print("  4. Duplicate the custom role")
    print("  5. Confirm system roles cannot be disabled/deleted")
    print("  6. Confirm non-admin users receive FORBIDDEN unless explicitly granted roles.* permissions")


if __name__ == "__main__":
    main()
