#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.cwd()
POLICY = ROOT / "server/security/corePermissionPolicy.ts"
POLICY_TEST = ROOT / "server/security/corePermissionPolicy.test.ts"
SCOPE = ROOT / "server/security/coreScopeEnforcement.ts"
SCOPE_TEST = ROOT / "server/security/coreScopeEnforcement.test.ts"
DB = ROOT / "server/db.ts"
ROUTERS = ROOT / "server/routers.ts"

for path in (POLICY, POLICY_TEST, DB, ROUTERS):
    if not path.exists():
        raise SystemExit(f"ERROR: missing expected TCRM file: {path}")

def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"ERROR: {label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)

# 1) Extend core permission gate to the real Account Management client routes.
policy = POLICY.read_text(encoding="utf-8")
old_module = '''const CORE_MODULES = new Set<CorePermissionModule>(["leads", "deals", "clients"]);

function moduleFromPath(path: string): CorePermissionModule | null {
  const module = String(path || "").split(".", 1)[0] as CorePermissionModule;
  return CORE_MODULES.has(module) ? module : null;
}
'''
new_module = '''const CORE_MODULES = new Set<CorePermissionModule>(["leads", "deals", "clients"]);

// TCRM_PERMISSIONS_SCOPE_ENFORCEMENT_V1
// Client CRUD/list routes live under accountManagement.* rather than clients.*.
// Keep this alias list explicit so unrelated AM workflow/contract/task endpoints
// never inherit a client permission accidentally.
const ACCOUNT_MANAGEMENT_CLIENT_OPERATIONS = new Set([
  "listclients",
  "getclientpoolstats",
  "getclientprofile",
  "getclientbusinessflow",
  "syncclientbusinessflow",
  "createclient",
  "updateclient",
  "deleteclient",
  "previewclientpoolexcel",
  "exportclientpoolexcel",
]);

function moduleFromPath(path: string): CorePermissionModule | null {
  const segments = String(path || "").split(".").filter(Boolean);
  const root = segments[0] as CorePermissionModule;
  if (CORE_MODULES.has(root)) return root;

  if (segments[0] === "accountManagement") {
    const operation = segments
      .slice(1)
      .join("")
      .replace(/[^a-zA-Z0-9]/g, "")
      .toLowerCase();
    if (ACCOUNT_MANAGEMENT_CLIENT_OPERATIONS.has(operation)) return "clients";
  }
  return null;
}
'''
if "TCRM_PERMISSIONS_SCOPE_ENFORCEMENT_V1" not in policy:
    policy = replace_once(policy, old_module, new_module, "core permission client alias")
POLICY.write_text(policy, encoding="utf-8")

policy_test = POLICY_TEST.read_text(encoding="utf-8")
test_anchor = '''  it("maps core CRUD mutations", () => {
'''
alias_test = '''  it("maps the real Account Management client endpoints", () => {
    expect(resolveCorePermissionKey("accountManagement.listClients", "query")).toBe("clients.view");
    expect(resolveCorePermissionKey("accountManagement.getClientProfile", "query")).toBe("clients.view");
    expect(resolveCorePermissionKey("accountManagement.getClientPoolStats", "query")).toBe("clients.view");
    expect(resolveCorePermissionKey("accountManagement.createClient", "mutation")).toBe("clients.create");
    expect(resolveCorePermissionKey("accountManagement.updateClient", "mutation")).toBe("clients.edit");
    expect(resolveCorePermissionKey("accountManagement.deleteClient", "mutation")).toBe("clients.delete");
    expect(resolveCorePermissionKey("accountManagement.exportClientPoolExcel", "mutation")).toBe("clients.export");
    expect(resolveCorePermissionKey("accountManagement.createContract", "mutation")).toBeNull();
  });

'''
if "maps the real Account Management client endpoints" not in policy_test:
    if test_anchor not in policy_test:
        raise SystemExit("ERROR: corePermissionPolicy.test.ts anchor not found")
    policy_test = policy_test.replace(test_anchor, alias_test + test_anchor, 1)
POLICY_TEST.write_text(policy_test, encoding="utf-8")

# 2) Scope context helpers reusing the existing phase3 row-scope engine.
scope_source = r'''// TCRM_PERMISSIONS_SCOPE_ENFORCEMENT_V1
import { TRPCError } from "@trpc/server";
import type { PermissionDecision, PermissionUser } from "./permissionEngine";
import { isRowInScope } from "./phase3ScopeFilters";
import { getClientById, getLeadById, getUserById } from "../db";

export type CoreScopedModule = "leads" | "deals" | "clients";

export type CoreScopeContext = {
  user: PermissionUser;
  permissionDecision?: PermissionDecision | null;
};

export function getCorePermissionDecision(
  ctx: CoreScopeContext | any,
  module: CoreScopedModule,
): PermissionDecision | null {
  const decision = ctx?.permissionDecision as PermissionDecision | undefined;
  if (!decision?.allowed) return null;
  if (!String(decision.permission || "").startsWith(`${module}.`)) return null;
  return decision;
}

function requireCorePermissionDecision(
  ctx: CoreScopeContext | any,
  module: CoreScopedModule,
): PermissionDecision {
  const decision = getCorePermissionDecision(ctx, module);
  if (!decision) {
    throw new TRPCError({
      code: "FORBIDDEN",
      message: `Missing effective ${module} permission decision`,
    });
  }
  return decision;
}

function scopedUser(ctx: CoreScopeContext | any): PermissionUser {
  return {
    id: Number(ctx?.user?.id ?? 0),
    role: String(ctx?.user?.role ?? ""),
    email: ctx?.user?.email ?? null,
    teamId: ctx?.user?.teamId ?? null,
  };
}

export function getCoreListScopeFilter(
  ctx: CoreScopeContext | any,
  module: CoreScopedModule,
) {
  const decision = getCorePermissionDecision(ctx, module);
  if (!decision) return null;
  const user = scopedUser(ctx);
  return {
    permissionScope: decision.scope,
    permissionUserId: Number(user.id),
    permissionTeamId: user.teamId ?? null,
    permissionRole: user.role ?? null,
  };
}

async function assertRowAllowed(
  module: CoreScopedModule,
  decision: PermissionDecision,
  user: PermissionUser,
  row: any,
) {
  const kind = module === "leads" ? "lead" : module === "deals" ? "deal" : "client";
  const allowed = await isRowInScope(kind, decision, user, row);
  if (!allowed) {
    throw new TRPCError({
      code: "FORBIDDEN",
      message: `${module} record is outside your permission scope`,
    });
  }
}

export async function assertLeadScopeForContext(ctx: CoreScopeContext | any, leadId: number) {
  const decision = requireCorePermissionDecision(ctx, "leads");
  const lead = await getLeadById(Number(leadId));
  if (!lead || lead.deletedAt) throw new TRPCError({ code: "NOT_FOUND", message: "Lead not found" });
  await assertRowAllowed("leads", decision, scopedUser(ctx), lead);
  return lead;
}

export async function assertDealLeadScopeForContext(ctx: CoreScopeContext | any, leadId: number) {
  const decision = requireCorePermissionDecision(ctx, "deals");
  await assertRowAllowed("deals", decision, scopedUser(ctx), { leadId: Number(leadId) });
}

export async function filterDealRowsForContext<T extends { leadId?: number | null }>(
  ctx: CoreScopeContext | any,
  rows: T[],
): Promise<T[]> {
  const decision = requireCorePermissionDecision(ctx, "deals");
  if (decision.scope === "all") return rows;
  const user = scopedUser(ctx);
  const checks = await Promise.all(rows.map(row => isRowInScope("deal", decision, user, row)));
  return rows.filter((_, index) => checks[index]);
}

export async function assertClientScopeForContext(ctx: CoreScopeContext | any, clientId: number) {
  const decision = requireCorePermissionDecision(ctx, "clients");
  const client = await getClientById(Number(clientId));
  if (!client || (client as any).deletedAt) {
    throw new TRPCError({ code: "NOT_FOUND", message: "Client not found" });
  }
  await assertRowAllowed("clients", decision, scopedUser(ctx), client);
  return client;
}

// Creation has no persisted row yet. Use the same ownership model as the
// canonical row-scope engine: own/assigned => target self, team => target user
// must belong to the caller's team, all => unrestricted.
export async function assertCreateOwnerScopeForContext(
  ctx: CoreScopeContext | any,
  module: "leads" | "clients",
  requestedOwnerId: number | null | undefined,
): Promise<number> {
  const decision = requireCorePermissionDecision(ctx, module);
  const user = scopedUser(ctx);
  const userId = Number(user.id);
  const requested = Number(requestedOwnerId ?? userId);

  if (!(userId > 0) || !(requested > 0)) {
    throw new TRPCError({ code: "FORBIDDEN", message: "Invalid permission scope identity" });
  }

  if (decision.scope === "all") return requested;

  if (decision.scope === "own" || decision.scope === "assigned") {
    if (requested !== userId) {
      throw new TRPCError({
        code: "FORBIDDEN",
        message: `${module} create target is outside your permission scope`,
      });
    }
    return requested;
  }

  if (decision.scope === "team") {
    const teamId = Number(user.teamId ?? 0);
    if (!(teamId > 0)) {
      throw new TRPCError({ code: "FORBIDDEN", message: "Team scope requires an assigned team" });
    }
    if (requested === userId) return requested;
    const target = await getUserById(requested);
    if (!target || Number((target as any).teamId ?? 0) !== teamId || !(target as any).isActive || (target as any).deletedAt) {
      throw new TRPCError({
        code: "FORBIDDEN",
        message: `${module} create target is outside your team scope`,
      });
    }
    return requested;
  }

  throw new TRPCError({
    code: "FORBIDDEN",
    message: `${module} create is not supported for permission scope ${decision.scope}`,
  });
}
'''
SCOPE.write_text(scope_source, encoding="utf-8")

scope_test_source = r'''import { describe, expect, it } from "vitest";
import { getCoreListScopeFilter, getCorePermissionDecision } from "./coreScopeEnforcement";

const ctx = (permission: string, scope: any) => ({
  user: { id: 17, role: "SalesAgent", teamId: 9 },
  permissionDecision: { allowed: true, permission, scope, source: "role" },
});

describe("coreScopeEnforcement", () => {
  it("carries the effective permission scope into DB list filters", () => {
    expect(getCoreListScopeFilter(ctx("leads.view", "assigned"), "leads")).toEqual({
      permissionScope: "assigned",
      permissionUserId: 17,
      permissionTeamId: 9,
      permissionRole: "SalesAgent",
    });
  });

  it("does not reuse a decision for a different module", () => {
    expect(getCorePermissionDecision(ctx("leads.view", "assigned"), "clients")).toBeNull();
  });

  it("keeps all/team/own scopes intact instead of widening them", () => {
    expect(getCoreListScopeFilter(ctx("clients.view", "team"), "clients")?.permissionScope).toBe("team");
    expect(getCoreListScopeFilter(ctx("leads.view", "own"), "leads")?.permissionScope).toBe("own");
    expect(getCoreListScopeFilter(ctx("deals.view", "all"), "deals")?.permissionScope).toBe("all");
  });
});
'''
SCOPE_TEST.write_text(scope_test_source, encoding="utf-8")

# 3) Apply scope conditions inside canonical DB list/count queries.
db = DB.read_text(encoding="utf-8")
db_import_anchor = 'import { matchesSystemSmartSearch } from "@shared/systemSmartSearch";\n'
db_imports = '''import type { PermissionScope } from "./security/permissionCatalog";
import { buildClientScopeCondition, buildLeadScopeCondition } from "./security/phase3ScopeFilters";
'''
if db_imports not in db:
    if db_import_anchor not in db:
        raise SystemExit("ERROR: db import anchor not found")
    db = db.replace(db_import_anchor, db_import_anchor + db_imports, 1)

lead_filter_anchor = '''  offset?: number;
}

function taraLeadMetadataConditions'''
lead_filter_new = '''  offset?: number;
  // TCRM_PERMISSIONS_SCOPE_ENFORCEMENT_V1
  permissionScope?: PermissionScope;
  permissionUserId?: number;
  permissionTeamId?: number | null;
  permissionRole?: string | null;
}

function taraLeadMetadataConditions'''
lead_header = db.split("// ─── Leads", 1)[1].split("function taraLeadMetadataConditions", 1)[0]
if "permissionScope?: PermissionScope;" not in lead_header:
    db = replace_once(db, lead_filter_anchor, lead_filter_new, "LeadFilters scope fields")

old_lead_scope = '''  const conditions = [isNull(leads.deletedAt)];
  if (filters.currentTamUserId) {
'''
new_lead_scope = '''  const conditions = [isNull(leads.deletedAt)];
  if (filters.permissionScope) {
    conditions.push(buildLeadScopeCondition(
      filters.permissionScope,
      {
        id: Number(filters.permissionUserId ?? 0),
        role: filters.permissionRole ?? null,
        teamId: filters.permissionTeamId ?? null,
      },
      "leads.ownerId",
    ));
  } else if (filters.currentTamUserId) {
'''
count = db.count(old_lead_scope)
if count == 2:
    db = db.replace(old_lead_scope, new_lead_scope)
elif count not in (0,):
    raise SystemExit(f"ERROR: expected 0 or 2 lead scope anchors, found {count}")

client_type_anchor = '''  paymentStatus?: string;
};

function buildClientListConditions'''
client_type_new = '''  paymentStatus?: string;
  // TCRM_PERMISSIONS_SCOPE_ENFORCEMENT_V1
  permissionScope?: PermissionScope;
  permissionUserId?: number;
  permissionTeamId?: number | null;
  permissionRole?: string | null;
};

function buildClientListConditions'''
client_header = db.split("// ─── Account Management: Clients", 1)[1].split("function buildClientListConditions", 1)[0]
if "permissionScope?: PermissionScope;" not in client_header:
    db = replace_once(db, client_type_anchor, client_type_new, "ClientListFilters scope fields")

legacy_client_scope = '''  if (filters.userRole === "AccountManager" && filters.userId) conditions.push(eq(clients.accountManagerId, filters.userId));
  if (filters.userRole === "AccountManagerLead") {
    const teamId = Number(filters.teamId ?? 0);
    conditions.push(Number.isInteger(teamId) && teamId > 0
      ? sql`(
          EXISTS (SELECT 1 FROM users am_list_scope WHERE am_list_scope.id = ${clients.accountManagerId} AND am_list_scope.teamId = ${teamId} AND am_list_scope.isActive = 1 AND am_list_scope.deletedAt IS NULL)
          OR (
            ${clients.accountManagerId} IS NULL
            AND EXISTS (SELECT 1 FROM leads am_neutral_lead JOIN users am_neutral_owner ON am_neutral_owner.id = am_neutral_lead.ownerId AND am_neutral_owner.deletedAt IS NULL WHERE am_neutral_lead.id = ${clients.leadId} AND am_neutral_lead.deletedAt IS NULL AND am_neutral_owner.teamId = ${teamId})
          )
        )`
      : sql`1 = 0`);
  }
  if (filters.userRole === "SalesManager") {
    const teamId = Number(filters.teamId ?? 0);
    conditions.push(Number.isInteger(teamId) && teamId > 0
      ? sql`EXISTS (SELECT 1 FROM leads sales_list_scope_lead JOIN users sales_list_scope_user ON sales_list_scope_user.id = sales_list_scope_lead.ownerId AND sales_list_scope_user.deletedAt IS NULL WHERE sales_list_scope_lead.id = ${clients.leadId} AND sales_list_scope_lead.deletedAt IS NULL AND sales_list_scope_user.teamId = ${teamId})`
      : sql`1 = 0`);
  }
  if (["ServiceAdvisor", "PartsAgent", "CrmFollowUp"].includes(filters.userRole ?? "")) {
    // Phase 1.3: task assignment never grants full client-list access.
    conditions.push(sql`1 = 0`);
  }
'''
permission_client_scope = '''  if (filters.permissionScope) {
    conditions.push(buildClientScopeCondition(
      filters.permissionScope,
      {
        id: Number(filters.permissionUserId ?? 0),
        role: filters.permissionRole ?? null,
        teamId: filters.permissionTeamId ?? null,
      },
      "clients",
    ));
  } else {
    if (filters.userRole === "AccountManager" && filters.userId) conditions.push(eq(clients.accountManagerId, filters.userId));
    if (filters.userRole === "AccountManagerLead") {
      const teamId = Number(filters.teamId ?? 0);
      conditions.push(Number.isInteger(teamId) && teamId > 0
        ? sql`(
            EXISTS (SELECT 1 FROM users am_list_scope WHERE am_list_scope.id = ${clients.accountManagerId} AND am_list_scope.teamId = ${teamId} AND am_list_scope.isActive = 1 AND am_list_scope.deletedAt IS NULL)
            OR (
              ${clients.accountManagerId} IS NULL
              AND EXISTS (SELECT 1 FROM leads am_neutral_lead JOIN users am_neutral_owner ON am_neutral_owner.id = am_neutral_lead.ownerId AND am_neutral_owner.deletedAt IS NULL WHERE am_neutral_lead.id = ${clients.leadId} AND am_neutral_lead.deletedAt IS NULL AND am_neutral_owner.teamId = ${teamId})
            )
          )`
        : sql`1 = 0`);
    }
    if (filters.userRole === "SalesManager") {
      const teamId = Number(filters.teamId ?? 0);
      conditions.push(Number.isInteger(teamId) && teamId > 0
        ? sql`EXISTS (SELECT 1 FROM leads sales_list_scope_lead JOIN users sales_list_scope_user ON sales_list_scope_user.id = sales_list_scope_lead.ownerId AND sales_list_scope_user.deletedAt IS NULL WHERE sales_list_scope_lead.id = ${clients.leadId} AND sales_list_scope_lead.deletedAt IS NULL AND sales_list_scope_user.teamId = ${teamId})`
        : sql`1 = 0`);
    }
    if (["ServiceAdvisor", "PartsAgent", "CrmFollowUp"].includes(filters.userRole ?? "")) {
      conditions.push(sql`1 = 0`);
    }
  }
'''
if permission_client_scope not in db:
    db = replace_once(db, legacy_client_scope, permission_client_scope, "client list canonical scope")
DB.write_text(db, encoding="utf-8")

# 4) Router integration.
routers = ROUTERS.read_text(encoding="utf-8")
scope_import_anchor = 'import { protectedProcedure, publicProcedure, router } from "./_core/trpc";\n'
scope_import = '''import {
  assertClientScopeForContext,
  assertCreateOwnerScopeForContext,
  assertDealLeadScopeForContext,
  assertLeadScopeForContext,
  filterDealRowsForContext,
  getCoreListScopeFilter,
  getCorePermissionDecision,
} from "./security/coreScopeEnforcement";
'''
if scope_import not in routers:
    if scope_import_anchor not in routers:
        raise SystemExit("ERROR: routers trpc import anchor not found")
    routers = routers.replace(scope_import_anchor, scope_import_anchor + scope_import, 1)

old_client_procs = '''const clientOpsProcedure = protectedProcedure.use(({ ctx, next }) => {
  const role = normalizeUserRole(ctx.user.role);
  if (!["Admin", "SalesManager", "AccountManager", "AccountManagerLead"].includes(role)) {
    throw new TRPCError({ code: "FORBIDDEN", message: "Client read access required" });
  }
  return next({ ctx });
});

const clientWriteProcedure = protectedProcedure.use(({ ctx, next }) => {
  const role = normalizeUserRole(ctx.user.role);
  if (!["Admin", "AccountManager", "AccountManagerLead"].includes(role)) {
    throw new TRPCError({ code: "FORBIDDEN", message: "Client write access required" });
  }
  return next({ ctx });
});

const clientCreateProcedure = protectedProcedure.use(({ ctx, next }) => {
  const role = normalizeUserRole(ctx.user.role);
  if (!["Admin", "SalesManager", "AccountManager", "AccountManagerLead"].includes(role)) {
    throw new TRPCError({ code: "FORBIDDEN", message: "Client creation access required" });
  }
  return next({ ctx });
});
'''
new_client_procs = '''const clientOpsProcedure = protectedProcedure.use(({ ctx, next }) => {
  if (getCorePermissionDecision(ctx, "clients")?.permission === "clients.view") return next({ ctx });
  const role = normalizeUserRole(ctx.user.role);
  if (!["Admin", "SalesManager", "AccountManager", "AccountManagerLead"].includes(role)) {
    throw new TRPCError({ code: "FORBIDDEN", message: "Client read access required" });
  }
  return next({ ctx });
});

const clientWriteProcedure = protectedProcedure.use(({ ctx, next }) => {
  const corePermission = getCorePermissionDecision(ctx, "clients")?.permission;
  if (corePermission === "clients.edit" || corePermission === "clients.delete") return next({ ctx });
  const role = normalizeUserRole(ctx.user.role);
  if (!["Admin", "AccountManager", "AccountManagerLead"].includes(role)) {
    throw new TRPCError({ code: "FORBIDDEN", message: "Client write access required" });
  }
  return next({ ctx });
});

const clientCreateProcedure = protectedProcedure.use(({ ctx, next }) => {
  if (getCorePermissionDecision(ctx, "clients")?.permission === "clients.create") return next({ ctx });
  const role = normalizeUserRole(ctx.user.role);
  if (!["Admin", "SalesManager", "AccountManager", "AccountManagerLead"].includes(role)) {
    throw new TRPCError({ code: "FORBIDDEN", message: "Client creation access required" });
  }
  return next({ ctx });
});
'''
if new_client_procs not in routers:
    routers = replace_once(routers, old_client_procs, new_client_procs, "client procedures permission-aware")

old_leads_list_rls = '''        const filters: any = { ...input };
        // ── ROW-LEVEL SECURITY ──
        if (isTechnicalAccountManagerRole(ctx.user.role)) {
          // TAM users see only leads whose current active TAM case is assigned to them.
          filters.currentTamUserId = ctx.user.id;
          delete filters.assignedUserId;
          delete filters.ownerId;
        } else if (isSalesAgentRole(ctx.user.role) || ctx.user.role === "AccountManager" || ctx.user.role === "AccountManagerLead") {
          // SalesAgent / AccountManager see only leads they own or are assigned to.
          filters.assignedUserId = ctx.user.id;
        }
        // SalesManager sees all leads (no team filter needed for now since teamId is not widely used)
'''
new_leads_list_rls = '''        const filters: any = { ...input };
        const permissionScope = getCoreListScopeFilter(ctx, "leads");
        if (permissionScope) {
          Object.assign(filters, permissionScope);
          delete filters.assignedUserId;
          delete filters.currentTamUserId;
          delete filters.ownerId;
        } else {
          if (isTechnicalAccountManagerRole(ctx.user.role)) {
            filters.currentTamUserId = ctx.user.id;
            delete filters.assignedUserId;
            delete filters.ownerId;
          } else if (isSalesAgentRole(ctx.user.role) || ctx.user.role === "AccountManager" || ctx.user.role === "AccountManagerLead") {
            filters.assignedUserId = ctx.user.id;
          }
        }
'''
if new_leads_list_rls not in routers:
    routers = replace_once(routers, old_leads_list_rls, new_leads_list_rls, "leads list scope")

lead_by_id_anchor = '''        const lead = await getLeadById(input.id);
        if (!lead) throw new TRPCError({ code: "NOT_FOUND" });
        // ── ROW-LEVEL SECURITY ──
'''
lead_by_id_new = '''        const lead = await getLeadById(input.id);
        if (!lead) throw new TRPCError({ code: "NOT_FOUND" });
        if (getCorePermissionDecision(ctx, "leads")) {
          await assertLeadScopeForContext(ctx, input.id);
        }
        // ── ROW-LEVEL SECURITY ──
'''
if lead_by_id_new not in routers:
    routers = replace_once(routers, lead_by_id_anchor, lead_by_id_new, "lead byId scope")

lead_create_anchor = '''        if (!ownerId) {
          ownerId = ctx.user.id;
        }

        // ── Duplicate phone check ──
'''
lead_create_new = '''        if (!ownerId) {
          ownerId = ctx.user.id;
        }
        if (getCorePermissionDecision(ctx, "leads")) {
          ownerId = await assertCreateOwnerScopeForContext(ctx, "leads", ownerId);
        }

        // ── Duplicate phone check ──
'''
if lead_create_new not in routers:
    routers = replace_once(routers, lead_create_anchor, lead_create_new, "lead create scope")

old_lead_update_rls = '''        const existingLead = await getLeadById(id);
        if (isSalesAgentRole(ctx.user.role)) {
          if (!existingLead || existingLead.ownerId !== ctx.user.id) {
            throw new TRPCError({ code: "FORBIDDEN", message: "You can only edit leads assigned to you" });
          }
          // SalesAgent cannot reassign leads to other agents
          if (data.ownerId !== undefined && data.ownerId !== ctx.user.id) {
'''
new_lead_update_rls = '''        const existingLead = await getLeadById(id);
        const coreLeadDecision = getCorePermissionDecision(ctx, "leads");
        if (coreLeadDecision) {
          await assertLeadScopeForContext(ctx, id);
        } else if (isSalesAgentRole(ctx.user.role)) {
          if (!existingLead || existingLead.ownerId !== ctx.user.id) {
            throw new TRPCError({ code: "FORBIDDEN", message: "You can only edit leads assigned to you" });
          }
        }
        if (isSalesAgentRole(ctx.user.role)) {
          // SalesAgent cannot reassign leads to other agents
          if (data.ownerId !== undefined && data.ownerId !== ctx.user.id) {
'''
if new_lead_update_rls not in routers:
    routers = replace_once(routers, old_lead_update_rls, new_lead_update_rls, "lead update scope")

lead_delete_marker = '''    delete: salesEditProcedure
      .input(z.object({ id: z.number() }))
      .mutation(async ({ ctx, input }) => {
'''
if lead_delete_marker in routers and 'await assertLeadScopeForContext(ctx, input.id);' not in routers[routers.find(lead_delete_marker):routers.find(lead_delete_marker)+700]:
    replacement = lead_delete_marker + '''        if (getCorePermissionDecision(ctx, "leads")) {
          await assertLeadScopeForContext(ctx, input.id);
        }
'''
    routers = routers.replace(lead_delete_marker, replacement, 1)

deal_by_lead_anchor = '''    byLead: protectedProcedure
      .input(z.object({ leadId: z.number() }))
      .query(async ({ ctx, input }) => {
'''
if deal_by_lead_anchor in routers:
    start = routers.find(deal_by_lead_anchor)
    body = start + len(deal_by_lead_anchor)
    if 'assertDealLeadScopeForContext(ctx, input.leadId)' not in routers[body:body+500]:
        routers = routers[:body] + '''        if (getCorePermissionDecision(ctx, "deals")) {
          await assertDealLeadScopeForContext(ctx, input.leadId);
        }
''' + routers[body:]

old_deals_by_user_return = '''        return getDealsByUser(input.userId);
      }),
'''
new_deals_by_user_return = '''        const rows = await getDealsByUser(input.userId);
        return getCorePermissionDecision(ctx, "deals")
          ? filterDealRowsForContext(ctx, rows as any[])
          : rows;
      }),
'''
if new_deals_by_user_return not in routers and old_deals_by_user_return in routers:
    routers = routers.replace(old_deals_by_user_return, new_deals_by_user_return, 1)

# Scope deal handlers that already carry a leadId. Keep every insertion bounded
# to the deals router so similarly named activity/client procedures are untouched.
deals_start = routers.find('  deals: router({\n')
if deals_start < 0:
    raise SystemExit("ERROR: deals router not found")
deals_end = routers.find('\n  campaigns:', deals_start)
if deals_end < 0:
    deals_end = routers.find('\n  pipelineStages:', deals_start)
if deals_end < 0:
    raise SystemExit("ERROR: deals router end not found")

for section_name in ("create", "addPayment", "updatePayment", "deletePayment", "cancel"):
    section_start = routers.find(f'    {section_name}: notMediaBuyerProcedure\n', deals_start, deals_end)
    if section_start < 0:
        continue
    mutation_pos = routers.find('.mutation(async ({ ctx, input }) => {\n', section_start, deals_end)
    if mutation_pos < 0:
        continue
    body = mutation_pos + len('.mutation(async ({ ctx, input }) => {\n')
    if 'assertDealLeadScopeForContext(ctx, input.leadId)' not in routers[body:body+500]:
        insertion = '''        if (getCorePermissionDecision(ctx, "deals")) {
          await assertDealLeadScopeForContext(ctx, input.leadId);
        }
'''
        routers = routers[:body] + insertion + routers[body:]
        deals_end += len(insertion)

update_start = routers.find('    update: notMediaBuyerProcedure\n', deals_start, deals_end)
if update_start >= 0:
    update_pos = routers.find('.mutation(async ({ ctx, input }) => {\n', update_start, deals_end)
    if update_pos >= 0:
        body = update_pos + len('.mutation(async ({ ctx, input }) => {\n')
        if 'getCorePermissionDecision(ctx, "deals") && input.leadId' not in routers[body:body+700]:
            insertion = '''        if (getCorePermissionDecision(ctx, "deals") && input.leadId) {
          await assertDealLeadScopeForContext(ctx, input.leadId);
        }
'''
            routers = routers[:body] + insertion + routers[body:]
            deals_end += len(insertion)

old_client_list_call = '''        const result = await getClients({
          ...input,
          userRole: normalizeUserRole(ctx.user.role),
          userId: ctx.user.id,
          teamId: ctx.user.teamId,
        });
'''
new_client_list_call = '''        const coreScope = getCoreListScopeFilter(ctx, "clients");
        const result = await getClients({
          ...input,
          ...(coreScope ?? {
            userRole: normalizeUserRole(ctx.user.role),
            userId: ctx.user.id,
            teamId: ctx.user.teamId,
          }),
        });
'''
if new_client_list_call not in routers:
    routers = replace_once(routers, old_client_list_call, new_client_list_call, "client list route scope")

old_client_stats_call = '''        return getClientPoolStats({
          ...(input ?? {}),
          userRole: normalizeUserRole(ctx.user.role),
          userId: ctx.user.id,
          teamId: ctx.user.teamId,
        } as any);
'''
new_client_stats_call = '''        const coreScope = getCoreListScopeFilter(ctx, "clients");
        return getClientPoolStats({
          ...(input ?? {}),
          ...(coreScope ?? {
            userRole: normalizeUserRole(ctx.user.role),
            userId: ctx.user.id,
            teamId: ctx.user.teamId,
          }),
        } as any);
'''
if new_client_stats_call not in routers:
    routers = replace_once(routers, old_client_stats_call, new_client_stats_call, "client stats route scope")

old_client_access = '''async function assertAccountManagementClientAccess(
  ctx: any,
  clientId: number,
  operation: "client.read.summary" | "client.read.full" | "client.update" | "client.delete" | "contract.create" | "payment.create" | "payment.read" = "client.read.full",
) {
  await assertClientOperationAllowed({ id: Number(ctx.user.id), role: normalizeUserRole(ctx.user.role), teamId: ctx.user.teamId }, clientId, operation);
  const client = await getClientById(clientId);
'''
new_client_access = '''async function assertAccountManagementClientAccess(
  ctx: any,
  clientId: number,
  operation: "client.read.summary" | "client.read.full" | "client.update" | "client.delete" | "contract.create" | "payment.create" | "payment.read" = "client.read.full",
) {
  if (getCorePermissionDecision(ctx, "clients")) {
    await assertClientScopeForContext(ctx, clientId);
  } else {
    await assertClientOperationAllowed({ id: Number(ctx.user.id), role: normalizeUserRole(ctx.user.role), teamId: ctx.user.teamId }, clientId, operation);
  }
  const client = await getClientById(clientId);
'''
if new_client_access not in routers:
    routers = replace_once(routers, old_client_access, new_client_access, "client direct row scope")

old_client_create_role = '''        const role = normalizeUserRole(ctx.user.role);
        const canCreateClient = isManagerRole(role) || role === "AccountManager" || role === "AccountManagerLead";
        if (!canCreateClient) {
          throw new TRPCError({ code: "FORBIDDEN", message: "Only managers and Account Management roles can create clients." });
        }
        if (role === "AccountManager" && input.accountManagerId && input.accountManagerId !== ctx.user.id) {
          throw new TRPCError({ code: "FORBIDDEN", message: "Account Managers can only create direct clients assigned to themselves." });
        }
'''
new_client_create_role = '''        const role = normalizeUserRole(ctx.user.role);
        const coreClientCreate = getCorePermissionDecision(ctx, "clients");
        if (coreClientCreate) {
          const scopedAccountManagerId = await assertCreateOwnerScopeForContext(
            ctx,
            "clients",
            input.accountManagerId ?? ctx.user.id,
          );
          if (input.accountManagerId == null && coreClientCreate.scope !== "all") {
            input.accountManagerId = scopedAccountManagerId;
          }
        } else {
          const canCreateClient = isManagerRole(role) || role === "AccountManager" || role === "AccountManagerLead";
          if (!canCreateClient) {
            throw new TRPCError({ code: "FORBIDDEN", message: "Only managers and Account Management roles can create clients." });
          }
          if (role === "AccountManager" && input.accountManagerId && input.accountManagerId !== ctx.user.id) {
            throw new TRPCError({ code: "FORBIDDEN", message: "Account Managers can only create direct clients assigned to themselves." });
          }
        }
'''
if new_client_create_role not in routers:
    routers = replace_once(routers, old_client_create_role, new_client_create_role, "client create scope")

ROUTERS.write_text(routers, encoding="utf-8")

final_policy = POLICY.read_text(encoding="utf-8")
final_db = DB.read_text(encoding="utf-8")
final_routers = ROUTERS.read_text(encoding="utf-8")
required = {
    "ACCOUNT_MANAGEMENT_CLIENT_ALIAS": "ACCOUNT_MANAGEMENT_CLIENT_OPERATIONS" in final_policy,
    "LEAD_DB_SCOPE": 'buildLeadScopeCondition(' in final_db and '"leads.ownerId"' in final_db,
    "CLIENT_DB_SCOPE": 'buildClientScopeCondition(' in final_db and '"clients"' in final_db,
    "LEAD_LIST_SCOPE": 'getCoreListScopeFilter(ctx, "leads")' in final_routers,
    "CLIENT_LIST_SCOPE": 'getCoreListScopeFilter(ctx, "clients")' in final_routers,
    "LEAD_ROW_SCOPE": "assertLeadScopeForContext" in final_routers,
    "DEAL_ROW_SCOPE": "assertDealLeadScopeForContext" in final_routers,
    "CLIENT_ROW_SCOPE": "assertClientScopeForContext" in final_routers,
}
failed = [key for key, ok in required.items() if not ok]
if failed:
    raise SystemExit("ERROR: partial scope patch: " + ",".join(failed))

print("PATCH=TCRM-PERMISSIONS-SCOPE-ENFORCEMENT-V1")
print("MODULES=leads,deals,clients")
print("ACCOUNT_MANAGEMENT_CLIENT_ALIAS=YES")
print("LEAD_LIST_DB_SCOPE=YES")
print("CLIENT_LIST_DB_SCOPE=YES")
print("LEAD_ENTITY_SCOPE=YES")
print("DEAL_ENTITY_SCOPE=YES")
print("CLIENT_ENTITY_SCOPE=YES")
print("CREATE_OWNER_SCOPE=YES")
print("CANONICAL_PHASE3_SCOPE_REUSED=YES")
print("DB_SCHEMA_CHANGED=NO")
print("DATA_CHANGED=NO")
print("FILES_CHANGED=server/security/corePermissionPolicy.ts,server/security/corePermissionPolicy.test.ts,server/security/coreScopeEnforcement.ts,server/security/coreScopeEnforcement.test.ts,server/db.ts,server/routers.ts")
