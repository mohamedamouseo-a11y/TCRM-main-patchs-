#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.cwd()
TRPC = ROOT / "server" / "_core" / "trpc.ts"
POLICY = ROOT / "server" / "security" / "corePermissionPolicy.ts"
TEST = ROOT / "server" / "security" / "corePermissionPolicy.test.ts"

if not TRPC.exists():
    raise SystemExit(f"ERROR: missing {TRPC}")

policy_text = r'''import type { PermissionKey } from "./permissionCatalog";

type ProcedureType = "query" | "mutation" | "subscription" | string;

type CorePermissionModule = "leads" | "deals" | "clients";

const CORE_MODULES = new Set<CorePermissionModule>(["leads", "deals", "clients"]);

function moduleFromPath(path: string): CorePermissionModule | null {
  const module = String(path || "").split(".", 1)[0] as CorePermissionModule;
  return CORE_MODULES.has(module) ? module : null;
}

function operationFromPath(path: string): string {
  return String(path || "")
    .split(".")
    .slice(1)
    .join(".")
    .replace(/[^a-zA-Z0-9]/g, "")
    .toLowerCase();
}

function hasAny(value: string, words: readonly string[]) {
  return words.some((word) => value.includes(word));
}

/**
 * Transitional server-side permission policy for the three core CRM modules.
 *
 * This is deliberately centralized at the protectedProcedure boundary so a
 * missed router-level guard cannot silently expose a core CRM operation. It
 * does NOT replace row/scope filtering; it only selects the required
 * permission key for the operation. Row-level scope remains a separate layer.
 */
export function resolveCorePermissionKey(path: string, type: ProcedureType): PermissionKey | null {
  const module = moduleFromPath(path);
  if (!module) return null;

  const operation = operationFromPath(path);

  if (hasAny(operation, ["export", "downloadexcel", "downloadcsv"])) {
    return `${module}.export` as PermissionKey;
  }

  if (module === "leads" && hasAny(operation, ["import", "uploadexcel", "uploadcsv"])) {
    return "leads.import";
  }

  if (type === "query" || type === "subscription") {
    return `${module}.view` as PermissionKey;
  }

  if (module === "leads" && hasAny(operation, ["reassign", "transferassignment"])) {
    return "leads.reassign";
  }

  if (module === "leads" && hasAny(operation, ["assign", "claimlead"])) {
    return "leads.assign";
  }

  if (module === "leads" && hasAny(operation, ["restore", "undelete"])) {
    return "leads.restore";
  }

  if (hasAny(operation, ["delete", "remove", "purge", "trash"])) {
    return `${module}.delete` as PermissionKey;
  }

  if (hasAny(operation, ["create", "add", "new", "convert"])) {
    return `${module}.create` as PermissionKey;
  }

  // Existing core mutation names include status/stage/move/update-style verbs.
  // Defaulting remaining authenticated mutations to edit is intentionally
  // restrictive versus the previous protectedProcedure-only behavior while
  // avoiding accidental exposure from a newly-added mutation.
  return `${module}.edit` as PermissionKey;
}
'''

policy_test_text = r'''import { describe, expect, it } from "vitest";
import { resolveCorePermissionKey } from "./corePermissionPolicy";

describe("corePermissionPolicy", () => {
  it("requires view for core CRM queries", () => {
    expect(resolveCorePermissionKey("leads.list", "query")).toBe("leads.view");
    expect(resolveCorePermissionKey("deals.getById", "query")).toBe("deals.view");
    expect(resolveCorePermissionKey("clients.search", "query")).toBe("clients.view");
  });

  it("maps core CRUD mutations", () => {
    expect(resolveCorePermissionKey("leads.create", "mutation")).toBe("leads.create");
    expect(resolveCorePermissionKey("deals.updateStage", "mutation")).toBe("deals.edit");
    expect(resolveCorePermissionKey("clients.delete", "mutation")).toBe("clients.delete");
  });

  it("maps lead-specific privileged operations", () => {
    expect(resolveCorePermissionKey("leads.assign", "mutation")).toBe("leads.assign");
    expect(resolveCorePermissionKey("leads.reassignBulk", "mutation")).toBe("leads.reassign");
    expect(resolveCorePermissionKey("leads.restore", "mutation")).toBe("leads.restore");
    expect(resolveCorePermissionKey("leads.importExcel", "mutation")).toBe("leads.import");
  });

  it("maps exports and ignores unrelated modules", () => {
    expect(resolveCorePermissionKey("leads.export", "query")).toBe("leads.export");
    expect(resolveCorePermissionKey("deals.exportCsv", "mutation")).toBe("deals.export");
    expect(resolveCorePermissionKey("tasks.list", "query")).toBeNull();
  });
});
'''

if POLICY.exists():
    existing = POLICY.read_text(encoding="utf-8")
    if existing != policy_text:
        raise SystemExit("ERROR: corePermissionPolicy.ts already exists with different content")
else:
    POLICY.write_text(policy_text, encoding="utf-8")

if TEST.exists():
    existing = TEST.read_text(encoding="utf-8")
    if existing != policy_test_text:
        raise SystemExit("ERROR: corePermissionPolicy.test.ts already exists with different content")
else:
    TEST.write_text(policy_test_text, encoding="utf-8")

text = TRPC.read_text(encoding="utf-8")

import_anchor = 'import { evaluatePermission } from "../security/permissionEngine";\n'
policy_import = 'import { resolveCorePermissionKey } from "../security/corePermissionPolicy";\n'
if policy_import not in text:
    if import_anchor not in text:
        raise SystemExit("ERROR: permissionEngine import anchor not found")
    text = text.replace(import_anchor, import_anchor + policy_import, 1)

middleware_marker = "// TCRM_CORE_API_PERMISSION_ENFORCEMENT_V1"
if middleware_marker not in text:
    anchor = 'export const protectedProcedure = moderatorDenyByDefault\n'
    if anchor not in text:
        raise SystemExit("ERROR: protectedProcedure anchor not found")
    middleware = r'''// TCRM_CORE_API_PERMISSION_ENFORCEMENT_V1
// Server-side fail-closed permission gate for the three core CRM modules.
// This closes the authenticated-user bypass at the tRPC procedure boundary.
// Row-level own/assigned/team scope filtering is intentionally handled by the
// existing scope layer and is not weakened here.
const coreApiPermissionEnforcement = t.middleware(async (opts) => {
  const permission = resolveCorePermissionKey(opts.path, opts.type);
  if (!permission) return opts.next();

  const decision = await evaluatePermission(
    opts.ctx.user!,
    permission,
    opts.type === "query" ? opts.ctx.req : undefined,
  );

  if (!decision.allowed) {
    throw new TRPCError({ code: "FORBIDDEN", message: `Permission denied: ${permission}` });
  }

  return opts.next({
    ctx: { ...opts.ctx, permissionDecision: decision } as any,
  });
});

'''
    text = text.replace(anchor, middleware + anchor, 1)

old_chain = '''export const protectedProcedure = moderatorDenyByDefault
  .use(centralMutationAudit as any)
  .use(developerAccessProtection as any)
  .use(developerDataProtection as any);'''
new_chain = '''export const protectedProcedure = moderatorDenyByDefault
  .use(centralMutationAudit as any)
  .use(coreApiPermissionEnforcement as any)
  .use(developerAccessProtection as any)
  .use(developerDataProtection as any);'''

if new_chain not in text:
    if old_chain not in text:
        raise SystemExit("ERROR: protectedProcedure chain changed; refusing unsafe patch")
    text = text.replace(old_chain, new_chain, 1)

required = [
    policy_import.strip(),
    middleware_marker,
    '.use(coreApiPermissionEnforcement as any)',
    'opts.type === "query" ? opts.ctx.req : undefined',
    'Permission denied: ${permission}',
]
for marker in required:
    if marker not in text:
        raise SystemExit(f"ERROR: missing required marker after patch: {marker}")

TRPC.write_text(text, encoding="utf-8")

print("PATCH=TCRM-PERMISSIONS-API-ENFORCEMENT-V1")
print("CORE_MODULES=leads,deals,clients")
print("SERVER_PERMISSION_GATE=YES")
print("REQUEST_CACHE_FOR_QUERIES=PRESERVED")
print("CENTRAL_AUDIT_DENIED_MUTATIONS=PRESERVED")
print("SCOPE_ENGINE=UNCHANGED")
print("DB_SCHEMA_CHANGED=NO")
print("DATA_CHANGED=NO")
print("FILES_CHANGED=server/_core/trpc.ts,server/security/corePermissionPolicy.ts,server/security/corePermissionPolicy.test.ts")
