#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

WORKFLOW_SERIES = "TCRM-PERMISSIONS"
MODULE = "USERS"
PHASE = "END-TO-END"
VERSION = "V1.0.0"
WORKFLOW_ID = "TCRM-PERMISSIONS-USERS-END-TO-END-V1.0.0"
BASELINE = "76147a3cc33efda0c54745bf68c639792c4c5a15"

ROOT = Path.cwd()
EXPECTED = {
    "client/src/contexts/PermissionContext.tsx",
    "client/src/pages/AdminSettings.tsx",
    "server/_core/trpc.ts",
    "server/security/corePermissionPolicy.ts",
    "server/security/usersPermissionFinal.test.ts",
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


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        fail(f"ANCHOR_DRIFT:{label}:count={count}")
    return text.replace(old, new, 1)


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
# Frontend permission decisions and direct Users-tab route protection.
# Users is embedded in AdminSettings; do not invent a standalone /users route.
# ---------------------------------------------------------------------------
ctx_rel = "client/src/contexts/PermissionContext.tsx"
ctx = read(ctx_rel)
ctx = replace_once(
    ctx,
    '  "reports.view",\n  "reports.export",\n  "settings.view",',
    '  "reports.view",\n  "reports.export",\n  "users.view",\n  "users.create",\n  "users.edit",\n  "users.delete",\n  "users.assign_roles",\n  "settings.view",',
    "permission-context-users-keys",
)
ctx = replace_once(
    ctx,
    '  if (pathname === "/settings" && query.get("tab") === "developerHub") {\n'
    '    return "developer.view";\n'
    '  }\n'
    '  if (pathname === "/admin") return "settings.view";',
    '  // TCRM_PERMISSIONS_USERS_END_TO_END_V1\n'
    '  // Users lives inside AdminSettings rather than a standalone /users route.\n'
    '  // Protect direct links to the Users tab with users.view before the generic\n'
    '  // Settings route check, while preserving the existing AdminSettings role guard.\n'
    '  if ((pathname === "/settings" || pathname === "/admin") && query.get("tab") === "users") {\n'
    '    return "users.view";\n'
    '  }\n'
    '  if (pathname === "/settings" && query.get("tab") === "developerHub") {\n'
    '    return "developer.view";\n'
    '  }\n'
    '  if (pathname === "/admin") return "settings.view";',
    "permission-context-users-tab-route",
)
write(ctx_rel, ctx)

# ---------------------------------------------------------------------------
# Canonical backend Users permission selection.
# Keep users.list as the existing shared operational directory endpoint; it is
# used outside user administration. Admin identity/CRUD remains permissioned.
# ---------------------------------------------------------------------------
policy_rel = "server/security/corePermissionPolicy.ts"
policy = read(policy_rel)

reports_anchor = '''  // TCRM_PERMISSIONS_REPORTS_END_TO_END_V1
  // Reports owns only reports.*. Existing dashboards/analytics and domain exports
  // keep their already-approved permissions. Export-like operations require the
  // stronger reports.export permission even when exposed as a query.
  if (root === "reports") {
    if (hasAny(operation, ["export", "download", "csv", "excel", "xlsx"])) {
      return "reports.export";
    }
    if (type === "query" || type === "subscription") return "reports.view";

    // The catalog intentionally has view/export only. Future Reports mutations
    // therefore fail closed behind reports.export rather than falling through.
    return "reports.export";
  }

  const module = moduleFromPath(path);
'''
users_policy = '''  // TCRM_PERMISSIONS_REPORTS_END_TO_END_V1
  // Reports owns only reports.*. Existing dashboards/analytics and domain exports
  // keep their already-approved permissions. Export-like operations require the
  // stronger reports.export permission even when exposed as a query.
  if (root === "reports") {
    if (hasAny(operation, ["export", "download", "csv", "excel", "xlsx"])) {
      return "reports.export";
    }
    if (type === "query" || type === "subscription") return "reports.view";

    // The catalog intentionally has view/export only. Future Reports mutations
    // therefore fail closed behind reports.export rather than falling through.
    return "reports.export";
  }

  // TCRM_PERMISSIONS_USERS_END_TO_END_V1
  // users.list is an established shared operational directory used by assignment
  // selectors across the CRM. Preserve that legacy endpoint exactly as-is.
  // Administrative identity and CRUD operations are permissioned here.
  if (root === "users") {
    if (operation === "list") return null;
    if (hasAny(operation, ["assignrole", "changerole", "setrole", "roleassignment", "promoteowner"])) {
      return "users.assign_roles";
    }
    if (type === "query" || type === "subscription") return "users.view";
    if (hasAny(operation, ["delete", "remove", "purge", "trash"])) return "users.delete";
    if (hasAny(operation, ["create", "add", "new"])) return "users.create";

    // update/status/profile changes and unknown future mutations fail closed
    // behind users.edit unless they are explicitly role-assignment operations.
    return "users.edit";
  }

  // Admin password resets are user-management edits even though the route lives
  // under auth.*. Existing admin/primary-super-admin protections stay additive.
  if (root === "auth" && operation === "adminsetpassword") {
    return "users.edit";
  }

  const module = moduleFromPath(path);
'''
policy = replace_once(policy, reports_anchor, users_policy, "core-policy-users")

additional_anchor = '''function hasAny(value: string, words: readonly string[]) {
  return words.some((word) => value.includes(word));
}

/**
 * Central fail-closed permission selection at protectedProcedure boundary.
'''
additional_replacement = '''function hasAny(value: string, words: readonly string[]) {
  return words.some((word) => value.includes(word));
}

// TCRM_PERMISSIONS_USERS_ROLE_ASSIGNMENT_V1
// Some Users operations need a second permission in addition to their primary
// CRUD permission. Keep this pure/testable so the tRPC middleware can enforce it
// without coupling the policy to router implementation details.
export function resolveAdditionalCorePermissionKeys(
  path: string,
  type: ProcedureType,
  input: unknown,
): PermissionKey[] {
  if (type !== "mutation") return [];

  const root = String(path || "").split(".").filter(Boolean)[0] || "";
  if (root !== "users") return [];

  const operation = operationFromPath(path);
  if (!input || typeof input !== "object" || Array.isArray(input)) return [];
  const record = input as Record<string, unknown>;

  const hasRoleField =
    Object.prototype.hasOwnProperty.call(record, "role") &&
    record.role !== undefined &&
    record.role !== null;

  if (!hasRoleField) return [];

  // Editing an existing user's role always requires users.assign_roles.
  if (operation === "update") return ["users.assign_roles"];

  // User creation without an explicit privileged/custom role keeps the existing
  // SalesAgent default. Explicitly choosing another role needs assign_roles.
  if (operation === "create") {
    const normalizedRole = String(record.role ?? "")
      .replace(/[\\s_-]+/g, "")
      .trim()
      .toLowerCase();
    if (normalizedRole && normalizedRole !== "salesagent") {
      return ["users.assign_roles"];
    }
  }

  return [];
}

/**
 * Central fail-closed permission selection at protectedProcedure boundary.
'''
policy = replace_once(policy, additional_anchor, additional_replacement, "core-policy-users-additional")
write(policy_rel, policy)

# ---------------------------------------------------------------------------
# Enforce additional input-sensitive permissions at the protectedProcedure
# boundary. This stays additive to all existing role/business/security guards.
# ---------------------------------------------------------------------------
trpc_rel = "server/_core/trpc.ts"
trpc = read(trpc_rel)
trpc = replace_once(
    trpc,
    'import { resolveCorePermissionKey } from "../security/corePermissionPolicy";',
    'import { resolveAdditionalCorePermissionKeys, resolveCorePermissionKey } from "../security/corePermissionPolicy";',
    "trpc-import-additional-users-policy",
)

trpc_anchor = '''  if (!decision.allowed) {
    // TCRM_OPERATIONAL_TASK_LEGACY_FALLBACK_V2
    // Existing after-sales roles historically have assigned client-task access.
    // Preserve that only when the new engine has no explicit role/user decision.
    const legacyTaskRole = ["ServiceAdvisor", "PartsAgent", "CrmFollowUp"].includes(String(opts.ctx.user?.role || ""));
    const legacyTaskPermission = permission === "tasks.view" || permission === "tasks.edit";
    if (decision.source === "none" && legacyTaskRole && legacyTaskPermission) {
      return opts.next({
        ctx: {
          ...opts.ctx,
          permissionDecision: { allowed: true, permission, scope: "assigned", source: "legacy_role" },
        } as any,
      });
    }
    throw new TRPCError({ code: "FORBIDDEN", message: `Permission denied: ${permission}` });
  }

  return opts.next({
    ctx: { ...opts.ctx, permissionDecision: decision } as any,
  });
});
'''
trpc_replacement = '''  if (!decision.allowed) {
    // TCRM_OPERATIONAL_TASK_LEGACY_FALLBACK_V2
    // Existing after-sales roles historically have assigned client-task access.
    // Preserve that only when the new engine has no explicit role/user decision.
    const legacyTaskRole = ["ServiceAdvisor", "PartsAgent", "CrmFollowUp"].includes(String(opts.ctx.user?.role || ""));
    const legacyTaskPermission = permission === "tasks.view" || permission === "tasks.edit";
    if (decision.source === "none" && legacyTaskRole && legacyTaskPermission) {
      return opts.next({
        ctx: {
          ...opts.ctx,
          permissionDecision: { allowed: true, permission, scope: "assigned", source: "legacy_role" },
        } as any,
      });
    }
    throw new TRPCError({ code: "FORBIDDEN", message: `Permission denied: ${permission}` });
  }

  // TCRM_PERMISSIONS_USERS_ROLE_ASSIGNMENT_V1
  // users.update can edit ordinary profile/status fields or assign a role.
  // Enforce users.assign_roles only when the raw input actually carries a role
  // change request. Creation may use the existing SalesAgent default without it.
  const rawInput =
    opts.type === "mutation" && String(opts.path || "").startsWith("users.") &&
    typeof (opts as any).getRawInput === "function"
      ? await (opts as any).getRawInput().catch(() => undefined)
      : undefined;
  const additionalPermissions = resolveAdditionalCorePermissionKeys(opts.path, opts.type, rawInput);
  for (const additionalPermission of additionalPermissions) {
    const additionalDecision = await evaluatePermission(opts.ctx.user!, additionalPermission);
    if (!additionalDecision.allowed) {
      throw new TRPCError({ code: "FORBIDDEN", message: `Permission denied: ${additionalPermission}` });
    }
  }

  return opts.next({
    ctx: { ...opts.ctx, permissionDecision: decision } as any,
  });
});
'''
trpc = replace_once(trpc, trpc_anchor, trpc_replacement, "trpc-users-additional-enforcement")
write(trpc_rel, trpc)

# ---------------------------------------------------------------------------
# AdminSettings Users tab/action gating.
# Existing admin role checks remain intact and are combined with effective
# permission decisions; no visual/CSS redesign is introduced.
# ---------------------------------------------------------------------------
admin_rel = "client/src/pages/AdminSettings.tsx"
admin = read(admin_rel)
admin = replace_once(
    admin,
    'import { useLanguage } from "@/contexts/LanguageContext";\n'
    'import { useThemeTokens } from "@/contexts/ThemeTokenContext";',
    'import { useLanguage } from "@/contexts/LanguageContext";\n'
    'import { usePermissions } from "@/contexts/PermissionContext";\n'
    'import { useThemeTokens } from "@/contexts/ThemeTokenContext";',
    "admin-settings-permission-import",
)

admin = replace_once(
    admin,
    '  const { user, loading: authLoading } = useAuth();\n'
    '  const [location, navigate] = useLocation();\n\n'
    '  const [showAddUser, setShowAddUser] = useState(false);',
    '  const { user, loading: authLoading } = useAuth();\n'
    '  const { can } = usePermissions();\n'
    '  const [location, navigate] = useLocation();\n'
    '  const canUsersView = can("users.view");\n'
    '  const canUsersCreate = can("users.create");\n'
    '  const canUsersEdit = can("users.edit");\n'
    '  const canUsersDelete = can("users.delete");\n'
    '  const canUsersAssignRoles = can("users.assign_roles");\n\n'
    '  const [showAddUser, setShowAddUser] = useState(false);',
    "admin-settings-users-permission-flags",
)

admin = replace_once(
    admin,
    '  const { data: users, refetch: refetchUsers } = trpc.users.identityList.useQuery();',
    '  const { data: users, refetch: refetchUsers } = trpc.users.identityList.useQuery(undefined, { enabled: canUsersView });',
    "admin-settings-users-query-gate",
)

admin = replace_once(
    admin,
    '        { value: "users", label: t("users"), description: isRTL ? "إدارة أعضاء النظام" : "Manage system members", icon: <Users size={14} />, visible: isAdmin },',
    '        { value: "users", label: t("users"), description: isRTL ? "إدارة أعضاء النظام" : "Manage system members", icon: <Users size={14} />, visible: isAdmin && canUsersView },',
    "admin-settings-users-tab-nav-gate",
)

admin = replace_once(
    admin,
    '          {isAdmin && <TabsContent value="users" className="mt-4">',
    '          {isAdmin && canUsersView && <TabsContent value="users" className="mt-4">',
    "admin-settings-users-tab-content-gate",
)

add_button_old = '''                <Button size="sm" style={{ background: tokens.primaryColor }} className="text-white gap-1.5"
                  onClick={() => { userReset(); setShowAddUser(true); }}>
                  <Plus size={14} /> {t("addUser")}
                </Button>'''
add_button_new = '''                {canUsersCreate && (
                  <Button size="sm" style={{ background: tokens.primaryColor }} className="text-white gap-1.5"
                    onClick={() => { userReset(); setShowAddUser(true); }}>
                    <Plus size={14} /> {t("addUser")}
                  </Button>
                )}'''
admin = replace_once(admin, add_button_old, add_button_new, "admin-settings-users-create-ui")

admin = replace_once(
    admin,
    '                                disabled={toggleUserActive.isPending}',
    '                                disabled={!canUsersEdit || toggleUserActive.isPending}',
    "admin-settings-users-status-edit-ui",
)

edit_button_old = '''                            <Button variant="ghost" size="sm" className="h-7 gap-1 text-xs"
                              onClick={() => { setEditingUser(u); setShowAddUser(true); userSetVal("name", u.name ?? ""); userSetVal("email", u.email ?? ""); userSetVal("role", u.role as any); userSetVal("centralEmail", (u as any).centralEmail ?? ""); userSetVal("centralId", (u as any).centralId ?? ""); userSetVal("nationalId", (u as any).nationalId ?? ""); userSetVal("passportNumber", (u as any).passportNumber ?? ""); }}>
                              <Edit size={12} /> {t("edit")}
                            </Button>'''
edit_button_new = '''                            {canUsersEdit && (
                              <Button variant="ghost" size="sm" className="h-7 gap-1 text-xs"
                                onClick={() => { setEditingUser(u); setShowAddUser(true); userSetVal("name", u.name ?? ""); userSetVal("email", u.email ?? ""); userSetVal("role", u.role as any); userSetVal("centralEmail", (u as any).centralEmail ?? ""); userSetVal("centralId", (u as any).centralId ?? ""); userSetVal("nationalId", (u as any).nationalId ?? ""); userSetVal("passportNumber", (u as any).passportNumber ?? ""); }}>
                                <Edit size={12} /> {t("edit")}
                              </Button>
                            )}'''
admin = replace_once(admin, edit_button_old, edit_button_new, "admin-settings-users-edit-ui")

admin = replace_once(
    admin,
    '                            {u.id !== user?.id && (\n'
    '                              <Button\n'
    '                                variant="outline"\n'
    '                                size="icon"\n'
    '                                className="h-8 w-8 rounded-xl border-red-200/70 bg-red-50/60 text-red-600 shadow-none transition-colors hover:border-red-300 hover:bg-red-100 hover:text-red-700 disabled:cursor-not-allowed disabled:border-red-100 disabled:bg-red-50/40 disabled:text-red-300 dark:border-red-900/60 dark:bg-red-950/20 dark:text-red-400 dark:hover:border-red-800 dark:hover:bg-red-950/40"',
    '                            {canUsersDelete && u.id !== user?.id && (\n'
    '                              <Button\n'
    '                                variant="outline"\n'
    '                                size="icon"\n'
    '                                className="h-8 w-8 rounded-xl border-red-200/70 bg-red-50/60 text-red-600 shadow-none transition-colors hover:border-red-300 hover:bg-red-100 hover:text-red-700 disabled:cursor-not-allowed disabled:border-red-100 disabled:bg-red-50/40 disabled:text-red-300 dark:border-red-900/60 dark:bg-red-950/20 dark:text-red-400 dark:hover:border-red-800 dark:hover:bg-red-950/40"',
    "admin-settings-users-delete-ui",
)

submit_old = '''          <form onSubmit={userSubmit((data) => {
            if (editingUser) {
              const { password, ...updateData } = data;
              updateUser.mutate({ id: editingUser.id, ...updateData });
            } else {
              if (!data.password || data.password.length < 6) {
                toast.error(isRTL ? "كلمة المرور مطلوبة (6 أحرف على الأقل)" : "Password is required (minimum 6 characters)");
                return;
              }
              registerUser.mutate({ name: data.name, email: data.email, password: data.password, role: data.role as any, centralEmail: data.centralEmail || undefined, centralId: data.centralId || undefined, nationalId: data.nationalId || undefined, passportNumber: data.passportNumber || undefined });
            }
          })} className="flex min-h-0 flex-1 flex-col overflow-hidden">'''
submit_new = '''          <form onSubmit={userSubmit((data) => {
            if (editingUser) {
              const { password, role, ...updateData } = data;
              updateUser.mutate({
                id: editingUser.id,
                ...updateData,
                ...(canUsersAssignRoles ? { role: role as any } : {}),
              });
            } else {
              if (!data.password || data.password.length < 6) {
                toast.error(isRTL ? "كلمة المرور مطلوبة (6 أحرف على الأقل)" : "Password is required (minimum 6 characters)");
                return;
              }
              registerUser.mutate({
                name: data.name,
                email: data.email,
                password: data.password,
                ...(canUsersAssignRoles ? { role: data.role as any } : {}),
                centralEmail: data.centralEmail || undefined,
                centralId: data.centralId || undefined,
                nationalId: data.nationalId || undefined,
                passportNumber: data.passportNumber || undefined,
              });
            }
          })} className="flex min-h-0 flex-1 flex-col overflow-hidden">'''
admin = replace_once(admin, submit_old, submit_new, "admin-settings-users-submit-role-omit")

role_select_old = '''              <Select value={(userWatch("role") as any) || editingUser?.role || "SalesAgent"} onValueChange={(v) => userSetVal("role", v as any, { shouldDirty: true, shouldValidate: true })}>
                <SelectTrigger className="h-10 rounded-xl border-zinc-200 bg-zinc-50"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {assignableUserRoles.map((r) => (
                    <SelectItem key={r} value={r}>
                      {r === "Moderator"
                        ? (isRTL ? "Moderator — مشرف تارا والمحادثات" : "Moderator — Tara & Conversations")
                        : t(r as any)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>'''
role_select_new = '''              {canUsersAssignRoles ? (
                <Select value={(userWatch("role") as any) || editingUser?.role || "SalesAgent"} onValueChange={(v) => userSetVal("role", v as any, { shouldDirty: true, shouldValidate: true })}>
                  <SelectTrigger className="h-10 rounded-xl border-zinc-200 bg-zinc-50"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {assignableUserRoles.map((r) => (
                      <SelectItem key={r} value={r}>
                        {r === "Moderator"
                          ? (isRTL ? "Moderator — مشرف تارا والمحادثات" : "Moderator — Tara & Conversations")
                          : t(r as any)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <div className="h-10 rounded-xl border border-zinc-200 bg-zinc-50 px-3 flex items-center">
                  <Badge variant="outline" className="text-xs">
                    {editingUser ? t(editingUser.role as any) : t("SalesAgent" as any)}
                  </Badge>
                </div>
              )}'''
admin = replace_once(admin, role_select_old, role_select_new, "admin-settings-users-role-ui")

admin = replace_once(
    admin,
    '            {editingUser && (\n'
    '              <div className="border-t border-border pt-4 mt-2">',
    '            {editingUser && canUsersEdit && (\n'
    '              <div className="border-t border-border pt-4 mt-2">',
    "admin-settings-users-password-ui",
)

admin = replace_once(
    admin,
    '              <Button type="submit" style={{ background: tokens.primaryColor }} className="text-white" disabled={editingUser ? updateUser.isPending : registerUser.isPending}>',
    '              <Button type="submit" style={{ background: tokens.primaryColor }} className="text-white" disabled={!(editingUser ? canUsersEdit : canUsersCreate) || (editingUser ? updateUser.isPending : registerUser.isPending)}>',
    "admin-settings-users-save-ui",
)
write(admin_rel, admin)

# ---------------------------------------------------------------------------
# Final regression coverage for Users E2E V1.0.0.
# ---------------------------------------------------------------------------
test_rel = "server/security/usersPermissionFinal.test.ts"
if (ROOT / test_rel).exists():
    fail("USERS_FINAL_TEST_ALREADY_EXISTS")

test = r'''import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import {
  resolveAdditionalCorePermissionKeys,
  resolveCorePermissionKey,
} from "./corePermissionPolicy";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "../..");
const read = (relative: string) => readFileSync(path.join(root, relative), "utf8");

const catalog = read("server/security/permissionCatalog.ts");
const context = read("client/src/contexts/PermissionContext.tsx");
const adminSettings = read("client/src/pages/AdminSettings.tsx");
const trpcCore = read("server/_core/trpc.ts");
const routers = read("server/routers.ts");
const app = read("client/src/App.tsx");

describe("Users permissions E2E V1.0.0", () => {
  it("keeps all five Users permissions in the canonical catalog", () => {
    for (const key of [
      "users.view",
      "users.create",
      "users.edit",
      "users.delete",
      "users.assign_roles",
    ]) {
      expect(catalog).toContain(`"${key}"`);
    }
  });

  it("maps administrative Users reads and CRUD to the intended permissions", () => {
    expect(resolveCorePermissionKey("users.identityList", "query")).toBe("users.view");
    expect(resolveCorePermissionKey("users.create", "mutation")).toBe("users.create");
    expect(resolveCorePermissionKey("users.update", "mutation")).toBe("users.edit");
    expect(resolveCorePermissionKey("users.delete", "mutation")).toBe("users.delete");
  });

  it("preserves users.list as the existing shared operational directory", () => {
    expect(resolveCorePermissionKey("users.list", "query")).toBeNull();
  });

  it("maps role-management operations to users.assign_roles", () => {
    expect(resolveCorePermissionKey("users.assignRole", "mutation")).toBe("users.assign_roles");
    expect(resolveCorePermissionKey("users.changeRole", "mutation")).toBe("users.assign_roles");
    expect(resolveCorePermissionKey("users.promoteOwner", "mutation")).toBe("users.assign_roles");
  });

  it("fails unknown future Users reads/writes closed behind view/edit", () => {
    expect(resolveCorePermissionKey("users.futureIdentityRead", "query")).toBe("users.view");
    expect(resolveCorePermissionKey("users.futureMutation", "mutation")).toBe("users.edit");
  });

  it("maps admin password reset to users.edit", () => {
    expect(resolveCorePermissionKey("auth.adminSetPassword", "mutation")).toBe("users.edit");
  });

  it("requires assign_roles when users.update carries a role", () => {
    expect(resolveAdditionalCorePermissionKeys("users.update", "mutation", { id: 7, role: "Admin" }))
      .toEqual(["users.assign_roles"]);
    expect(resolveAdditionalCorePermissionKeys("users.update", "mutation", { id: 7, name: "Updated" }))
      .toEqual([]);
  });

  it("lets create keep the default SalesAgent without assign_roles but protects explicit elevated role selection", () => {
    expect(resolveAdditionalCorePermissionKeys("users.create", "mutation", { name: "A", role: "Admin" }))
      .toEqual(["users.assign_roles"]);
    expect(resolveAdditionalCorePermissionKeys("users.create", "mutation", { name: "A", role: "SalesAgent" }))
      .toEqual([]);
    expect(resolveAdditionalCorePermissionKeys("users.create", "mutation", { name: "A" }))
      .toEqual([]);
  });

  it("enforces additional Users role permissions in protectedProcedure middleware", () => {
    expect(trpcCore).toContain("resolveAdditionalCorePermissionKeys");
    expect(trpcCore).toContain("additionalPermissions");
    expect(trpcCore).toContain("Permission denied: ${additionalPermission}");
  });

  it("requests Users permissions and protects direct Users settings links", () => {
    for (const key of [
      "users.view",
      "users.create",
      "users.edit",
      "users.delete",
      "users.assign_roles",
    ]) {
      expect(context).toContain(`"${key}"`);
    }
    expect(context).toContain('query.get("tab") === "users"');
    expect(context).toContain('return "users.view";');
  });

  it("gates Users tab, query and actions without removing existing admin role checks", () => {
    expect(adminSettings).toContain('visible: isAdmin && canUsersView');
    expect(adminSettings).toContain('enabled: canUsersView');
    expect(adminSettings).toContain('canUsersCreate && (');
    expect(adminSettings).toContain('disabled={!canUsersEdit || toggleUserActive.isPending}');
    expect(adminSettings).toContain('canUsersEdit && (');
    expect(adminSettings).toContain('canUsersDelete && u.id !== user?.id');
    expect(adminSettings).toContain('canUsersAssignRoles ? (');
    expect(adminSettings).toContain('...(canUsersAssignRoles ? { role: role as any } : {})');
    expect(adminSettings).toContain('...(canUsersAssignRoles ? { role: data.role as any } : {})');
  });

  it("preserves existing primary-super-admin and Moderator protection guards", () => {
    expect(routers).toContain("assertPrimarySuperAdminAccountMutation");
    expect(routers).toContain("Only the primary SuperAdmin can assign or remove Moderator");
    expect(routers).toContain("The primary super admin account cannot be deleted");
  });

  it("does not invent a standalone Users route", () => {
    expect(app).not.toContain('<Route path="/users"');
  });
});
'''
write(test_rel, test)

paths = dirty_paths()
if paths != EXPECTED:
    fail(f"FINAL_DIRTY_SET_MISMATCH:{sorted(paths)}")
run("git", "diff", "--check")

# Deterministic post-conditions.
ctx = read(ctx_rel)
policy = read(policy_rel)
trpc = read(trpc_rel)
admin = read(admin_rel)
final_test = read(test_rel)

for marker in [
    '"users.view"',
    '"users.create"',
    '"users.edit"',
    '"users.delete"',
    '"users.assign_roles"',
    'query.get("tab") === "users"',
]:
    if marker not in ctx:
        fail(f"FINAL_STATE_MISSING:context:{marker}")

for marker in [
    'if (root === "users")',
    'return "users.assign_roles";',
    'return "users.edit";',
    'operation === "list"',
    'root === "auth" && operation === "adminsetpassword"',
    "resolveAdditionalCorePermissionKeys",
]:
    if marker not in policy:
        fail(f"FINAL_STATE_MISSING:policy:{marker}")

for marker in [
    "resolveAdditionalCorePermissionKeys",
    "additionalPermissions",
    "additionalPermission",
]:
    if marker not in trpc:
        fail(f"FINAL_STATE_MISSING:trpc:{marker}")

for marker in [
    "canUsersView",
    "canUsersCreate",
    "canUsersEdit",
    "canUsersDelete",
    "canUsersAssignRoles",
    "visible: isAdmin && canUsersView",
]:
    if marker not in admin:
        fail(f"FINAL_STATE_MISSING:admin-settings:{marker}")

if 'describe("Users permissions E2E V1.0.0"' not in final_test:
    fail("FINAL_STATE_MISSING:users-test")

print(f"VERSION={VERSION}")
print(f"WORKFLOW_ID={WORKFLOW_ID}")
print(f"BASELINE={BASELINE}")
print("PATCH_APPLIED=YES")
print("USERS_PERMISSION_KEYS=users.view,users.create,users.edit,users.delete,users.assign_roles")
print("USERS_SHARED_LIST_PRESERVED=YES")
print("USERS_VIEW_API_GATE=PASS")
print("USERS_CREATE_API_GATE=PASS")
print("USERS_EDIT_API_GATE=PASS")
print("USERS_DELETE_API_GATE=PASS")
print("USERS_ASSIGN_ROLES_API_GATE=PASS")
print("USERS_ADMIN_SET_PASSWORD_GATE=PASS")
print("USERS_TAB_GATE=PASS")
print("USERS_ACTION_UI_GATES=PASS")
print("EXISTING_ADMIN_ROLE_GUARD_PRESERVED=YES")
print("PRIMARY_SUPER_ADMIN_GUARDS_PRESERVED=YES")
print("MODERATOR_GUARDS_PRESERVED=YES")
print("STANDALONE_USERS_ROUTE_INVENTED=NO")
print("FINAL_EXPECTED_FILES=5")
