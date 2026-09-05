#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

EXPECTED_HEAD = "46c97d6df963bcedb12150b226385026f5d549d7"
SERVER_MARKER = "ADVANCED_PERMISSIONS_PHASE4A_PERMISSION_TESTER"
UI_MARKER = "ADVANCED_PERMISSIONS_PHASE4A_PERMISSION_TESTER_UI"

root = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TCRM-MAIN").resolve()
router_path = root / "server/permissionsAdminRouter.ts"
ui_path = root / "client/src/pages/RolesPermissions.tsx"

for path in (router_path, ui_path):
    if not path.exists():
        raise SystemExit(f"Missing required target file: {path}")

try:
    head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
except Exception as exc:
    raise SystemExit(f"Unable to read target HEAD: {exc}")

if head != EXPECTED_HEAD:
    raise SystemExit(f"Baseline mismatch: expected {EXPECTED_HEAD}, got {head}. No files changed.")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"Anchor mismatch for {label}: expected exactly 1 match, got {count}. No files changed.")
    return text.replace(old, new, 1)


def insert_before_last(text: str, anchor: str, payload: str, label: str) -> str:
    pos = text.rfind(anchor)
    if pos < 0:
        raise SystemExit(f"Anchor mismatch for {label}: final anchor not found. No files changed.")
    return text[:pos] + payload + text[pos:]

router = router_path.read_text(encoding="utf-8")
ui = ui_path.read_text(encoding="utf-8")
new_router = router
new_ui = ui

if SERVER_MARKER not in router:
    new_router = replace_once(
        new_router,
        'import { PERMISSION_SCOPES } from "./security/permissionCatalog";',
        'import { PERMISSION_SCOPES, PHASE1_PERMISSION_CATALOG, type PermissionKey } from "./security/permissionCatalog";',
        "permission catalog import",
    )

    override_import = '''import {\n  getPermissionUserProfile,\n  listPermissionUsers,\n  replacePermissionUserOverrides,\n} from "./security/permissionUserOverrideAdmin";\n'''
    new_router = replace_once(
        new_router,
        override_import,
        override_import + 'import { evaluatePermission } from "./security/permissionEngine";\n',
        "permission engine import",
    )

    helper = '''\nfunction permissionDecisionReason(\n  decision: Awaited<ReturnType<typeof evaluatePermission>>,\n  legacyRole: string,\n) {\n  if (decision.source === "super_admin") return "Granted by Super Admin bypass";\n  if (decision.source === "user_deny") return "Denied by User Override";\n  if (decision.source === "user_allow") return "Granted by User Override";\n  if (decision.source === "role") return decision.allowed ? "Granted by dynamic role permission" : "Denied by dynamic role permission";\n  if (decision.source === "legacy_role") return `${decision.allowed ? "Granted" : "Denied"} by legacy role${legacyRole ? `: ${legacyRole}` : ""}`;\n  return "No matching permission grant";\n}\n\n'''
    new_router = replace_once(
        new_router,
        'const roleIdInput = z.object({ roleId: z.number().int().positive() });\n',
        helper + 'const roleIdInput = z.object({ roleId: z.number().int().positive() });\n',
        "tester reason helper",
    )

    endpoint_anchor = '  listUsersForPermissions: permissionProcedure("users.view").query(async () => listPermissionUsers()),\n'
    endpoint = '''  // ADVANCED_PERMISSIONS_PHASE4A_PERMISSION_TESTER\n  testUserPermissions: permissionProcedure("roles.view")\n    .input(z.object({\n      userId: z.number().int().positive(),\n      permissionKey: z.string().trim().min(3).max(190).optional(),\n    }))\n    .query(async ({ input }) => {\n      try {\n        const profile = await getPermissionUserProfile(input.userId);\n        const catalogKeys = PHASE1_PERMISSION_CATALOG.map(String);\n        if (input.permissionKey && !catalogKeys.includes(input.permissionKey)) {\n          throw new PermissionAdminError("BAD_REQUEST", `Unknown permission: ${input.permissionKey}`);\n        }\n        const permissionKeys = input.permissionKey ? [input.permissionKey] : catalogKeys;\n        const permissionUser = {\n          id: Number(profile.id),\n          role: profile.legacyRole ?? null,\n          email: profile.email ?? null,\n          teamId: profile.teamId == null ? null : Number(profile.teamId),\n        };\n        const decisions: Array<Awaited<ReturnType<typeof evaluatePermission>> & { reason: string }> = [];\n        for (const permissionKey of permissionKeys) {\n          const decision = await evaluatePermission(permissionUser, permissionKey as PermissionKey);\n          decisions.push({ ...decision, reason: permissionDecisionReason(decision, String(profile.legacyRole ?? "")) });\n        }\n        const allowed = decisions.filter(decision => decision.allowed).length;\n        return {\n          user: {\n            id: Number(profile.id),\n            name: profile.name ?? null,\n            email: profile.email ?? null,\n            legacyRole: profile.legacyRole ?? null,\n            teamId: profile.teamId == null ? null : Number(profile.teamId),\n          },\n          summary: { total: decisions.length, allowed, denied: decisions.length - allowed },\n          decisions,\n        };\n      } catch (error) { return mapError(error); }\n    }),\n'''
    new_router = replace_once(
        new_router,
        endpoint_anchor,
        endpoint_anchor + endpoint,
        "permission tester endpoint",
    )

if UI_MARKER not in ui:
    new_ui = replace_once(
        new_ui,
        '  const [tab, setTab] = useState<"roles" | "overrides">("roles");',
        '  const [tab, setTab] = useState<"roles" | "overrides" | "tester">("roles");',
        "tester tab state",
    )
    new_ui = replace_once(
        new_ui,
        '  const [userDraft, setUserDraft] = useState<Record<string, PermissionDraft>>({});\n',
        '  const [userDraft, setUserDraft] = useState<Record<string, PermissionDraft>>({});\n  const [testerUserId, setTesterUserId] = useState<number | null>(null);\n  const [testerSearch, setTesterSearch] = useState("");\n  const [testerPermissionKey, setTesterPermissionKey] = useState("all");\n',
        "tester state",
    )
    new_ui = replace_once(
        new_ui,
        '  const usersQuery = trpc.permissionsAdmin.listUsersForPermissions.useQuery(undefined, { enabled: tab === "overrides" });',
        '  const usersQuery = trpc.permissionsAdmin.listUsersForPermissions.useQuery(undefined, { enabled: tab === "overrides" || tab === "tester" });',
        "tester users query enablement",
    )
    user_profile_line = '  const userProfileQuery = trpc.permissionsAdmin.getUserPermissionProfile.useQuery({ userId: selectedUserId || 1 }, { enabled: !!selectedUserId && tab === "overrides" });\n'
    tester_query = '''  const testerQuery = trpc.permissionsAdmin.testUserPermissions.useQuery(\n    { userId: testerUserId || 1, ...(testerPermissionKey === "all" ? {} : { permissionKey: testerPermissionKey }) },\n    { enabled: !!testerUserId && tab === "tester" },\n  );\n'''
    new_ui = replace_once(
        new_ui,
        user_profile_line,
        user_profile_line + tester_query,
        "tester query",
    )

    visible_users = '''  const visibleUsers = useMemo(() => {\n    const q = userSearch.trim().toLowerCase();\n    return (usersQuery.data || []).filter((u: any) => !q || String(u.name || "").toLowerCase().includes(q) || String(u.email || "").toLowerCase().includes(q));\n  }, [usersQuery.data, userSearch]);\n'''
    visible_tester = '''  const visibleTesterUsers = useMemo(() => {\n    const q = testerSearch.trim().toLowerCase();\n    return (usersQuery.data || []).filter((u: any) => !q || String(u.name || "").toLowerCase().includes(q) || String(u.email || "").toLowerCase().includes(q));\n  }, [usersQuery.data, testerSearch]);\n'''
    new_ui = replace_once(
        new_ui,
        visible_users,
        visible_users + visible_tester,
        "tester user filter",
    )

    override_tab = '          <button onClick={() => setTab("overrides")} className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition ${tab === "overrides" ? "bg-background shadow-sm" : "text-muted-foreground hover:text-foreground"}`}><UserCog className="h-4 w-4" />{isRTL ? "استثناءات المستخدمين" : "User Overrides"}</button>\n'
    tester_tab = '          <button onClick={() => setTab("tester")} className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition ${tab === "tester" ? "bg-background shadow-sm" : "text-muted-foreground hover:text-foreground"}`}><Shield className="h-4 w-4" />{isRTL ? "اختبار الصلاحيات" : "Permission Tester"}</button>\n'
    new_ui = replace_once(
        new_ui,
        override_tab,
        override_tab + tester_tab,
        "tester tab button",
    )

    tester_block = '''\n        {/* ADVANCED_PERMISSIONS_PHASE4A_PERMISSION_TESTER_UI */}\n        {tab === "tester" && (\n          <div className="grid grid-cols-1 xl:grid-cols-[300px_minmax(0,1fr)] gap-5">\n            <Card className="h-fit xl:sticky xl:top-4">\n              <CardHeader className="pb-3"><CardTitle className="text-base flex items-center gap-2"><Shield className="h-4 w-4" />{isRTL ? "اختيار المستخدم" : "Select User"}</CardTitle></CardHeader>\n              <CardContent className="space-y-2 max-h-[72vh] overflow-auto">\n                <div className="relative mb-2"><Search className="absolute start-3 top-2.5 h-4 w-4 text-muted-foreground" /><Input className="ps-9" value={testerSearch} onChange={e => setTesterSearch(e.target.value)} placeholder={isRTL ? "بحث عن مستخدم..." : "Search users..."} /></div>\n                {usersQuery.error && <div className="text-sm text-destructive p-2">{usersQuery.error.message}</div>}\n                {visibleTesterUsers.map((u: any) => <button key={u.id} onClick={() => setTesterUserId(Number(u.id))} className={`w-full rounded-lg border p-3 text-start transition ${testerUserId === Number(u.id) ? "border-primary bg-primary/5" : "hover:bg-muted/40"}`}>\n                  <div className="font-medium truncate">{u.name || u.email}</div>\n                  <div className="mt-1 text-xs text-muted-foreground">{u.email}</div>\n                  <div className="mt-1 text-xs text-muted-foreground">{u.legacyRole || (isRTL ? "بدون دور legacy" : "No legacy role")}</div>\n                </button>)}\n              </CardContent>\n            </Card>\n\n            <div className="space-y-4">\n              {!testerUserId ? <Card><CardContent className="p-10 text-center text-muted-foreground">{isRTL ? "اختر مستخدمًا لاختبار صلاحياته الفعلية" : "Select a user to test effective permissions"}</CardContent></Card> : <>\n                <Card><CardContent className="p-4 flex flex-col lg:flex-row lg:items-center justify-between gap-4">\n                  <div>\n                    <h2 className="font-semibold text-lg">{testerQuery.data?.user.name || testerQuery.data?.user.email || (isRTL ? "اختبار الصلاحيات" : "Permission test")}</h2>\n                    <p className="text-xs text-muted-foreground mt-1">{testerQuery.data?.user.email}</p>\n                    {testerQuery.data?.user.legacyRole && <Badge variant="outline" className="mt-2">{testerQuery.data.user.legacyRole}</Badge>}\n                  </div>\n                  <Select value={testerPermissionKey} onValueChange={setTesterPermissionKey}>\n                    <SelectTrigger className="w-full lg:w-[320px]"><SelectValue /></SelectTrigger>\n                    <SelectContent>\n                      <SelectItem value="all">{isRTL ? "كل الصلاحيات" : "All permissions"}</SelectItem>\n                      {(catalog as any[]).map((p: any) => <SelectItem key={String(p.permissionKey)} value={String(p.permissionKey)}>{String(p.permissionKey)}</SelectItem>)}\n                    </SelectContent>\n                  </Select>\n                </CardContent></Card>\n\n                {testerQuery.isLoading ? <Card><CardContent className="p-8 text-center text-muted-foreground">{isRTL ? "جاري حساب الصلاحيات الفعلية..." : "Calculating effective permissions..."}</CardContent></Card> : testerQuery.error ? <Card><CardContent className="p-8 text-center text-destructive">{testerQuery.error.message}</CardContent></Card> : testerQuery.data ? <>\n                  <div className="grid grid-cols-3 gap-3">\n                    <Card><CardContent className="p-4"><div className="text-xs text-muted-foreground">{isRTL ? "الإجمالي" : "Total"}</div><div className="text-2xl font-bold mt-1">{testerQuery.data.summary.total}</div></CardContent></Card>\n                    <Card><CardContent className="p-4"><div className="text-xs text-muted-foreground">{isRTL ? "مسموح" : "Allowed"}</div><div className="text-2xl font-bold mt-1">{testerQuery.data.summary.allowed}</div></CardContent></Card>\n                    <Card><CardContent className="p-4"><div className="text-xs text-muted-foreground">{isRTL ? "ممنوع" : "Denied"}</div><div className="text-2xl font-bold mt-1">{testerQuery.data.summary.denied}</div></CardContent></Card>\n                  </div>\n                  <Card>\n                    <CardHeader className="pb-3"><CardTitle className="text-base">{isRTL ? "النتيجة الفعلية ولماذا" : "Effective Result & Why"}</CardTitle></CardHeader>\n                    <CardContent className="p-0">\n                      <div className="divide-y max-h-[65vh] overflow-auto">\n                        {testerQuery.data.decisions.map((d: any) => <div key={String(d.permission)} className="grid grid-cols-1 md:grid-cols-[minmax(190px,1fr)_110px_130px_minmax(220px,1fr)] gap-3 p-3 items-center">\n                          <code className="text-xs">{String(d.permission)}</code>\n                          <Badge variant={d.allowed ? "default" : "destructive"} className="w-fit">{d.allowed ? (isRTL ? "مسموح" : "Allowed") : (isRTL ? "ممنوع" : "Denied")}</Badge>\n                          <span className="text-xs text-muted-foreground">{isRTL ? "النطاق: " : "Scope: "}{String(d.scope)}</span>\n                          <div><div className="text-sm">{String(d.reason)}</div><div className="text-[11px] text-muted-foreground mt-1">source: {String(d.source)}{Array.isArray(d.roleIds) && d.roleIds.length ? ` • roleIds: ${d.roleIds.join(",")}` : ""}</div></div>\n                        </div>)}\n                      </div>\n                    </CardContent>\n                  </Card>\n                </> : null}\n              </>}\n            </div>\n          </div>\n        )}\n'''
    final_anchor = '      </div>\n\n      <RoleDialog open={createOpen}'
    new_ui = insert_before_last(
        new_ui,
        final_anchor,
        tester_block,
        "tester UI block",
    )

# Write only after every required anchor has been verified in memory.
if new_router != router:
    router_path.write_text(new_router, encoding="utf-8")
if new_ui != ui:
    ui_path.write_text(new_ui, encoding="utf-8")

print(f"BASELINE_HEAD={head}")
print(f"SERVER_PATCHED={'YES' if SERVER_MARKER in new_router else 'NO'}")
print(f"UI_PATCHED={'YES' if UI_MARKER in new_ui else 'NO'}")
print("TARGET_FILES=server/permissionsAdminRouter.ts, client/src/pages/RolesPermissions.tsx")
