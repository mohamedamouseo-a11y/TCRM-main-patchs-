import type { AccessCondition, AccessDecision, AccessEffect, AccessScope } from "@shared/accessControl";

export interface AccessCandidate {
  source: "user_override" | "temporary_grant" | "role_permission" | "legacy_role_bridge";
  sourceId?: number | string | null;
  effect: AccessEffect;
  scope: AccessScope;
  conditions?: AccessCondition[] | null;
}

export interface AccessEvaluationInput {
  permission: string;
  user: Record<string, unknown>;
  resource?: Record<string, unknown> | null;
  context?: Record<string, unknown> | null;
  candidates: AccessCandidate[];
}

const SCOPE_RANK: Record<AccessScope, number> = {
  own: 1,
  assigned: 2,
  team: 3,
  department: 4,
  branch: 5,
  custom: 6,
  all: 7,
};

const SOURCE_RANK: Record<AccessCandidate["source"], number> = {
  role_permission: 1,
  legacy_role_bridge: 2,
  temporary_grant: 3,
  user_override: 4,
};

function valueAtPath(input: AccessEvaluationInput, path: string): unknown {
  const [root, ...parts] = path.split(".");
  let value: unknown =
    root === "user" ? input.user :
    root === "resource" ? input.resource :
    root === "context" ? input.context : undefined;

  for (const part of parts) {
    if (!value || typeof value !== "object") return undefined;
    value = (value as Record<string, unknown>)[part];
  }
  return value;
}

function matchesCondition(input: AccessEvaluationInput, condition: AccessCondition): boolean {
  const left = valueAtPath(input, condition.left);
  const right = condition.right;

  switch (condition.operator) {
    case "eq": return left === right;
    case "neq": return left !== right;
    case "in": return Array.isArray(right) && right.includes(left);
    case "not_in": return Array.isArray(right) && !right.includes(left);
    case "lt": return Number(left) < Number(right);
    case "lte": return Number(left) <= Number(right);
    case "gt": return Number(left) > Number(right);
    case "gte": return Number(left) >= Number(right);
    case "exists":
      return right === false
        ? left === undefined || left === null
        : left !== undefined && left !== null;
    default:
      return false;
  }
}

function matchesCandidate(input: AccessEvaluationInput, candidate: AccessCandidate) {
  return !candidate.conditions?.length || candidate.conditions.every((condition) => matchesCondition(input, condition));
}

function sortCandidates(a: AccessCandidate, b: AccessCandidate) {
  const sourceDelta = SOURCE_RANK[b.source] - SOURCE_RANK[a.source];
  return sourceDelta || SCOPE_RANK[b.scope] - SCOPE_RANK[a.scope];
}

export function evaluateAccessCandidates(input: AccessEvaluationInput): AccessDecision {
  const matched = input.candidates.filter((candidate) => matchesCandidate(input, candidate));

  const denies = matched.filter((candidate) => candidate.effect === "deny").sort(sortCandidates);
  if (denies.length) {
    return {
      allowed: false,
      effect: "deny",
      permission: input.permission,
      scope: denies[0].scope,
      reason: "explicit_deny",
      source: denies[0].source,
      matchedPolicies: denies.map((candidate) => ({
        source: candidate.source,
        sourceId: candidate.sourceId ?? null,
        effect: candidate.effect,
        scope: candidate.scope,
      })),
    };
  }

  const allows = matched.filter((candidate) => candidate.effect === "allow").sort(sortCandidates);
  if (allows.length) {
    const widestScope = [...allows].sort((a, b) => SCOPE_RANK[b.scope] - SCOPE_RANK[a.scope])[0].scope;
    return {
      allowed: true,
      effect: "allow",
      permission: input.permission,
      scope: widestScope,
      reason: "matching_allow",
      source: allows[0].source,
      matchedPolicies: allows.map((candidate) => ({
        source: candidate.source,
        sourceId: candidate.sourceId ?? null,
        effect: candidate.effect,
        scope: candidate.scope,
      })),
    };
  }

  return {
    allowed: false,
    effect: "deny",
    permission: input.permission,
    scope: null,
    reason: input.candidates.length ? "conditions_not_met" : "no_matching_policy",
    source: "default_deny",
    matchedPolicies: [],
  };
}
