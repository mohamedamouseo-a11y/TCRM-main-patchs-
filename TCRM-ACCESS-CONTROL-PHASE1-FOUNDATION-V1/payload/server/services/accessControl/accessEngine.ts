import { TRPCError } from "@trpc/server";
import type { AccessDecision } from "@shared/accessControl";
import { evaluateAccessCandidates } from "./accessDecision";
import { isAccessControlInstalled, listAccessCandidates, writeAccessDecisionLog } from "./accessStore";

export interface AccessCheckInput {
  user: {
    id: number;
    role?: string | null;
    teamId?: number | null;
    email?: string | null;
    [key: string]: unknown;
  };
  permission: string;
  resource?: Record<string, unknown> | null;
  context?: Record<string, unknown> | null;
  resourceType?: string | null;
  resourceId?: string | number | null;
  logDecision?: boolean;
}

export async function checkAccess(input: AccessCheckInput): Promise<AccessDecision> {
  if (!(await isAccessControlInstalled())) {
    return {
      allowed: false,
      effect: "deny",
      permission: input.permission,
      scope: null,
      reason: "access_control_not_configured",
      source: "default_deny",
      matchedPolicies: [],
    };
  }

  const candidates = await listAccessCandidates({
    userId: Number(input.user.id),
    legacyRole: input.user.role == null ? null : String(input.user.role),
    permissionKey: input.permission,
  });

  const decision = evaluateAccessCandidates({
    permission: input.permission,
    user: input.user,
    resource: input.resource,
    context: input.context,
    candidates,
  });

  if (input.logDecision) {
    await writeAccessDecisionLog({
      userId: Number(input.user.id),
      permissionKey: input.permission,
      resourceType: input.resourceType,
      resourceId: input.resourceId,
      effect: decision.effect,
      scope: decision.scope,
      source: decision.source,
      reason: decision.reason,
      matchedPolicies: decision.matchedPolicies,
    }).catch((error) => console.error("[AccessControl] decision log failed", error));
  }

  return decision;
}

export async function requireAccess(input: AccessCheckInput): Promise<AccessDecision> {
  const decision = await checkAccess({ ...input, logDecision: true });
  if (!decision.allowed) {
    throw new TRPCError({
      code: "FORBIDDEN",
      message: `Access denied: ${input.permission} (${decision.reason})`,
    });
  }
  return decision;
}
