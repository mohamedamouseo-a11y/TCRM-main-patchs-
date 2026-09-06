#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

EXPECTED_HEAD = "7da712b977843ee28c2de2b49b7cc6ad94338a41"
ADMIN_MARKER = "ADVANCED_PERMISSIONS_PHASE4C_ROLE_INHERITANCE_ADMIN"
ROUTER_MARKER = "ADVANCED_PERMISSIONS_PHASE4C_ROLE_INHERITANCE_ROUTER"
ENGINE_MARKER = "ADVANCED_PERMISSIONS_PHASE4C_ROLE_INHERITANCE_ENGINE"
UI_MARKER = "ADVANCED_PERMISSIONS_PHASE4C_ROLE_INHERITANCE_UI"

root = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TCRM-MAIN").resolve()
admin_path = root / "server/security/permissionAdminService.ts"
router_path = root / "server/permissionsAdminRouter.ts"
engine_path = root / "server/security/permissionEngine.ts"
ui_path = root / "client/src/pages/RolesPermissions.tsx"
paths = (admin_path, router_path, engine_path, ui_path)

for path in paths:
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


admin = admin_path.read_text()
router = router_path.read_text()
engine = engine_path.read_text()
ui = ui_path.read_text()
new_admin, new_router, new_engine, new_ui = admin, router, engine, ui

if ADMIN_MARKER not in admin:
    new_admin = replace_once(new_admin, '''function safeJson(value: unknown) {
  return value == null ? null : JSON.stringify(value);
}
''', '''function safeJson(value: unknown) {
  return value == null ? null : JSON.stringify(value);
}

// ADVANCED_PERMISSIONS_PHASE4C_ROLE_INHERITANCE_ADMIN
async function validateParentRoleId(
  db: any,
  parentRoleId: number | null | undefined,
  targetRoleId?: number | null,
): Promise<number | null> {
  if (parentRoleId == null) return null;
  const normalized = Number(parentRoleId);
  if (!Number.isInteger(normalized) || normalized <= 0) {
    throw new PermissionAdminError("BAD_REQUEST", "Invalid parent role");
  }
  if (targetRoleId && normalized === Number(targetRoleId)) {
    throw new PermissionAdminError("BAD_REQUEST", "A role cannot inherit from itself");
  }

  const roleRows = rows(await db.execute(sql`
    SELECT id, parent_role_id AS parentRoleId, is_active AS isActive
    FROM roles
  `));
  const byId = new Map<number, any>(roleRows.map((item: any) => [Number(item.id), item]));
  let current = normalized;
  const seen = new Set<number>();

  for (let depth = 0; current; depth += 1) {
    if (depth > 32) throw new PermissionAdminError("BAD_REQUEST", "Role inheritance chain is too deep");
    if (targetRoleId && current === Number(targetRoleId)) {
      throw new PermissionAdminError("BAD_REQUEST", "Role inheritance cycle detected");
    }
    if (seen.has(current)) {
      throw new PermissionAdminError("BAD_REQUEST", "Role inheritance cycle detected");
    }
    seen.add(current);

    const item = byId.get(current);
    if (!item) throw new PermissionAdminError("BAD_REQUEST", "Parent role not found");
    if (Number(item.isActive) !== 1) {
      throw new PermissionAdminError("BAD_REQUEST", "Parent role must be active");
    }
    current = item.parentRoleId == null ? 0 : Number(item.parentRoleId);
  }

  return normalized;
}
''', "admin inheritance validation helper")

    new_admin = replace_once(new_admin, '''export async function createPermissionRole(input: {
  roleKey?: string;
  name: string;
  nameAr?: string | null;
  description?: string | null;
}, actorUserId: number) {''', '''export async function createPermissionRole(input: {
  roleKey?: string;
  name: string;
  nameAr?: string | null;
  description?: string | null;
  parentRoleId?: number | null;
}, actorUserId: number) {''', "create role parent input")

    new_admin = replace_once(new_admin, '''  const db = await getDb();
  if (!db) throw new PermissionAdminError("BAD_REQUEST", "Database is unavailable");
  const roleKey = slugifyRoleKey(input.roleKey || input.name);''', '''  const db = await getDb();
  if (!db) throw new PermissionAdminError("BAD_REQUEST", "Database is unavailable");
  const parentRoleId = await validateParentRoleId(db, input.parentRoleId);
  const roleKey = slugifyRoleKey(input.roleKey || input.name);''', "create role parent validation")

    new_admin = replace_once(new_admin, '''    INSERT INTO roles (role_key, name, name_ar, description, is_system, is_active, created_by, updated_by)
    VALUES (${roleKey}, ${input.name.trim()}, ${input.nameAr?.trim() || null}, ${input.description?.trim() || null}, 0, 1, ${actorUserId}, ${actorUserId})''', '''    INSERT INTO roles (role_key, name, name_ar, description, parent_role_id, is_system, is_active, created_by, updated_by)
    VALUES (${roleKey}, ${input.name.trim()}, ${input.nameAr?.trim() || null}, ${input.description?.trim() || null}, ${parentRoleId}, 0, 1, ${actorUserId}, ${actorUserId})''', "create role parent insert")

    new_admin = replace_once(new_admin, '''export async function updatePermissionRole(roleId: number, input: {
  name: string;
  nameAr?: string | null;
  description?: string | null;
}, actorUserId: number) {''', '''export async function updatePermissionRole(roleId: number, input: {
  name: string;
  nameAr?: string | null;
  description?: string | null;
  parentRoleId?: number | null;
}, actorUserId: number) {''', "update role parent input")

    new_admin = replace_once(new_admin, '''  const db = await getDb();
  if (!db) throw new PermissionAdminError("BAD_REQUEST", "Database is unavailable");
  await db.execute(sql`
    UPDATE roles SET name = ${input.name.trim()}, name_ar = ${input.nameAr?.trim() || null},
      description = ${input.description?.trim() || null}, updated_by = ${actorUserId}
    WHERE id = ${roleId}
  `);''', '''  const db = await getDb();
  if (!db) throw new PermissionAdminError("BAD_REQUEST", "Database is unavailable");
  const parentRoleId = input.parentRoleId === undefined
    ? (before.parentRoleId == null ? null : Number(before.parentRoleId))
    : await validateParentRoleId(db, input.parentRoleId, roleId);
  await db.execute(sql`
    UPDATE roles SET name = ${input.name.trim()}, name_ar = ${input.nameAr?.trim() || null},
      description = ${input.description?.trim() || null}, parent_role_id = ${parentRoleId}, updated_by = ${actorUserId}
    WHERE id = ${roleId}
  `);''', "update role parent persistence")

    new_admin = replace_once(new_admin, '''  const created = await createPermissionRole({ roleKey: input.roleKey, name: input.name, nameAr: input.nameAr, description: `Copied from ${source.name}` }, actorUserId);''', '''  const created = await createPermissionRole({
    roleKey: input.roleKey,
    name: input.name,
    nameAr: input.nameAr,
    description: `Copied from ${source.name}`,
    parentRoleId: source.parentRoleId == null ? null : Number(source.parentRoleId),
  }, actorUserId);''', "duplicate role preserves parent")

if ROUTER_MARKER not in router:
    new_router = replace_once(new_router, '''const roleDetailsInput = z.object({
  name: z.string().trim().min(2).max(150),
  nameAr: z.string().trim().max(150).optional().nullable(),
  description: z.string().trim().max(2000).optional().nullable(),
});''', '''// ADVANCED_PERMISSIONS_PHASE4C_ROLE_INHERITANCE_ROUTER
const roleDetailsInput = z.object({
  name: z.string().trim().min(2).max(150),
  nameAr: z.string().trim().max(150).optional().nullable(),
  description: z.string().trim().max(2000).optional().nullable(),
  parentRoleId: z.number().int().positive().optional().nullable(),
});''', "router role details parent input")

    new_router = replace_once(new_router, '''          description: input.description,
        }, actorId(ctx));''', '''          description: input.description,
          parentRoleId: input.parentRoleId,
        }, actorId(ctx));''', "router update parent payload")

if ENGINE_MARKER not in engine:
    new_engine = replace_once(new_engine, '''function strongestScope(scopes: Array<PermissionScope | null | undefined>): PermissionScope {
  return scopes.reduce<PermissionScope>((best, item) => {
    const current = item && item in SCOPE_WEIGHT ? item : "none";
    return SCOPE_WEIGHT[current] > SCOPE_WEIGHT[best] ? current : best;
  }, "none");
}
''', '''function strongestScope(scopes: Array<PermissionScope | null | undefined>): PermissionScope {
  return scopes.reduce<PermissionScope>((best, item) => {
    const current = item && item in SCOPE_WEIGHT ? item : "none";
    return SCOPE_WEIGHT[current] > SCOPE_WEIGHT[best] ? current : best;
  }, "none");
}

// ADVANCED_PERMISSIONS_PHASE4C_ROLE_INHERITANCE_ENGINE
function resolveInheritedRoleRows(graphRows: any[], rootRoleIds: number[]) {
  const byRole = new Map<number, any[]>();
  for (const row of graphRows) {
    const roleId = Number(row.roleId);
    if (!Number.isFinite(roleId) || roleId <= 0) continue;
    const bucket = byRole.get(roleId) || [];
    bucket.push(row);
    byRole.set(roleId, bucket);
  }

  const effective: any[] = [];
  for (const rootRoleId of Array.from(new Set(rootRoleIds))) {
    let current = Number(rootRoleId);
    const seen = new Set<number>();
    for (let depth = 0; current && depth <= 32; depth += 1) {
      if (seen.has(current)) break;
      seen.add(current);
      const candidates = byRole.get(current) || [];
      if (!candidates.length) break;

      const explicit = candidates.filter((item: any) => {
        const effect = String(item.effect || "");
        return effect === "allow" || effect === "deny";
      });
      if (explicit.length) {
        effective.push(...explicit.map((item: any) => ({ ...item, rootRoleId, depth })));
        break;
      }

      const parentRoleId = candidates[0]?.parentRoleId;
      current = parentRoleId == null ? 0 : Number(parentRoleId);
    }
  }
  return effective;
}
''', "engine inheritance resolver")

    old_role_block = '''  const roleRows = rows(await db.execute(sql`
    SELECT r.id AS roleId, rp.effect, rp.data_scope AS dataScope
    FROM user_roles ur
    JOIN roles r ON r.id = ur.role_id AND r.is_active = 1
    JOIN role_permissions rp ON rp.role_id = r.id
    JOIN permissions p ON p.id = rp.permission_id AND p.is_active = 1
    WHERE ur.user_id = ${userId}
      AND ur.is_active = 1
      AND (ur.expires_at IS NULL OR ur.expires_at > NOW())
      AND p.permission_key = ${String(permission)}
  `));

  if (roleRows.some((r: any) => String(r.effect) === "deny")) {
    return { allowed: false, permission, scope: "none", source: "role", roleIds: roleRows.map((r: any) => Number(r.roleId)) };
  }

  const roleAllows = roleRows.filter((r: any) => String(r.effect) === "allow");
  if (roleAllows.length) {
    return {
      allowed: true,
      permission,
      scope: strongestScope(roleAllows.map((r: any) => String(r.dataScope || "all") as PermissionScope)),
      source: "role",
      roleIds: roleAllows.map((r: any) => Number(r.roleId)),
    };
  }

  const legacyRole = String(user.role ?? "").trim();
  if (legacyRole) {
    const legacyRows = rows(await db.execute(sql`
      SELECT rp.effect, rp.data_scope AS dataScope, r.id AS roleId
      FROM roles r
      JOIN role_permissions rp ON rp.role_id = r.id
      JOIN permissions p ON p.id = rp.permission_id
      WHERE r.legacy_role_key = ${legacyRole}
        AND r.is_active = 1
        AND p.is_active = 1
        AND p.permission_key = ${String(permission)}
    `));
    if (legacyRows.some((r: any) => String(r.effect) === "deny")) {
      return { allowed: false, permission, scope: "none", source: "legacy_role" };
    }
    const legacyAllows = legacyRows.filter((r: any) => String(r.effect) === "allow");
    if (legacyAllows.length) {
      return {
        allowed: true,
        permission,
        scope: strongestScope(legacyAllows.map((r: any) => String(r.dataScope || "all") as PermissionScope)),
        source: "legacy_role",
        roleIds: legacyAllows.map((r: any) => Number(r.roleId)),
      };
    }
  }
'''
    new_role_block = '''  const roleGraphRows = rows(await db.execute(sql`
    SELECT r.id AS roleId, r.parent_role_id AS parentRoleId, r.legacy_role_key AS legacyRoleKey,
           rp.effect, rp.data_scope AS dataScope,
           EXISTS(
             SELECT 1
             FROM user_roles ur
             WHERE ur.role_id = r.id
               AND ur.user_id = ${userId}
               AND ur.is_active = 1
               AND (ur.expires_at IS NULL OR ur.expires_at > NOW())
           ) AS isAssigned
    FROM roles r
    LEFT JOIN permissions p
      ON p.permission_key = ${String(permission)} AND p.is_active = 1
    LEFT JOIN role_permissions rp
      ON rp.role_id = r.id AND rp.permission_id = p.id
    WHERE r.is_active = 1
  `));

  const assignedRoleIds = roleGraphRows
    .filter((r: any) => Number(r.isAssigned) === 1)
    .map((r: any) => Number(r.roleId));
  const roleRows = resolveInheritedRoleRows(roleGraphRows, assignedRoleIds);

  if (roleRows.some((r: any) => String(r.effect) === "deny")) {
    return {
      allowed: false,
      permission,
      scope: "none",
      source: "role",
      roleIds: Array.from(new Set(roleRows.map((r: any) => Number(r.roleId)))),
    };
  }

  const roleAllows = roleRows.filter((r: any) => String(r.effect) === "allow");
  if (roleAllows.length) {
    return {
      allowed: true,
      permission,
      scope: strongestScope(roleAllows.map((r: any) => String(r.dataScope || "all") as PermissionScope)),
      source: "role",
      roleIds: Array.from(new Set(roleAllows.map((r: any) => Number(r.roleId)))),
    };
  }

  const legacyRole = String(user.role ?? "").trim();
  if (legacyRole) {
    const legacyRootIds = roleGraphRows
      .filter((r: any) => String(r.legacyRoleKey ?? "") === legacyRole)
      .map((r: any) => Number(r.roleId));
    const legacyRows = resolveInheritedRoleRows(roleGraphRows, legacyRootIds);
    if (legacyRows.some((r: any) => String(r.effect) === "deny")) {
      return {
        allowed: false,
        permission,
        scope: "none",
        source: "legacy_role",
        roleIds: Array.from(new Set(legacyRows.map((r: any) => Number(r.roleId)))),
      };
    }
    const legacyAllows = legacyRows.filter((r: any) => String(r.effect) === "allow");
    if (legacyAllows.length) {
      return {
        allowed: true,
        permission,
        scope: strongestScope(legacyAllows.map((r: any) => String(r.dataScope || "all") as PermissionScope)),
        source: "legacy_role",
        roleIds: Array.from(new Set(legacyAllows.map((r: any) => Number(r.roleId)))),
      };
    }
  }
'''
    new_engine = replace_once(new_engine, old_role_block, new_role_block, "engine dynamic and legacy inheritance")

if UI_MARKER not in ui:
    new_ui = replace_once(new_ui, '''  const [form, setForm] = useState({ roleKey: "", name: "", nameAr: "", description: "" });''', '''  // ADVANCED_PERMISSIONS_PHASE4C_ROLE_INHERITANCE_UI
  const [form, setForm] = useState({ roleKey: "", name: "", nameAr: "", description: "", parentRoleId: "none" });''', "UI role form parent field")

    new_ui = replace_once(new_ui, '''{tab === "roles" && <Button onClick={() => { setForm({ roleKey: "", name: "", nameAr: "", description: "" }); setCreateOpen(true); }}><Plus className="h-4 w-4 me-2" />{isRTL ? "دور جديد" : "New role"}</Button>}''', '''{tab === "roles" && <Button onClick={() => { setForm({ roleKey: "", name: "", nameAr: "", description: "", parentRoleId: "none" }); setCreateOpen(true); }}><Plus className="h-4 w-4 me-2" />{isRTL ? "دور جديد" : "New role"}</Button>}''', "UI create role form reset")

    new_ui = replace_once(new_ui, '''<Button variant="outline" size="sm" onClick={() => { setForm({ roleKey: selectedRole.roleKey, name: selectedRole.name || "", nameAr: selectedRole.nameAr || "", description: selectedRole.description || "" }); setEditOpen(true); }}>{isRTL ? "تعديل" : "Edit"}</Button>''', '''<Button variant="outline" size="sm" onClick={() => { setForm({ roleKey: selectedRole.roleKey, name: selectedRole.name || "", nameAr: selectedRole.nameAr || "", description: selectedRole.description || "", parentRoleId: selectedRole.parentRoleId == null ? "none" : String(selectedRole.parentRoleId) }); setEditOpen(true); }}>{isRTL ? "تعديل" : "Edit"}</Button>''', "UI edit role parent hydration")

    new_ui = replace_once(new_ui, '''<Button variant="outline" size="sm" onClick={() => { setForm({ roleKey: "", name: `${selectedRole.name} Copy`, nameAr: selectedRole.nameAr ? `${selectedRole.nameAr} - نسخة` : "", description: "" }); setCopyOpen(true); }}><Copy className="h-4 w-4 me-1" />{isRTL ? "نسخ" : "Duplicate"}</Button>''', '''<Button variant="outline" size="sm" onClick={() => { setForm({ roleKey: "", name: `${selectedRole.name} Copy`, nameAr: selectedRole.nameAr ? `${selectedRole.nameAr} - نسخة` : "", description: "", parentRoleId: selectedRole.parentRoleId == null ? "none" : String(selectedRole.parentRoleId) }); setCopyOpen(true); }}><Copy className="h-4 w-4 me-1" />{isRTL ? "نسخ" : "Duplicate"}</Button>''', "UI duplicate role form shape")

    old_dialog_calls = '''      <RoleDialog open={createOpen} onOpenChange={setCreateOpen} title={isRTL ? "إنشاء دور جديد" : "Create role"} form={form} setForm={setForm} isRTL={isRTL} showKey onSubmit={() => createMutation.mutate({ roleKey: form.roleKey || undefined, name: form.name, nameAr: form.nameAr || null, description: form.description || null })} busy={createMutation.isPending} />
      <RoleDialog open={editOpen} onOpenChange={setEditOpen} title={isRTL ? "تعديل الدور" : "Edit role"} form={form} setForm={setForm} isRTL={isRTL} onSubmit={() => selectedRoleId && updateMutation.mutate({ roleId: selectedRoleId, name: form.name, nameAr: form.nameAr || null, description: form.description || null })} busy={updateMutation.isPending} />
      <RoleDialog open={copyOpen} onOpenChange={setCopyOpen} title={isRTL ? "نسخ الدور" : "Duplicate role"} form={form} setForm={setForm} isRTL={isRTL} showKey onSubmit={() => selectedRoleId && duplicateMutation.mutate({ sourceRoleId: selectedRoleId, roleKey: form.roleKey || undefined, name: form.name, nameAr: form.nameAr || null })} busy={duplicateMutation.isPending} />'''
    new_dialog_calls = '''      <RoleDialog open={createOpen} onOpenChange={setCreateOpen} title={isRTL ? "إنشاء دور جديد" : "Create role"} form={form} setForm={setForm} isRTL={isRTL} showKey showParent roles={visibleRoles} onSubmit={() => createMutation.mutate({ roleKey: form.roleKey || undefined, name: form.name, nameAr: form.nameAr || null, description: form.description || null, parentRoleId: form.parentRoleId !== "none" ? Number(form.parentRoleId) : null })} busy={createMutation.isPending} />
      <RoleDialog open={editOpen} onOpenChange={setEditOpen} title={isRTL ? "تعديل الدور" : "Edit role"} form={form} setForm={setForm} isRTL={isRTL} showParent roles={visibleRoles} currentRoleId={selectedRoleId} onSubmit={() => selectedRoleId && updateMutation.mutate({ roleId: selectedRoleId, name: form.name, nameAr: form.nameAr || null, description: form.description || null, parentRoleId: form.parentRoleId !== "none" ? Number(form.parentRoleId) : null })} busy={updateMutation.isPending} />
      <RoleDialog open={copyOpen} onOpenChange={setCopyOpen} title={isRTL ? "نسخ الدور" : "Duplicate role"} form={form} setForm={setForm} isRTL={isRTL} showKey onSubmit={() => selectedRoleId && duplicateMutation.mutate({ sourceRoleId: selectedRoleId, roleKey: form.roleKey || undefined, name: form.name, nameAr: form.nameAr || null })} busy={duplicateMutation.isPending} />'''
    new_ui = replace_once(new_ui, old_dialog_calls, new_dialog_calls, "UI role dialog wiring")

    old_role_dialog = '''function RoleDialog({ open, onOpenChange, title, form, setForm, isRTL, showKey = false, onSubmit, busy }: any) {
  return <Dialog open={open} onOpenChange={onOpenChange}><DialogContent dir={isRTL ? "rtl" : "ltr"}><DialogHeader><DialogTitle>{title}</DialogTitle></DialogHeader><div className="space-y-4"><div><Label>{isRTL ? "الاسم" : "Name"}</Label><Input value={form.name} onChange={e => setForm((p: any) => ({ ...p, name: e.target.value }))} /></div><div><Label>{isRTL ? "الاسم بالعربية" : "Arabic name"}</Label><Input value={form.nameAr} onChange={e => setForm((p: any) => ({ ...p, nameAr: e.target.value }))} /></div>{showKey && <div><Label>Role key</Label><Input value={form.roleKey} onChange={e => setForm((p: any) => ({ ...p, roleKey: e.target.value }))} placeholder="senior_sales_agent" /></div>}<div><Label>{isRTL ? "الوصف" : "Description"}</Label><Textarea value={form.description} onChange={e => setForm((p: any) => ({ ...p, description: e.target.value }))} /></div></div><DialogFooter><Button variant="outline" onClick={() => onOpenChange(false)}>{isRTL ? "إلغاء" : "Cancel"}</Button><Button onClick={onSubmit} disabled={busy || !form.name.trim()}>{isRTL ? "حفظ" : "Save"}</Button></DialogFooter></DialogContent></Dialog>;
}'''
    new_role_dialog = '''function RoleDialog({ open, onOpenChange, title, form, setForm, isRTL, showKey = false, showParent = false, roles = [], currentRoleId = null, onSubmit, busy }: any) {
  const parentOptions = (roles || []).filter((role: any) => Number(role.id) !== Number(currentRoleId));
  return <Dialog open={open} onOpenChange={onOpenChange}><DialogContent dir={isRTL ? "rtl" : "ltr"}><DialogHeader><DialogTitle>{title}</DialogTitle></DialogHeader><div className="space-y-4"><div><Label>{isRTL ? "الاسم" : "Name"}</Label><Input value={form.name} onChange={e => setForm((p: any) => ({ ...p, name: e.target.value }))} /></div><div><Label>{isRTL ? "الاسم بالعربية" : "Arabic name"}</Label><Input value={form.nameAr} onChange={e => setForm((p: any) => ({ ...p, nameAr: e.target.value }))} /></div>{showKey && <div><Label>Role key</Label><Input value={form.roleKey} onChange={e => setForm((p: any) => ({ ...p, roleKey: e.target.value }))} placeholder="senior_sales_agent" /></div>}{showParent && <div><Label>{isRTL ? "يرث الصلاحيات من" : "Inherits permissions from"}</Label><Select value={form.parentRoleId || "none"} onValueChange={value => setForm((p: any) => ({ ...p, parentRoleId: value }))}><SelectTrigger className="mt-1"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="none">{isRTL ? "بدون دور أب" : "No parent role"}</SelectItem>{parentOptions.map((role: any) => <SelectItem key={role.id} value={String(role.id)}>{isRTL && role.nameAr ? role.nameAr : role.name}</SelectItem>)}</SelectContent></Select><p className="text-xs text-muted-foreground mt-1">{isRTL ? "صلاحيات الدور الحالي تتغلب على الصلاحيات الموروثة." : "Direct permissions on this role override inherited permissions."}</p></div>}<div><Label>{isRTL ? "الوصف" : "Description"}</Label><Textarea value={form.description} onChange={e => setForm((p: any) => ({ ...p, description: e.target.value }))} /></div></div><DialogFooter><Button variant="outline" onClick={() => onOpenChange(false)}>{isRTL ? "إلغاء" : "Cancel"}</Button><Button onClick={onSubmit} disabled={busy || !form.name.trim()}>{isRTL ? "حفظ" : "Save"}</Button></DialogFooter></DialogContent></Dialog>;
}'''
    new_ui = replace_once(new_ui, old_role_dialog, new_role_dialog, "UI parent role selector")

if new_admin == admin and new_router == router and new_engine == engine and new_ui == ui:
    print("Phase 4C already applied; no changes needed.")
    raise SystemExit(0)

admin_path.write_text(new_admin)
router_path.write_text(new_router)
engine_path.write_text(new_engine)
ui_path.write_text(new_ui)

print("Phase 4C Role Inheritance V1 applied.")
for path in paths:
    print(f"Modified: {path.relative_to(root)}")
