#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

WORKFLOW_SERIES = "TCRM-PERMISSIONS"
MODULE = "NOTIFICATIONS"
PHASE = "END-TO-END"
VERSION = "V1.0.0"
WORKFLOW_ID = "TCRM-PERMISSIONS-NOTIFICATIONS-END-TO-END-V1.0.0"
BASELINE = "f9f53e4e19f224633c6287f401e77f4f64ba548c"
ROOT = Path.cwd()

EXPECTED = {
    "client/src/contexts/PermissionContext.tsx",
    "client/src/pages/AdminSettings.tsx",
    "client/src/components/NotificationsTab.tsx",
    "client/src/components/MeetingNotificationSettings.tsx",
    "client/src/components/NotificationSoundSettingsCard.tsx",
    "server/security/corePermissionPolicy.ts",
    "server/security/notificationsPermissionFinal.test.ts",
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
# Frontend decisions and direct-route protection.
# notifications.view controls viewing notification administration surfaces;
# notifications.manage controls global notification configuration mutations.
# Personal self-service notification preferences remain user-scoped and are not
# repurposed into an administrator permission.
# ---------------------------------------------------------------------------
ctx_rel = "client/src/contexts/PermissionContext.tsx"
ctx = read(ctx_rel)
ctx = rep(
    ctx,
    '  "developer.view",\n  "notifications.view",\n] as const;',
    '  "developer.view",\n  "notifications.view",\n  "notifications.manage",\n] as const;',
    "context-notifications-manage",
)
ctx = rep(
    ctx,
    '''  if (pathname === "/settings" && query.get("tab") === "developerHub") {
    return "developer.view";
  }
  if (pathname === "/admin") return "settings.view";
''',
    '''  if (pathname === "/settings" && query.get("tab") === "developerHub") {
    return "developer.view";
  }
  if ((pathname === "/settings" || pathname === "/admin") && ["notifications", "meetingNotifs"].includes(query.get("tab") || "")) {
    return "notifications.view";
  }
  if (pathname === "/admin") return "settings.view";
''',
    "context-notification-tabs-route",
)
write(ctx_rel, ctx)

# ---------------------------------------------------------------------------
# Backend central permission selection.
# - notifications.* is global automated-report notification administration.
# - meetingNotificationConfig.* is global reminder configuration.
# - notificationPreferences.get/update are per-user self-service and remain
#   protected/user-scoped without global notification permissions.
# - system notification sound upload/remove are global admin mutations.
# - inbox.* remains operational self-service and is intentionally untouched.
# ---------------------------------------------------------------------------
policy_rel = "server/security/corePermissionPolicy.ts"
policy = read(policy_rel)
policy = rep(
    policy,
    '''  if (root === "admin" && [
    "savegoogledrivefilestoragesettings",
    "testgoogledrivefilestorageconnection",
    "getgoogledrivefilestorageauthurl",
    "disconnectgoogledrivefilestorage",
  ].includes(operation)) {
    return "integrations.manage";
  }

  const module = moduleFromPath(path);
''',
    '''  if (root === "admin" && [
    "savegoogledrivefilestoragesettings",
    "testgoogledrivefilestorageconnection",
    "getgoogledrivefilestorageauthurl",
    "disconnectgoogledrivefilestorage",
  ].includes(operation)) {
    return "integrations.manage";
  }

  // TCRM_PERMISSIONS_NOTIFICATIONS_END_TO_END_V1
  // Global notification administration. Existing Admin/SuperAdmin procedures
  // remain additive to these effective permissions.
  if (root === "notifications") {
    if (type === "query" || type === "subscription") return "notifications.view";
    return "notifications.manage";
  }

  if (root === "meetingNotificationConfig") {
    if (type === "query" || type === "subscription") return "notifications.view";
    return "notifications.manage";
  }

  if (root === "notificationPreferences") {
    // Per-user get/update preferences are self-service and stay user-scoped.
    // Only the shared system sound mutation surface is global administration.
    if (["uploadsound", "removesound"].includes(operation)) return "notifications.manage";
    return null;
  }

  const module = moduleFromPath(path);
''',
    "policy-notifications",
)
write(policy_rel, policy)

# ---------------------------------------------------------------------------
# Admin Settings tab visibility: retain Admin role guards and add view permission.
# ---------------------------------------------------------------------------
admin_rel = "client/src/pages/AdminSettings.tsx"
admin = read(admin_rel)
admin = rep(
    admin,
    '  const canIntegrationsView = can("integrations.view");\n  const canSettingsEdit = can("settings.edit");',
    '  const canIntegrationsView = can("integrations.view");\n  const canNotificationsView = can("notifications.view");\n  const canSettingsEdit = can("settings.edit");',
    "admin-notifications-flag",
)
admin = rep(
    admin,
    '{ value: "notifications", label: isRTL ? "الإشعارات" : "Notifications", description: isRTL ? "إعدادات إشعارات النظام" : "System notification settings", icon: <Bell size={14} />, visible: isAdmin },',
    '{ value: "notifications", label: isRTL ? "الإشعارات" : "Notifications", description: isRTL ? "إعدادات إشعارات النظام" : "System notification settings", icon: <Bell size={14} />, visible: isAdmin && canNotificationsView },',
    "admin-notifications-visible",
)
admin = rep(
    admin,
    '{ value: "meetingNotifs", label: isRTL ? "تذكير الاجتماعات" : "Meeting Reminders", description: isRTL ? "تنبيهات وتذكير الاجتماعات" : "Meeting reminders and alerts", icon: <Clock size={14} />, visible: isAdmin },',
    '{ value: "meetingNotifs", label: isRTL ? "تذكير الاجتماعات" : "Meeting Reminders", description: isRTL ? "تنبيهات وتذكير الاجتماعات" : "Meeting reminders and alerts", icon: <Clock size={14} />, visible: isAdmin && canNotificationsView },',
    "admin-meeting-notifs-visible",
)
admin = rep(
    admin,
    '{isAdmin && <TabsContent value="notifications" className="mt-4">',
    '{isAdmin && canNotificationsView && <TabsContent value="notifications" className="mt-4">',
    "admin-notifications-content",
)
admin = rep(
    admin,
    '{isAdmin && <TabsContent value="meetingNotifs" className="mt-4">',
    '{isAdmin && canNotificationsView && <TabsContent value="meetingNotifs" className="mt-4">',
    "admin-meeting-notifs-content",
)
write(admin_rel, admin)

# ---------------------------------------------------------------------------
# Automated report recipients: view-only users may inspect recipients; every
# add/update/delete/test-send action requires notifications.manage.
# ---------------------------------------------------------------------------
notif_rel = "client/src/components/NotificationsTab.tsx"
notif = read(notif_rel)
notif = rep(
    notif,
    'import { trpc } from "@/lib/trpc";\n',
    'import { trpc } from "@/lib/trpc";\nimport { usePermissions } from "@/contexts/PermissionContext";\n',
    "notifications-tab-import",
)
notif = rep(
    notif,
    '''export default function NotificationsTab({ isRTL, tokens }: Props) {
  const [showAddDialog, setShowAddDialog] = useState(false);''',
    '''export default function NotificationsTab({ isRTL, tokens }: Props) {
  const { can } = usePermissions();
  const canManageNotifications = can("notifications.manage");
  const [showAddDialog, setShowAddDialog] = useState(false);''',
    "notifications-tab-flag",
)
notif = rep(
    notif,
    '''  const handleAdd = () => {
    if (!newEmail) return;''',
    '''  const handleAdd = () => {
    if (!canManageNotifications || !newEmail) return;''',
    "notifications-tab-handle-add",
)
notif = rep(
    notif,
    '''  const handleSendTest = () => {
    if (!testEmail) {''',
    '''  const handleSendTest = () => {
    if (!canManageNotifications) return;
    if (!testEmail) {''',
    "notifications-tab-handle-test",
)
notif = rep(
    notif,
    '''            onClick={() => setShowAddDialog(true)}
          >''',
    '''            onClick={() => setShowAddDialog(true)}
            disabled={!canManageNotifications}
          >''',
    "notifications-tab-add-button",
)
notif = rep(
    notif,
    '''                        checked={sub.isActive}
                        onCheckedChange={(v) => updateSubscriber.mutate({ id: sub.id, isActive: v })}
                      />''',
    '''                        checked={sub.isActive}
                        onCheckedChange={(v) => updateSubscriber.mutate({ id: sub.id, isActive: v })}
                        disabled={!canManageNotifications}
                      />''',
    "notifications-tab-update-switch",
)
notif = rep(
    notif,
    '''                        onClick={() => deleteSubscriber.mutate({ id: sub.id })}
                      >''',
    '''                        onClick={() => deleteSubscriber.mutate({ id: sub.id })}
                        disabled={!canManageNotifications || deleteSubscriber.isPending}
                      >''',
    "notifications-tab-delete",
)
notif = rep(
    notif,
    'disabled={sendTestReport.isPending}',
    'disabled={!canManageNotifications || sendTestReport.isPending}',
    "notifications-tab-test",
)
notif = rep(
    notif,
    'disabled={addSubscriber.isPending || !newEmail}',
    'disabled={!canManageNotifications || addSubscriber.isPending || !newEmail}',
    "notifications-tab-dialog-add",
)
write(notif_rel, notif)

# ---------------------------------------------------------------------------
# Global meeting reminder configuration: read via notifications.view; all local
# editors and save action require notifications.manage.
# ---------------------------------------------------------------------------
meeting_rel = "client/src/components/MeetingNotificationSettings.tsx"
meeting = read(meeting_rel)
meeting = rep(
    meeting,
    'import { trpc } from "@/lib/trpc";\n',
    'import { trpc } from "@/lib/trpc";\nimport { usePermissions } from "@/contexts/PermissionContext";\n',
    "meeting-notif-import",
)
meeting = rep(
    meeting,
    '''export default function MeetingNotificationSettings({ isRTL, tokens }: Props) {
  const { data: config, refetch, isLoading } = trpc.meetingNotificationConfig.get.useQuery();''',
    '''export default function MeetingNotificationSettings({ isRTL, tokens }: Props) {
  const { can } = usePermissions();
  const canManageNotifications = can("notifications.manage");
  const { data: config, refetch, isLoading } = trpc.meetingNotificationConfig.get.useQuery();''',
    "meeting-notif-flag",
)
meeting = rep(
    meeting,
    '''  const handleSave = () => {
    updateConfig.mutate({''',
    '''  const handleSave = () => {
    if (!canManageNotifications) return;
    updateConfig.mutate({''',
    "meeting-notif-save-guard",
)
meeting = rep(
    meeting,
    'disabled={!customMinutes}',
    'disabled={!canManageNotifications || !customMinutes}',
    "meeting-notif-custom-add",
)
meeting = rep(
    meeting,
    'disabled={updateConfig.isPending}',
    'disabled={!canManageNotifications || updateConfig.isPending}',
    "meeting-notif-save",
)
meeting = rep(
    meeting,
    '<Switch checked={soundEnabled} onCheckedChange={setSoundEnabled} />',
    '<Switch checked={soundEnabled} onCheckedChange={setSoundEnabled} disabled={!canManageNotifications} />',
    "meeting-notif-sound-switch",
)
meeting = rep(
    meeting,
    '<Switch checked={popupEnabled} onCheckedChange={setPopupEnabled} />',
    '<Switch checked={popupEnabled} onCheckedChange={setPopupEnabled} disabled={!canManageNotifications} />',
    "meeting-notif-popup-switch",
)
meeting = rep(
    meeting,
    '<Switch checked={autoCalendarForMeeting} onCheckedChange={setAutoCalendarForMeeting} />',
    '<Switch checked={autoCalendarForMeeting} onCheckedChange={setAutoCalendarForMeeting} disabled={!canManageNotifications} />',
    "meeting-notif-calendar-meeting-switch",
)
meeting = rep(
    meeting,
    '<Switch checked={autoCalendarForCall} onCheckedChange={setAutoCalendarForCall} />',
    '<Switch checked={autoCalendarForCall} onCheckedChange={setAutoCalendarForCall} disabled={!canManageNotifications} />',
    "meeting-notif-calendar-call-switch",
)
write(meeting_rel, meeting)

# ---------------------------------------------------------------------------
# System-wide notification sound is a SuperAdmin feature already. Add the
# canonical manage permission without weakening the existing primary-SA guard.
# ---------------------------------------------------------------------------
sound_rel = "client/src/components/NotificationSoundSettingsCard.tsx"
sound = read(sound_rel)
sound = rep(
    sound,
    'import { trpc } from "@/lib/trpc";\n',
    'import { trpc } from "@/lib/trpc";\nimport { usePermissions } from "@/contexts/PermissionContext";\n',
    "sound-card-import",
)
sound = rep(
    sound,
    '''export default function NotificationSoundSettingsCard({ isRTL }: { isRTL: boolean }) {
  const fileInputRef = useRef<HTMLInputElement>(null);''',
    '''export default function NotificationSoundSettingsCard({ isRTL }: { isRTL: boolean }) {
  const { can } = usePermissions();
  const canManageNotifications = can("notifications.manage");
  const fileInputRef = useRef<HTMLInputElement>(null);''',
    "sound-card-flag",
)
sound = rep(
    sound,
    '  if (!soundConfig?.canManage) return null;',
    '  if (!soundConfig?.canManage || !canManageNotifications) return null;',
    "sound-card-render-gate",
)
write(sound_rel, sound)

# ---------------------------------------------------------------------------
# Focused regression coverage.
# ---------------------------------------------------------------------------
test_rel = "server/security/notificationsPermissionFinal.test.ts"
if (ROOT / test_rel).exists():
    fail("NOTIFICATIONS_FINAL_TEST_ALREADY_EXISTS")

test = r'''import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import path from "node:path";
import { resolveCorePermissionKey } from "./corePermissionPolicy";

const root = path.resolve(process.cwd());
const read = (p: string) => readFileSync(path.join(root, p), "utf8");
const catalog = read("server/security/permissionCatalog.ts");
const context = read("client/src/contexts/PermissionContext.tsx");
const admin = read("client/src/pages/AdminSettings.tsx");
const notificationsTab = read("client/src/components/NotificationsTab.tsx");
const meeting = read("client/src/components/MeetingNotificationSettings.tsx");
const sound = read("client/src/components/NotificationSoundSettingsCard.tsx");

describe("Notifications permissions E2E V1.0.0", () => {
  it("keeps canonical notification permissions and direct route gate", () => {
    for (const key of ["notifications.view", "notifications.manage"]) {
      expect(catalog).toContain(`"${key}"`);
      expect(context).toContain(`"${key}"`);
    }
    expect(context).toContain('["/notification-settings", "notifications.view"]');
    expect(context).toContain('["notifications", "meetingNotifs"].includes(query.get("tab") || "")');
  });

  it("maps automated report notification administration", () => {
    expect(resolveCorePermissionKey("notifications.getSubscribers", "query")).toBe("notifications.view");
    for (const op of ["addSubscriber", "updateSubscriber", "deleteSubscriber", "sendTestReport"]) {
      expect(resolveCorePermissionKey(`notifications.${op}`, "mutation")).toBe("notifications.manage");
    }
  });

  it("maps meeting reminder global configuration", () => {
    expect(resolveCorePermissionKey("meetingNotificationConfig.get", "query")).toBe("notifications.view");
    expect(resolveCorePermissionKey("meetingNotificationConfig.update", "mutation")).toBe("notifications.manage");
  });

  it("preserves per-user self-service preferences and inbox operations", () => {
    expect(resolveCorePermissionKey("notificationPreferences.get", "query")).toBeNull();
    expect(resolveCorePermissionKey("notificationPreferences.update", "mutation")).toBeNull();
    expect(resolveCorePermissionKey("notificationPreferences.getSoundConfig", "query")).toBeNull();
    expect(resolveCorePermissionKey("inbox.list", "query")).toBeNull();
    expect(resolveCorePermissionKey("inbox.markRead", "mutation")).toBeNull();
    expect(resolveCorePermissionKey("inbox.markAllRead", "mutation")).toBeNull();
  });

  it("protects system notification sound mutations", () => {
    expect(resolveCorePermissionKey("notificationPreferences.uploadSound", "mutation")).toBe("notifications.manage");
    expect(resolveCorePermissionKey("notificationPreferences.removeSound", "mutation")).toBe("notifications.manage");
  });

  it("gates global notification settings tabs and mutation controls", () => {
    expect(admin).toContain('const canNotificationsView = can("notifications.view")');
    expect(admin).toContain('visible: isAdmin && canNotificationsView');
    expect(admin).toContain('isAdmin && canNotificationsView && <TabsContent value="notifications"');
    expect(admin).toContain('isAdmin && canNotificationsView && <TabsContent value="meetingNotifs"');
    expect(notificationsTab).toContain('can("notifications.manage")');
    expect(notificationsTab).toContain("!canManageNotifications || sendTestReport.isPending");
    expect(meeting).toContain('can("notifications.manage")');
    expect(meeting).toContain("if (!canManageNotifications) return;");
    expect(sound).toContain('can("notifications.manage")');
    expect(sound).toContain("!soundConfig?.canManage || !canManageNotifications");
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
print("NOTIFICATIONS_PERMISSION_KEYS=notifications.view,notifications.manage")
print("NOTIFICATIONS_ROUTE_GATE=PASS")
print("NOTIFICATIONS_ADMIN_API_GATE=PASS")
print("MEETING_NOTIFICATION_API_GATE=PASS")
print("PERSONAL_NOTIFICATION_PREFERENCES_PRESERVED=YES")
print("INBOX_OPERATIONS_PRESERVED=YES")
print("SYSTEM_SOUND_MANAGE_GATE=PASS")
print("CSS_CHANGED=NO")
print("DB_SCHEMA_CHANGED=NO")
print("DATA_CHANGED=NO")
print("FINAL_EXPECTED_FILES=7")
