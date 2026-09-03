import CRMLayout from "@/components/CRMLayout";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { useLanguage } from "@/contexts/LanguageContext";
import { trpc } from "@/lib/trpc";
import { CheckCircle2, Copy, Plus, Save, Search, Shield, Trash2, Users } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

type EffectState = "inherit" | "allow" | "deny";
type PermissionDraft = { effect: EffectState; dataScope: string; scopeConfig?: Record<string, unknown> | null };

const MODULE_LABELS: Record<string, { ar: string; en: string }> = {
  dashboard: { ar: "لوحة التحكم", en: "Dashboard" }, leads: { ar: "العملاء المحتملون", en: "Leads" },
  deals: { ar: "الصفقات", en: "Deals" }, clients: { ar: "العملاء", en: "Clients" }, activities: { ar: "الأنشطة", en: "Activities" },
  tasks: { ar: "المهام", en: "Tasks" }, meetings: { ar: "الاجتماعات", en: "Meetings" }, contracts: { ar: "العقود", en: "Contracts" },
  campaigns: { ar: "الحملات", en: "Campaigns" }, whatsapp: { ar: "واتساب", en: "WhatsApp" }, messenger: { ar: "الماسنجر", en: "Messenger" },
  files: { ar: "الملفات", en: "Files" }, reports: { ar: "التقارير", en: "Reports" }, users: { ar: "المستخدمون", en: "Users" },
  roles: { ar: "الأدوار والصلاحيات", en: "Roles & Permissions" }, settings: { ar: "الإعدادات", en: "Settings" }, integrations: { ar: "التكاملات", en: "Integrations" },
  notifications: { ar: "الإشعارات", en: "Notifications" }, backup: { ar: "النسخ الاحتياطي", en: "Backup" }, audit: { ar: "سجل العمليات", en: "Audit" },
  developer: { ar: "أدوات المطور", en: "Developer" },
};
const ACTION_LABELS: Record<string, { ar: string; en: string }> = {
  view: { ar: "عرض", en: "View" }, create: { ar: "إنشاء", en: "Create" }, edit: { ar: "تعديل", en: "Edit" }, delete: { ar: "حذف", en: "Delete" },
  restore: { ar: "استعادة", en: "Restore" }, assign: { ar: "إسناد", en: "Assign" }, reassign: { ar: "إعادة إسناد", en: "Reassign" }, export: { ar: "تصدير", en: "Export" },
  import: { ar: "استيراد", en: "Import" }, send: { ar: "إرسال", en: "Send" }, manage: { ar: "إدارة", en: "Manage" }, upload: { ar: "رفع", en: "Upload" },
  share: { ar: "مشاركة", en: "Share" }, assign_roles: { ar: "إسناد أدوار", en: "Assign roles" }, assign_permissions: { ar: "إسناد صلاحيات", en: "Assign permissions" }, run: { ar: "تشغيل", en: "Run" },
};
const SCOPE_LABELS: Record<string, { ar: string; en: string }> = {
  all: { ar: "كل البيانات", en: "All data" }, team: { ar: "الفريق", en: "Team" }, department: { ar: "القسم", en: "Department" }, own: { ar: "بياناته فقط", en: "Own" },
  assigned: { ar: "المسند له", en: "Assigned" }, created_by: { ar: "التي أنشأها", en: "Created by" }, custom: { ar: "مخصص", en: "Custom" }, none: { ar: "بدون نطاق", en: "None" },
};

export default function RolesPermissions() {
  const { isRTL } = useLanguage();
  const [selectedRoleId, setSelectedRoleId] = useState<number | null>(null);
  const [search, setSearch] = useState("");
  const [moduleFilter, setModuleFilter] = useState("all");
  const [draft, setDraft] = useState<Record<string, PermissionDraft>>({});
  const [createOpen, setCreateOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [copyOpen, setCopyOpen] = useState(false);
  const [form, setForm] = useState({ roleKey: "", name: "", nameAr: "", description: "" });

  const rolesQuery = trpc.permissionsAdmin.listRoles.useQuery();
  const catalogQuery = trpc.permissionsAdmin.catalog.useQuery();
  const roleQuery = trpc.permissionsAdmin.getRole.useQuery({ roleId: selectedRoleId || 1 }, { enabled: !!selectedRoleId });

  useEffect(() => {
    if (!selectedRoleId && rolesQuery.data?.length) setSelectedRoleId(Number(rolesQuery.data[0].id));
  }, [rolesQuery.data, selectedRoleId]);

  useEffect(() => {
    if (!roleQuery.data) return;
    const next: Record<string, PermissionDraft> = {};
    for (const item of roleQuery.data.permissions || []) {
      next[String(item.permissionKey)] = {
        effect: String(item.effect) === "deny" ? "deny" : "allow",
        dataScope: String(item.dataScope || "all"),
        scopeConfig: item.scopeConfig ?? null,
      };
    }
    setDraft(next);
  }, [roleQuery.data]);

  const invalidate = async (roleId?: number) => {
    await Promise.all([rolesQuery.refetch(), catalogQuery.refetch()]);
    if (roleId && selectedRoleId === roleId) await roleQuery.refetch();
  };

  const createMutation = trpc.permissionsAdmin.createRole.useMutation({
    onSuccess: async (role) => { toast.success(isRTL ? "تم إنشاء الدور" : "Role created"); setCreateOpen(false); setSelectedRoleId(Number(role.id)); await invalidate(); },
    onError: e => toast.error(e.message),
  });
  const updateMutation = trpc.permissionsAdmin.updateRole.useMutation({
    onSuccess: async () => { toast.success(isRTL ? "تم تحديث الدور" : "Role updated"); setEditOpen(false); await invalidate(selectedRoleId || undefined); },
    onError: e => toast.error(e.message),
  });
  const saveMutation = trpc.permissionsAdmin.replacePermissions.useMutation({
    onSuccess: async () => { toast.success(isRTL ? "تم حفظ الصلاحيات" : "Permissions saved"); await invalidate(selectedRoleId || undefined); },
    onError: e => toast.error(e.message),
  });
  const activeMutation = trpc.permissionsAdmin.setActive.useMutation({
    onSuccess: async () => { toast.success(isRTL ? "تم تحديث حالة الدور" : "Role status updated"); await invalidate(selectedRoleId || undefined); },
    onError: e => toast.error(e.message),
  });
  const deleteMutation = trpc.permissionsAdmin.deleteRole.useMutation({
    onSuccess: async () => { toast.success(isRTL ? "تم حذف الدور" : "Role deleted"); setSelectedRoleId(null); await invalidate(); },
    onError: e => toast.error(e.message),
  });
  const duplicateMutation = trpc.permissionsAdmin.duplicateRole.useMutation({
    onSuccess: async (role) => { toast.success(isRTL ? "تم نسخ الدور" : "Role duplicated"); setCopyOpen(false); setSelectedRoleId(Number(role.id)); await invalidate(); },
    onError: e => toast.error(e.message),
  });

  const catalog = catalogQuery.data?.permissions || [];
  const modules = useMemo(() => Array.from(new Set(catalog.map((p: any) => String(p.moduleKey)))), [catalog]);
  const filtered = useMemo(() => catalog.filter((p: any) => {
    const matchesModule = moduleFilter === "all" || String(p.moduleKey) === moduleFilter;
    const q = search.trim().toLowerCase();
    const matchesSearch = !q || String(p.permissionKey).toLowerCase().includes(q) || String(p.moduleKey).toLowerCase().includes(q) || String(p.actionKey).toLowerCase().includes(q);
    return matchesModule && matchesSearch;
  }), [catalog, moduleFilter, search]);
  const grouped = useMemo(() => filtered.reduce((acc: Record<string, any[]>, p: any) => {
    (acc[String(p.moduleKey)] ||= []).push(p); return acc;
  }, {}), [filtered]);

  const setPermission = (key: string, patch: Partial<PermissionDraft>) => setDraft(prev => ({
    ...prev,
    [key]: { effect: prev[key]?.effect || "inherit", dataScope: prev[key]?.dataScope || "all", ...prev[key], ...patch },
  }));
  const bulk = (mode: "clear" | "view" | "full") => {
    const next: Record<string, PermissionDraft> = {};
    for (const p of catalog as any[]) {
      if (mode === "full" || (mode === "view" && String(p.actionKey) === "view")) next[String(p.permissionKey)] = { effect: "allow", dataScope: "all" };
    }
    setDraft(next);
  };
  const save = () => {
    if (!selectedRoleId) return;
    const entries = Object.entries(draft).filter(([, v]) => v.effect !== "inherit").map(([permissionKey, v]) => ({
      permissionKey, effect: v.effect as "allow" | "deny", dataScope: (v.effect === "deny" ? "none" : v.dataScope) as any, scopeConfig: v.scopeConfig ?? null,
    }));
    saveMutation.mutate({ roleId: selectedRoleId, entries });
  };
  const selectedRole: any = roleQuery.data;

  if (rolesQuery.error || catalogQuery.error) {
    return <CRMLayout><div className="p-6"><Card><CardContent className="p-8 text-center text-destructive">{rolesQuery.error?.message || catalogQuery.error?.message}</CardContent></Card></div></CRMLayout>;
  }

  return (
    <CRMLayout title={isRTL ? "الأدوار والصلاحيات" : "Roles & Permissions"}>
      <div className="p-4 md:p-6 space-y-5" dir={isRTL ? "rtl" : "ltr"}>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div><h1 className="text-2xl font-bold flex items-center gap-2"><Shield className="h-6 w-6" />{isRTL ? "الأدوار والصلاحيات" : "Roles & Permissions"}</h1><p className="text-sm text-muted-foreground mt-1">{isRTL ? "تحكم مركزي في الأدوار، الإجراءات ونطاق البيانات. تطبيق نطاق البيانات على الاستعلامات سيتم في Phase 3." : "Central role, action and data-scope control. Query-scope enforcement comes in Phase 3."}</p></div>
          <Button onClick={() => { setForm({ roleKey: "", name: "", nameAr: "", description: "" }); setCreateOpen(true); }}><Plus className="h-4 w-4 me-2" />{isRTL ? "دور جديد" : "New role"}</Button>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-[300px_minmax(0,1fr)] gap-5">
          <Card className="h-fit xl:sticky xl:top-4"><CardHeader className="pb-3"><CardTitle className="text-base flex items-center gap-2"><Users className="h-4 w-4" />{isRTL ? "الأدوار" : "Roles"}</CardTitle></CardHeader><CardContent className="space-y-2 max-h-[72vh] overflow-auto">
            {(rolesQuery.data || []).map((r: any) => <button key={r.id} onClick={() => setSelectedRoleId(Number(r.id))} className={`w-full rounded-lg border p-3 text-start transition ${selectedRoleId === Number(r.id) ? "border-primary bg-primary/5" : "hover:bg-muted/40"}`}>
              <div className="flex items-center justify-between gap-2"><span className="font-medium truncate">{isRTL && r.nameAr ? r.nameAr : r.name}</span>{Number(r.isSystem) === 1 && <Badge variant="secondary">System</Badge>}</div>
              <div className="mt-2 flex gap-2 text-xs text-muted-foreground"><span>{Number(r.permissionCount || 0)} {isRTL ? "صلاحية" : "permissions"}</span><span>•</span><span>{Number(r.userCount || 0)} {isRTL ? "مستخدم" : "users"}</span></div>
            </button>)}
          </CardContent></Card>

          <div className="space-y-4">
            {!selectedRole ? <Card><CardContent className="p-10 text-center text-muted-foreground">{isRTL ? "اختر دورًا لعرض صلاحياته" : "Select a role to manage permissions"}</CardContent></Card> : <>
              <Card><CardContent className="p-4 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                <div><div className="flex items-center gap-2"><h2 className="font-semibold text-lg">{isRTL && selectedRole.nameAr ? selectedRole.nameAr : selectedRole.name}</h2><Badge variant={Number(selectedRole.isActive) === 1 ? "default" : "secondary"}>{Number(selectedRole.isActive) === 1 ? (isRTL ? "نشط" : "Active") : (isRTL ? "متوقف" : "Inactive")}</Badge></div><p className="text-xs text-muted-foreground mt-1 font-mono">{selectedRole.roleKey}</p></div>
                <div className="flex flex-wrap items-center gap-2"><Button variant="outline" size="sm" onClick={() => { setForm({ roleKey: selectedRole.roleKey, name: selectedRole.name || "", nameAr: selectedRole.nameAr || "", description: selectedRole.description || "" }); setEditOpen(true); }}>{isRTL ? "تعديل البيانات" : "Edit details"}</Button><Button variant="outline" size="sm" onClick={() => { setForm({ roleKey: "", name: `${selectedRole.name} Copy`, nameAr: selectedRole.nameAr ? `${selectedRole.nameAr} - نسخة` : "", description: "" }); setCopyOpen(true); }}><Copy className="h-4 w-4 me-1" />{isRTL ? "نسخ الدور" : "Duplicate"}</Button>{Number(selectedRole.isSystem) !== 1 && <><div className="flex items-center gap-2 px-2"><Switch checked={Number(selectedRole.isActive) === 1} onCheckedChange={v => activeMutation.mutate({ roleId: Number(selectedRole.id), isActive: v })} /><span className="text-xs">{isRTL ? "نشط" : "Active"}</span></div><Button variant="destructive" size="sm" onClick={() => window.confirm(isRTL ? "حذف هذا الدور؟" : "Delete this role?") && deleteMutation.mutate({ roleId: Number(selectedRole.id) })}><Trash2 className="h-4 w-4" /></Button></>}</div>
              </CardContent></Card>

              <Card><CardHeader className="pb-3"><div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3"><CardTitle className="text-base">{isRTL ? "مصفوفة الصلاحيات" : "Permission Matrix"}</CardTitle><div className="flex flex-wrap gap-2"><Button variant="outline" size="sm" onClick={() => bulk("clear")}>{isRTL ? "مسح الكل" : "Clear all"}</Button><Button variant="outline" size="sm" onClick={() => bulk("view")}>{isRTL ? "عرض فقط" : "View only"}</Button><Button variant="outline" size="sm" onClick={() => bulk("full")}>{isRTL ? "صلاحية كاملة" : "Full access"}</Button><Button size="sm" onClick={save} disabled={saveMutation.isPending}><Save className="h-4 w-4 me-1" />{isRTL ? "حفظ" : "Save"}</Button></div></div></CardHeader><CardContent>
                <div className="grid md:grid-cols-[1fr_220px] gap-3 mb-4"><div className="relative"><Search className="absolute start-3 top-2.5 h-4 w-4 text-muted-foreground" /><Input className="ps-9" value={search} onChange={e => setSearch(e.target.value)} placeholder={isRTL ? "بحث في الصلاحيات..." : "Search permissions..."} /></div><Select value={moduleFilter} onValueChange={setModuleFilter}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="all">{isRTL ? "كل الأقسام" : "All modules"}</SelectItem>{modules.map(m => <SelectItem key={m} value={m}>{MODULE_LABELS[m]?.[isRTL ? "ar" : "en"] || m}</SelectItem>)}</SelectContent></Select></div>
                <div className="space-y-5">{Object.entries(grouped).map(([moduleKey, items]) => <div key={moduleKey} className="border rounded-xl overflow-hidden"><div className="px-4 py-3 bg-muted/40 font-semibold">{MODULE_LABELS[moduleKey]?.[isRTL ? "ar" : "en"] || moduleKey}<span className="ms-2 text-xs font-normal text-muted-foreground">{items.length}</span></div><div className="divide-y">{items.map((p: any) => { const state = draft[String(p.permissionKey)] || { effect: "inherit", dataScope: "all" }; return <div key={p.permissionKey} className="grid grid-cols-1 md:grid-cols-[minmax(180px,1fr)_170px_190px] gap-3 p-3 items-center"><div><div className="font-medium text-sm">{ACTION_LABELS[String(p.actionKey)]?.[isRTL ? "ar" : "en"] || p.actionKey}</div><code className="text-[11px] text-muted-foreground">{p.permissionKey}</code></div><Select value={state.effect} onValueChange={(v: EffectState) => setPermission(String(p.permissionKey), { effect: v, dataScope: v === "deny" ? "none" : (state.dataScope === "none" ? "all" : state.dataScope) })}><SelectTrigger className={state.effect === "allow" ? "border-emerald-500/50" : state.effect === "deny" ? "border-destructive/50" : ""}><SelectValue /></SelectTrigger><SelectContent><SelectItem value="inherit">{isRTL ? "بدون تعيين" : "Not assigned"}</SelectItem><SelectItem value="allow">{isRTL ? "سماح" : "Allow"}</SelectItem><SelectItem value="deny">{isRTL ? "منع صريح" : "Explicit deny"}</SelectItem></SelectContent></Select><Select disabled={state.effect !== "allow"} value={state.effect === "allow" ? state.dataScope : "none"} onValueChange={v => setPermission(String(p.permissionKey), { dataScope: v })}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{(catalogQuery.data?.scopes || []).map((s: string) => <SelectItem key={s} value={s}>{SCOPE_LABELS[s]?.[isRTL ? "ar" : "en"] || s}</SelectItem>)}</SelectContent></Select></div>; })}</div></div>)}</div>
                <div className="mt-4 flex items-start gap-2 rounded-lg bg-muted/40 p-3 text-xs text-muted-foreground"><CheckCircle2 className="h-4 w-4 shrink-0 mt-0.5" /><span>{isRTL ? "الحفظ هنا يغيّر role_permissions فقط. نطاق البيانات يتم تخزينه وحسابه، لكن فلترة Leads/Deals/Clients حسب النطاق لن تُفعّل قبل Phase 3." : "Saving here changes role_permissions only. Scopes are stored and evaluated, but Leads/Deals/Clients query filtering is intentionally deferred to Phase 3."}</span></div>
              </CardContent></Card>
            </>}
          </div>
        </div>
      </div>

      <RoleDialog open={createOpen} onOpenChange={setCreateOpen} title={isRTL ? "إنشاء دور جديد" : "Create role"} form={form} setForm={setForm} isRTL={isRTL} showKey onSubmit={() => createMutation.mutate({ roleKey: form.roleKey || undefined, name: form.name, nameAr: form.nameAr || null, description: form.description || null })} busy={createMutation.isPending} />
      <RoleDialog open={editOpen} onOpenChange={setEditOpen} title={isRTL ? "تعديل الدور" : "Edit role"} form={form} setForm={setForm} isRTL={isRTL} onSubmit={() => selectedRoleId && updateMutation.mutate({ roleId: selectedRoleId, name: form.name, nameAr: form.nameAr || null, description: form.description || null })} busy={updateMutation.isPending} />
      <RoleDialog open={copyOpen} onOpenChange={setCopyOpen} title={isRTL ? "نسخ الدور" : "Duplicate role"} form={form} setForm={setForm} isRTL={isRTL} showKey onSubmit={() => selectedRoleId && duplicateMutation.mutate({ sourceRoleId: selectedRoleId, roleKey: form.roleKey || undefined, name: form.name, nameAr: form.nameAr || null })} busy={duplicateMutation.isPending} />
    </CRMLayout>
  );
}

function RoleDialog({ open, onOpenChange, title, form, setForm, isRTL, showKey = false, onSubmit, busy }: any) {
  return <Dialog open={open} onOpenChange={onOpenChange}><DialogContent dir={isRTL ? "rtl" : "ltr"}><DialogHeader><DialogTitle>{title}</DialogTitle></DialogHeader><div className="space-y-4"><div><Label>{isRTL ? "الاسم" : "Name"}</Label><Input value={form.name} onChange={e => setForm((p: any) => ({ ...p, name: e.target.value }))} /></div><div><Label>{isRTL ? "الاسم بالعربية" : "Arabic name"}</Label><Input value={form.nameAr} onChange={e => setForm((p: any) => ({ ...p, nameAr: e.target.value }))} /></div>{showKey && <div><Label>Role key</Label><Input value={form.roleKey} onChange={e => setForm((p: any) => ({ ...p, roleKey: e.target.value }))} placeholder="senior_sales_agent" /></div>}<div><Label>{isRTL ? "الوصف" : "Description"}</Label><Textarea value={form.description} onChange={e => setForm((p: any) => ({ ...p, description: e.target.value }))} /></div></div><DialogFooter><Button variant="outline" onClick={() => onOpenChange(false)}>{isRTL ? "إلغاء" : "Cancel"}</Button><Button onClick={onSubmit} disabled={busy || !form.name.trim()}>{isRTL ? "حفظ" : "Save"}</Button></DialogFooter></DialogContent></Dialog>;
}
