#!/usr/bin/env python3
from pathlib import Path

ROOT = Path("/var/www/TCRM-MAIN")
BASELINE = "1f4ee37a8cf77697a4380ff846667d997455af9b"

def read(rel: str) -> str:
    path = ROOT / rel
    if not path.exists():
        raise SystemExit(f"MISSING_FILE={rel}")
    return path.read_text(encoding="utf-8")

def write(rel: str, content: str):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    before = path.read_text(encoding="utf-8") if path.exists() else None
    if before == content:
        print(f"SKIP={rel}:already_current")
        return
    path.write_text(content, encoding="utf-8")
    print(f"UPDATED={rel}")

def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"ANCHOR_ERROR={label}:expected=1:actual={count}")
    return text.replace(old, new, 1)

def replace_existing_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text and new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"ANCHOR_ERROR={label}:expected=1:actual={count}")
    return text.replace(old, new, 1)

def replace_in_section(text: str, start: str, end: str, old: str, new: str, label: str, occurrence: int = 1) -> str:
    s = text.find(start)
    if s < 0:
        raise SystemExit(f"SECTION_START_MISSING={label}")
    e = text.find(end, s + len(start))
    if e < 0:
        raise SystemExit(f"SECTION_END_MISSING={label}")
    section = text[s:e]
    if old not in section and new in section:
        return text
    positions = []
    pos = 0
    while True:
        i = section.find(old, pos)
        if i < 0:
            break
        positions.append(i)
        pos = i + len(old)
    if len(positions) < occurrence:
        raise SystemExit(f"ANCHOR_ERROR={label}:expected_occurrence={occurrence}:actual={len(positions)}")
    i = positions[occurrence - 1]
    section2 = section[:i] + new + section[i + len(old):]
    return text[:s] + section2 + text[e:]

# 1) Self-only effective permission endpoint.
rel = "server/_core/systemRouter.ts"
text = read(rel)
text = replace_once(
    text,
    'import { adminProcedure, publicProcedure, router } from "./trpc";',
    'import { adminProcedure, protectedProcedure, publicProcedure, router } from "./trpc";\n'
    'import { evaluatePermission } from "../security/permissionEngine";\n'
    'import { PHASE1_PERMISSION_CATALOG, type PermissionKey } from "../security/permissionCatalog";',
    "system_router_imports",
)
endpoint = '''  // TCRM_FRONTEND_EFFECTIVE_PERMISSIONS_V1
  // Self-only: callers can request decisions only for the authenticated ctx.user.
  effectivePermissions: protectedProcedure
    .input(z.object({
      permissions: z.array(z.enum(PHASE1_PERMISSION_CATALOG)).min(1).max(64),
    }))
    .query(async ({ ctx, input }) => {
      const keys = Array.from(new Set(input.permissions));
      const entries = await Promise.all(
        keys.map(async permission => {
          const decision = await evaluatePermission(
            ctx.user,
            permission as PermissionKey,
            ctx.req,
          );
          return [
            permission,
            {
              allowed: decision.allowed,
              scope: decision.scope,
              source: decision.source,
            },
          ] as const;
        }),
      );
      return { decisions: Object.fromEntries(entries) };
    }),

'''
if "TCRM_FRONTEND_EFFECTIVE_PERMISSIONS_V1" not in text:
    text = replace_once(text, "  notifyOwner: adminProcedure\n", endpoint + "  notifyOwner: adminProcedure\n", "system_router_endpoint")
write(rel, text)

# 2) Shared frontend effective-permission context and route map.
permission_context = r'''// TCRM_FRONTEND_PERMISSION_CONTEXT_V1
import { useAuth } from "@/_core/hooks/useAuth";
import { trpc } from "@/lib/trpc";
import {
  createContext,
  useContext,
  useMemo,
  type ReactNode,
} from "react";
import { Redirect, useLocation } from "wouter";

type UiPermissionDecision = {
  allowed: boolean;
  scope: string;
  source: string;
};

type PermissionContextValue = {
  authenticated: boolean;
  loading: boolean;
  can: (permission: string) => boolean;
  scope: (permission: string) => string;
};

const UI_PERMISSION_KEYS = [
  "dashboard.view",
  "leads.view",
  "leads.create",
  "leads.delete",
  "leads.restore",
  "leads.export",
  "leads.import",
  "clients.view",
  "clients.create",
  "clients.delete",
  "clients.export",
  "activities.create",
  "tasks.view",
  "meetings.view",
  "meetings.create",
  "meetings.edit",
  "meetings.delete",
  "contracts.view",
  "campaigns.view",
  "whatsapp.view",
  "whatsapp.manage",
  "tara.view",
  "settings.view",
  "roles.view",
  "audit.view",
  "developer.view",
  "notifications.view",
] as const;

const PermissionContext = createContext<PermissionContextValue>({
  authenticated: false,
  loading: true,
  can: () => false,
  scope: () => "none",
});

function pathMatches(pathname: string, prefix: string) {
  return pathname === prefix || pathname.startsWith(`${prefix}/`);
}

export function getPermissionForPath(rawLocation: string): string | null {
  const [pathnameRaw, queryRaw = ""] = String(rawLocation || "/").split("?", 2);
  const pathname = pathnameRaw || "/";
  const query = new URLSearchParams(queryRaw);

  if (pathname === "/settings" && query.get("tab") === "developerHub") {
    return "developer.view";
  }

  const mappings: Array<[string, string]> = [
    ["/settings/roles-permissions", "roles.view"],
    ["/wa-gateway/accounts", "whatsapp.manage"],
    ["/wa-gateway/settings", "whatsapp.manage"],
    ["/notification-settings", "notifications.view"],
    ["/operations-dashboard", "tasks.view"],
    ["/workflow-dashboard", "tasks.view"],
    ["/am-lead-dashboard", "clients.view"],
    ["/team-dashboard", "dashboard.view"],
    ["/sales-funnel", "dashboard.view"],
    ["/tiktok-campaigns", "campaigns.view"],
    ["/snapchat-ads", "campaigns.view"],
    ["/linkedin-ads", "campaigns.view"],
    ["/meta-campaigns", "campaigns.view"],
    ["/google-ads", "campaigns.view"],
    ["/am-dashboard", "clients.view"],
    ["/am-calendar", "meetings.view"],
    ["/tam-dashboard", "clients.view"],
    ["/audit-log", "audit.view"],
    ["/calendar", "meetings.view"],
    ["/renewals", "contracts.view"],
    ["/task-sla", "tasks.view"],
    ["/clients", "clients.view"],
    ["/leads", "leads.view"],
    ["/import", "leads.import"],
    ["/trash", "leads.restore"],
    ["/wa-gateway", "whatsapp.view"],
    ["/tara", "tara.view"],
    ["/settings", "settings.view"],
    ["/admin", "settings.view"],
    ["/dashboard", "dashboard.view"],
  ];

  for (const [prefix, permission] of mappings) {
    if (pathMatches(pathname, prefix)) return permission;
  }
  if (pathname === "/") return "dashboard.view";
  return null;
}

export function PermissionProvider({ children }: { children: ReactNode }) {
  const { user, loading: authLoading } = useAuth();
  const authenticated = Boolean(user?.id);
  const query = trpc.system.effectivePermissions.useQuery(
    { permissions: [...UI_PERMISSION_KEYS] },
    {
      enabled: authenticated,
      retry: 1,
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
  );

  const decisions =
    (query.data?.decisions ?? {}) as Record<string, UiPermissionDecision>;

  const value = useMemo<PermissionContextValue>(
    () => ({
      authenticated,
      loading: authLoading || (authenticated && query.isLoading),
      can: permission => Boolean(decisions[permission]?.allowed),
      scope: permission => String(decisions[permission]?.scope ?? "none"),
    }),
    [authenticated, authLoading, decisions, query.isLoading],
  );

  return (
    <PermissionContext.Provider value={value}>
      {children}
    </PermissionContext.Provider>
  );
}

export function usePermissions() {
  return useContext(PermissionContext);
}

export function PermissionRouteGuard({ children }: { children: ReactNode }) {
  const [location] = useLocation();
  const { authenticated, loading, can } = usePermissions();
  const permission = getPermissionForPath(location);

  if (!permission) return <>{children}</>;
  if (loading) return null;
  if (!authenticated) return <>{children}</>;
  if (!can(permission)) return <Redirect to="/404" />;
  return <>{children}</>;
}
'''
write("client/src/contexts/PermissionContext.tsx", permission_context)

# 3) App-level provider + direct-route permission guard.
rel = "client/src/App.tsx"
text = read(rel)
text = replace_once(
    text,
    'import { ThemeTokenProvider } from "./contexts/ThemeTokenContext";',
    'import { ThemeTokenProvider } from "./contexts/ThemeTokenContext";\n'
    'import { PermissionProvider, PermissionRouteGuard } from "./contexts/PermissionContext";',
    "app_permission_import",
)
old_tree = '''            <ThemeTokenProvider>
              <TooltipProvider>
                <InnoCallProvider>
                  <InnoCallWebCallWidget />
                  <Toaster />
                  <AppRouteSeo />
                  <ModeratorRouteGuard><Router /></ModeratorRouteGuard>
                  <SalesHeroesChatGated />
                </InnoCallProvider>
              </TooltipProvider>
            </ThemeTokenProvider>'''
new_tree = '''            <ThemeTokenProvider>
              <PermissionProvider>
                <TooltipProvider>
                  <InnoCallProvider>
                    <InnoCallWebCallWidget />
                    <Toaster />
                    <AppRouteSeo />
                    <ModeratorRouteGuard>
                      <PermissionRouteGuard><Router /></PermissionRouteGuard>
                    </ModeratorRouteGuard>
                    <SalesHeroesChatGated />
                  </InnoCallProvider>
                </TooltipProvider>
              </PermissionProvider>
            </ThemeTokenProvider>'''
text = replace_existing_once(text, old_tree, new_tree, "app_provider_tree")
write(rel, text)

# 4) Sidebar permission-driven visibility for mapped routes.
rel = "client/src/components/CRMLayout.tsx"
text = read(rel)
text = replace_once(
    text,
    'import { useTheme } from "@/contexts/ThemeContext";',
    'import { useTheme } from "@/contexts/ThemeContext";\n'
    'import { getPermissionForPath, usePermissions } from "@/contexts/PermissionContext";',
    "layout_permission_import",
)
text = replace_once(
    text,
    '  const { theme, toggleTheme } = useTheme();\n',
    '  const { theme, toggleTheme } = useTheme();\n'
    '  const { can: hasPermission } = usePermissions();\n',
    "layout_permission_hook",
)
text = replace_existing_once(
    text,
    '      visible: isAdminRole(role) || normalizeUserRole(user?.role) === "Developer",\n',
    '      // Visibility is resolved from the roles.view effective permission.\n',
    "layout_roles_permission_visible",
)
old_visible = '''  const visibleNavItems = navItems.filter((item) => {
    if (!(item.visible ?? true)) return false;
    if (isModerator) return !isModeratorBlockedRoute(item.href);
    if (isBdOnly) return BD_ALLOWED_HREFS.includes(item.href);
    return !item.roles || item.roles.includes(role);
  });'''
new_visible = '''  const visibleNavItems = navItems.filter((item) => {
    if (!(item.visible ?? true)) return false;
    if (isModerator && isModeratorBlockedRoute(item.href)) return false;
    if (isBdOnly && !BD_ALLOWED_HREFS.includes(item.href)) return false;
    const routePermission = getPermissionForPath(item.href);
    if (routePermission) return hasPermission(routePermission);
    return !item.roles || item.roles.includes(role);
  });'''
text = replace_existing_once(text, old_visible, new_visible, "layout_visible_nav")
text = replace_existing_once(
    text,
    '          const showWaGateway = role !== "Viewer";',
    '          const showWaGateway = hasPermission("whatsapp.view") || hasPermission("whatsapp.manage");',
    "layout_show_whatsapp",
)
text = replace_existing_once(
    text,
    '          const showMarketing = ["Admin", "SalesManager", "MediaBuyer"].includes(role);',
    '          const showMarketing = hasPermission("campaigns.view");',
    "layout_show_marketing",
)
text = replace_existing_once(
    text,
    '          const showSales = ["Admin", "SalesManager", "SalesAgent", "ColdSalesAgent", "TechnicalAccountManager", "ServiceAdvisor", "PartsAgent", "CrmFollowUp", "Viewer", "MediaBuyer"].includes(role);',
    '          const showSales = salesHrefs.some(href => {\n'
    '            const permission = getPermissionForPath(href);\n'
    '            return permission ? hasPermission(permission) : false;\n'
    '          });',
    "layout_show_sales",
)
text = replace_existing_once(
    text,
    '          const showAm = ["Admin", "SalesManager", "TechnicalAccountManager", "AccountManager", "AccountManagerLead", "ServiceAdvisor", "PartsAgent", "CrmFollowUp"].includes(role);',
    '          const showAm = amHrefs.some(href => {\n'
    '            const permission = getPermissionForPath(href);\n'
    '            return permission ? hasPermission(permission) : false;\n'
    '          });',
    "layout_show_am",
)

sales_start = '{/* ── Sales collapsible group ── */}'
sales_end = '{/* ── Marketing collapsible group ── */}'
old_sales_filter = '''                      ].filter(sub => {
                        if (sub.href === "/team-dashboard") return ["Admin","SalesManager","Viewer"].includes(role);
                        if (sub.href === "/leads") return ["Admin","SalesManager","SalesAgent","ColdSalesAgent","TechnicalAccountManager","ServiceAdvisor","PartsAgent","CrmFollowUp","Viewer","MediaBuyer"].includes(role);
                        if (sub.href === "/sales-funnel") return ["Admin","SalesManager","SalesAgent","ColdSalesAgent","Viewer"].includes(role);
                        if (sub.href === "/task-sla") return ["Admin","SalesManager","SalesAgent","ColdSalesAgent","Viewer"].includes(role);
                        if (sub.href === "/calendar") return ["Admin","SalesManager","SalesAgent","ColdSalesAgent","ServiceAdvisor","CrmFollowUp","MediaBuyer"].includes(role);
                        return true;
                      }).map(sub => {'''
new_sales_filter = '''                      ].filter(sub => {
                        const permission = getPermissionForPath(sub.href);
                        return permission ? hasPermission(permission) : true;
                      }).map(sub => {'''
text = replace_in_section(text, sales_start, sales_end, old_sales_filter, new_sales_filter, "layout_sales_expanded_filter")
text = replace_in_section(
    text,
    sales_start,
    sales_end,
    '{["/leads", "/sales-funnel", "/task-sla", "/calendar"].map((href, i) => {',
    '{["/leads", "/sales-funnel", "/task-sla", "/calendar"].filter((href) => {\n'
    '                        const permission = getPermissionForPath(href);\n'
    '                        return permission ? hasPermission(permission) : true;\n'
    '                      }).map((href, i) => {',
    "layout_sales_collapsed_filter",
)

wa_start = '{/* ── WhatsApp grouped preview links ── */}'
wa_end = '{/* ── AI Staff collapsible group ── */}'
old_group_filter = '].filter(sub => isModerator ? !isModeratorBlockedRoute(sub.href) : sub.roles.includes(role)).map(sub => {'
new_group_filter = '''].filter(sub => {
                        if (isModerator && isModeratorBlockedRoute(sub.href)) return false;
                        const permission = getPermissionForPath(sub.href);
                        return permission ? hasPermission(permission) : sub.roles.includes(role);
                      }).map(sub => {'''
text = replace_in_section(text, wa_start, wa_end, old_group_filter, new_group_filter, "layout_wa_expanded_filter", occurrence=1)
text = replace_in_section(text, wa_start, wa_end, old_group_filter, new_group_filter, "layout_wa_collapsed_filter", occurrence=1)

am_start = '{/* ── Account Management collapsible group ── */}'
am_end = '{/* ── Business Development collapsible group ── */}'
text = replace_in_section(text, am_start, am_end, old_group_filter, new_group_filter, "layout_am_expanded_filter", occurrence=1)
text = replace_in_section(text, am_start, am_end, old_group_filter, new_group_filter, "layout_am_collapsed_filter", occurrence=1)
write(rel, text)

# 5) Leads list action buttons use effective permissions.
rel = "client/src/pages/LeadsList.tsx"
text = read(rel)
text = replace_once(
    text,
    'import { useThemeTokens } from "@/contexts/ThemeTokenContext";',
    'import { useThemeTokens } from "@/contexts/ThemeTokenContext";\n'
    'import { usePermissions } from "@/contexts/PermissionContext";',
    "leads_permission_import",
)
text = replace_once(
    text,
    '  const { user } = useAuth();\n',
    '  const { user } = useAuth();\n'
    '  const { can: hasPermission } = usePermissions();\n',
    "leads_permission_hook",
)
quick_old = '''            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 text-muted-foreground hover:text-primary"
              title={isRTL ? "إضافة نشاط" : "Add Activity"}
              onClick={(e) => {
                e.stopPropagation();
                setQuickActivityLeadId(lead.id);
              }}
            >
              <MessageSquare size={14} />
            </Button>'''
quick_new = '''            {hasPermission("activities.create") && (
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 text-muted-foreground hover:text-primary"
                title={isRTL ? "إضافة نشاط" : "Add Activity"}
                onClick={(e) => {
                  e.stopPropagation();
                  setQuickActivityLeadId(lead.id);
                }}
              >
                <MessageSquare size={14} />
              </Button>
            )}'''
text = replace_existing_once(text, quick_old, quick_new, "leads_quick_activity")
text = replace_existing_once(
    text,
    '{(user?.role === "Admin" || user?.role === "admin") && (\n              <Button\n                variant="ghost"\n                size="icon"\n                className="h-7 w-7 text-muted-foreground hover:text-destructive"',
    '{hasPermission("leads.delete") && (\n              <Button\n                variant="ghost"\n                size="icon"\n                className="h-7 w-7 text-muted-foreground hover:text-destructive"',
    "leads_delete_action",
)
text = replace_existing_once(
    text,
    '{(user?.role === "Admin" || user?.role === "admin" || user?.role === "SalesManager") && (\n              <Button variant="outline" onClick={() => setShowExport(true)} className="gap-2 rounded-2xl">',
    '{hasPermission("leads.export") && (\n              <Button variant="outline" onClick={() => setShowExport(true)} className="gap-2 rounded-2xl">',
    "leads_export_action",
)
text = replace_existing_once(
    text,
    '{user?.role !== "MediaBuyer" && (\n              <Button\n                onClick={() => setShowNewLead(true)}',
    '{hasPermission("leads.create") && (\n              <Button\n                onClick={() => setShowNewLead(true)}',
    "leads_create_action",
)
write(rel, text)

# 6) Calendar action gating.
rel = "client/src/pages/CalendarPage.tsx"
text = read(rel)
text = replace_once(
    text,
    'import { useLanguage } from "@/contexts/LanguageContext";',
    'import { useLanguage } from "@/contexts/LanguageContext";\n'
    'import { usePermissions } from "@/contexts/PermissionContext";',
    "calendar_permission_import",
)
text = replace_once(
    text,
    '  const { user } = useAuth();\n',
    '  const { user } = useAuth();\n'
    '  const { can: hasPermission } = usePermissions();\n',
    "calendar_permission_hook",
)
header_create_old = '''          <Button
            onClick={() => { setForm(defaultForm); setShowCreateDialog(true); }}
            className="gap-2 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-700 hover:to-indigo-700 shadow-md shadow-violet-200"
          >
            <Plus size={16} />
            {isRTL ? "اجتماع جديد" : "New Meeting"}
          </Button>'''
header_create_new = '''          {hasPermission("meetings.create") && (
            <Button
              onClick={() => { setForm(defaultForm); setShowCreateDialog(true); }}
              className="gap-2 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-700 hover:to-indigo-700 shadow-md shadow-violet-200"
            >
              <Plus size={16} />
              {isRTL ? "اجتماع جديد" : "New Meeting"}
            </Button>
          )}'''
text = replace_existing_once(text, header_create_old, header_create_new, "calendar_header_create")
text = replace_existing_once(
    text,
    '                      onClick={() => openCreateForDate(day)}',
    '                      onClick={() => { if (hasPermission("meetings.create")) openCreateForDate(day); }}',
    "calendar_day_create",
)
empty_create_old = '''                  <button
                    onClick={() => { setForm(defaultForm); setShowCreateDialog(true); }}
                    className="mt-2 text-xs text-violet-500 hover:text-violet-700 font-medium"
                  >
                    {isRTL ? "+ إنشاء اجتماع" : "+ Create meeting"}
                  </button>'''
empty_create_new = '''                  {hasPermission("meetings.create") && (
                    <button
                      onClick={() => { setForm(defaultForm); setShowCreateDialog(true); }}
                      className="mt-2 text-xs text-violet-500 hover:text-violet-700 font-medium"
                    >
                      {isRTL ? "+ إنشاء اجتماع" : "+ Create meeting"}
                    </button>
                  )}'''
text = replace_existing_once(text, empty_create_old, empty_create_new, "calendar_empty_create")
edit_delete_old = '''                  <div className="flex gap-2 justify-end pt-2 border-t border-slate-100">
                    <Button variant="outline" size="sm" onClick={() => setEditMode(true)} className="gap-1.5 rounded-xl">
                      <Edit size={13} /> {isRTL ? "تعديل" : "Edit"}
                    </Button>
                    <Button variant="destructive" size="sm" onClick={handleDeleteEvent} disabled={deleteEvent.isPending} className="gap-1.5 rounded-xl">
                      {deleteEvent.isPending ? <Loader2 className="animate-spin" size={13} /> : <Trash2 size={13} />}
                      {isRTL ? "حذف" : "Delete"}
                    </Button>
                  </div>'''
edit_delete_new = '''                  <div className="flex gap-2 justify-end pt-2 border-t border-slate-100">
                    {hasPermission("meetings.edit") && (
                      <Button variant="outline" size="sm" onClick={() => setEditMode(true)} className="gap-1.5 rounded-xl">
                        <Edit size={13} /> {isRTL ? "تعديل" : "Edit"}
                      </Button>
                    )}
                    {hasPermission("meetings.delete") && (
                      <Button variant="destructive" size="sm" onClick={handleDeleteEvent} disabled={deleteEvent.isPending} className="gap-1.5 rounded-xl">
                        {deleteEvent.isPending ? <Loader2 className="animate-spin" size={13} /> : <Trash2 size={13} />}
                        {isRTL ? "حذف" : "Delete"}
                      </Button>
                    )}
                  </div>'''
text = replace_existing_once(text, edit_delete_old, edit_delete_new, "calendar_edit_delete")
text = replace_existing_once(
    text,
    '{editMode ? (\n                <>',
    '{editMode && hasPermission("meetings.edit") ? (\n                <>',
    "calendar_edit_state",
)
write(rel, text)

# 7) Client Pool create/delete/export buttons use effective permissions.
rel = "client/src/pages/ClientPool.tsx"
text = read(rel)
text = replace_once(
    text,
    'import { useLanguage } from "@/contexts/LanguageContext";',
    'import { useLanguage } from "@/contexts/LanguageContext";\n'
    'import { usePermissions } from "@/contexts/PermissionContext";',
    "client_pool_permission_import",
)
text = replace_once(
    text,
    '  const { user } = useAuth();\n',
    '  const { user } = useAuth();\n'
    '  const { can: hasPermission } = usePermissions();\n',
    "client_pool_permission_hook",
)
old_write = '''  const canWriteClient = [
    "Admin",
    "admin",
    "SalesManager",
    "AccountManager",
    "AccountManagerLead",
  ].includes(userRole);
  const canDeleteClient = [
    "Admin",
    "admin",
    "SalesManager",
    "AccountManagerLead",
  ].includes(userRole);'''
new_write = '''  const canCreateClient = hasPermission("clients.create");
  const canDeleteClient = hasPermission("clients.delete");'''
text = replace_existing_once(text, old_write, new_write, "client_pool_role_actions")
text = replace_existing_once(
    text,
    '{exportCapabilityQ.data?.allowed && (',
    '{exportCapabilityQ.data?.allowed && hasPermission("clients.export") && (',
    "client_pool_export_action",
)
text = replace_existing_once(text, '{canWriteClient && (', '{canCreateClient && (', "client_pool_create_action")
write(rel, text)

# Static post-apply checks.
checks = {
    "server/_core/systemRouter.ts": [
        "TCRM_FRONTEND_EFFECTIVE_PERMISSIONS_V1",
        "effectivePermissions: protectedProcedure",
        "evaluatePermission(",
        "ctx.user",
        "ctx.req",
    ],
    "client/src/contexts/PermissionContext.tsx": [
        "TCRM_FRONTEND_PERMISSION_CONTEXT_V1",
        "PermissionProvider",
        "PermissionRouteGuard",
        "getPermissionForPath",
        "system.effectivePermissions",
    ],
    "client/src/App.tsx": [
        "PermissionProvider",
        "PermissionRouteGuard",
    ],
    "client/src/components/CRMLayout.tsx": [
        "usePermissions",
        'hasPermission("campaigns.view")',
        'hasPermission("whatsapp.view")',
        "getPermissionForPath(sub.href)",
    ],
    "client/src/pages/LeadsList.tsx": [
        'hasPermission("leads.create")',
        'hasPermission("leads.delete")',
        'hasPermission("leads.export")',
        'hasPermission("activities.create")',
    ],
    "client/src/pages/CalendarPage.tsx": [
        'hasPermission("meetings.create")',
        'hasPermission("meetings.edit")',
        'hasPermission("meetings.delete")',
    ],
    "client/src/pages/ClientPool.tsx": [
        'hasPermission("clients.create")',
        'hasPermission("clients.delete")',
        'hasPermission("clients.export")',
    ],
}
for rel, needles in checks.items():
    data = read(rel)
    missing = [needle for needle in needles if needle not in data]
    if missing:
        raise SystemExit(f"POSTCHECK_FAILED={rel}:{missing}")

print("PATCH=TCRM-PERMISSIONS-FRONTEND-ENFORCEMENT-V1")
print(f"BASELINE={BASELINE}")
print("SELF_ONLY_EFFECTIVE_PERMISSION_ENDPOINT=YES")
print("DIRECT_ROUTE_GUARD=YES")
print("SIDEBAR_EFFECTIVE_PERMISSION_GATING=YES")
print("LEADS_ACTION_GATING=YES")
print("CALENDAR_ACTION_GATING=YES")
print("CLIENT_POOL_ACTION_GATING=YES")
print("DB_SCHEMA_CHANGED=NO")
print("DATA_CHANGED=NO")
