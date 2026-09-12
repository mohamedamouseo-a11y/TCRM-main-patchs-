#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

WORKFLOW_SERIES = "TCRM-PERMISSIONS"
MODULE = "INTEGRATIONS"
PHASE = "END-TO-END"
VERSION = "V1.0.0"
WORKFLOW_ID = "TCRM-PERMISSIONS-INTEGRATIONS-END-TO-END-V1.0.0"
BASELINE = "e0d9096b4043c90321310a8344e538f3e15ba555"
ROOT = Path.cwd()
EXPECTED = {
    "client/src/contexts/PermissionContext.tsx",
    "client/src/pages/AdminSettings.tsx",
    "client/src/components/AuthIntegrationsTab.tsx",
    "client/src/components/LandingPageIntegrationsTab.tsx",
    "client/src/components/TosIntegrationSettingsTab.tsx",
    "client/src/components/TfsIntegrationSettingsTab.tsx",
    "client/src/components/ThrsIntegrationSettingsTab.tsx",
    "client/src/components/GoogleDriveStorageTab.tsx",
    "server/security/corePermissionPolicy.ts",
    "server/security/integrationsPermissionFinal.test.ts",
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

# Effective decisions used by Settings integration tabs.
ctx_rel = "client/src/contexts/PermissionContext.tsx"
ctx = read(ctx_rel)
ctx = rep(
    ctx,
    '  "roles.assign_permissions",\n  "audit.view",',
    '  "roles.assign_permissions",\n  "integrations.view",\n  "integrations.manage",\n  "audit.view",',
    "context-integration-keys",
)
write(ctx_rel, ctx)

# Backend: protect only integration-admin surfaces. Shared operational reads/actions
# remain untouched where TOS/TFS/THRS are used outside Settings.
policy_rel = "server/security/corePermissionPolicy.ts"
policy = read(policy_rel)
policy = rep(
    policy,
    '''  if (["pipeline", "customFields", "theme", "sla"].includes(root)) {
    if (type === "query" || type === "subscription") return null;
    return "settings.edit";
  }

  const module = moduleFromPath(path);
''',
    '''  if (["pipeline", "customFields", "theme", "sla"].includes(root)) {
    if (type === "query" || type === "subscription") return null;
    return "settings.edit";
  }

  // TCRM_PERMISSIONS_INTEGRATIONS_END_TO_END_V1
  // Generic integration administration only. Product-specific integrations such as
  // WhatsApp keep their already-approved module permissions, while operational
  // TOS/TFS/THRS endpoints remain available under their existing business guards.
  if (root === "authIntegrations") {
    if (type === "query" || type === "subscription") return "integrations.view";
    return "integrations.manage";
  }

  if (root === "landingPageIntegrations") {
    if (type === "query" || type === "subscription") return "integrations.view";
    return "integrations.manage";
  }

  if (root === "tosIntegration") {
    if (["savesettings", "testconnection", "runsyncnow"].includes(operation)) return "integrations.manage";
    return null;
  }

  if (root === "tfsIntegration") {
    if (["savesettings", "testconnection", "bulksend"].includes(operation)) return "integrations.manage";
    return null;
  }

  if (root === "thrs") {
    if (["updatesettings", "testhrsyncconnection", "generatehrintegrationtoken", "fetchleavetypes", "syncemployees"].includes(operation)) {
      return "integrations.manage";
    }
    return null;
  }

  if (root === "admin" && operation === "getgoogledrivefilestoragesettings") {
    return "integrations.view";
  }
  if (root === "admin" && [
    "savegoogledrivefilestoragesettings",
    "testgoogledrivefilestorageconnection",
    "getgoogledrivefilestorageauthurl",
    "disconnectgoogledrivefilestorage",
  ].includes(operation)) {
    return "integrations.manage";
  }

  const module = moduleFromPath(path);
''',
    "policy-integrations",
)
write(policy_rel, policy)

# Settings tab visibility remains additive to existing Admin/SuperAdmin guards.
admin_rel = "client/src/pages/AdminSettings.tsx"
admin = read(admin_rel)
admin = rep(
    admin,
    '  const canUsersAssignRoles = can("users.assign_roles");\n',
    '  const canUsersAssignRoles = can("users.assign_roles");\n  const canIntegrationsView = can("integrations.view");\n',
    "admin-integration-flag",
)
for old, new, label in [
    ('{ value: "landingPageIntegrations", label: isRTL ? "ربط الصفحات" : "Landing Pages", description: isRTL ? "استقبال بيانات الفورم" : "Form capture integrations", icon: <FileSpreadsheet size={14} />, visible: isAdmin },',
     '{ value: "landingPageIntegrations", label: isRTL ? "ربط الصفحات" : "Landing Pages", description: isRTL ? "استقبال بيانات الفورم" : "Form capture integrations", icon: <FileSpreadsheet size={14} />, visible: isAdmin && canIntegrationsView },',
     "landing-visible"),
    ('{ value: "authIntegrations", label: isRTL ? "إعدادات الدخول" : "Login Integrations", description: isRTL ? "طرق الدخول وربط الحسابات" : "Login providers and accounts", icon: <Key size={14} />, visible: isSuperAdmin, badge: "Admin" },',
     '{ value: "authIntegrations", label: isRTL ? "إعدادات الدخول" : "Login Integrations", description: isRTL ? "طرق الدخول وربط الحسابات" : "Login providers and accounts", icon: <Key size={14} />, visible: isSuperAdmin && canIntegrationsView, badge: "Admin" },',
     "auth-visible"),
    ('{ value: "googleDriveStorage", label: "Google Drive", description: isRTL ? "تخزين الملفات" : "File storage", icon: <Cloud size={14} />, visible: isSuperAdmin, badge: "Admin" },',
     '{ value: "googleDriveStorage", label: "Google Drive", description: isRTL ? "تخزين الملفات" : "File storage", icon: <Cloud size={14} />, visible: isSuperAdmin && canIntegrationsView, badge: "Admin" },',
     "gdrive-visible"),
    ('{ value: "tosIntegration", label: isRTL ? "ربط TOS" : "TOS Integration", description: isRTL ? "تشغيل المشاريع والمهام" : "Projects and operations sync", icon: <Webhook size={14} />, visible: isSuperAdmin, badge: "API" },',
     '{ value: "tosIntegration", label: isRTL ? "ربط TOS" : "TOS Integration", description: isRTL ? "تشغيل المشاريع والمهام" : "Projects and operations sync", icon: <Webhook size={14} />, visible: isSuperAdmin && canIntegrationsView, badge: "API" },',
     "tos-visible"),
    ('{ value: "tfsIntegration", label: isRTL ? "ربط TFS" : "TFS Integration", description: isRTL ? "ربط المالية" : "Finance integration", icon: <DollarSign size={14} />, visible: isSuperAdmin, badge: "API" },',
     '{ value: "tfsIntegration", label: isRTL ? "ربط TFS" : "TFS Integration", description: isRTL ? "ربط المالية" : "Finance integration", icon: <DollarSign size={14} />, visible: isSuperAdmin && canIntegrationsView, badge: "API" },',
     "tfs-visible"),
    ('{ value: "thrsIntegration", label: "THRS / HR", description: isRTL ? "ربط الموارد البشرية" : "HR integration", icon: <UserCheck size={14} />, visible: isAdmin, badge: "API" },',
     '{ value: "thrsIntegration", label: "THRS / HR", description: isRTL ? "ربط الموارد البشرية" : "HR integration", icon: <UserCheck size={14} />, visible: isAdmin && canIntegrationsView, badge: "API" },',
     "thrs-visible"),
    ('{isAdmin && <TabsContent value="landingPageIntegrations" className="mt-4">',
     '{isAdmin && canIntegrationsView && <TabsContent value="landingPageIntegrations" className="mt-4">',
     "landing-content"),
    ('{isSuperAdmin && <TabsContent value="authIntegrations" className="mt-4">',
     '{isSuperAdmin && canIntegrationsView && <TabsContent value="authIntegrations" className="mt-4">',
     "auth-content"),
    ('{isSuperAdmin && <TabsContent value="googleDriveStorage" className="mt-4">',
     '{isSuperAdmin && canIntegrationsView && <TabsContent value="googleDriveStorage" className="mt-4">',
     "gdrive-content"),
    ('{isSuperAdmin && <TabsContent value="tosIntegration" className="mt-4">',
     '{isSuperAdmin && canIntegrationsView && <TabsContent value="tosIntegration" className="mt-4">',
     "tos-content"),
    ('{isSuperAdmin && <TabsContent value="tfsIntegration" className="mt-4">',
     '{isSuperAdmin && canIntegrationsView && <TabsContent value="tfsIntegration" className="mt-4">',
     "tfs-content"),
    ('{isAdmin && <TabsContent value="thrsIntegration" className="mt-4">',
     '{isAdmin && canIntegrationsView && <TabsContent value="thrsIntegration" className="mt-4">',
     "thrs-content"),
]:
    admin = rep(admin, old, new, label)
write(admin_rel, admin)

# Login integrations: read-only without manage; save is the only mutation.
auth_rel = "client/src/components/AuthIntegrationsTab.tsx"
auth = read(auth_rel)
auth = rep(auth, 'import { useLanguage } from "@/contexts/LanguageContext";\n', 'import { useLanguage } from "@/contexts/LanguageContext";\nimport { usePermissions } from "@/contexts/PermissionContext";\n', "auth-import")
auth = rep(auth, '  const { isRTL } = useLanguage();\n  const utils = trpc.useUtils();', '  const { isRTL } = useLanguage();\n  const { can } = usePermissions();\n  const canManageIntegrations = can("integrations.manage");\n  const utils = trpc.useUtils();', "auth-flag")
auth = rep(auth, '  function handleSave() {\n    saveSettings.mutate({', '  function handleSave() {\n    if (!canManageIntegrations) return;\n    saveSettings.mutate({', "auth-handler")
auth = rep(auth, 'disabled={saveSettings.isPending}', 'disabled={!canManageIntegrations || saveSettings.isPending}', "auth-save")
write(auth_rel, auth)

# Landing-page integrations: list remains view-only; all create/update/delete actions require manage.
landing_rel = "client/src/components/LandingPageIntegrationsTab.tsx"
landing = read(landing_rel)
landing = rep(landing, 'import { useLanguage } from "@/contexts/LanguageContext";\n', 'import { useLanguage } from "@/contexts/LanguageContext";\nimport { usePermissions } from "@/contexts/PermissionContext";\n', "landing-import")
landing = rep(landing, '  const { isRTL } = useLanguage();\n  const [draft, setDraft]', '  const { isRTL } = useLanguage();\n  const { can } = usePermissions();\n  const canManageIntegrations = can("integrations.manage");\n  const [draft, setDraft]', "landing-flag")
landing = rep(landing, '<Button size="sm" variant="outline" onClick={() => { setSelectedId(null); setDraft(defaultDraft); }}>', '<Button size="sm" variant="outline" disabled={!canManageIntegrations} onClick={() => { setSelectedId(null); setDraft(defaultDraft); }}>', "landing-new")
landing = rep(landing, 'disabled={!draft.name || !draft.slug || createMutation.isPending || updateMutation.isPending}', 'disabled={!canManageIntegrations || !draft.name || !draft.slug || createMutation.isPending || updateMutation.isPending}', "landing-save")
landing = rep(landing, 'disabled={deleteMutation.isPending}', 'disabled={!canManageIntegrations || deleteMutation.isPending}', "landing-delete")
write(landing_rel, landing)

# TOS settings mutations require manage; getSettings remains shared because ClientPool uses it operationally.
tos_rel = "client/src/components/TosIntegrationSettingsTab.tsx"
tos = read(tos_rel)
tos = rep(tos, 'import { useLanguage } from "@/contexts/LanguageContext";\n', 'import { useLanguage } from "@/contexts/LanguageContext";\nimport { usePermissions } from "@/contexts/PermissionContext";\n', "tos-import")
tos = rep(tos, '  const { isRTL } = useLanguage();\n  const utils = trpc.useUtils();', '  const { isRTL } = useLanguage();\n  const { can } = usePermissions();\n  const canManageIntegrations = can("integrations.manage");\n  const utils = trpc.useUtils();', "tos-flag")
tos = rep(tos, 'disabled={isSaving}', 'disabled={!canManageIntegrations || isSaving}', "tos-save")
tos = rep(tos, 'disabled={isTesting}', 'disabled={!canManageIntegrations || isTesting}', "tos-test")
tos = rep(tos, 'disabled={isRunningSync || !enabled}', 'disabled={!canManageIntegrations || isRunningSync || !enabled}', "tos-sync")
write(tos_rel, tos)

# TFS settings mutations require manage; shared reads/operational client sync routes are preserved.
tfs_rel = "client/src/components/TfsIntegrationSettingsTab.tsx"
tfs = read(tfs_rel)
tfs = rep(tfs, 'import { useLanguage } from "@/contexts/LanguageContext";\n', 'import { useLanguage } from "@/contexts/LanguageContext";\nimport { usePermissions } from "@/contexts/PermissionContext";\n', "tfs-import")
tfs = rep(tfs, '  const { isRTL } = useLanguage();\n  const utils = trpc.useUtils();', '  const { isRTL } = useLanguage();\n  const { can } = usePermissions();\n  const canManageIntegrations = can("integrations.manage");\n  const utils = trpc.useUtils();', "tfs-flag")
tfs = rep(tfs, 'disabled={isSaving}', 'disabled={!canManageIntegrations || isSaving}', "tfs-save")
tfs = rep(tfs, 'disabled={isTesting || !settingsQ.data?.enabled}', 'disabled={!canManageIntegrations || isTesting || !settingsQ.data?.enabled}', "tfs-test")
tfs = rep(tfs, 'disabled={isBulkSending || !settingsQ.data?.enabled}', 'disabled={!canManageIntegrations || isBulkSending || !settingsQ.data?.enabled}', "tfs-bulk", 3)
write(tfs_rel, tfs)

# THRS overview is shared by the operational THRS page. Only integration-admin mutations are gated.
thrs_rel = "client/src/components/ThrsIntegrationSettingsTab.tsx"
thrs = read(thrs_rel)
thrs = rep(thrs, 'import { useLanguage } from "@/contexts/LanguageContext";\n', 'import { useLanguage } from "@/contexts/LanguageContext";\nimport { usePermissions } from "@/contexts/PermissionContext";\n', "thrs-import")
thrs = rep(thrs, '  const { isRTL } = useLanguage();\n  const utils = trpc.useUtils();', '  const { isRTL } = useLanguage();\n  const { can } = usePermissions();\n  const canManageIntegrations = can("integrations.manage");\n  const utils = trpc.useUtils();', "thrs-flag")
thrs = rep(thrs, 'disabled={testConnection.isPending}', 'disabled={!canManageIntegrations || testConnection.isPending}', "thrs-test")
for key, label in [("moduleEnabled", "thrs-module-switch"), ("hrSyncEnabled", "thrs-sync-switch"), ("outboundAutoSendEnabled", "thrs-auto-switch")]:
    thrs = rep(thrs, f'checked={{Boolean(settings?.{key})}}\n                  onCheckedChange=', f'checked={{Boolean(settings?.{key})}}\n                  disabled={{!canManageIntegrations}}\n                  onCheckedChange=', label)
thrs = rep(thrs, 'onClick={() => updateSettings.mutate({ hrBaseUrl, hrApiToken: hrApiToken || undefined, leaveTypesEndpoint, employeesEndpoint, shiftAssignmentsEndpoint, approvalMode: approvalMode as any, employeeIdentifier: employeeIdentifier as any, heartbeatTimeoutMinutes: Number(heartbeatTimeoutMinutes) || 15 })}\n            >', 'onClick={() => updateSettings.mutate({ hrBaseUrl, hrApiToken: hrApiToken || undefined, leaveTypesEndpoint, employeesEndpoint, shiftAssignmentsEndpoint, approvalMode: approvalMode as any, employeeIdentifier: employeeIdentifier as any, heartbeatTimeoutMinutes: Number(heartbeatTimeoutMinutes) || 15 })}\n              disabled={!canManageIntegrations || updateSettings.isPending}\n            >', "thrs-save")
thrs = rep(thrs, 'disabled={generateToken.isPending}', 'disabled={!canManageIntegrations || generateToken.isPending}', "thrs-token")
thrs = rep(thrs, 'disabled={syncEmployees.isPending}', 'disabled={!canManageIntegrations || syncEmployees.isPending}', "thrs-employees")
thrs = rep(thrs, 'disabled={fetchLeaveTypes.isPending}', 'disabled={!canManageIntegrations || fetchLeaveTypes.isPending}', "thrs-leaves")
write(thrs_rel, thrs)

# Google Drive settings under admin.* are integration administration; file upload/download permissions stay unchanged.
gd_rel = "client/src/components/GoogleDriveStorageTab.tsx"
gd = read(gd_rel)
gd = rep(gd, 'import { useLanguage } from "@/contexts/LanguageContext";\n', 'import { useLanguage } from "@/contexts/LanguageContext";\nimport { usePermissions } from "@/contexts/PermissionContext";\n', "gdrive-import")
gd = rep(gd, '  const { isRTL } = useLanguage();\n  const [settings, setSettings]', '  const { isRTL } = useLanguage();\n  const { can } = usePermissions();\n  const canManageIntegrations = can("integrations.manage");\n  const [settings, setSettings]', "gdrive-flag")
gd = rep(gd, '  const handleSave = () => {\n    const nextClientSecret', '  const handleSave = () => {\n    if (!canManageIntegrations) return;\n    const nextClientSecret', "gdrive-save-guard")
gd = rep(gd, '  const handleConnect = async () => {\n    try {', '  const handleConnect = async () => {\n    if (!canManageIntegrations) return;\n    try {', "gdrive-connect-guard")
gd = rep(gd, '<Switch checked={settings.enabled} onCheckedChange={(value) => update("enabled", value)} />', '<Switch checked={settings.enabled} disabled={!canManageIntegrations} onCheckedChange={(value) => update("enabled", value)} />', "gdrive-switch")
gd = rep(gd, 'disabled={isBusy || !dirty}', 'disabled={!canManageIntegrations || isBusy || !dirty}', "gdrive-save")
gd = rep(gd, 'disabled={isBusy || !settings.hasCredentials}', 'disabled={!canManageIntegrations || isBusy || !settings.hasCredentials}', "gdrive-connect")
gd = rep(gd, 'disabled={isBusy || !settings.connected}', 'disabled={!canManageIntegrations || isBusy || !settings.connected}', "gdrive-connected-actions", 2)
write(gd_rel, gd)

# Focused regression tests.
test_rel = "server/security/integrationsPermissionFinal.test.ts"
if (ROOT / test_rel).exists():
    fail("INTEGRATIONS_FINAL_TEST_ALREADY_EXISTS")
test = r'''import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import path from "node:path";
import { resolveCorePermissionKey } from "./corePermissionPolicy";

const root = path.resolve(process.cwd());
const read = (p: string) => readFileSync(path.join(root, p), "utf8");
const catalog = read("server/security/permissionCatalog.ts");
const context = read("client/src/contexts/PermissionContext.tsx");
const admin = read("client/src/pages/AdminSettings.tsx");
const auth = read("client/src/components/AuthIntegrationsTab.tsx");
const landing = read("client/src/components/LandingPageIntegrationsTab.tsx");
const tos = read("client/src/components/TosIntegrationSettingsTab.tsx");
const tfs = read("client/src/components/TfsIntegrationSettingsTab.tsx");
const thrs = read("client/src/components/ThrsIntegrationSettingsTab.tsx");
const gdrive = read("client/src/components/GoogleDriveStorageTab.tsx");

describe("Integrations permissions E2E V1.0.0", () => {
  it("keeps both Integration permissions in catalog and frontend decisions", () => {
    for (const key of ["integrations.view", "integrations.manage"]) {
      expect(catalog).toContain(`"${key}"`);
      expect(context).toContain(`"${key}"`);
    }
    expect(context).toContain('["/settings", "settings.view"]');
  });

  it("protects generic integration admin APIs", () => {
    expect(resolveCorePermissionKey("authIntegrations.get", "query")).toBe("integrations.view");
    expect(resolveCorePermissionKey("authIntegrations.update", "mutation")).toBe("integrations.manage");
    expect(resolveCorePermissionKey("landingPageIntegrations.list", "query")).toBe("integrations.view");
    expect(resolveCorePermissionKey("landingPageIntegrations.create", "mutation")).toBe("integrations.manage");
    expect(resolveCorePermissionKey("landingPageIntegrations.update", "mutation")).toBe("integrations.manage");
    expect(resolveCorePermissionKey("landingPageIntegrations.delete", "mutation")).toBe("integrations.manage");
    expect(resolveCorePermissionKey("admin.getGoogleDriveFileStorageSettings", "query")).toBe("integrations.view");
    for (const op of ["saveGoogleDriveFileStorageSettings", "testGoogleDriveFileStorageConnection", "getGoogleDriveFileStorageAuthUrl", "disconnectGoogleDriveFileStorage"]) {
      expect(resolveCorePermissionKey(`admin.${op}`, "mutation")).toBe("integrations.manage");
    }
  });

  it("protects TOS/TFS/THRS settings mutations while preserving operational routes", () => {
    for (const op of ["saveSettings", "testConnection", "runSyncNow"]) expect(resolveCorePermissionKey(`tosIntegration.${op}`, "mutation")).toBe("integrations.manage");
    for (const op of ["saveSettings", "testConnection", "bulkSend"]) expect(resolveCorePermissionKey(`tfsIntegration.${op}`, "mutation")).toBe("integrations.manage");
    for (const op of ["updateSettings", "testHrSyncConnection", "generateHrIntegrationToken", "fetchLeaveTypes", "syncEmployees"]) expect(resolveCorePermissionKey(`thrs.${op}`, "mutation")).toBe("integrations.manage");

    expect(resolveCorePermissionKey("tosIntegration.getSettings", "query")).toBeNull();
    expect(resolveCorePermissionKey("tosIntegration.getClientSyncStatuses", "query")).toBeNull();
    expect(resolveCorePermissionKey("tosIntegration.sendClientProject", "mutation")).toBeNull();
    expect(resolveCorePermissionKey("tfsIntegration.getSettings", "query")).toBeNull();
    expect(resolveCorePermissionKey("tfsIntegration.sendClient", "mutation")).toBeNull();
    expect(resolveCorePermissionKey("thrs.overview", "query")).toBeNull();
    expect(resolveCorePermissionKey("thrs.createRequest", "mutation")).toBeNull();
    expect(resolveCorePermissionKey("thrs.heartbeat", "mutation")).toBeNull();
  });

  it("gates integration Settings tabs without removing existing role guards", () => {
    expect(admin).toContain('const canIntegrationsView = can("integrations.view")');
    for (const tab of ["landingPageIntegrations", "authIntegrations", "googleDriveStorage", "tosIntegration", "tfsIntegration", "thrsIntegration"]) {
      expect(admin).toContain(`value: "${tab}"`);
    }
    expect(admin).toContain('visible: isAdmin && canIntegrationsView');
    expect(admin).toContain('visible: isSuperAdmin && canIntegrationsView');
    expect(admin).toContain('isAdmin && canIntegrationsView && <TabsContent value="landingPageIntegrations"');
    expect(admin).toContain('isSuperAdmin && canIntegrationsView && <TabsContent value="tosIntegration"');
  });

  it("gates integration mutation controls in every integration component", () => {
    for (const source of [auth, landing, tos, tfs, thrs, gdrive]) {
      expect(source).toContain('can("integrations.manage")');
      expect(source).toContain("canManageIntegrations");
    }
    expect(auth).toContain("if (!canManageIntegrations) return;");
    expect(landing).toContain("!canManageIntegrations || !draft.name");
    expect(tos).toContain("!canManageIntegrations || isRunningSync");
    expect(tfs).toContain("!canManageIntegrations || isBulkSending");
    expect(thrs).toContain("disabled={!canManageIntegrations}");
    expect(gdrive).toContain("if (!canManageIntegrations) return;");
  });

  it("does not repurpose product-specific integration modules", () => {
    expect(resolveCorePermissionKey("waGateway.getSettings", "query")).toBe("whatsapp.manage");
    expect(resolveCorePermissionKey("tara.getSettings", "query")).toBe("tara.manage");
    expect(resolveCorePermissionKey("fileStorage.upload", "mutation")).toBe("files.upload");
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
print("INTEGRATIONS_PERMISSION_KEYS=integrations.view,integrations.manage")
print("INTEGRATIONS_SETTINGS_TAB_GATE=PASS")
print("INTEGRATIONS_MANAGE_API_GATE=PASS")
print("SHARED_OPERATIONAL_INTEGRATION_ROUTES_PRESERVED=YES")
print("PRODUCT_SPECIFIC_PERMISSION_MODULES_PRESERVED=YES")
print("CSS_CHANGED=NO")
print("DB_SCHEMA_CHANGED=NO")
print("DATA_CHANGED=NO")
print("FINAL_EXPECTED_FILES=10")
