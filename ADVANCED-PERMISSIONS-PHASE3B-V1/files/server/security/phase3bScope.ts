import { TRPCError } from "@trpc/server";
import type { PermissionDecision, PermissionUser } from "./permissionEngine";
import { isRowInScope } from "./phase3ScopeFilters";
import { getClientById, getLeadById } from "../db";

function uid(user: PermissionUser): number {
  const value = Number(user.id);
  return Number.isFinite(value) && value > 0 ? value : 0;
}

function deny(label: string): never {
  throw new TRPCError({ code: "FORBIDDEN", message: `Access denied: ${label} is outside your permission scope` });
}

export async function assertLeadPermissionScope(decision: PermissionDecision, user: PermissionUser, leadId: number, label = `Lead #${leadId}`) {
  if (decision.scope === "all") return true;
  const lead = await getLeadById(Number(leadId));
  if (!lead || !(await isRowInScope("lead", decision, user, lead))) deny(label);
  return true;
}

export async function assertClientPermissionScope(decision: PermissionDecision, user: PermissionUser, clientId: number, label = `Client #${clientId}`) {
  if (decision.scope === "all") return true;
  const client = await getClientById(Number(clientId));
  if (!client || !(await isRowInScope("client", decision, user, client))) deny(label);
  return true;
}

export async function assertActivityPermissionScope(decision: PermissionDecision, user: PermissionUser, activity: any) {
  if (!activity) deny("Activity");
  return assertLeadPermissionScope(decision, user, Number(activity.leadId), `Activity #${activity.id}`);
}

export async function isTaskInPermissionScope(decision: PermissionDecision, user: PermissionUser, task: any): Promise<boolean> {
  if (!decision.allowed) return false;
  if (decision.scope === "all") return true;
  if (decision.scope === "none") return false;
  if (decision.scope === "assigned") return Number(task?.assignedTo ?? 0) === uid(user);
  if (decision.scope === "own" || decision.scope === "team") {
    const client = await getClientById(Number(task?.clientId ?? 0));
    return !!client && isRowInScope("client", decision, user, client);
  }
  return false;
}

export async function assertTaskPermissionScope(decision: PermissionDecision, user: PermissionUser, task: any, label?: string) {
  if (!(await isTaskInPermissionScope(decision, user, task))) deny(label ?? `Task #${task?.id ?? "?"}`);
  return true;
}

export async function filterTasksByPermissionScope(decision: PermissionDecision, user: PermissionUser, tasks: any[]) {
  if (decision.scope === "all") return tasks;
  const allowed: any[] = [];
  for (const task of tasks) if (await isTaskInPermissionScope(decision, user, task)) allowed.push(task);
  return allowed;
}

export async function assertTaskCreatePermissionScope(decision: PermissionDecision, user: PermissionUser, clientId: number, assignedTo?: number | null) {
  if (decision.scope === "all") return true;
  if (decision.scope === "assigned") {
    if (Number(assignedTo ?? 0) !== uid(user)) deny("Task create assignment");
    return true;
  }
  if (decision.scope === "own" || decision.scope === "team") {
    return assertClientPermissionScope(decision, user, clientId, `Client #${clientId} (task create)`);
  }
  deny("Task create");
}

export async function isContractInPermissionScope(decision: PermissionDecision, user: PermissionUser, contract: any): Promise<boolean> {
  if (!decision.allowed) return false;
  if (decision.scope === "all") return true;
  if (decision.scope === "none") return false;
  if (decision.scope === "assigned") return Number(contract?.renewalAssignedTo ?? 0) === uid(user);
  if (decision.scope === "own" || decision.scope === "team") {
    const client = await getClientById(Number(contract?.clientId ?? 0));
    return !!client && isRowInScope("client", decision, user, client);
  }
  return false;
}

export async function assertContractPermissionScope(decision: PermissionDecision, user: PermissionUser, contract: any, label?: string) {
  if (!(await isContractInPermissionScope(decision, user, contract))) deny(label ?? `Contract #${contract?.id ?? "?"}`);
  return true;
}
