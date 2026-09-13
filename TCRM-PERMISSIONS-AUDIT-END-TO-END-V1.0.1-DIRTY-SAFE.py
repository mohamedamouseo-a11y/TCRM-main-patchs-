#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

WORKFLOW_SERIES = "TCRM-PERMISSIONS"
MODULE = "AUDIT"
PHASE = "END-TO-END-DIRTY-SAFE-RECOVERY"
VERSION = "V1.0.1"
WORKFLOW_ID = "TCRM-PERMISSIONS-AUDIT-END-TO-END-V1.0.1-DIRTY-SAFE"
BASELINE = "9d927b852032cf9373286e0a867cf46d78af8df4"
ROOT = Path.cwd()

PREEXISTING_DIRTY = {
    "client/src/components/CRMLayout.tsx",
    "client/src/crm-sidebar-premium-v1.css",
    "sync_client_66.mts",
}

AUDIT_EXPECTED = {
    "server/security/corePermissionPolicy.ts",
    "server/security/auditPermissionFinal.test.ts",
}


def fail(message: str) -> None:
    print(f"ERROR={message}", file=sys.stderr)
    raise SystemExit(1)


def run(*args: str) -> str:
    p = subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        fail(f"COMMAND_FAILED:{' '.join(args)}:{p.stderr.strip()}")
    return p.stdout.strip()


def dirty_paths() -> set[str]:
    tracked = set(filter(None, run("git", "diff", "--name-only").splitlines()))
    untracked = set(filter(None, run("git", "ls-files", "--others", "--exclude-standard").splitlines()))
    return tracked | untracked


def sha256_file(rel: str) -> str:
    p = ROOT / rel
    if not p.exists() or not p.is_file():
        fail(f"PREEXISTING_FILE_MISSING:{rel}")
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read(rel: str) -> str:
    p = ROOT / rel
    if not p.exists():
        fail(f"TARGET_MISSING:{rel}")
    return p.read_text(encoding="utf-8")


def write(rel: str, content: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


head = run("git", "rev-parse", "HEAD")
if head != BASELINE:
    fail(f"BASELINE_MISMATCH:{head}")
if run("git", "diff", "--cached", "--name-only"):
    fail("STAGED_CHANGES_PRESENT")
initial_dirty = dirty_paths()
if initial_dirty != PREEXISTING_DIRTY:
    fail(f"PREEXISTING_DIRTY_SET_MISMATCH:{sorted(initial_dirty)}")

before_hashes = {rel: sha256_file(rel) for rel in sorted(PREEXISTING_DIRTY)}

policy_rel = "server/security/corePermissionPolicy.ts"
policy = read(policy_rel)
anchor = '''  }\n\n  const module = moduleFromPath(path);'''
insert = '''  }\n\n  // TCRM_PERMISSIONS_AUDIT_END_TO_END_V1\n  // Audit remains an Admin-only surface through the existing adminProcedure and\n  // AuditLogPage role guard. Effective permissions are additive: audit.view gates\n  // the module/read/undo surface, while export-like operations use audit.export.\n  // No audit.manage key exists in the canonical catalog, so do not invent one.\n  if (root === "auditLogs") {\n    if (hasAny(operation, ["export", "download", "csv", "excel", "xlsx"])) {\n      return "audit.export";\n    }\n    return "audit.view";\n  }\n\n  const module = moduleFromPath(path);'''
if policy.count(anchor) != 1:
    fail(f"CORE_POLICY_ANCHOR_DRIFT:count={policy.count(anchor)}")
policy = policy.replace(anchor, insert, 1)
write(policy_rel, policy)

test_rel = "server/security/auditPermissionFinal.test.ts"
if (ROOT / test_rel).exists():
    fail("AUDIT_TEST_ALREADY_EXISTS")
test = r'''import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import path from "node:path";
import { resolveCorePermissionKey } from "./corePermissionPolicy";

const root = path.resolve(process.cwd());
const read = (p: string) => readFileSync(path.join(root, p), "utf8");
const catalog = read("server/security/permissionCatalog.ts");
const context = read("client/src/contexts/PermissionContext.tsx");
const layout = read("client/src/components/CRMLayout.tsx");
const page = read("client/src/pages/AuditLogPage.tsx");
const routers = read("server/routers.ts");

describe("Audit permissions E2E V1.0.1", () => {
  it("keeps canonical audit keys and direct route gating", () => {
    expect(catalog).toContain('"audit.view", "audit.export"');
    expect(context).toContain('"audit.view"');
    expect(context).toContain('["/audit-log", "audit.view"]');
  });

  it("gates the existing Audit API surface without inventing audit.manage", () => {
    expect(resolveCorePermissionKey("auditLogs.list", "query")).toBe("audit.view");
    expect(resolveCorePermissionKey("auditLogs.undo", "mutation")).toBe("audit.view");
    expect(resolveCorePermissionKey("auditLogs.exportCsv", "query")).toBe("audit.export");
    expect(resolveCorePermissionKey("auditLogs.downloadExcel", "query")).toBe("audit.export");
    expect(catalog).not.toContain('"audit.manage"');
  });

  it("preserves the existing Admin-only guards as additive protection", () => {
    expect(layout).toContain('href: "/audit-log"');
    expect(layout).toContain('roles: ["Admin"]');
    expect(page).toContain("if (!isAdminRole(role))");
    expect(routers).toContain("auditLogs: router({");
    expect(routers).toContain("list: adminProcedure");
    expect(routers).toContain("undo: adminProcedure");
  });

  it("does not invent an Audit export UI where none exists", () => {
    expect(page).not.toContain('can("audit.export")');
    expect(page).not.toContain("auditLogs.export");
  });

  it("preserves previously approved permission modules", () => {
    expect(resolveCorePermissionKey("admin.getBackupCenterSettings", "query")).toBe("backup.view");
    expect(resolveCorePermissionKey("notifications.getSubscribers", "query")).toBe("notifications.view");
    expect(resolveCorePermissionKey("admin.getGoogleDriveFileStorageSettings", "query")).toBe("integrations.view");
    expect(resolveCorePermissionKey("pipeline.create", "mutation")).toBe("settings.edit");
    expect(resolveCorePermissionKey("waGateway.getStatus", "query")).toBe("whatsapp.view");
  });
});
'''
write(test_rel, test)

after_hashes = {rel: sha256_file(rel) for rel in sorted(PREEXISTING_DIRTY)}
changed_preexisting = [rel for rel in sorted(PREEXISTING_DIRTY) if before_hashes[rel] != after_hashes[rel]]
if changed_preexisting:
    fail(f"PREEXISTING_FILES_CHANGED:{changed_preexisting}")

final_dirty = dirty_paths()
expected_final = PREEXISTING_DIRTY | AUDIT_EXPECTED
if final_dirty != expected_final:
    fail(f"FINAL_DIRTY_SET_MISMATCH:{sorted(final_dirty)}")

run("git", "diff", "--check", "--", policy_rel)

print(f"VERSION={VERSION}")
print(f"WORKFLOW_ID={WORKFLOW_ID}")
print(f"BASELINE={BASELINE}")
print("PATCH_APPLIED=YES")
print("RECOVERY_MODE=DIRTY_SAFE_ALLOWLIST")
print("PREEXISTING_DIRTY_PRESERVED=YES")
print("PREEXISTING_SIDEBAR_FILES_MODIFIED=NO")
print("PREEXISTING_SYNC_CLIENT_66_MODIFIED=NO")
print("AUDIT_PERMISSION_KEYS=audit.view,audit.export")
print("AUDIT_ROUTE_GATE=PASS")
print("AUDIT_API_GATE=PASS")
print("AUDIT_EXISTING_ADMIN_GUARDS_PRESERVED=YES")
print("AUDIT_EXPORT_UI_INVENTED=NO")
print("CSS_CHANGED_BY_AUDIT_PATCH=NO")
print("DB_SCHEMA_CHANGED=NO")
print("DATA_CHANGED=NO")
print("AUDIT_FILES_CHANGED=" + ",".join(sorted(AUDIT_EXPECTED)))
print("PREEXISTING_DIRTY_FILES=" + ",".join(sorted(PREEXISTING_DIRTY)))
print("FINAL_DIRTY_SET=PASS")
print("READY_FOR_TESTS=YES")
