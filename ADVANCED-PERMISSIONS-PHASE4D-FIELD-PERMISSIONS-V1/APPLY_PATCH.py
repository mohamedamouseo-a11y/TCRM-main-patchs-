#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

EXPECTED_HEAD = "3e0aa9de85e55253dba928b5dedf96098286bec8"
ENGINE_MARKER = "ADVANCED_PERMISSIONS_PHASE4D_FIELD_POLICY_ENGINE"
ROUTER_MARKER = "ADVANCED_PERMISSIONS_PHASE4D_FIELD_POLICY_ROUTER"
UI_MARKER = "ADVANCED_PERMISSIONS_PHASE4D_FIELD_POLICY_UI"

root = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TCRM-MAIN").resolve()
engine_path = root / "server/security/permissionEngine.ts"
routers_path = root / "server/routers.ts"
ui_path = root / "client/src/pages/RolesPermissions.tsx"
paths = (engine_path, routers_path, ui_path)

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


engine = engine_path.read_text()
routers = routers_path.read_text()
ui = ui_path.read_text()
new_engine, new_routers, new_ui = engine, routers, ui

if ENGINE_MARKER not in engine:
    new_engine = replace_once(new_engine, '''export type PermissionDecision = {
  allowed: boolean;
  permission: string;
  scope: PermissionScope;
  source: "super_admin" | "user_deny" | "user_allow" | "role" | "legacy_role" | "none";
  roleIds?: number[];
};''', '''export type PermissionFieldPolicy = {
  allow: string[] | null;
  deny: string[];
  configured: boolean;
};

export type PermissionDecision = {
  allowed: boolean;
  permission: string;
  scope: PermissionScope;
  source: "super_admin" | "user_deny" | "user_allow" | "role" | "legacy_role" | "none";
  roleIds?: number[];
  fieldPolicy?: PermissionFieldPolicy;
};''', "permission decision field policy type")

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

// ADVANCED_PERMISSIONS_PHASE4D_FIELD_POLICY_ENGINE
function parseScopeConfig(value: unknown): Record<string, any> | null {
  if (!value) return null;
  if (typeof value === "string") {
    try {
      const parsed = JSON.parse(value);
      return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : null;
    } catch {
      return null;
    }
  }
  return typeof value === "object" && !Array.isArray(value) ? value as Record<string, any> : null;
}

function normalizeFieldList(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return Array.from(new Set(value
    .map(item => String(item ?? "").trim())
    .filter(item => item.length > 0 && item.length <= 120)));
}

export function resolvePermissionFieldPolicy(scopeConfig: unknown): PermissionFieldPolicy | undefined {
  const config = parseScopeConfig(scopeConfig);
  const fields = config?.fields;
  if (!fields || typeof fields !== "object" || Array.isArray(fields)) return undefined;
  const hasAllow = Object.prototype.hasOwnProperty.call(fields, "allow") && Array.isArray((fields as any).allow);
  const hasDeny = Object.prototype.hasOwnProperty.call(fields, "deny") && Array.isArray((fields as any).deny);
  if (!hasAllow && !hasDeny) return undefined;
  return {
    allow: hasAllow ? normalizeFieldList((fields as any).allow) : null,
    deny: hasDeny ? normalizeFieldList((fields as any).deny) : [],
    configured: true,
  };
}

function mergePermissionFieldPolicies(scopeConfigs: unknown[]): PermissionFieldPolicy | undefined {
  const resolved = scopeConfigs.map(resolvePermissionFieldPolicy);
  const configured = resolved.filter((item): item is PermissionFieldPolicy => !!item?.configured);
  if (!configured.length) return undefined;

  // Multiple role grants remain additive. A grant without an allow-list keeps the
  // allow side unrestricted, while explicit denied fields remain denied across grants.
  const unrestrictedAllow = resolved.some(item => !item || item.allow === null);
  const allow = unrestrictedAllow
    ? null
    : Array.from(new Set(configured.flatMap(item => item.allow ?? [])));
  const deny = Array.from(new Set(configured.flatMap(item => item.deny)));
  return { allow, deny, configured: true };
}

export function isPermissionFieldAllowed(policy: PermissionFieldPolicy | undefined, field: string): boolean {
  if (!policy?.configured) return true;
  if (policy.deny.includes(field)) return false;
  if (policy.allow !== null && !policy.allow.includes(field)) return false;
  return true;
}

export function filterPermissionFields<T>(
  record: T,
  decision?: PermissionDecision | null,
  preserveFields: string[] = [],
): T {
  if (!record || typeof record !== "object" || Array.isArray(record) || !decision?.fieldPolicy?.configured) return record;
  const preserve = new Set(preserveFields);
  const output: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(record as Record<string, unknown>)) {
    if (preserve.has(key) || isPermissionFieldAllowed(decision.fieldPolicy, key)) output[key] = value;
  }
  return output as T;
}

export function filterPermissionFieldRows<T>(
  records: T[],
  decision?: PermissionDecision | null,
  preserveFields: string[] = [],
): T[] {
  if (!Array.isArray(records)) return records;
  return records.map(record => filterPermissionFields(record, decision, preserveFields));
}

export function getDeniedPermissionWriteFields(
  input: Record<string, unknown>,
  decision?: PermissionDecision | null,
  ignoredFields: string[] = [],
): string[] {
  if (!decision?.fieldPolicy?.configured || !input || typeof input !== "object") return [];
  const ignored = new Set(ignoredFields);
  return Object.keys(input).filter(key =>
    !ignored.has(key) &&
    input[key] !== undefined &&
    !isPermissionFieldAllowed(decision.fieldPolicy, key),
  );
}
''', "field policy helpers")

    new_engine = replace_once(new_engine, '''    SELECT upo.effect, upo.data_scope AS dataScope
    FROM user_permission_overrides upo''', '''    SELECT upo.effect, upo.data_scope AS dataScope, upo.scope_config AS scopeConfig
    FROM user_permission_overrides upo''', "user override scope config selection")

    new_engine = replace_once(new_engine, '''    return {
      allowed: true,
      permission,
      scope: strongestScope(allows.map((r: any) => String(r.dataScope || "all") as PermissionScope)),
      source: "user_allow",
    };''', '''    return {
      allowed: true,
      permission,
      scope: strongestScope(allows.map((r: any) => String(r.dataScope || "all") as PermissionScope)),
      source: "user_allow",
      fieldPolicy: mergePermissionFieldPolicies(allows.map((r: any) => r.scopeConfig)),
    };''', "user allow field policy")

    new_engine = replace_once(new_engine, '''           rp.effect, rp.data_scope AS dataScope,
           EXISTS(''', '''           rp.effect, rp.data_scope AS dataScope, rp.scope_config AS scopeConfig,
           EXISTS(''', "role scope config selection")

    new_engine = replace_once(new_engine, '''    return {
      allowed: true,
      permission,
      scope: strongestScope(roleAllows.map((r: any) => String(r.dataScope || "all") as PermissionScope)),
      source: "role",
      roleIds: Array.from(new Set(roleAllows.map((r: any) => Number(r.roleId)))),
    };''', '''    return {
      allowed: true,
      permission,
      scope: strongestScope(roleAllows.map((r: any) => String(r.dataScope || "all") as PermissionScope)),
      source: "role",
      roleIds: Array.from(new Set(roleAllows.map((r: any) => Number(r.roleId)))),
      fieldPolicy: mergePermissionFieldPolicies(roleAllows.map((r: any) => r.scopeConfig)),
    };''', "dynamic role field policy")

    new_engine = replace_once(new_engine, '''      return {
        allowed: true,
        permission,
        scope: strongestScope(legacyAllows.map((r: any) => String(r.dataScope || "all") as PermissionScope)),
        source: "legacy_role",
        roleIds: Array.from(new Set(legacyAllows.map((r: any) => Number(r.roleId)))),
      };''', '''      return {
        allowed: true,
        permission,
        scope: strongestScope(legacyAllows.map((r: any) => String(r.dataScope || "all") as PermissionScope)),
        source: "legacy_role",
        roleIds: Array.from(new Set(legacyAllows.map((r: any) => Number(r.roleId)))),
        fieldPolicy: mergePermissionFieldPolicies(legacyAllows.map((r: any) => r.scopeConfig)),
      };''', "legacy role field policy")

if ROUTER_MARKER not in routers:
    new_routers = replace_once(new_routers, '''import { isRowInScope, assertRowScope, buildLeadScopeCondition, buildDealScopeCondition, buildClientScopeCondition } from "./security/phase3ScopeFilters";
import { assertLeadPermissionScope, assertClientPermissionScope, assertActivityPermissionScope, assertTaskPermissionScope, filterTasksByPermissionScope, assertTaskCreatePermissionScope, assertContractPermissionScope, filterContractsByPermissionScope, assertContractCreatePermissionScope } from "./security/phase3bScope";''', '''import { isRowInScope, assertRowScope, buildLeadScopeCondition, buildDealScopeCondition, buildClientScopeCondition } from "./security/phase3ScopeFilters";
import { assertLeadPermissionScope, assertClientPermissionScope, assertActivityPermissionScope, assertTaskPermissionScope, filterTasksByPermissionScope, assertTaskCreatePermissionScope, assertContractPermissionScope, filterContractsByPermissionScope, assertContractCreatePermissionScope } from "./security/phase3bScope";
import { evaluatePermission, filterPermissionFields, filterPermissionFieldRows, getDeniedPermissionWriteFields } from "./security/permissionEngine";

// ADVANCED_PERMISSIONS_PHASE4D_FIELD_POLICY_ROUTER
function assertPermissionFieldWrite(
  decision: any,
  data: Record<string, unknown>,
  entityLabel: string,
  ignoredFields: string[] = [],
) {
  const deniedFields = getDeniedPermissionWriteFields(data, decision, ignoredFields);
  if (deniedFields.length) {
    throw new TRPCError({
      code: "FORBIDDEN",
      message: `Field permission denied for ${entityLabel}: ${deniedFields.join(", ")}`,
    });
  }
}
''', "router field policy import and helper")

    new_routers = replace_once(new_routers, '''        const [items, total] = await Promise.all([
          getLeads(filters),
          getLeadsCount(filters),
        ]);
        return { items, total };''', '''        const [items, total] = await Promise.all([
          getLeads(filters),
          getLeadsCount(filters),
        ]);
        return {
          items: filterPermissionFieldRows(items as any[], (ctx as any).permissionDecision, ["id"]),
          total,
        };''', "leads list read fields")

    new_routers = replace_once(new_routers, '''        if (ctx.user.role === "ServiceAdvisor") {
          const serviceRows = await listAutomotiveServiceBookings({ leadId: input.id, assignedTo: ctx.user.id, limit: 1 });
          if (!serviceRows.length) throw new TRPCError({ code: "FORBIDDEN", message: "Access denied: this lead is outside your service queue" });
        }
        return lead;''', '''        if (ctx.user.role === "ServiceAdvisor") {
          const serviceRows = await listAutomotiveServiceBookings({ leadId: input.id, assignedTo: ctx.user.id, limit: 1 });
          if (!serviceRows.length) throw new TRPCError({ code: "FORBIDDEN", message: "Access denied: this lead is outside your service queue" });
        }
        return filterPermissionFields(lead, (ctx as any).permissionDecision, ["id"]);''', "lead byId read fields")

    new_routers = replace_once(new_routers, '''      )
      .mutation(async ({ ctx, input }) => {
        let ownerId = input.ownerId;

        // For manual lead creation''', '''      )
      .mutation(async ({ ctx, input }) => {
        assertPermissionFieldWrite((ctx as any).permissionDecision, input as any, "lead");
        let ownerId = input.ownerId;

        // For manual lead creation''', "lead create write fields")

    new_routers = replace_once(new_routers, '''      )
      .mutation(async ({ ctx, input }) => {
        const { id, ...data } = input;
        // ── ROW-LEVEL SECURITY ──
        const existingLead = await getLeadById(id);''', '''      )
      .mutation(async ({ ctx, input }) => {
        const { id, ...data } = input;
        assertPermissionFieldWrite((ctx as any).permissionDecision, data as any, "lead");
        // ── ROW-LEVEL SECURITY ──
        const existingLead = await getLeadById(id);''', "lead update write fields")

    new_routers = replace_once(new_routers, '''        const scopeSql = (ctx as any).permissionDecision
          ? buildLeadScopeCondition((ctx as any).permissionDecision.scope, ctx.user as any, "l.ownerId")
          : undefined;
        return getLeadsForExport({ ...input.filters ?? {}, permissionScopeSql: scopeSql });''', '''        const scopeSql = (ctx as any).permissionDecision
          ? buildLeadScopeCondition((ctx as any).permissionDecision.scope, ctx.user as any, "l.ownerId")
          : undefined;
        const rows = await getLeadsForExport({ ...input.filters ?? {}, permissionScopeSql: scopeSql });
        const viewDecision = await evaluatePermission(ctx.user as any, "leads.view");
        const fieldDecision = viewDecision.allowed ? viewDecision : (ctx as any).permissionDecision;
        return filterPermissionFieldRows(rows as any[], fieldDecision, ["id"]);''', "lead export read fields")

    new_routers = replace_once(new_routers, '''        const dealLead = await getLeadById(input.leadId);
        if (dealLead) await assertRowScope("lead", (ctx as any).permissionDecision, ctx.user as any, dealLead, `Lead #${input.leadId} (deal access)`);
        return getDealByLead(input.leadId);''', '''        const dealLead = await getLeadById(input.leadId);
        if (dealLead) await assertRowScope("lead", (ctx as any).permissionDecision, ctx.user as any, dealLead, `Lead #${input.leadId} (deal access)`);
        const deal = await getDealByLead(input.leadId);
        return filterPermissionFields(deal, (ctx as any).permissionDecision, ["id", "leadId", "payments"]);''', "deal byLead read fields")

    new_routers = replace_once(new_routers, '''        const scopeSql = dealPermissionScopeSql(ctx);
        return getDealsScoped(scopeSql);''', '''        const scopeSql = dealPermissionScopeSql(ctx);
        const deals = await getDealsScoped(scopeSql);
        return filterPermissionFieldRows(deals as any[], (ctx as any).permissionDecision, ["id", "leadId"]);''', "deal byUser read fields")

    new_routers = replace_once(new_routers, '''      )
      .mutation(async ({ ctx, input }) => {
        // ── ROW-LEVEL SECURITY ──
        const dealLeadCreate = await getLeadById(input.leadId);''', '''      )
      .mutation(async ({ ctx, input }) => {
        assertPermissionFieldWrite((ctx as any).permissionDecision, input as any, "deal", ["leadId"]);
        // ── ROW-LEVEL SECURITY ──
        const dealLeadCreate = await getLeadById(input.leadId);''', "deal create write fields")

    new_routers = replace_once(new_routers, '''      )
      .mutation(async ({ ctx, input }) => {
        const { id, legacyPaymentAmount, legacyPaymentDate, legacyPaymentNotes, ...data } = input;
        const isFinancialEditor = ["Admin", "admin", "SalesManager"].includes(ctx.user.role);''', '''      )
      .mutation(async ({ ctx, input }) => {
        const { id, legacyPaymentAmount, legacyPaymentDate, legacyPaymentNotes, ...data } = input;
        assertPermissionFieldWrite((ctx as any).permissionDecision, data as any, "deal", ["leadId"]);
        const isFinancialEditor = ["Admin", "admin", "SalesManager"].includes(ctx.user.role);''', "deal update write fields")

    new_routers = replace_once(new_routers, '''        const role = normalizeUserRole(ctx.user.role);
        if (role === "SalesManager") {
          return { ...result, data: result.data.map((row: any) => toClientSummaryRecord(row)) };
        }
        if (role === "AccountManagerLead") {
          return {
            ...result,
            data: result.data.map((row: any) => row.accountManagerId == null ? toClientSummaryRecord(row) : row),
          };
        }
        return result;''', '''        const role = normalizeUserRole(ctx.user.role);
        if (role === "SalesManager") {
          return {
            ...result,
            data: filterPermissionFieldRows(result.data.map((row: any) => toClientSummaryRecord(row)), (ctx as any).permissionDecision, ["id", "leadId", "dealId"]),
          };
        }
        if (role === "AccountManagerLead") {
          return {
            ...result,
            data: filterPermissionFieldRows(result.data.map((row: any) => row.accountManagerId == null ? toClientSummaryRecord(row) : row), (ctx as any).permissionDecision, ["id", "leadId", "dealId"]),
          };
        }
        return {
          ...result,
          data: filterPermissionFieldRows(result.data as any[], (ctx as any).permissionDecision, ["id", "leadId", "dealId"]),
        };''', "client list read fields")

    new_routers = replace_once(new_routers, '''        if (normalizeUserRole(ctx.user.role) === "SalesManager") {
          const client = await getClientSummaryContext({ id: Number(ctx.user.id), role: normalizeUserRole(ctx.user.role), teamId: ctx.user.teamId }, input.id);
          if (client) await assertRowScope("client", (ctx as any).permissionDecision, ctx.user as any, client, `Client #${input.id}`);
          return client;
        }
        const client = await assertAccountManagementClientAccess(ctx, input.id, "client.read.full");
        if (client) await assertRowScope("client", (ctx as any).permissionDecision, ctx.user as any, client, `Client #${input.id}`);
        return client;''', '''        if (normalizeUserRole(ctx.user.role) === "SalesManager") {
          const client = await getClientSummaryContext({ id: Number(ctx.user.id), role: normalizeUserRole(ctx.user.role), teamId: ctx.user.teamId }, input.id);
          if (client) await assertRowScope("client", (ctx as any).permissionDecision, ctx.user as any, client, `Client #${input.id}`);
          return filterPermissionFields(client, (ctx as any).permissionDecision, ["id", "leadId", "dealId"]);
        }
        const client = await assertAccountManagementClientAccess(ctx, input.id, "client.read.full");
        if (client) await assertRowScope("client", (ctx as any).permissionDecision, ctx.user as any, client, `Client #${input.id}`);
        return filterPermissionFields(client, (ctx as any).permissionDecision, ["id", "leadId", "dealId"]);''', "client get read fields")

    new_routers = replace_once(new_routers, '''      }))
      .mutation(async ({ input, ctx }) => {
        const role = normalizeUserRole(ctx.user.role);
        const canCreateClient = isManagerRole(role) || role === "AccountManager" || role === "AccountManagerLead";''', '''      }))
      .mutation(async ({ input, ctx }) => {
        assertPermissionFieldWrite((ctx as any).permissionDecision, input as any, "client", ["clientRequestId", "leadId", "dealId"]);
        const role = normalizeUserRole(ctx.user.role);
        const canCreateClient = isManagerRole(role) || role === "AccountManager" || role === "AccountManagerLead";''', "client create write fields")

    new_routers = replace_once(new_routers, '''      }))
      .mutation(async ({ input, ctx }) => {
        const { id, ...data } = input;
        const role = normalizeUserRole(ctx.user.role);
        await assertAccountManagementClientAccess(ctx, id, "client.update");''', '''      }))
      .mutation(async ({ input, ctx }) => {
        const { id, ...data } = input;
        const clientEditDecision = await evaluatePermission(ctx.user as any, "clients.edit");
        if (clientEditDecision.allowed) assertPermissionFieldWrite(clientEditDecision, data as any, "client");
        const role = normalizeUserRole(ctx.user.role);
        await assertAccountManagementClientAccess(ctx, id, "client.update");''', "client update write fields")

    new_routers = replace_once(new_routers, '''      }))
      .mutation(async ({ input, ctx }) => {
        const role = normalizeUserRole(ctx.user.role);
        const accountManagerId = role === "AccountManager" ? Number(ctx.user.id) : (input.client.accountManagerId ?? null);''', '''      }))
      .mutation(async ({ input, ctx }) => {
        const clientCreateDecision = await evaluatePermission(ctx.user as any, "clients.create");
        if (clientCreateDecision.allowed) {
          assertPermissionFieldWrite(clientCreateDecision, input.client as any, "client", ["leadId", "dealId"]);
        }
        const role = normalizeUserRole(ctx.user.role);
        const accountManagerId = role === "AccountManager" ? Number(ctx.user.id) : (input.client.accountManagerId ?? null);''', "course subscription client create fields")

if UI_MARKER not in ui:
    new_ui = replace_once(new_ui, '''type EffectState = "inherit" | "allow" | "deny";
type PermissionDraft = { effect: EffectState; dataScope: string; scopeConfig?: Record<string, unknown> | null; startsAt?: string | null; expiresAt?: string | null; reason?: string | null };
''', '''type EffectState = "inherit" | "allow" | "deny";
type PermissionDraft = { effect: EffectState; dataScope: string; scopeConfig?: Record<string, unknown> | null; startsAt?: string | null; expiresAt?: string | null; reason?: string | null };
type FieldEditorTarget = "role" | "user";
type FieldEditorState = { target: FieldEditorTarget; permissionKey: string };
''', "field editor types")

    new_ui = replace_once(new_ui, '''const SCOPE_LABELS: Record<string, { ar: string; en: string }> = {
  all: { ar: "كل البيانات", en: "All data" }, team: { ar: "الفريق", en: "Team" }, department: { ar: "القسم", en: "Department" }, own: { ar: "بياناته فقط", en: "Own" },
  assigned: { ar: "المسند له", en: "Assigned" }, created_by: { ar: "التي أنشأها", en: "Created by" }, custom: { ar: "مخصص", en: "Custom" }, none: { ar: "بدون نطاق", en: "None" },
};
''', '''const SCOPE_LABELS: Record<string, { ar: string; en: string }> = {
  all: { ar: "كل البيانات", en: "All data" }, team: { ar: "الفريق", en: "Team" }, department: { ar: "القسم", en: "Department" }, own: { ar: "بياناته فقط", en: "Own" },
  assigned: { ar: "المسند له", en: "Assigned" }, created_by: { ar: "التي أنشأها", en: "Created by" }, custom: { ar: "مخصص", en: "Custom" }, none: { ar: "بدون نطاق", en: "None" },
};

// ADVANCED_PERMISSIONS_PHASE4D_FIELD_POLICY_UI
const FIELD_PERMISSION_KEYS = [
  "leads.view", "leads.create", "leads.edit",
  "clients.view", "clients.create", "clients.edit",
  "deals.view", "deals.create", "deals.edit",
] as const;

const FIELD_CATALOG: Record<string, Array<{ key: string; ar: string; en: string }>> = {
  leads: [
    { key: "name", ar: "الاسم", en: "Name" }, { key: "phone", ar: "الجوال", en: "Phone" },
    { key: "country", ar: "الدولة", en: "Country" }, { key: "businessProfile", ar: "ملف النشاط", en: "Business profile" },
    { key: "leadQuality", ar: "جودة الليد", en: "Lead quality" }, { key: "fitStatus", ar: "حالة الملاءمة", en: "Fit status" },
    { key: "campaignName", ar: "الحملة", en: "Campaign" }, { key: "adCreative", ar: "الإعلان", en: "Ad creative" },
    { key: "ownerId", ar: "المالك", en: "Owner" }, { key: "stage", ar: "المرحلة", en: "Stage" },
    { key: "notes", ar: "الملاحظات", en: "Notes" }, { key: "mediaBuyerNotes", ar: "ملاحظات الميديا باير", en: "Media buyer notes" },
    { key: "serviceIntroduced", ar: "الخدمة المقدمة", en: "Service introduced" }, { key: "priceOfferSent", ar: "إرسال العرض", en: "Price offer sent" },
    { key: "priceOfferLink", ar: "رابط العرض", en: "Price offer link" }, { key: "leadTime", ar: "وقت الليد", en: "Lead time" },
    { key: "contactTime", ar: "وقت التواصل", en: "Contact time" },
  ],
  clients: [
    { key: "businessProfile", ar: "ملف النشاط", en: "Business profile" }, { key: "group", ar: "المجموعة", en: "Group" },
    { key: "planStatus", ar: "حالة الخطة", en: "Plan status" }, { key: "renewalStatus", ar: "حالة التجديد", en: "Renewal status" },
    { key: "competentPerson", ar: "الشخص المسؤول", en: "Contact person" }, { key: "contactEmail", ar: "البريد", en: "Contact email" },
    { key: "contactPhone", ar: "هاتف التواصل", en: "Contact phone" }, { key: "leadName", ar: "اسم العميل", en: "Lead name" },
    { key: "phone", ar: "الجوال", en: "Phone" }, { key: "otherPhones", ar: "أرقام أخرى", en: "Other phones" },
    { key: "contractLink", ar: "رابط العقد", en: "Contract link" }, { key: "marketingObjective", ar: "الهدف التسويقي", en: "Marketing objective" },
    { key: "servicesNeeded", ar: "الخدمات المطلوبة", en: "Services needed" }, { key: "socialMedia", ar: "السوشيال ميديا", en: "Social media" },
    { key: "feedback", ar: "التقييم", en: "Feedback" }, { key: "notes", ar: "الملاحظات", en: "Notes" },
    { key: "sourceMarketerCode", ar: "كود المسوق", en: "Marketer code" }, { key: "crmTag", ar: "وسم CRM", en: "CRM tag" },
    { key: "registrationDate", ar: "تاريخ التسجيل", en: "Registration date" }, { key: "paymentStatus", ar: "حالة الدفع", en: "Payment status" },
    { key: "paidAmount", ar: "المبلغ المدفوع", en: "Paid amount" }, { key: "handoverStatus", ar: "حالة التسليم", en: "Handover status" },
    { key: "briefStatus", ar: "حالة البريف", en: "Brief status" }, { key: "accountManagerId", ar: "مدير الحساب", en: "Account manager" },
  ],
  deals: [
    { key: "valueSar", ar: "قيمة الصفقة", en: "Deal value" }, { key: "currency", ar: "العملة", en: "Currency" },
    { key: "paidAmount", ar: "المدفوع", en: "Paid amount" }, { key: "installmentCount", ar: "عدد الدفعات", en: "Installments" },
    { key: "status", ar: "الحالة", en: "Status" }, { key: "closedAt", ar: "تاريخ الإغلاق", en: "Closed at" },
    { key: "dealType", ar: "نوع الصفقة", en: "Deal type" }, { key: "lossReason", ar: "سبب الخسارة", en: "Loss reason" },
    { key: "notes", ar: "الملاحظات", en: "Notes" }, { key: "servicesNeeded", ar: "الخدمات", en: "Services needed" },
    { key: "dealDuration", ar: "مدة الصفقة", en: "Deal duration" },
  ],
};

function normalizeScopeConfig(value: unknown): Record<string, any> | null {
  if (!value) return null;
  if (typeof value === "string") {
    try {
      const parsed = JSON.parse(value);
      return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : null;
    } catch { return null; }
  }
  return typeof value === "object" && !Array.isArray(value) ? value as Record<string, any> : null;
}
''', "field policy UI catalog")

    new_ui = replace_once(new_ui, '''  const [testerUserId, setTesterUserId] = useState<number | null>(null);
  const [testerSearch, setTesterSearch] = useState("");
  const [testerPermissionKey, setTesterPermissionKey] = useState("all");''', '''  const [testerUserId, setTesterUserId] = useState<number | null>(null);
  const [testerSearch, setTesterSearch] = useState("");
  const [testerPermissionKey, setTesterPermissionKey] = useState("all");
  const [fieldEditor, setFieldEditor] = useState<FieldEditorState | null>(null);''', "field editor state")

    new_ui = new_ui.replace('scopeConfig: item.scopeConfig ?? null,', 'scopeConfig: normalizeScopeConfig(item.scopeConfig),')
    if new_ui.count('scopeConfig: normalizeScopeConfig(item.scopeConfig),') != 2:
        raise SystemExit("Expected exactly two scopeConfig hydration replacements. No files changed.")

    new_ui = replace_once(new_ui, '''  const bulk = (mode: "clear" | "view" | "full") => {
    const next: Record<string, PermissionDraft> = {};
    for (const p of catalog as any[]) {
      if (mode === "full" || (mode === "view" && String(p.actionKey) === "view")) next[String(p.permissionKey)] = { effect: "allow", dataScope: "all" };
    }
    setDraft(next);
  };''', '''  const bulk = (mode: "clear" | "view" | "full") => {
    const next: Record<string, PermissionDraft> = {};
    for (const p of catalog as any[]) {
      const key = String(p.permissionKey);
      if (mode === "full" || (mode === "view" && String(p.actionKey) === "view")) {
        next[key] = { effect: "allow", dataScope: "all", scopeConfig: draft[key]?.scopeConfig ?? null };
      }
    }
    setDraft(next);
  };''', "bulk preserves field config")

    new_ui = replace_once(new_ui, '''        next[key] = { effect, dataScope: effect === "deny" ? "none" : "all" };''', '''        next[key] = { ...next[key], effect, dataScope: effect === "deny" ? "none" : "all" };''', "module bulk preserves field config")

    new_ui = replace_once(new_ui, '''<Button variant="outline" size="sm" onClick={() => { const next: Record<string, PermissionDraft> = {}; setDraft(next); }}>{isRTL ? "مسح الكل" : "Clear all"}</Button><Button variant="outline" size="sm" onClick={() => { const next: Record<string, PermissionDraft> = {}; for (const p of catalog as any[]) if (String(p.actionKey) === "view") next[String(p.permissionKey)] = { effect: "allow", dataScope: "all" }; setDraft(next); }}>{isRTL ? "عرض فقط" : "View only"}</Button><Button variant="outline" size="sm" onClick={() => { const next: Record<string, PermissionDraft> = {}; for (const p of catalog as any[]) next[String(p.permissionKey)] = { effect: "allow", dataScope: "all" }; setDraft(next); }}>{isRTL ? "صلاحية كاملة" : "Full access"}</Button>''', '''<Button variant="outline" size="sm" onClick={() => bulk("clear")}>{isRTL ? "مسح الكل" : "Clear all"}</Button><Button variant="outline" size="sm" onClick={() => bulk("view")}>{isRTL ? "عرض فقط" : "View only"}</Button><Button variant="outline" size="sm" onClick={() => bulk("full")}>{isRTL ? "صلاحية كاملة" : "Full access"}</Button>''', "basic bulk uses preserving helper")

    new_ui = replace_once(new_ui, '''<Button variant="outline" size="sm" onClick={() => bulk("full")}>{isRTL ? "صلاحية كاملة" : "Full access"}</Button><Button size="sm" onClick={save} disabled={saveMutation.isPending}><Save className="h-4 w-4 me-1" />{isRTL ? "حفظ" : "Save"}</Button>''', '''<Button variant="outline" size="sm" onClick={() => bulk("full")}>{isRTL ? "صلاحية كاملة" : "Full access"}</Button><Button variant="outline" size="sm" onClick={() => setFieldEditor({ target: "role", permissionKey: "leads.view" })}>{isRTL ? "صلاحيات الحقول" : "Field Access"}</Button><Button size="sm" onClick={save} disabled={saveMutation.isPending}><Save className="h-4 w-4 me-1" />{isRTL ? "حفظ" : "Save"}</Button>''', "role field access button")

    new_ui = replace_once(new_ui, '''<div className="flex gap-2"><Button size="sm" onClick={saveUserOverrides} disabled={userOverridesMutation.isPending}><Save className="h-4 w-4 me-1" />{isRTL ? "حفظ الاستثناءات" : "Save overrides"}</Button></div>''', '''<div className="flex gap-2"><Button variant="outline" size="sm" onClick={() => setFieldEditor({ target: "user", permissionKey: "leads.view" })}>{isRTL ? "صلاحيات الحقول" : "Field Access"}</Button><Button size="sm" onClick={saveUserOverrides} disabled={userOverridesMutation.isPending}><Save className="h-4 w-4 me-1" />{isRTL ? "حفظ الاستثناءات" : "Save overrides"}</Button></div>''', "user field access button")

    new_ui = replace_once(new_ui, '''<div><div className="text-sm">{String(d.reason)}</div><div className="text-[11px] text-muted-foreground mt-1">source: {String(d.source)}{Array.isArray(d.roleIds) && d.roleIds.length ? ` • roleIds: ${d.roleIds.join(",")}` : ""}</div></div>''', '''<div><div className="text-sm">{String(d.reason)}</div><div className="text-[11px] text-muted-foreground mt-1">source: {String(d.source)}{Array.isArray(d.roleIds) && d.roleIds.length ? ` • roleIds: ${d.roleIds.join(",")}` : ""}</div>{d.fieldPolicy?.configured && <div className="text-[11px] text-muted-foreground mt-1">{isRTL ? "الحقول" : "fields"}: {d.fieldPolicy.allow === null ? (isRTL ? "الكل" : "all") : `${d.fieldPolicy.allow.length} allowed`} • {d.fieldPolicy.deny?.length || 0} denied</div>}</div>''', "tester field policy summary")

    new_ui = replace_once(new_ui, '''      <RoleDialog open={createOpen} onOpenChange={setCreateOpen} title={isRTL ? "إنشاء دور جديد" : "Create role"} form={form} setForm={setForm} isRTL={isRTL} showKey showParent roles={visibleRoles} onSubmit={() => createMutation.mutate({ roleKey: form.roleKey || undefined, name: form.name, nameAr: form.nameAr || null, description: form.description || null, parentRoleId: form.parentRoleId !== "none" ? Number(form.parentRoleId) : null })} busy={createMutation.isPending} />''', '''      <FieldPolicyDialog editor={fieldEditor} setEditor={setFieldEditor} roleDraft={draft} userDraft={userDraft} setPermission={setPermission} setUserPermission={setUserPermission} isRTL={isRTL} />
      <RoleDialog open={createOpen} onOpenChange={setCreateOpen} title={isRTL ? "إنشاء دور جديد" : "Create role"} form={form} setForm={setForm} isRTL={isRTL} showKey showParent roles={visibleRoles} onSubmit={() => createMutation.mutate({ roleKey: form.roleKey || undefined, name: form.name, nameAr: form.nameAr || null, description: form.description || null, parentRoleId: form.parentRoleId !== "none" ? Number(form.parentRoleId) : null })} busy={createMutation.isPending} />''', "field policy dialog mount")

    new_ui = replace_once(new_ui, '''function RoleDialog({ open, onOpenChange, title, form, setForm, isRTL, showKey = false, showParent = false, roles = [], currentRoleId = null, onSubmit, busy }: any) {''', '''function FieldPolicyDialog({ editor, setEditor, roleDraft, userDraft, setPermission, setUserPermission, isRTL }: any) {
  if (!editor) return null;
  const permissionKey = String(editor.permissionKey || FIELD_PERMISSION_KEYS[0]);
  const targetDraft = editor.target === "user" ? userDraft : roleDraft;
  const state: PermissionDraft = targetDraft[permissionKey] || { effect: "inherit", dataScope: "all", scopeConfig: null };
  const scopeConfig = normalizeScopeConfig(state.scopeConfig) || {};
  const fieldsConfig = scopeConfig.fields && typeof scopeConfig.fields === "object" && !Array.isArray(scopeConfig.fields) ? scopeConfig.fields as any : {};
  const mode = Array.isArray(fieldsConfig.allow) ? "allow" : Array.isArray(fieldsConfig.deny) ? "deny" : "all";
  const selected = new Set<string>(mode === "allow" ? fieldsConfig.allow.map(String) : mode === "deny" ? fieldsConfig.deny.map(String) : []);
  const moduleKey = permissionKey.split(".")[0];
  const fieldOptions = FIELD_CATALOG[moduleKey] || [];
  const enabled = state.effect === "allow";

  const updateConfig = (nextMode: "all" | "allow" | "deny", nextSelected: string[]) => {
    const nextConfig: Record<string, any> = { ...scopeConfig };
    if (nextMode === "all") delete nextConfig.fields;
    else if (nextMode === "allow") nextConfig.fields = { allow: nextSelected };
    else nextConfig.fields = { deny: nextSelected };
    const patch = { scopeConfig: Object.keys(nextConfig).length ? nextConfig : null };
    if (editor.target === "user") setUserPermission(permissionKey, patch);
    else setPermission(permissionKey, patch);
  };

  const changeMode = (nextMode: "all" | "allow" | "deny") => updateConfig(nextMode, []);
  const toggleField = (field: string, checked: boolean) => {
    const next = new Set(selected);
    if (checked) next.add(field); else next.delete(field);
    updateConfig(mode === "all" ? "deny" : mode, Array.from(next));
  };

  return <Dialog open={!!editor} onOpenChange={(open) => !open && setEditor(null)}>
    <DialogContent className="max-w-2xl" dir={isRTL ? "rtl" : "ltr"}>
      <DialogHeader><DialogTitle>{isRTL ? "صلاحيات الحقول" : "Field Access"}</DialogTitle></DialogHeader>
      <div className="space-y-4">
        <div>
          <Label>{isRTL ? "الصلاحية" : "Permission"}</Label>
          <Select value={permissionKey} onValueChange={(value) => setEditor({ ...editor, permissionKey: value })}>
            <SelectTrigger className="mt-1"><SelectValue /></SelectTrigger>
            <SelectContent>{FIELD_PERMISSION_KEYS.map(key => <SelectItem key={key} value={key}>{key}</SelectItem>)}</SelectContent>
          </Select>
        </div>
        {!enabled && <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-700">{isRTL ? "فعّل هذه الصلاحية على Allow أولًا. إعداد الحقول لا يُحفظ لصلاحية Inherit/Deny." : "Set this permission to Allow first. Field settings are not persisted for Inherit/Deny."}</div>}
        <div>
          <Label>{isRTL ? "وضع الوصول للحقول" : "Field access mode"}</Label>
          <Select disabled={!enabled} value={mode} onValueChange={(value: "all" | "allow" | "deny") => changeMode(value)}>
            <SelectTrigger className="mt-1"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{isRTL ? "كل الحقول" : "All fields"}</SelectItem>
              <SelectItem value="allow">{isRTL ? "الحقول المحددة فقط" : "Only selected fields"}</SelectItem>
              <SelectItem value="deny">{isRTL ? "كل الحقول ما عدا المحددة" : "All except selected fields"}</SelectItem>
            </SelectContent>
          </Select>
        </div>
        {mode !== "all" && <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-[46vh] overflow-auto rounded-lg border p-3">
          {fieldOptions.map(field => <div key={field.key} className="flex items-center justify-between gap-3 rounded-md border p-2">
            <div><div className="text-sm font-medium">{isRTL ? field.ar : field.en}</div><code className="text-[11px] text-muted-foreground">{field.key}</code></div>
            <Switch disabled={!enabled} checked={selected.has(field.key)} onCheckedChange={(checked) => toggleField(field.key, checked)} />
          </div>)}
        </div>}
        {mode === "allow" && enabled && selected.size === 0 && <div className="text-xs text-destructive">{isRTL ? "تنبيه: القائمة الفارغة تعني منع كل حقول البيانات في هذه الصلاحية." : "Warning: an empty allow-list blocks all business fields for this permission."}</div>}
        <p className="text-xs text-muted-foreground">{isRTL ? "المعرفات التقنية اللازمة للتنقل تظل متاحة. منع الحقول يتم من السيرفر، وليس إخفاء UI فقط." : "Technical identifiers needed for routing remain available. Field restrictions are enforced by the server, not only hidden in the UI."}</p>
      </div>
      <DialogFooter><Button onClick={() => setEditor(null)}>{isRTL ? "إغلاق" : "Close"}</Button></DialogFooter>
    </DialogContent>
  </Dialog>;
}

function RoleDialog({ open, onOpenChange, title, form, setForm, isRTL, showKey = false, showParent = false, roles = [], currentRoleId = null, onSubmit, busy }: any) {''', "field policy dialog component")

# Write only after every anchor has been validated.
if new_engine != engine:
    engine_path.write_text(new_engine)
if new_routers != routers:
    routers_path.write_text(new_routers)
if new_ui != ui:
    ui_path.write_text(new_ui)

print("PATCH_APPLIED=YES")
print("EXPECTED_HEAD=" + EXPECTED_HEAD)
print("FILES=server/security/permissionEngine.ts,server/routers.ts,client/src/pages/RolesPermissions.tsx")
