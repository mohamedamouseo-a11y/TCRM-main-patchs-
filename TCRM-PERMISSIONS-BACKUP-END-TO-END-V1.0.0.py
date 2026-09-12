#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

WORKFLOW_SERIES = "TCRM-PERMISSIONS"
MODULE = "BACKUP"
PHASE = "END-TO-END"
VERSION = "V1.0.0"
WORKFLOW_ID = "TCRM-PERMISSIONS-BACKUP-END-TO-END-V1.0.0"
BASELINE = "846cbdbf610bd6d118b05272db76b262c701be6b"
ROOT = Path.cwd()

EXPECTED = {
    "client/src/contexts/PermissionContext.tsx",
    "client/src/pages/AdminSettings.tsx",
    "client/src/components/BackupTab.tsx",
    "client/src/components/DatabaseBackupSettingsTab.tsx",
    "server/security/corePermissionPolicy.ts",
    "server/routes/tcrmDatabaseBackup.ts",
    "server/_core/index.ts",
    "server/security/backupPermissionFinal.test.ts",
}


def fail(message: str) -> None:
    print(f"ERROR={message}", file=sys.stderr)
    raise SystemExit(1)


def run(*args: str) -> str:
    p = subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        fail(f"COMMAND_FAILED:{' '.join(args)}:{p.stderr.strip()}")
    return p.stdout.strip()


def read(rel: str) -> str:
    p = ROOT / rel
    if not p.exists():
        fail(f"MISSING_FILE:{rel}")
    return p.read_text(encoding="utf-8")


def write(rel: str, text: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def rep(text: str, old: str, new: str, label: str, expected: int = 1) -> str:
    count = text.count(old)
    if count != expected:
        fail(f"ANCHOR_DRIFT:{label}:count={count}:expected={expected}")
    return text.replace(old, new)


def dirty_paths() -> set[str]:
    tracked = set(filter(None, run("git", "diff", "--name-only").splitlines()))
    untracked = set(filter(None, run("git", "ls-files", "--others", "--exclude-standard").splitlines()))
    return tracked | untracked


head = run("git", "rev-parse", "HEAD")
if head != BASELINE:
    fail(f"BASELINE_MISMATCH:{head}")
if run("git", "diff", "--cached", "--name-only"):
    fail("STAGED_CHANGES_PRESENT")
if dirty_paths():
    fail(f"WORKTREE_NOT_CLEAN:{sorted(dirty_paths())}")

# ---------------------------------------------------------------------------
# Frontend permission decisions and direct Settings tab routing.
# ---------------------------------------------------------------------------
ctx_rel = "client/src/contexts/PermissionContext.tsx"
ctx = read(ctx_rel)
ctx = rep(
    ctx,
    '  "notifications.view",\n  "notifications.manage",\n] as const;',
    '  "notifications.view",\n  "notifications.manage",\n  "backup.view",\n  "backup.run",\n  "backup.restore",\n  "backup.manage",\n] as const;',
    "context-backup-keys",
)
ctx = rep(
    ctx,
    '''  if ((pathname === "/settings" || pathname === "/admin") && ["notifications", "meetingNotifs"].includes(query.get("tab") || "")) {
    return "notifications.view";
  }
  if (pathname === "/admin") return "settings.view";
''',
    '''  if ((pathname === "/settings" || pathname === "/admin") && ["notifications", "meetingNotifs"].includes(query.get("tab") || "")) {
    return "notifications.view";
  }
  if ((pathname === "/settings" || pathname === "/admin") && ["backup", "databaseBackup"].includes(query.get("tab") || "")) {
    return "backup.view";
  }
  if (pathname === "/admin") return "settings.view";
''',
    "context-backup-tab-route",
)
write(ctx_rel, ctx)

# ---------------------------------------------------------------------------
# Central tRPC permission selection. Cover both current Backup Center endpoints
# and legacy backup/archive endpoints living under admin.* without broad-gating
# unrelated admin operations.
# ---------------------------------------------------------------------------
policy_rel = "server/security/corePermissionPolicy.ts"
policy = read(policy_rel)
policy = rep(
    policy,
    '''  if (root === "notificationPreferences") {
    // Per-user get/update preferences are self-service and stay user-scoped.
    // Only the shared system sound mutation surface is global administration.
    if (["uploadsound", "removesound"].includes(operation)) return "notifications.manage";
    return null;
  }

  const module = moduleFromPath(path);
''',
    '''  if (root === "notificationPreferences") {
    // Per-user get/update preferences are self-service and stay user-scoped.
    // Only the shared system sound mutation surface is global administration.
    if (["uploadsound", "removesound"].includes(operation)) return "notifications.manage";
    return null;
  }

  // TCRM_PERMISSIONS_BACKUP_END_TO_END_V1
  // Backup permissions apply only to explicit backup operations under admin.*.
  // Existing Admin/SuperAdmin/Primary-SuperAdmin guards remain additive.
  if (root === "admin") {
    if ([
      "getbackupcentersettings",
      "getbackupcenterjobs",
      "getbackupcenterrestorelogs",
      "getbackups",
      "getautobackupsettings",
      "getarchivestats",
    ].includes(operation)) return "backup.view";

    if (["runbackupcenternow", "retrybackupcenterjob", "createbackup", "runmanualfullbackup"].includes(operation)) {
      return "backup.run";
    }

    if (operation === "restorebackupcenterartifact") return "backup.restore";

    if ([
      "savebackupcentersettings",
      "deletebackup",
      "saveautobackupsettings",
      "testbackupemail",
      "archivedata",
    ].includes(operation)) return "backup.manage";
  }

  const module = moduleFromPath(path);
''',
    "policy-backup",
)
write(policy_rel, policy)

# ---------------------------------------------------------------------------
# Admin Settings visibility: preserve SuperAdmin guard and add backup.view.
# ---------------------------------------------------------------------------
admin_rel = "client/src/pages/AdminSettings.tsx"
admin = read(admin_rel)
admin = rep(
    admin,
    '  const canNotificationsView = can("notifications.view");\n  const canSettingsEdit = can("settings.edit");',
    '  const canNotificationsView = can("notifications.view");\n  const canBackupView = can("backup.view");\n  const canSettingsEdit = can("settings.edit");',
    "admin-backup-flag",
)
admin = rep(
    admin,
    '{ value: "backup", label: isRTL ? "النسخ الاحتياطية" : "Backup", description: isRTL ? "نسخ واسترجاع آمن" : "Safe backup and restore", icon: <Archive size={14} />, visible: isSuperAdmin, badge: "Admin" },',
    '{ value: "backup", label: isRTL ? "النسخ الاحتياطية" : "Backup", description: isRTL ? "نسخ واسترجاع آمن" : "Safe backup and restore", icon: <Archive size={14} />, visible: isSuperAdmin && canBackupView, badge: "Admin" },',
    "admin-backup-visible",
)
admin = rep(
    admin,
    '{ value: "databaseBackup", label: isRTL ? "نسخ قاعدة البيانات" : "Database Backup", description: isRTL ? "نسخ MySQL مشفرة على Google Drive" : "Encrypted MySQL backups to Google Drive", icon: <Archive size={14} />, visible: isSuperAdmin, badge: "Admin" },',
    '{ value: "databaseBackup", label: isRTL ? "نسخ قاعدة البيانات" : "Database Backup", description: isRTL ? "نسخ MySQL مشفرة على Google Drive" : "Encrypted MySQL backups to Google Drive", icon: <Archive size={14} />, visible: isSuperAdmin && canBackupView, badge: "Admin" },',
    "admin-db-backup-visible",
)
admin = rep(
    admin,
    '{isSuperAdmin && <TabsContent value="backup" className="mt-4">',
    '{isSuperAdmin && canBackupView && <TabsContent value="backup" className="mt-4">',
    "admin-backup-content",
)
admin = rep(
    admin,
    '{isSuperAdmin && <TabsContent value="databaseBackup" className="mt-4">',
    '{isSuperAdmin && canBackupView && <TabsContent value="databaseBackup" className="mt-4">',
    "admin-db-backup-content",
)
write(admin_rel, admin)

# ---------------------------------------------------------------------------
# Backup Center UI: view remains available to existing SuperAdmin surface, while
# save/run/retry/restore actions require their distinct canonical permissions.
# ---------------------------------------------------------------------------
backup_rel = "client/src/components/BackupTab.tsx"
backup = read(backup_rel)
backup = rep(
    backup,
    'import { useLanguage } from "@/contexts/LanguageContext";\n',
    'import { useLanguage } from "@/contexts/LanguageContext";\nimport { usePermissions } from "@/contexts/PermissionContext";\n',
    "backup-import",
)
backup = rep(
    backup,
    '''export default function BackupTab() {
  const { isRTL } = useLanguage();
  const [settings, setSettings]''',
    '''export default function BackupTab() {
  const { isRTL } = useLanguage();
  const { can } = usePermissions();
  const canBackupManage = can("backup.manage");
  const canBackupRun = can("backup.run");
  const canBackupRestore = can("backup.restore");
  const [settings, setSettings]''',
    "backup-flags",
)
backup = rep(
    backup,
    '''  const handleSave = () => {
    const nullableStringKeys''',
    '''  const handleSave = () => {
    if (!canBackupManage) return;
    const nullableStringKeys''',
    "backup-save-guard",
)
backup = rep(
    backup,
    '''  const handleRunNow = () => {
    runNowMutation.mutate({''',
    '''  const handleRunNow = () => {
    if (!canBackupRun) return;
    runNowMutation.mutate({''',
    "backup-run-guard",
)
backup = rep(
    backup,
    '''  const handleRestore = (artifact: any) => {
    const isDatabaseRestore''',
    '''  const handleRestore = (artifact: any) => {
    if (!canBackupRestore) return;
    const isDatabaseRestore''',
    "backup-restore-guard",
)
backup = rep(
    backup,
    'disabled={!dirty || saveMutation.isLoading}',
    'disabled={!canBackupManage || !dirty || saveMutation.isLoading}',
    "backup-save-button",
)
backup = rep(
    backup,
    'disabled={runNowMutation.isLoading || hasActiveJob}',
    'disabled={!canBackupRun || runNowMutation.isLoading || hasActiveJob}',
    "backup-run-button",
)
backup = rep(
    backup,
    'onClick={() => retryMutation.mutate({ jobId: job.id })} disabled={retryMutation.isLoading}',
    'onClick={() => retryMutation.mutate({ jobId: job.id })} disabled={!canBackupRun || retryMutation.isLoading}',
    "backup-retry-button",
)
backup = rep(
    backup,
    'onClick={() => handleRestore(artifact)} disabled={restoreMutation.isLoading || hasActiveRestore}',
    'onClick={() => handleRestore(artifact)} disabled={!canBackupRestore || restoreMutation.isLoading || hasActiveRestore}',
    "backup-restore-button",
)
write(backup_rel, backup)

# ---------------------------------------------------------------------------
# Dedicated database-backup UI uses direct REST, so gate controls locally and
# enforce the same permissions again on the Express router below.
# ---------------------------------------------------------------------------
dbui_rel = "client/src/components/DatabaseBackupSettingsTab.tsx"
dbui = read(dbui_rel)
dbui = rep(
    dbui,
    'import { useLanguage } from "@/contexts/LanguageContext";\n',
    'import { useLanguage } from "@/contexts/LanguageContext";\nimport { usePermissions } from "@/contexts/PermissionContext";\n',
    "db-backup-import",
)
dbui = rep(
    dbui,
    '''export default function DatabaseBackupSettingsTab(){
  const {isRTL}=useLanguage(); const t=(ar:string,en:string)=>isRTL?ar:en;''',
    '''export default function DatabaseBackupSettingsTab(){
  const {isRTL}=useLanguage(); const {can}=usePermissions(); const canBackupManage=can("backup.manage"),canBackupRun=can("backup.run"); const t=(ar:string,en:string)=>isRTL?ar:en;''',
    "db-backup-flags",
)
dbui = rep(dbui, '  const save=async()=>{setBusy("save");', '  const save=async()=>{if(!canBackupManage)return;setBusy("save");', "db-backup-save-guard")
dbui = rep(dbui, '  const connect=async()=>{setBusy("connect");', '  const connect=async()=>{if(!canBackupManage)return;setBusy("connect");', "db-backup-connect-guard")
dbui = rep(dbui, '  const disconnect=async()=>{if(!confirm(', '  const disconnect=async()=>{if(!canBackupManage)return;if(!confirm(', "db-backup-disconnect-guard")
dbui = rep(dbui, '  const backup=async()=>{if(!confirm(', '  const backup=async()=>{if(!canBackupRun)return;if(!confirm(', "db-backup-run-guard")
dbui = rep(
    dbui,
    '<Switch checked={f.enabled} onCheckedChange={v=>setF(x=>({...x,enabled:v}))}/>',
    '<Switch checked={f.enabled} disabled={!canBackupManage} onCheckedChange={v=>setF(x=>({...x,enabled:v}))}/>',
    "db-backup-enable-switch",
)
dbui = rep(
    dbui,
    '<Button type="button" variant="outline" className="h-11 rounded-xl" onClick={()=>{setEditSecret(true);setF(x=>({...x,clientSecret:""}))}}>',
    '<Button type="button" variant="outline" className="h-11 rounded-xl" disabled={!canBackupManage} onClick={()=>{setEditSecret(true);setF(x=>({...x,clientSecret:""}))}}>',
    "db-backup-secret-button",
)
dbui = rep(dbui, '<Button className="rounded-xl" disabled={!!busy} onClick={save}>', '<Button className="rounded-xl" disabled={!canBackupManage||!!busy} onClick={save}>', "db-backup-save-button")
dbui = rep(dbui, '<Button variant="outline" className="rounded-xl text-primary" disabled={!!busy} onClick={connect}>', '<Button variant="outline" className="rounded-xl text-primary" disabled={!canBackupManage||!!busy} onClick={connect}>', "db-backup-connect-button")
dbui = rep(dbui, '<Button variant="outline" className="rounded-xl text-destructive" disabled={!!busy||!connected} onClick={disconnect}>', '<Button variant="outline" className="rounded-xl text-destructive" disabled={!canBackupManage||!!busy||!connected} onClick={disconnect}>', "db-backup-disconnect-button")
dbui = rep(dbui, '<Button className="rounded-xl" disabled={!!busy||!connected} onClick={backup}>', '<Button className="rounded-xl" disabled={!canBackupRun||!!busy||!connected} onClick={backup}>', "db-backup-run-button")
write(dbui_rel, dbui)

# ---------------------------------------------------------------------------
# Dedicated database backup REST API: preserve existing Admin/non-Developer
# role restriction and add explicit permission checks for view/manage/run.
# ---------------------------------------------------------------------------
dbroute_rel = "server/routes/tcrmDatabaseBackup.ts"
dbroute = read(dbroute_rel)
dbroute = rep(
    dbroute,
    'import { isAdminRole, isDeveloperRole } from "../roleUtils";\n',
    'import { isAdminRole, isDeveloperRole } from "../roleUtils";\nimport { evaluatePermission } from "../security/permissionEngine";\nimport type { PermissionKey } from "../security/permissionCatalog";\n',
    "db-route-imports",
)
dbroute = rep(
    dbroute,
    '  const sendErr=(res:any,e:any)=>res.status(Number(e?.statusCode)||500).json({error:e?.message||"Database backup error"});\n',
    '''  const sendErr=(res:any,e:any)=>res.status(Number(e?.statusCode)||500).json({error:e?.message||"Database backup error"});
  const requireBackupPermission=(permission:PermissionKey)=>async(req:any,res:any,next:any)=>{try{const decision=await evaluatePermission(req.backupActor,permission,req);if(!decision.allowed)return res.status(403).json({error:`Permission denied: ${permission}`});return next()}catch(e){return sendErr(res,e)}};
''',
    "db-route-permission-helper",
)
for old, new, label in [
    ('  r.get("/",async(_req,res)=>', '  r.get("/",requireBackupPermission("backup.view"),async(_req,res)=>', "db-route-root-view"),
    ('  r.get("/status",async(_q,s)=>', '  r.get("/status",requireBackupPermission("backup.view"),async(_q,s)=>', "db-route-status-view"),
    ('  r.put("/settings",express.json(),async(q,s)=>', '  r.put("/settings",requireBackupPermission("backup.manage"),express.json(),async(q,s)=>', "db-route-settings-manage"),
    ('  r.get("/google-drive/auth-url",async(q,s)=>', '  r.get("/google-drive/auth-url",requireBackupPermission("backup.manage"),async(q,s)=>', "db-route-auth-manage"),
    ('  r.get("/google-drive/callback",async(q,s)=>', '  r.get("/google-drive/callback",requireBackupPermission("backup.manage"),async(q,s)=>', "db-route-callback-manage"),
    ('  r.delete("/google-drive/disconnect",async(_q,s)=>', '  r.delete("/google-drive/disconnect",requireBackupPermission("backup.manage"),async(_q,s)=>', "db-route-disconnect-manage"),
    ('  r.post("/backup-now",async(q,s)=>', '  r.post("/backup-now",requireBackupPermission("backup.run"),async(q,s)=>', "db-route-run"),
]:
    dbroute = rep(dbroute, old, new, label)
write(dbroute_rel, dbroute)

# ---------------------------------------------------------------------------
# Raw backup download endpoints bypass tRPC. Preserve Primary-SuperAdmin guards
# and add backup.view explicitly after those stronger checks.
# ---------------------------------------------------------------------------
core_rel = "server/_core/index.ts"
core = read(core_rel)
core = rep(
    core,
    '''      if (!isPrimarySuperAdminDownloadUser(user)) {
        res.status(403).json({ error: "Primary super admin access required" });
        return;
      }
''',
    '''      if (!isPrimarySuperAdminDownloadUser(user)) {
        res.status(403).json({ error: "Primary super admin access required" });
        return;
      }
      const backupViewPermission = await evaluatePermission(user, "backup.view", req);
      if (!backupViewPermission.allowed) {
        res.status(403).json({ error: "Permission denied: backup.view" });
        return;
      }
''',
    "raw-backup-download-view",
    2,
)
write(core_rel, core)

# ---------------------------------------------------------------------------
# Focused regression tests.
# ---------------------------------------------------------------------------
test_rel = "server/security/backupPermissionFinal.test.ts"
if (ROOT / test_rel).exists():
    fail("BACKUP_FINAL_TEST_ALREADY_EXISTS")
test = r'''import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import path from "node:path";
import { resolveCorePermissionKey } from "./corePermissionPolicy";

const root = path.resolve(process.cwd());
const read = (p: string) => readFileSync(path.join(root, p), "utf8");
const catalog = read("server/security/permissionCatalog.ts");
const context = read("client/src/contexts/PermissionContext.tsx");
const admin = read("client/src/pages/AdminSettings.tsx");
const backup = read("client/src/components/BackupTab.tsx");
const databaseBackup = read("client/src/components/DatabaseBackupSettingsTab.tsx");
const databaseRoute = read("server/routes/tcrmDatabaseBackup.ts");
const coreIndex = read("server/_core/index.ts");

describe("Backup permissions E2E V1.0.0", () => {
  it("keeps canonical backup permissions and direct Settings tab route gates", () => {
    for (const key of ["backup.view", "backup.run", "backup.restore", "backup.manage"]) {
      expect(catalog).toContain(`"${key}"`);
      expect(context).toContain(`"${key}"`);
    }
    expect(context).toContain('["backup", "databaseBackup"].includes(query.get("tab") || "")');
    expect(context).toContain('return "backup.view"');
  });

  it("maps Backup Center read APIs to backup.view", () => {
    for (const op of ["getBackupCenterSettings", "getBackupCenterJobs", "getBackupCenterRestoreLogs", "getBackups", "getAutoBackupSettings", "getArchiveStats"]) {
      expect(resolveCorePermissionKey(`admin.${op}`, "query")).toBe("backup.view");
    }
  });

  it("maps Backup Center run, restore and management APIs distinctly", () => {
    for (const op of ["runBackupCenterNow", "retryBackupCenterJob", "createBackup", "runManualFullBackup"]) {
      expect(resolveCorePermissionKey(`admin.${op}`, "mutation")).toBe("backup.run");
    }
    expect(resolveCorePermissionKey("admin.restoreBackupCenterArtifact", "mutation")).toBe("backup.restore");
    for (const op of ["saveBackupCenterSettings", "deleteBackup", "saveAutoBackupSettings", "testBackupEmail", "archiveData"]) {
      expect(resolveCorePermissionKey(`admin.${op}`, "mutation")).toBe("backup.manage");
    }
    expect(resolveCorePermissionKey("admin.someUnknownOperation", "mutation")).toBeNull();
  });

  it("protects direct database-backup REST endpoints without removing role guards", () => {
    expect(databaseRoute).toContain('isDeveloperRole(u.role)||!isAdminRole(u.role)');
    expect(databaseRoute).toContain('requireBackupPermission=(permission:PermissionKey)');
    expect(databaseRoute).toContain('r.get("/",requireBackupPermission("backup.view")');
    expect(databaseRoute).toContain('r.get("/status",requireBackupPermission("backup.view")');
    expect(databaseRoute).toContain('r.put("/settings",requireBackupPermission("backup.manage")');
    expect(databaseRoute).toContain('r.get("/google-drive/auth-url",requireBackupPermission("backup.manage")');
    expect(databaseRoute).toContain('r.get("/google-drive/callback",requireBackupPermission("backup.manage")');
    expect(databaseRoute).toContain('r.delete("/google-drive/disconnect",requireBackupPermission("backup.manage")');
    expect(databaseRoute).toContain('r.post("/backup-now",requireBackupPermission("backup.run")');
  });

  it("protects raw backup downloads with backup.view in addition to Primary SuperAdmin", () => {
    expect(coreIndex).toContain('app.get("/admin/backup-center/download/:artifactId"');
    expect(coreIndex).toContain('app.get("/admin/backup/download/:fileName"');
    expect((coreIndex.match(/evaluatePermission\(user, "backup\.view", req\)/g) || []).length).toBeGreaterThanOrEqual(2);
    expect(coreIndex).toContain("Primary super admin access required");
  });

  it("gates Backup Settings tabs without weakening SuperAdmin visibility", () => {
    expect(admin).toContain('const canBackupView = can("backup.view")');
    expect(admin).toContain('visible: isSuperAdmin && canBackupView');
    expect(admin).toContain('isSuperAdmin && canBackupView && <TabsContent value="backup"');
    expect(admin).toContain('isSuperAdmin && canBackupView && <TabsContent value="databaseBackup"');
  });

  it("gates Backup Center actions by manage/run/restore", () => {
    expect(backup).toContain('can("backup.manage")');
    expect(backup).toContain('can("backup.run")');
    expect(backup).toContain('can("backup.restore")');
    expect(backup).toContain("if (!canBackupManage) return;");
    expect(backup).toContain("if (!canBackupRun) return;");
    expect(backup).toContain("if (!canBackupRestore) return;");
    expect(backup).toContain("!canBackupRun || retryMutation.isLoading");
    expect(backup).toContain("!canBackupRestore || restoreMutation.isLoading");
  });

  it("gates dedicated database-backup management and manual run controls", () => {
    expect(databaseBackup).toContain('can("backup.manage")');
    expect(databaseBackup).toContain('can("backup.run")');
    expect(databaseBackup).toContain("if(!canBackupManage)return;");
    expect(databaseBackup).toContain("if(!canBackupRun)return;");
    expect(databaseBackup).toContain("disabled={!canBackupManage||!!busy}");
    expect(databaseBackup).toContain("disabled={!canBackupRun||!!busy||!connected}");
  });

  it("preserves previously approved permission modules", () => {
    expect(resolveCorePermissionKey("notifications.getSubscribers", "query")).toBe("notifications.view");
    expect(resolveCorePermissionKey("notificationPreferences.uploadSound", "mutation")).toBe("notifications.manage");
    expect(resolveCorePermissionKey("admin.getGoogleDriveFileStorageSettings", "query")).toBe("integrations.view");
    expect(resolveCorePermissionKey("pipeline.create", "mutation")).toBe("settings.edit");
    expect(resolveCorePermissionKey("waGateway.getStatus", "query")).toBe("whatsapp.view");
  });
});
'''
write(test_rel, test)

if dirty_paths() != EXPECTED:
    fail(f"FINAL_DIRTY_SET_MISMATCH:{sorted(dirty_paths())}")
run("git", "diff", "--check")

print(f"VERSION={VERSION}")
print(f"WORKFLOW_ID={WORKFLOW_ID}")
print(f"BASELINE={BASELINE}")
print("PATCH_APPLIED=YES")
print("BACKUP_PERMISSION_KEYS=backup.view,backup.run,backup.restore,backup.manage")
print("BACKUP_ROUTE_GATE=PASS")
print("BACKUP_CENTER_VIEW_API_GATE=PASS")
print("BACKUP_CENTER_MANAGE_API_GATE=PASS")
print("BACKUP_CENTER_RUN_API_GATE=PASS")
print("BACKUP_CENTER_RESTORE_API_GATE=PASS")
print("DATABASE_BACKUP_REST_VIEW_GATE=PASS")
print("DATABASE_BACKUP_REST_MANAGE_GATE=PASS")
print("DATABASE_BACKUP_REST_RUN_GATE=PASS")
print("RAW_BACKUP_DOWNLOAD_GATE=PASS")
print("EXISTING_SUPER_ADMIN_GUARDS_PRESERVED=YES")
print("OTHER_PERMISSION_MODULES_PRESERVED=YES")
print("CSS_CHANGED=NO")
print("DB_SCHEMA_CHANGED=NO")
print("DATA_CHANGED=NO")
print("FINAL_EXPECTED_FILES=8")
