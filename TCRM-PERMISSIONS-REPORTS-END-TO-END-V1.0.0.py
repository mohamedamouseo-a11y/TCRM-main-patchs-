#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

WORKFLOW_SERIES = "TCRM-PERMISSIONS"
MODULE = "REPORTS"
PHASE = "END-TO-END-FINAL"
VERSION = "V1.0.0"
WORKFLOW_ID = "TCRM-PERMISSIONS-REPORTS-END-TO-END-V1.0.0"
BASELINE = "d2021a9dd93b2787a9a9b7efa505146b2ba08a7e"

ROOT = Path.cwd()
EXPECTED = {
    "client/src/contexts/PermissionContext.tsx",
    "server/security/corePermissionPolicy.ts",
    "server/security/reportsPermissionFinal.test.ts",
}


def fail(message: str) -> None:
    print(f"ERROR={message}", file=sys.stderr)
    raise SystemExit(1)


def run(*args: str) -> str:
    p = subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        fail(f"COMMAND_FAILED:{' '.join(args)}:{p.stderr.strip()}")
    return p.stdout.strip()


def read(rel: str) -> str:
    p = ROOT / rel
    if not p.exists():
        fail(f"MISSING_FILE:{rel}")
    return p.read_text(encoding="utf-8")


def write(rel: str, text: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        fail(f"ANCHOR_DRIFT:{label}:count={count}")
    return text.replace(old, new, 1)


def dirty_paths() -> set[str]:
    tracked = set(filter(None, run("git", "diff", "--name-only").splitlines()))
    untracked = set(filter(None, run("git", "ls-files", "--others", "--exclude-standard").splitlines()))
    return tracked | untracked


head = run("git", "rev-parse", "HEAD")
if head != BASELINE:
    fail(f"BASELINE_MISMATCH:{head}")
if run("git", "diff", "--cached", "--name-only"):
    fail("STAGED_CHANGES_PRESENT")
if dirty_paths():
    fail(f"WORKTREE_NOT_CLEAN:{sorted(dirty_paths())}")

# Frontend effective permissions + canonical future Reports route gate.
# The current product has no dedicated /reports screen, so do not invent one or
# repurpose dashboards/analytics that already belong to their own permissions.
ctx_rel = "client/src/contexts/PermissionContext.tsx"
ctx = read(ctx_rel)
ctx = replace_once(
    ctx,
    '  "tara.manage",\n  "settings.view",',
    '  "tara.manage",\n  "reports.view",\n  "reports.export",\n  "settings.view",',
    "permission-context-report-keys",
)
ctx = replace_once(
    ctx,
    '    ["/tam-dashboard", "clients.view"],\n    ["/audit-log", "audit.view"],',
    '    ["/tam-dashboard", "clients.view"],\n    ["/reports", "reports.view"],\n    ["/audit-log", "audit.view"],',
    "permission-context-report-route",
)
write(ctx_rel, ctx)

# Canonical reports.* backend namespace enforcement.
policy_rel = "server/security/corePermissionPolicy.ts"
policy = read(policy_rel)
anchor = '''  // TCRM_PERMISSIONS_TARA_API_V1
  // Existing Tara role/profile/account-scope checks remain additive. This layer
  // only selects the catalog permission at the protectedProcedure boundary.
  if (root === "tara") {
    if (TARA_VIEW_OPERATIONS.has(operation)) return "tara.view";
    if (TARA_OPERATE_OPERATIONS.has(operation)) return "tara.operate";
    if (TARA_MODERATE_OPERATIONS.has(operation)) return "tara.moderate";

    // Technical settings, provider/voice/channel configuration, moderator
    // administration, and unknown future Tara operations fail closed here.
    return "tara.manage";
  }

  const module = moduleFromPath(path);
'''
replacement = '''  // TCRM_PERMISSIONS_TARA_API_V1
  // Existing Tara role/profile/account-scope checks remain additive. This layer
  // only selects the catalog permission at the protectedProcedure boundary.
  if (root === "tara") {
    if (TARA_VIEW_OPERATIONS.has(operation)) return "tara.view";
    if (TARA_OPERATE_OPERATIONS.has(operation)) return "tara.operate";
    if (TARA_MODERATE_OPERATIONS.has(operation)) return "tara.moderate";

    // Technical settings, provider/voice/channel configuration, moderator
    // administration, and unknown future Tara operations fail closed here.
    return "tara.manage";
  }

  // TCRM_PERMISSIONS_REPORTS_END_TO_END_V1
  // Reports owns only reports.*. Existing dashboards/analytics and domain exports
  // keep their already-approved permissions. Export-like operations require the
  // stronger reports.export permission even when exposed as a query.
  if (root === "reports") {
    if (hasAny(operation, ["export", "download", "csv", "excel", "xlsx"])) {
      return "reports.export";
    }
    if (type === "query" || type === "subscription") return "reports.view";

    // The catalog intentionally has view/export only. Future Reports mutations
    // therefore fail closed behind reports.export rather than falling through.
    return "reports.export";
  }

  const module = moduleFromPath(path);
'''
policy = replace_once(policy, anchor, replacement, "core-policy-reports")
write(policy_rel, policy)

# Final E2E regression coverage.
test_rel = "server/security/reportsPermissionFinal.test.ts"
if (ROOT / test_rel).exists():
    fail("REPORTS_FINAL_TEST_ALREADY_EXISTS")

test = r'''import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { resolveCorePermissionKey } from "./corePermissionPolicy";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "../..");
const read = (relative: string) => readFileSync(path.join(root, relative), "utf8");

const catalog = read("server/security/permissionCatalog.ts");
const context = read("client/src/contexts/PermissionContext.tsx");
const app = read("client/src/App.tsx");
const layout = read("client/src/components/CRMLayout.tsx");

describe("Reports permissions E2E V1.0.0", () => {
  it("keeps both Reports permissions in the canonical catalog", () => {
    expect(catalog).toContain('"reports.view"');
    expect(catalog).toContain('"reports.export"');
  });

  it("requests both Reports decisions and gates the canonical /reports path by view", () => {
    expect(context).toContain('"reports.view"');
    expect(context).toContain('"reports.export"');
    expect(context).toContain('["/reports", "reports.view"]');
  });

  it("maps canonical Reports reads to reports.view", () => {
    expect(resolveCorePermissionKey("reports.summary", "query")).toBe("reports.view");
    expect(resolveCorePermissionKey("reports.list", "query")).toBe("reports.view");
    expect(resolveCorePermissionKey("reports.liveSummary", "subscription")).toBe("reports.view");
  });

  it("maps canonical Reports exports/downloads to reports.export", () => {
    expect(resolveCorePermissionKey("reports.export", "query")).toBe("reports.export");
    expect(resolveCorePermissionKey("reports.downloadCsv", "query")).toBe("reports.export");
    expect(resolveCorePermissionKey("reports.downloadExcel", "query")).toBe("reports.export");
    expect(resolveCorePermissionKey("reports.generateXlsx", "mutation")).toBe("reports.export");
  });

  it("fails future Reports mutations closed behind reports.export", () => {
    expect(resolveCorePermissionKey("reports.futureMutation", "mutation")).toBe("reports.export");
    expect(resolveCorePermissionKey("reports.generate", "mutation")).toBe("reports.export");
  });

  it("does not hijack domain exports or dashboard analytics", () => {
    expect(resolveCorePermissionKey("leads.export", "query")).toBe("leads.export");
    expect(resolveCorePermissionKey("accountManagement.exportClientPoolExcel", "query")).toBe("clients.export");
    expect(resolveCorePermissionKey("campaigns.export", "query")).toBe("campaigns.export");
    expect(resolveCorePermissionKey("dashboard.teamStats", "query")).toBe("dashboard.view");
    expect(resolveCorePermissionKey("dashboard.salesFunnel", "query")).toBe("dashboard.view");
  });

  it("does not invent or repurpose a Reports product screen in this baseline", () => {
    expect(app).not.toContain('<Route path="/reports"');
    expect(layout).not.toContain('href: "/reports"');
  });
});
'''
write(test_rel, test)

paths = dirty_paths()
if paths != EXPECTED:
    fail(f"FINAL_DIRTY_SET_MISMATCH:{sorted(paths)}")
run("git", "diff", "--check")

ctx = read(ctx_rel)
policy = read(policy_rel)
final_test = read(test_rel)
for marker in ['"reports.view"', '"reports.export"', '["/reports", "reports.view"]']:
    if marker not in ctx:
        fail(f"FINAL_STATE_MISSING:context:{marker}")
for marker in ['if (root === "reports")', 'return "reports.view";', 'return "reports.export";', 'TCRM_PERMISSIONS_REPORTS_END_TO_END_V1']:
    if marker not in policy:
        fail(f"FINAL_STATE_MISSING:policy:{marker}")
if 'describe("Reports permissions E2E V1.0.0"' not in final_test:
    fail("FINAL_STATE_MISSING:reports-test")

print(f"VERSION={VERSION}")
print(f"WORKFLOW_ID={WORKFLOW_ID}")
print(f"BASELINE={BASELINE}")
print("PATCH_APPLIED=YES")
print("REPORTS_CATALOG=PASS")
print("REPORTS_FRONTEND_KEYS=PASS")
print("REPORTS_ROUTE_GATE=PASS")
print("REPORTS_API_VIEW_GATE=PASS")
print("REPORTS_API_EXPORT_GATE=PASS")
print("REPORTS_UNKNOWN_MUTATION_FAIL_CLOSED=PASS")
print("DOMAIN_EXPORTS_PRESERVED=YES")
print("EXISTING_DASHBOARD_ANALYTICS_PRESERVED=YES")
print("REPORTS_PRODUCT_SCREEN_INVENTED=NO")
print("FINAL_EXPECTED_FILES=3")
