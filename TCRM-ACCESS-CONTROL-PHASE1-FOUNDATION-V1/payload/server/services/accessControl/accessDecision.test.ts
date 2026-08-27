import { describe, expect, it } from "vitest";
import { evaluateAccessCandidates } from "./accessDecision";

describe("accessDecision", () => {
  it("defaults to deny", () => {
    const result = evaluateAccessCandidates({ permission: "sales.leads.view", user: { id: 1 }, candidates: [] });
    expect(result.allowed).toBe(false);
    expect(result.reason).toBe("no_matching_policy");
  });

  it("explicit deny wins over allow", () => {
    const result = evaluateAccessCandidates({
      permission: "sales.leads.export",
      user: { id: 1 },
      candidates: [
        { source: "role_permission", effect: "allow", scope: "all" },
        { source: "user_override", effect: "deny", scope: "all" },
      ],
    });
    expect(result.allowed).toBe(false);
    expect(result.reason).toBe("explicit_deny");
    expect(result.source).toBe("user_override");
  });

  it("uses widest matching allow scope", () => {
    const result = evaluateAccessCandidates({
      permission: "clients.records.view",
      user: { id: 1 },
      candidates: [
        { source: "role_permission", effect: "allow", scope: "team" },
        { source: "temporary_grant", effect: "allow", scope: "department" },
      ],
    });
    expect(result.allowed).toBe(true);
    expect(result.scope).toBe("department");
  });

  it("supports safe ABAC conditions", () => {
    const result = evaluateAccessCandidates({
      permission: "marketing.campaigns.budget_change",
      user: { id: 1, department: "Marketing" },
      resource: { budget: 9000 },
      candidates: [{
        source: "role_permission",
        effect: "allow",
        scope: "department",
        conditions: [
          { left: "user.department", operator: "eq", right: "Marketing" },
          { left: "resource.budget", operator: "lte", right: 10000 },
        ],
      }],
    });
    expect(result.allowed).toBe(true);
  });

  it("denies when conditions fail", () => {
    const result = evaluateAccessCandidates({
      permission: "marketing.campaigns.budget_change",
      user: { id: 1 },
      resource: { budget: 50000 },
      candidates: [{
        source: "role_permission",
        effect: "allow",
        scope: "department",
        conditions: [{ left: "resource.budget", operator: "lt", right: 10000 }],
      }],
    });
    expect(result.allowed).toBe(false);
    expect(result.reason).toBe("conditions_not_met");
  });
});
