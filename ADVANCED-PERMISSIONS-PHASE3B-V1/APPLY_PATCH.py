#!/usr/bin/env python3
from pathlib import Path
import shutil, sys, time

ROOT = Path(__file__).resolve().parent
TARGET = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TCRM-MAIN").resolve()
FILES = ROOT / "files"
BACKUP = TARGET / ".patch-backups" / f"advanced-permissions-phase3b-{int(time.time())}"

required = [
    TARGET / "server/_core/trpc.ts",
    TARGET / "server/routers.ts",
    TARGET / "server/db.ts",
    TARGET / "server/security/phase3ScopeFilters.ts",
    TARGET / "server/security/permissionEngine.ts",
]
for p in required:
    if not p.exists(): raise SystemExit(f"Missing required file: {p}")

routers = (TARGET / "server/routers.ts").read_text()
if "getDealsScoped," not in routers or "ADVANCED_PERMISSIONS_PHASE3A_FIX2_V1" not in routers:
    raise SystemExit("Phase 3A reviewed baseline is required before Phase 3B")

BACKUP.mkdir(parents=True, exist_ok=True)
for rel in ["server/_core/trpc.ts", "server/routers.ts", "server/db.ts"]:
    dst = TARGET / rel
    (BACKUP / rel).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(dst, BACKUP / rel)

for rel in ["server/security/phase3bScope.ts", "scripts/verify-advanced-permissions-phase3b.ts"]:
    src, dst = FILES / rel, TARGET / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

trpc_path = TARGET / "server/_core/trpc.ts"
trpc = trpc_path.read_text()
anchor = 'export const clientsExportScope = phase3Scope("clients.export");\n'
insert = anchor + '''\n// ADVANCED_PERMISSIONS_PHASE3B_V1\nexport const activitiesViewScope = phase3Scope("activities.view");\nexport const activitiesCreateScope = phase3Scope("activities.create");\nexport const activitiesEditScope = phase3Scope("activities.edit");\nexport const activitiesDeleteScope = phase3Scope("activities.delete");\nexport const tasksViewScope = phase3Scope("tasks.view");\nexport const tasksCreateScope = phase3Scope("tasks.create");\nexport const tasksEditScope = phase3Scope("tasks.edit");\nexport const tasksDeleteScope = phase3Scope("tasks.delete");\nexport const tasksAssignScope = phase3Scope("tasks.assign");\nexport const contractsViewScope = phase3Scope("contracts.view");\nexport const contractsCreateScope = phase3Scope("contracts.create");\nexport const contractsEditScope = phase3Scope("contracts.edit");\nexport const contractsDeleteScope = phase3Scope("contracts.delete");\nexport const contractsExportScope = phase3Scope("contracts.export");\n'''
if "ADVANCED_PERMISSIONS_PHASE3B_V1" not in trpc:
    if anchor not in trpc: raise SystemExit("trpc Phase3 anchor changed")
    trpc = trpc.replace(anchor, insert, 1)
    trpc_path.write_text(trpc)

db_path = TARGET / "server/db.ts"
db = db_path.read_text()
anchor = '''export async function getActivitiesByUser(userId: number, limit = 20): Promise<Activity[]> {\n  const db = await getDb();\n  if (!db) return [];\n  return db\n    .select()\n    .from(activities)\n    .where(and(eq(activities.userId, userId), isNull(activities.deletedAt)))\n    .orderBy(desc(activities.activityTime))\n    .limit(limit);\n}\n'''
addition = anchor + '''\n// ADVANCED_PERMISSIONS_PHASE3B_V1 — SQL/source-level activity feed scope.\nexport async function getActivitiesByUserScoped(userId: number, limit = 20, permissionScopeSql?: any): Promise<Activity[]> {\n  const db = await getDb();\n  if (!db) return [];\n  const scopeClause = permissionScopeSql ? sql`AND (${permissionScopeSql})` : sql``;\n  const result = await db.execute(sql`\n    SELECT a.* FROM activities a\n    JOIN leads l ON l.id = a.leadId\n    WHERE a.userId = ${userId}\n      AND a.deletedAt IS NULL\n      AND l.deletedAt IS NULL\n      ${scopeClause}\n    ORDER BY a.activityTime DESC\n    LIMIT ${limit}\n  `);\n  return (result as any)[0] ?? [];\n}\n'''
if "getActivitiesByUserScoped" not in db:
    if anchor not in db: raise SystemExit("db activity anchor changed")
    db = db.replace(anchor, addition, 1)
    db_path.write_text(db)

rp = TARGET / "server/routers.ts"
r = rp.read_text()
old = 'import { protectedProcedure, publicProcedure, router, leadsViewScope, leadsCreateScope, leadsEditScope, leadsDeleteScope, leadsRestoreScope, leadsImportScope, leadsExportScope, dealsViewScope, dealsCreateScope, dealsEditScope, dealsDeleteScope, dealsExportScope, clientsViewScope, clientsCreateScope, clientsEditScope, clientsDeleteScope, clientsExportScope } from "./_core/trpc";'
new = 'import { protectedProcedure, publicProcedure, router, leadsViewScope, leadsCreateScope, leadsEditScope, leadsDeleteScope, leadsRestoreScope, leadsImportScope, leadsExportScope, dealsViewScope, dealsCreateScope, dealsEditScope, dealsDeleteScope, dealsExportScope, clientsViewScope, clientsCreateScope, clientsEditScope, clientsDeleteScope, clientsExportScope, activitiesViewScope, activitiesCreateScope, activitiesEditScope, activitiesDeleteScope, tasksViewScope, tasksCreateScope, tasksEditScope, tasksDeleteScope, contractsViewScope, contractsCreateScope, contractsEditScope } from "./_core/trpc";'
if old in r: r = r.replace(old, new, 1)
if 'from "./security/phase3bScope"' not in r:
    marker = 'import { isRowInScope, assertRowScope, buildLeadScopeCondition, buildDealScopeCondition, buildClientScopeCondition } from "./security/phase3ScopeFilters";'
    r = r.replace(marker, marker + '\nimport { assertLeadPermissionScope, assertClientPermissionScope, assertActivityPermissionScope, assertTaskPermissionScope, filterTasksByPermissionScope, assertTaskCreatePermissionScope, assertContractPermissionScope, filterContractsByPermissionScope, assertContractCreatePermissionScope } from "./security/phase3bScope";', 1)
if 'getActivitiesByUserScoped,' not in r:
    r = r.replace('  getActivitiesByUser,\n', '  getActivitiesByUser,\n  getActivitiesByUserScoped,\n', 1)

# Activities.
r = r.replace('    byLead: protectedProcedure\n      .input(z.object({ leadId: z.number() }))', '    byLead: protectedProcedure.use(activitiesViewScope)\n      .input(z.object({ leadId: z.number() }))', 1)
r = r.replace('      .query(async ({ ctx, input }) => {\n        // ── ROW-LEVEL SECURITY ──\n        if (isTechnicalAccountManagerRole(ctx.user.role)) {', '      .query(async ({ ctx, input }) => {\n        await assertLeadPermissionScope((ctx as any).permissionDecision, ctx.user as any, input.leadId, `Lead #${input.leadId} (activities)`);\n        // ── ROW-LEVEL SECURITY ──\n        if (isTechnicalAccountManagerRole(ctx.user.role)) {', 1)
r = r.replace('    byUser: protectedProcedure\n      .input(z.object({ userId: z.number().optional(), limit: z.number().default(20) }))', '    byUser: protectedProcedure.use(activitiesViewScope)\n      .input(z.object({ userId: z.number().optional(), limit: z.number().default(20) }))', 1)
r = r.replace('        return getActivitiesByUser(userId, input.limit);', '        const dec = (ctx as any).permissionDecision;\n        const scopeSql = buildLeadScopeCondition(dec.scope, ctx.user as any, "l.ownerId");\n        return getActivitiesByUserScoped(userId, input.limit, scopeSql);', 1)
r = r.replace('    create: notMediaBuyerProcedure\n      .input(\n        z.object({\n          leadId: z.number(),', '    create: notMediaBuyerProcedure.use(activitiesCreateScope)\n      .input(\n        z.object({\n          leadId: z.number(),', 1)
r = r.replace('      .mutation(async ({ ctx, input }) => {\n        // ── ROW-LEVEL SECURITY ──\n        if (isSalesAgentRole(ctx.user.role)) {', '      .mutation(async ({ ctx, input }) => {\n        await assertLeadPermissionScope((ctx as any).permissionDecision, ctx.user as any, input.leadId, `Lead #${input.leadId} (activity create)`);\n        // ── ROW-LEVEL SECURITY ──\n        if (isSalesAgentRole(ctx.user.role)) {', 1)
r = r.replace('    update: notMediaBuyerProcedure\n      .input(', '    update: notMediaBuyerProcedure.use(activitiesEditScope)\n      .input(', 1)
r = r.replace('      .mutation(({ input }) => {\n        const { id, ...data } = input;\n        return updateActivity(id, data as any);\n      }),', '      .mutation(async ({ ctx, input }) => {\n        const existing = await getActivityById(input.id);\n        await assertActivityPermissionScope((ctx as any).permissionDecision, ctx.user as any, existing);\n        const { id, ...data } = input;\n        return updateActivity(id, data as any);\n      }),', 1)
r = r.replace('    delete: notMediaBuyerProcedure\n      .input(z.object({ id: z.number() }))', '    delete: notMediaBuyerProcedure.use(activitiesDeleteScope)\n      .input(z.object({ id: z.number() }))', 1)
r = r.replace('        const existing = await getActivityById(input.id);\n        await deleteActivity(input.id, ctx.user.id);', '        const existing = await getActivityById(input.id);\n        await assertActivityPermissionScope((ctx as any).permissionDecision, ctx.user as any, existing);\n        await deleteActivity(input.id, ctx.user.id);', 1)

# Client Tasks.
r = r.replace('    assignedContext: taskOpsProcedure\n', '    assignedContext: taskOpsProcedure.use(tasksViewScope)\n', 1)
r = r.replace('      .query(async ({ input, ctx }) => getAssignedTaskContext({ id: Number(ctx.user.id), role: normalizeUserRole(ctx.user.role), teamId: ctx.user.teamId }, input.taskId)),', '      .query(async ({ input, ctx }) => {\n        const task = await getAssignedTaskContext({ id: Number(ctx.user.id), role: normalizeUserRole(ctx.user.role), teamId: ctx.user.teamId }, input.taskId);\n        await assertTaskPermissionScope((ctx as any).permissionDecision, ctx.user as any, task, `Task #${input.taskId}`);\n        return task;\n      }),', 1)
r = r.replace('    list: taskOpsProcedure\n', '    list: taskOpsProcedure.use(tasksViewScope)\n', 1)
r = r.replace('        const rows = await getClientTasks(input.clientId);', '        const rows = await getClientTasks(input.clientId);\n        const scopedRows = await filterTasksByPermissionScope((ctx as any).permissionDecision, ctx.user as any, rows as any[]);', 1)
r = r.replace('          return (rows as any[]).filter((row) => Number(row.assignedTo ?? 0) === Number(ctx.user.id));', '          return scopedRows.filter((row: any) => Number(row.assignedTo ?? 0) === Number(ctx.user.id));', 1)
r = r.replace('        return rows;\n      }),\n\n    referenceStorageReadiness:', '        return scopedRows;\n      }),\n\n    referenceStorageReadiness:', 1)
r = r.replace('    create: clientWriteProcedure\n      .input(z.object({\n        clientId:', '    create: clientWriteProcedure.use(tasksCreateScope)\n      .input(z.object({\n        clientId:', 1)
r = r.replace('      .mutation(async ({ input, ctx }) => {\n        await assertAccountManagementClientAccess(ctx, input.clientId, "client.update");', '      .mutation(async ({ input, ctx }) => {\n        await assertTaskCreatePermissionScope((ctx as any).permissionDecision, ctx.user as any, input.clientId, input.assignedTo);\n        await assertAccountManagementClientAccess(ctx, input.clientId, "client.update");', 1)
r = r.replace('    update: taskOpsProcedure\n', '    update: taskOpsProcedure.use(tasksEditScope)\n', 1)
r = r.replace('        const meta: any = await getClientTaskMeta(input.id);\n        const role = normalizeUserRole(ctx.user.role);', '        const meta: any = await getClientTaskMeta(input.id);\n        await assertTaskPermissionScope((ctx as any).permissionDecision, ctx.user as any, meta);\n        if (input.data.assignedTo !== undefined) {\n          const { evaluatePermission } = await import("./security/permissionEngine");\n          const assignDecision = await evaluatePermission(ctx.user as any, "tasks.assign");\n          if (!assignDecision.allowed) throw new TRPCError({ code: "FORBIDDEN", message: "Permission denied: tasks.assign" });\n          await assertTaskPermissionScope(assignDecision as any, ctx.user as any, meta, `Task #${input.id} (assign)`);\n        }\n        const role = normalizeUserRole(ctx.user.role);', 1)

# Contracts.
r = r.replace('    getContracts: clientOpsProcedure\n', '    getContracts: clientOpsProcedure.use(contractsViewScope)\n', 1)
r = r.replace('        await assertAccountManagementClientAccess(ctx, input.clientId);\n        return getContractsByClient(input.clientId);', '        await assertAccountManagementClientAccess(ctx, input.clientId);\n        const rows = await getContractsByClient(input.clientId);\n        return filterContractsByPermissionScope((ctx as any).permissionDecision, ctx.user as any, rows as any[]);', 1)
r = r.replace('    createContract: clientWriteProcedure\n', '    createContract: clientWriteProcedure.use(contractsCreateScope)\n', 1)
r = r.replace('        await assertAccountManagementClientAccess(ctx, input.clientId, "contract.create");\n        await assertValidRenewalAssignment(', '        await assertContractCreatePermissionScope((ctx as any).permissionDecision, ctx.user as any, input.clientId, input.renewalAssignedTo);\n        await assertAccountManagementClientAccess(ctx, input.clientId, "contract.create");\n        await assertValidRenewalAssignment(', 1)
r = r.replace('    updateContract: clientWriteProcedure\n', '    updateContract: clientWriteProcedure.use(contractsEditScope)\n', 1)
r = r.replace('        const existing = await assertAccountManagementContractAccess(ctx, id, "contract.update");\n        if (Object.prototype.hasOwnProperty.call(data, "renewalAssignedTo")) {', '        const existing = await assertAccountManagementContractAccess(ctx, id, "contract.update");\n        await assertContractPermissionScope((ctx as any).permissionDecision, ctx.user as any, existing);\n        if (Object.prototype.hasOwnProperty.call(data, "renewalAssignedTo")) {', 1)

if "ADVANCED_PERMISSIONS_PHASE3B_V1" not in r:
    r = r.replace('  // ─── Activities (with row-level security) ─────────────────────────────────\n', '  // ADVANCED_PERMISSIONS_PHASE3B_V1\n  // ─── Activities (with row-level security) ─────────────────────────────────\n', 1)

rp.write_text(r)
print(f"Phase 3B applied to {TARGET}")
print(f"Backup: {BACKUP}")
