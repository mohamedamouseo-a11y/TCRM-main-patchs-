// TCRM Advanced Permissions — Phase 3A Reviewed Fix V1
// Backend-enforced data-scope filters for Leads / Deals / Clients.
// Safe mappings only:
//   - Leads: own=ownerId, assigned=active lead_assignments, team=owner.teamId
//   - Deals: own=linked lead ownerId, assigned=linked lead active assignment, team=linked lead owner.teamId
//   - Clients: own/assigned=accountManagerId, team=accountManager.teamId (fallback to linked lead owner team only when no AM)
// Unsupported scopes (department / created_by / custom / none) deny by default.
import { sql } from "drizzle-orm";
import type { PermissionScope } from "./permissionCatalog";
import type { PermissionDecision, PermissionUser } from "./permissionEngine";

export type ScopeEntityKind = "lead" | "deal" | "client";

function userIdOf(user: PermissionUser): number {
  const id = Number(user.id);
  return Number.isFinite(id) && id > 0 ? id : 0;
}

function aliasFromOwnerColumn(ownerIdCol: string): string {
  const trimmed = String(ownerIdCol || "").trim();
  const dot = trimmed.lastIndexOf(".");
  return dot > 0 ? trimmed.slice(0, dot) : "leads";
}

async function getHandle() {
  const { getDb } = await import("../db");
  try {
    return await getDb();
  } catch {
    return null;
  }
}

export function buildLeadScopeCondition(scope: PermissionScope, user: PermissionUser, ownerIdCol = "ownerId") {
  const uid = userIdOf(user);
  const leadAlias = aliasFromOwnerColumn(ownerIdCol);
  if (scope === "all") return sql`1 = 1`;
  if (scope === "own") return sql`${sql.raw(ownerIdCol)} = ${uid}`;
  if (scope === "assigned") {
    return sql`EXISTS (
      SELECT 1 FROM lead_assignments la_scope
      WHERE la_scope.leadId = ${sql.raw(leadAlias)}.id
        AND la_scope.userId = ${uid}
        AND la_scope.isActive = 1
    )`;
  }
  if (scope === "team") {
    const teamId = Number(user.teamId ?? 0);
    if (!(Number.isInteger(teamId) && teamId > 0)) return sql`1 = 0`;
    return sql`EXISTS (
      SELECT 1 FROM users owner_scope
      WHERE owner_scope.id = ${sql.raw(ownerIdCol)}
        AND owner_scope.teamId = ${teamId}
        AND owner_scope.deletedAt IS NULL
    )`;
  }
  return sql`1 = 0`;
}

export function buildDealScopeCondition(scope: PermissionScope, user: PermissionUser, dealAlias = "d") {
  const uid = userIdOf(user);
  if (scope === "all") return sql`1 = 1`;
  if (scope === "own") {
    return sql`EXISTS (
      SELECT 1 FROM leads dl_scope
      WHERE dl_scope.id = ${sql.raw(dealAlias)}.leadId
        AND dl_scope.deletedAt IS NULL
        AND dl_scope.ownerId = ${uid}
    )`;
  }
  if (scope === "assigned") {
    return sql`EXISTS (
      SELECT 1 FROM leads dl_scope
      WHERE dl_scope.id = ${sql.raw(dealAlias)}.leadId
        AND dl_scope.deletedAt IS NULL
        AND EXISTS (
          SELECT 1 FROM lead_assignments dla_scope
          WHERE dla_scope.leadId = dl_scope.id
            AND dla_scope.userId = ${uid}
            AND dla_scope.isActive = 1
        )
    )`;
  }
  if (scope === "team") {
    const teamId = Number(user.teamId ?? 0);
    if (!(Number.isInteger(teamId) && teamId > 0)) return sql`1 = 0`;
    return sql`EXISTS (
      SELECT 1 FROM leads dl2_scope
      JOIN users dl2_owner ON dl2_owner.id = dl2_scope.ownerId
      WHERE dl2_scope.id = ${sql.raw(dealAlias)}.leadId
        AND dl2_scope.deletedAt IS NULL
        AND dl2_owner.teamId = ${teamId}
        AND dl2_owner.deletedAt IS NULL
    )`;
  }
  return sql`1 = 0`;
}

export function buildClientScopeCondition(scope: PermissionScope, user: PermissionUser, clientAlias = "clients") {
  const uid = userIdOf(user);
  if (scope === "all") return sql`1 = 1`;
  if (scope === "own" || scope === "assigned") {
    return sql`${sql.raw(clientAlias)}.accountManagerId = ${uid}`;
  }
  if (scope === "team") {
    const teamId = Number(user.teamId ?? 0);
    if (!(Number.isInteger(teamId) && teamId > 0)) return sql`1 = 0`;
    return sql`(
      EXISTS (
        SELECT 1 FROM users cm_owner_scope
        WHERE cm_owner_scope.id = ${sql.raw(clientAlias)}.accountManagerId
          AND cm_owner_scope.teamId = ${teamId}
          AND cm_owner_scope.deletedAt IS NULL
      )
      OR (
        ${sql.raw(clientAlias)}.accountManagerId IS NULL
        AND EXISTS (
          SELECT 1 FROM leads cl2_scope
          JOIN users cl2_owner ON cl2_owner.id = cl2_scope.ownerId
          WHERE cl2_scope.id = ${sql.raw(clientAlias)}.leadId
            AND cl2_scope.deletedAt IS NULL
            AND cl2_owner.teamId = ${teamId}
            AND cl2_owner.deletedAt IS NULL
        )
      )
    )`;
  }
  return sql`1 = 0`;
}

export function buildScopeConditionFor(kind: ScopeEntityKind, scope: PermissionScope, user: PermissionUser, alias?: string) {
  if (kind === "lead") return buildLeadScopeCondition(scope, user, alias ? `${alias}.ownerId` : "ownerId");
  if (kind === "deal") return buildDealScopeCondition(scope, user, alias || "d");
  return buildClientScopeCondition(scope, user, alias || "c");
}

async function ownerTeamMatches(ownerId: number, teamId: number): Promise<boolean> {
  if (!(ownerId > 0)) return false;
  const db = await getHandle();
  if (!db) return false;
  const rows: any = await db.execute(sql`SELECT teamId FROM users WHERE id = ${ownerId} AND deletedAt IS NULL LIMIT 1`);
  const row = (rows as any)[0]?.[0] as any;
  return row ? Number(row.teamId) === Number(teamId) : false;
}

async function leadOwnerId(leadId: number): Promise<number> {
  const db = await getHandle();
  if (!db || !(leadId > 0)) return 0;
  const rows: any = await db.execute(sql`SELECT ownerId FROM leads WHERE id = ${leadId} AND deletedAt IS NULL LIMIT 1`);
  return Number((rows as any)[0]?.[0]?.ownerId ?? 0);
}

async function hasActiveAssignment(leadId: number, userId: number): Promise<boolean> {
  const db = await getHandle();
  if (!db || !(leadId > 0)) return false;
  const rows: any = await db.execute(sql`SELECT id FROM lead_assignments WHERE leadId = ${leadId} AND userId = ${userId} AND isActive = 1 LIMIT 1`);
  return (((rows as any)[0] ?? []) as any[]).length > 0;
}

export async function isRowInScope(kind: ScopeEntityKind, decision: PermissionDecision, user: PermissionUser, row: any): Promise<boolean> {
  const scope = decision.scope;
  const uid = userIdOf(user);
  if (scope === "all") return true;
  if (scope === "none") return false;

  if (scope === "own") {
    if (kind === "lead") return Number(row?.ownerId) === uid;
    if (kind === "deal") return (await leadOwnerId(Number(row?.leadId))) === uid;
    return Number(row?.accountManagerId) === uid;
  }

  if (scope === "assigned") {
    if (kind === "lead") return hasActiveAssignment(Number(row?.id), uid);
    if (kind === "deal") return hasActiveAssignment(Number(row?.leadId), uid);
    return Number(row?.accountManagerId) === uid;
  }

  if (scope === "team") {
    const teamId = Number(user.teamId ?? 0);
    if (!(Number.isInteger(teamId) && teamId > 0)) return false;
    if (kind === "lead") return ownerTeamMatches(Number(row?.ownerId), teamId);
    if (kind === "deal") return ownerTeamMatches(await leadOwnerId(Number(row?.leadId)), teamId);
    if (row?.accountManagerId) return ownerTeamMatches(Number(row.accountManagerId), teamId);
    return ownerTeamMatches(await leadOwnerId(Number(row?.leadId)), teamId);
  }

  return false;
}

export function permissionScopeProcedureFactory(t: any, permission: string) {
  return t.middleware(async (opts: any) => {
    const user = opts.ctx?.user;
    if (!user) throw new Error("PERMISSION_AUTH_REQUIRED");
    const { TRPCError } = await import("@trpc/server");
    const { evaluatePermission } = await import("./permissionEngine");
    const decision = await evaluatePermission(user as PermissionUser, permission as any);
    if (!decision.allowed) {
      throw new TRPCError({ code: "FORBIDDEN", message: `Permission denied: ${permission}` });
    }
    return opts.next({ ctx: { ...opts.ctx, permissionDecision: decision } });
  });
}

export async function assertRowScope(kind: ScopeEntityKind, decision: PermissionDecision, user: PermissionUser, row: any, entityLabel: string) {
  const ok = await isRowInScope(kind, decision, user, row);
  if (!ok) {
    const { TRPCError } = await import("@trpc/server");
    throw new TRPCError({ code: "FORBIDDEN", message: `Access denied: ${entityLabel} is outside your permission scope` });
  }
  return true;
}
