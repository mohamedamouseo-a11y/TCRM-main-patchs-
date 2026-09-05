#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

EXPECTED_HEAD = "eb497212634c73a111b5ae7236797210be1a3a83"
UI_MARKER = "ADVANCED_PERMISSIONS_PHASE4B_TEMPORARY_ACCESS_UI"
ENGINE_MARKER = "ADVANCED_PERMISSIONS_PHASE4B_TEMPORARY_ACCESS_ENGINE"

root = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TCRM-MAIN").resolve()
ui_path = root / "client/src/pages/RolesPermissions.tsx"
engine_path = root / "server/security/permissionEngine.ts"

for path in (ui_path, engine_path):
    if not path.exists():
        raise SystemExit(f"Missing required target file: {path}")

head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
if head != EXPECTED_HEAD:
    raise SystemExit(f"Baseline mismatch: expected {EXPECTED_HEAD}, got {head}. No files changed.")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"Anchor mismatch for {label}: expected exactly 1 match, got {count}. No files changed.")
    return text.replace(old, new, 1)


ui = ui_path.read_text()
engine = engine_path.read_text()
new_ui = ui
new_engine = engine

if UI_MARKER not in ui:
    new_ui = replace_once(
        new_ui,
        'type PermissionDraft = { effect: EffectState; dataScope: string; scopeConfig?: Record<string, unknown> | null };',
        'type PermissionDraft = { effect: EffectState; dataScope: string; scopeConfig?: Record<string, unknown> | null; startsAt?: string | null; expiresAt?: string | null; reason?: string | null };',
        "PermissionDraft temporary access fields",
    )

    helpers = '''// ADVANCED_PERMISSIONS_PHASE4B_TEMPORARY_ACCESS_UI\nfunction toDateTimeLocalInput(value: unknown): string {\n  if (!value) return "";\n  const date = value instanceof Date ? value : new Date(String(value));\n  if (Number.isNaN(date.getTime())) return "";\n  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);\n  return local.toISOString().slice(0, 16);\n}\n\nfunction fromDateTimeLocalInput(value?: string | null): Date | null {\n  if (!value?.trim()) return null;\n  const date = new Date(value);\n  return Number.isNaN(date.getTime()) ? null : date;\n}\n\n'''
    new_ui = replace_once(
        new_ui,
        'export default function RolesPermissions() {',
        helpers + 'export default function RolesPermissions() {',
        "temporary access helpers",
    )

    old_load = '''      next[String(item.permissionKey)] = {\n        effect: String(item.effect) === "deny" ? "deny" : "allow",\n        dataScope: String(item.dataScope || "none"),\n        scopeConfig: item.scopeConfig ?? null,\n      };'''
    new_load = '''      next[String(item.permissionKey)] = {\n        effect: String(item.effect) === "deny" ? "deny" : "allow",\n        dataScope: String(item.dataScope || "none"),\n        scopeConfig: item.scopeConfig ?? null,\n        startsAt: toDateTimeLocalInput(item.startsAt),\n        expiresAt: toDateTimeLocalInput(item.expiresAt),\n        reason: item.reason == null ? "" : String(item.reason),\n      };'''
    new_ui = replace_once(new_ui, old_load, new_load, "override draft hydration")

    old_save = '''  const saveUserOverrides = () => {\n    if (!selectedUserId) return;\n    const entries = Object.entries(userDraft).filter(([, v]) => v.effect !== "inherit").map(([permissionKey, v]) => ({\n      permissionKey, effect: v.effect as "allow" | "deny", dataScope: (v.effect === "deny" ? "none" : v.dataScope) as any, scopeConfig: v.scopeConfig ?? null,\n    }));\n    userOverridesMutation.mutate({ userId: selectedUserId, entries });\n  };'''
    new_save = '''  const saveUserOverrides = () => {\n    if (!selectedUserId) return;\n    const entries: any[] = [];\n    for (const [permissionKey, v] of Object.entries(userDraft)) {\n      if (v.effect === "inherit") continue;\n      const startsAt = fromDateTimeLocalInput(v.startsAt);\n      const expiresAt = fromDateTimeLocalInput(v.expiresAt);\n      if (startsAt && expiresAt && expiresAt <= startsAt) {\n        toast.error(isRTL ? `وقت انتهاء ${permissionKey} يجب أن يكون بعد وقت البداية` : `${permissionKey}: expiry must be after start`);\n        return;\n      }\n      entries.push({\n        permissionKey,\n        effect: v.effect as "allow" | "deny",\n        dataScope: (v.effect === "deny" ? "none" : v.dataScope) as any,\n        scopeConfig: v.scopeConfig ?? null,\n        startsAt,\n        expiresAt,\n        reason: v.reason?.trim() || null,\n      });\n    }\n    userOverridesMutation.mutate({ userId: selectedUserId, entries });\n  };'''
    new_ui = replace_once(new_ui, old_save, new_save, "temporary override save payload")

    old_note = '                  <div className="mt-3 rounded-lg bg-amber-50 border border-amber-200 p-2 text-xs text-amber-700">{isRTL ? "استثناءات المستخدم تتفوق على صلاحيات الدور. Allow يسمح باختيار النطاق. Deny = بدون نطاق. Inherit = لا override." : "User overrides take precedence over role permissions. Allow lets you choose scope. Deny = none scope. Inherit = no override."}</div>'
    new_note = '                  <div className="mt-3 rounded-lg bg-amber-50 border border-amber-200 p-2 text-xs text-amber-700">{isRTL ? "استثناءات المستخدم تتفوق على صلاحيات الدور. يمكن تحديد بداية ونهاية مؤقتة لكل استثناء؛ اتركهما فارغين ليكون دائمًا. Deny = بدون نطاق، و Inherit = لا override." : "User overrides take precedence over role permissions. Each override can have an optional start and expiry; leave both blank for permanent access. Deny = none scope; Inherit = no override."}</div>'
    new_ui = replace_once(new_ui, old_note, new_note, "temporary access helper note")

    card_start = '                <Card><CardHeader className="pb-3"><CardTitle className="text-base">{isRTL ? "استثناءات الصلاحيات" : "Permission Overrides"}</CardTitle></CardHeader><CardContent>\n'
    start_pos = new_ui.find(card_start)
    if start_pos < 0:
        raise SystemExit("Anchor mismatch for overrides card start. No files changed.")
    card_end = '                </CardContent></Card>\n'
    end_pos = new_ui.find(card_end, start_pos)
    if end_pos < 0:
        raise SystemExit("Anchor mismatch for overrides card end. No files changed.")
    end_pos += len(card_end)

    new_card = '''                <Card><CardHeader className="pb-3"><CardTitle className="text-base">{isRTL ? "استثناءات الصلاحيات" : "Permission Overrides"}</CardTitle></CardHeader><CardContent>\n                  <div className="space-y-5">{Object.entries(grouped).map(([moduleKey, items]) => <div key={moduleKey} className="border rounded-xl overflow-hidden"><div className="px-4 py-3 bg-muted/40 font-semibold">{MODULE_LABELS[moduleKey]?.[isRTL ? "ar" : "en"] || moduleKey}</div><div className="divide-y">{items.map((p: any) => {\n                    const key = String(p.permissionKey);\n                    const state = userDraft[key] || { effect: "inherit", dataScope: "none", startsAt: "", expiresAt: "", reason: "" };\n                    const now = Date.now();\n                    const startMs = state.startsAt ? new Date(state.startsAt).getTime() : null;\n                    const expiryMs = state.expiresAt ? new Date(state.expiresAt).getTime() : null;\n                    const timingStatus = state.effect === "inherit" ? "inherit" : expiryMs != null && expiryMs <= now ? "expired" : startMs != null && startMs > now ? "scheduled" : state.startsAt || state.expiresAt ? "active" : "permanent";\n                    const timingLabel = timingStatus === "expired" ? (isRTL ? "منتهي" : "Expired") : timingStatus === "scheduled" ? (isRTL ? "مجدول" : "Scheduled") : timingStatus === "active" ? (isRTL ? "نشط مؤقتًا" : "Temporarily active") : timingStatus === "permanent" ? (isRTL ? "دائم" : "Permanent") : (isRTL ? "وراثة" : "Inherit");\n                    return <div key={p.permissionKey} className="p-3 space-y-3">\n                      <div className="grid grid-cols-1 md:grid-cols-[minmax(180px,1fr)_170px_190px] gap-3 items-center">\n                        <div><div className="font-medium text-sm">{ACTION_LABELS[String(p.actionKey)]?.[isRTL ? "ar" : "en"] || p.actionKey}</div><code className="text-[11px] text-muted-foreground">{p.permissionKey}</code></div>\n                        <Select value={state.effect} onValueChange={(v: EffectState) => setUserPermission(key, { effect: v, dataScope: v === "deny" ? "none" : (state.dataScope === "none" ? "all" : state.dataScope) })}><SelectTrigger className={state.effect === "allow" ? "border-emerald-500/50" : state.effect === "deny" ? "border-destructive/50" : ""}><SelectValue /></SelectTrigger><SelectContent><SelectItem value="inherit">{isRTL ? "وراثة" : "Inherit"}</SelectItem><SelectItem value="allow">{isRTL ? "سماح" : "Allow"}</SelectItem><SelectItem value="deny">{isRTL ? "منع" : "Deny"}</SelectItem></SelectContent></Select>\n                        <Select disabled={state.effect !== "allow"} value={state.effect === "allow" ? state.dataScope : "none"} onValueChange={v => setUserPermission(key, { dataScope: v })}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{(catalogQuery.data?.scopes || []).map((s: string) => <SelectItem key={s} value={s}>{SCOPE_LABELS[s]?.[isRTL ? "ar" : "en"] || s}</SelectItem>)}</SelectContent></Select>\n                      </div>\n                      {state.effect !== "inherit" && <div className="grid grid-cols-1 md:grid-cols-[1fr_1fr_minmax(180px,1fr)_auto] gap-3 items-end rounded-lg bg-muted/25 p-3">\n                        <div><Label className="text-xs">{isRTL ? "يبدأ في" : "Starts at"}</Label><Input type="datetime-local" value={state.startsAt || ""} onChange={e => setUserPermission(key, { startsAt: e.target.value })} className="mt-1" /></div>\n                        <div><Label className="text-xs">{isRTL ? "ينتهي في" : "Expires at"}</Label><Input type="datetime-local" value={state.expiresAt || ""} onChange={e => setUserPermission(key, { expiresAt: e.target.value })} className="mt-1" /></div>\n                        <div><Label className="text-xs">{isRTL ? "سبب / ملاحظة" : "Reason / note"}</Label><Input value={state.reason || ""} onChange={e => setUserPermission(key, { reason: e.target.value })} maxLength={500} placeholder={isRTL ? "اختياري" : "Optional"} className="mt-1" /></div>\n                        <Badge variant={timingStatus === "expired" ? "destructive" : timingStatus === "scheduled" ? "secondary" : "outline"} className="mb-2 w-fit">{timingLabel}</Badge>\n                      </div>}\n                    </div>;\n                  })}</div></div>)}</div>\n                </CardContent></Card>\n'''
    new_ui = new_ui[:start_pos] + new_card + new_ui[end_pos:]

if ENGINE_MARKER not in engine:
    old_engine = '''      AND p.permission_key = ${String(permission)}\n      AND p.is_active = 1\n      AND (upo.expires_at IS NULL OR upo.expires_at > NOW())'''
    new_engine_block = '''      AND p.permission_key = ${String(permission)}\n      AND p.is_active = 1\n      -- ADVANCED_PERMISSIONS_PHASE4B_TEMPORARY_ACCESS_ENGINE\n      AND (upo.starts_at IS NULL OR upo.starts_at <= NOW())\n      AND (upo.expires_at IS NULL OR upo.expires_at > NOW())'''
    new_engine = replace_once(engine, old_engine, new_engine_block, "permission engine override activation window")

if new_ui == ui and new_engine == engine:
    print("Phase 4B already applied; no changes needed.")
    raise SystemExit(0)

# All anchors are validated before writing either file.
ui_path.write_text(new_ui)
engine_path.write_text(new_engine)
print("Phase 4B Temporary Access V1 applied.")
print(f"Modified: {ui_path.relative_to(root)}")
print(f"Modified: {engine_path.relative_to(root)}")
