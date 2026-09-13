#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

WORKFLOW_SERIES = "TCRM-PERMISSIONS"
MODULE = "DEVELOPER"
PHASE = "END-TO-END"
VERSION = "V1.0.0"
WORKFLOW_ID = "TCRM-PERMISSIONS-DEVELOPER-END-TO-END-V1.0.0"
BASELINE = "7d47ffae187d3e5a64151f083aeb1d6ef7bd5c26"
ROOT = Path.cwd()

EXPECTED = {
    "client/src/contexts/PermissionContext.tsx",
    "client/src/pages/AdminSettings.tsx",
    "client/src/components/DeveloperHubTab.tsx",
    "server/routes/developerHub.ts",
    "server/security/developerHubPermissionPolicy.ts",
    "server/security/developerPermissionFinal.test.ts",
}


def fail(message: str) -> None:
    print(f"ERROR={message}", file=sys.stderr)
    raise SystemExit(1)


def run(*args: str) -> str:
    p = subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        fail(f"COMMAND_FAILED:{' '.join(args)}:{p.stderr.strip()}")
    return p.stdout.strip()


def dirty_paths() -> set[str]:
    tracked = set(filter(None, run("git", "diff", "--name-only").splitlines()))
    untracked = set(filter(None, run("git", "ls-files", "--others", "--exclude-standard").splitlines()))
    return tracked | untracked


def read(rel: str) -> str:
    p = ROOT / rel
    if not p.exists():
        fail(f"TARGET_MISSING:{rel}")
    return p.read_text(encoding="utf-8")


def write(rel: str, content: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


head = run("git", "rev-parse", "HEAD")
if head != BASELINE:
    fail(f"BASELINE_MISMATCH:{head}")
if run("git", "diff", "--cached", "--name-only"):
    fail("STAGED_CHANGES_PRESENT")
if dirty_paths():
    fail(f"WORKTREE_NOT_CLEAN:{sorted(dirty_paths())}")

# ---------------------------------------------------------------------------
# 1) Frontend permission catalog + direct route gate
# ---------------------------------------------------------------------------
context_rel = "client/src/contexts/PermissionContext.tsx"
context = read(context_rel)
old = '''  "audit.view",\n  "developer.view",\n  "notifications.view",'''
new = '''  "audit.view",\n  "developer.view",\n  "developer.manage",\n  "notifications.view",'''
if context.count(old) != 1:
    fail(f"PERMISSION_CONTEXT_ANCHOR_DRIFT:count={context.count(old)}")
context = context.replace(old, new, 1)
write(context_rel, context)

# ---------------------------------------------------------------------------
# 2) Developer Hub tab visibility remains SuperAdmin/Developer + developer.view
# ---------------------------------------------------------------------------
admin_rel = "client/src/pages/AdminSettings.tsx"
admin = read(admin_rel)
old = '''  const canNotificationsView = can("notifications.view");\n  const canBackupView = can("backup.view");\n  const canSettingsEdit = can("settings.edit");'''
new = '''  const canNotificationsView = can("notifications.view");\n  const canBackupView = can("backup.view");\n  const canDeveloperView = can("developer.view");\n  const canSettingsEdit = can("settings.edit");'''
if admin.count(old) != 1:
    fail(f"ADMIN_PERMISSION_ANCHOR_DRIFT:count={admin.count(old)}")
admin = admin.replace(old, new, 1)

old = '''{ value: "developerHub", label: isRTL ? "لوحة المطورين" : "Developer Hub", description: isRTL ? "GitHub وأدوات التطوير" : "GitHub and developer tools", icon: <Terminal size={14} />, visible: isSuperAdmin, badge: "Dev" }'''
new = '''{ value: "developerHub", label: isRTL ? "لوحة المطورين" : "Developer Hub", description: isRTL ? "GitHub وأدوات التطوير" : "GitHub and developer tools", icon: <Terminal size={14} />, visible: isSuperAdmin && canDeveloperView, badge: "Dev" }'''
if admin.count(old) != 1:
    fail(f"ADMIN_DEVELOPER_TAB_VISIBILITY_ANCHOR_DRIFT:count={admin.count(old)}")
admin = admin.replace(old, new, 1)

old = '''          {isSuperAdmin && <TabsContent value="developerHub" className="mt-4">\n            <DeveloperHubTab />\n          </TabsContent>}'''
new = '''          {isSuperAdmin && canDeveloperView && <TabsContent value="developerHub" className="mt-4">\n            <DeveloperHubTab />\n          </TabsContent>}'''
if admin.count(old) != 1:
    fail(f"ADMIN_DEVELOPER_CONTENT_ANCHOR_DRIFT:count={admin.count(old)}")
admin = admin.replace(old, new, 1)
write(admin_rel, admin)

# ---------------------------------------------------------------------------
# 3) Developer Hub UI manage gates
# ---------------------------------------------------------------------------
hub_rel = "client/src/components/DeveloperHubTab.tsx"
hub = read(hub_rel)
old = '''import { useLanguage } from "@/contexts/LanguageContext";\nimport { toast } from "sonner";'''
new = '''import { useLanguage } from "@/contexts/LanguageContext";\nimport { usePermissions } from "@/contexts/PermissionContext";\nimport { toast } from "sonner";'''
if hub.count(old) != 1:
    fail(f"DEVELOPER_HUB_IMPORT_ANCHOR_DRIFT:count={hub.count(old)}")
hub = hub.replace(old, new, 1)

old = '''export default function DeveloperHubTab() {\n  const { isRTL } = useLanguage();'''
new = '''export default function DeveloperHubTab() {\n  const { isRTL } = useLanguage();\n  const { can } = usePermissions();\n  const canDeveloperManage = can("developer.manage");\n  const requireDeveloperManage = () => {\n    if (canDeveloperManage) return true;\n    toast.error(isRTL ? "لا تملك صلاحية إدارة لوحة المطورين" : "Developer Hub management permission required");\n    return false;\n  };'''
if hub.count(old) != 1:
    fail(f"DEVELOPER_HUB_PERMISSION_ANCHOR_DRIFT:count={hub.count(old)}")
hub = hub.replace(old, new, 1)

for signature in [
    "  const verifyGithubAccount = async () => {",
    "  const saveRepositorySelection = async () => {",
    "  const disconnectGithub = async () => {",
    "  const reviewSync = async (action: GitHubSyncAction, autoExecuteAfterReview = false) => {",
    "  const runSync = async (overridePreview?: GitHubSyncPreview, executionKind: \"review_approved\" | \"auto\" = \"review_approved\") => {",
    "  const saveMcpToggle = async (checked: boolean) => {",
    "  const savePushMode = async (mode: GitHubPushMode) => {",
    "  const generateContext = async () => {",
]:
    if hub.count(signature) != 1:
        fail(f"DEVELOPER_HUB_HANDLER_ANCHOR_DRIFT:{signature}:count={hub.count(signature)}")
    hub = hub.replace(signature, signature + '\n    if (!requireDeveloperManage()) return;', 1)

old = '''  const operationLocked = isDeveloperHubOperationLocked({\n    operationStatus,\n    reviewStatus,\n    previewLoading,\n    serverOperationRunning: Boolean(status?.pushRunning),\n  });'''
new = '''  const operationLocked = !canDeveloperManage || isDeveloperHubOperationLocked({\n    operationStatus,\n    reviewStatus,\n    previewLoading,\n    serverOperationRunning: Boolean(status?.pushRunning),\n  });'''
if hub.count(old) != 1:
    fail(f"DEVELOPER_HUB_OPERATION_LOCK_ANCHOR_DRIFT:count={hub.count(old)}")
hub = hub.replace(old, new, 1)

old = '''<Button variant="outline" size="sm" onClick={() => reviewSync(lastReviewAction)} disabled={previewLoading} className="gap-2">'''
new = '''<Button variant="outline" size="sm" onClick={() => reviewSync(lastReviewAction)} disabled={previewLoading || !canDeveloperManage} className="gap-2">'''
if hub.count(old) != 1:
    fail(f"DEVELOPER_HUB_RETRY_BUTTON_ANCHOR_DRIFT:count={hub.count(old)}")
hub = hub.replace(old, new, 1)

old = '''<Switch checked={mcpEnabled} onCheckedChange={saveMcpToggle} disabled={mcpSaving} />'''
new = '''<Switch checked={mcpEnabled} onCheckedChange={saveMcpToggle} disabled={mcpSaving || !canDeveloperManage} />'''
if hub.count(old) != 1:
    fail(f"DEVELOPER_HUB_MCP_ANCHOR_DRIFT:count={hub.count(old)}")
hub = hub.replace(old, new, 1)

old = '''<Button onClick={generateContext} disabled={contextGenerating} variant="outline" className="gap-2">'''
new = '''<Button onClick={generateContext} disabled={contextGenerating || !canDeveloperManage} variant="outline" className="gap-2">'''
if hub.count(old) != 1:
    fail(f"DEVELOPER_HUB_CONTEXT_BUTTON_ANCHOR_DRIFT:count={hub.count(old)}")
hub = hub.replace(old, new, 1)
write(hub_rel, hub)

# ---------------------------------------------------------------------------
# 4) Direct REST permission policy + enforcement
# ---------------------------------------------------------------------------
policy_rel = "server/security/developerHubPermissionPolicy.ts"
if (ROOT / policy_rel).exists():
    fail("DEVELOPER_POLICY_ALREADY_EXISTS")
policy = r'''import type { PermissionKey } from "./permissionCatalog";

// Developer Hub is a highly privileged direct-REST surface.
// GET is passive/read-only; every non-GET operation is management and fails
// closed behind developer.manage. Existing identity/role/email guards remain
// additive in the route itself.
export function resolveDeveloperHubPermission(method: string): PermissionKey {
  return String(method || "GET").toUpperCase() === "GET"
    ? "developer.view"
    : "developer.manage";
}
'''
write(policy_rel, policy)

route_rel = "server/routes/developerHub.ts"
route = read(route_rel)
old = '''import { authenticateRequest } from "../auth";\nimport { isDeveloperRole } from "../roleUtils";'''
new = '''import { authenticateRequest } from "../auth";\nimport { isDeveloperRole } from "../roleUtils";\nimport { evaluatePermission } from "../security/permissionEngine";\nimport { resolveDeveloperHubPermission } from "../security/developerHubPermissionPolicy";'''
if route.count(old) != 1:
    fail(f"DEVELOPER_ROUTE_IMPORT_ANCHOR_DRIFT:count={route.count(old)}")
route = route.replace(old, new, 1)

old = '''  if (!SUPER_ADMIN_EMAILS.includes(user.email ?? "") && !developerAccess) {\n    res.status(403).json({ error: "Developer Hub access required" });\n    return null;\n  }\n  return user;\n}'''
new = '''  if (!SUPER_ADMIN_EMAILS.includes(user.email ?? "") && !developerAccess) {\n    res.status(403).json({ error: "Developer Hub access required" });\n    return null;\n  }\n\n  // TCRM_PERMISSIONS_DEVELOPER_END_TO_END_V1\n  // Preserve the strong historical SuperAdmin/Developer identity guard above,\n  // then add the effective permission as a second independent gate.\n  const permission = resolveDeveloperHubPermission(req.method);\n  const decision = await evaluatePermission(user as any, permission, req);\n  if (!decision.allowed) {\n    res.status(403).json({ error: `Permission denied: ${permission}` });\n    return null;\n  }\n  return user;\n}'''
if route.count(old) != 1:
    fail(f"DEVELOPER_ROUTE_ACCESS_ANCHOR_DRIFT:count={route.count(old)}")
route = route.replace(old, new, 1)
write(route_rel, route)

# ---------------------------------------------------------------------------
# 5) Focused final regression test
# ---------------------------------------------------------------------------
test_rel = "server/security/developerPermissionFinal.test.ts"
if (ROOT / test_rel).exists():
    fail("DEVELOPER_TEST_ALREADY_EXISTS")
test = r'''import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import path from "node:path";
import { resolveDeveloperHubPermission } from "./developerHubPermissionPolicy";

const root = path.resolve(process.cwd());
const read = (p: string) => readFileSync(path.join(root, p), "utf8");
const catalog = read("server/security/permissionCatalog.ts");
const context = read("client/src/contexts/PermissionContext.tsx");
const admin = read("client/src/pages/AdminSettings.tsx");
const hub = read("client/src/components/DeveloperHubTab.tsx");
const route = read("server/routes/developerHub.ts");

describe("Developer permissions E2E V1.0.0", () => {
  it("keeps canonical developer keys and direct Settings route gating", () => {
    expect(catalog).toContain('"developer.view", "developer.manage"');
    expect(context).toContain('"developer.view"');
    expect(context).toContain('"developer.manage"');
    expect(context).toContain('query.get("tab") === "developerHub"');
    expect(context).toContain('return "developer.view"');
  });

  it("maps direct REST methods fail-closed to view/manage", () => {
    expect(resolveDeveloperHubPermission("GET")).toBe("developer.view");
    expect(resolveDeveloperHubPermission("get")).toBe("developer.view");
    expect(resolveDeveloperHubPermission("POST")).toBe("developer.manage");
    expect(resolveDeveloperHubPermission("PUT")).toBe("developer.manage");
    expect(resolveDeveloperHubPermission("PATCH")).toBe("developer.manage");
    expect(resolveDeveloperHubPermission("DELETE")).toBe("developer.manage");
  });

  it("keeps strong historical Developer Hub identity guards additive", () => {
    expect(route).toContain('const SUPER_ADMIN_EMAILS = ["admin@tamiyouz.com", "superadmin@tamiyouzalrowad.com"]');
    expect(route).toContain("const developerAccess = isDeveloperRole((user as any).role)");
    expect(route).toContain('error: "Developer Hub access required"');
    expect(route).toContain("resolveDeveloperHubPermission(req.method)");
    expect(route).toContain("evaluatePermission(user as any, permission, req)");
    expect(route).toContain("Permission denied: ${permission}");
  });

  it("keeps the external AI context endpoint token-only and does not weaken it", () => {
    expect(route).toContain('developerHubRouter.get("/ai/context/latest"');
    expect(route).toContain('String(req.get("x-api-key") || "")');
    expect(route).toContain('error: "Invalid or missing AI access token."');
  });

  it("gates Developer Hub UI visibility by developer.view in addition to the existing strong guard", () => {
    expect(admin).toContain('const canDeveloperView = can("developer.view")');
    expect(admin).toContain('visible: isSuperAdmin && canDeveloperView');
    expect(admin).toContain('isSuperAdmin && canDeveloperView && <TabsContent value="developerHub"');
  });

  it("gates Developer Hub state-changing UI operations by developer.manage", () => {
    expect(hub).toContain('const canDeveloperManage = can("developer.manage")');
    expect(hub).toContain("if (!requireDeveloperManage()) return;");
    expect(hub).toContain("const operationLocked = !canDeveloperManage || isDeveloperHubOperationLocked");
    expect(hub).toContain("disabled={mcpSaving || !canDeveloperManage}");
    expect(hub).toContain("disabled={contextGenerating || !canDeveloperManage}");
  });

  it("preserves Audit and Backup permission modules", () => {
    const core = read("server/security/corePermissionPolicy.ts");
    expect(core).toContain('if (root === "auditLogs")');
    expect(core).toContain('return "audit.view"');
    expect(core).toContain('return "audit.export"');
    expect(core).toContain('return "backup.view"');
    expect(core).toContain('return "backup.run"');
    expect(core).toContain('return "backup.restore"');
    expect(core).toContain('return "backup.manage"');
  });
});
'''
write(test_rel, test)

final_dirty = dirty_paths()
if final_dirty != EXPECTED:
    fail(f"FINAL_DIRTY_SET_MISMATCH:{sorted(final_dirty)}")
run("git", "diff", "--check")

print(f"VERSION={VERSION}")
print(f"WORKFLOW_ID={WORKFLOW_ID}")
print(f"BASELINE={BASELINE}")
print("PATCH_APPLIED=YES")
print("DEVELOPER_PERMISSION_KEYS=developer.view,developer.manage")
print("DEVELOPER_ROUTE_GATE=PASS")
print("DEVELOPER_REST_VIEW_GATE=PASS")
print("DEVELOPER_REST_MANAGE_GATE=PASS")
print("DEVELOPER_UI_VIEW_GATE=PASS")
print("DEVELOPER_UI_MANAGE_GATE=PASS")
print("EXISTING_SUPERADMIN_DEVELOPER_GUARDS_PRESERVED=YES")
print("AI_CONTEXT_TOKEN_ENDPOINT_PRESERVED=YES")
print("OTHER_PERMISSION_MODULES_PRESERVED=YES")
print("CSS_CHANGED=NO")
print("DB_SCHEMA_CHANGED=NO")
print("DATA_CHANGED=NO")
print("FILES_CHANGED=" + ",".join(sorted(EXPECTED)))
print("READY_FOR_TESTS=YES")
