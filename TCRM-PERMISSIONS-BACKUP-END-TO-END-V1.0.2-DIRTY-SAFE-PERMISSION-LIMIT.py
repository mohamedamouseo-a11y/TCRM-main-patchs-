#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

WORKFLOW_SERIES = "TCRM-PERMISSIONS"
MODULE = "BACKUP"
PHASE = "END-TO-END-DIRTY-SAFE-RUNTIME-RECOVERY"
VERSION = "V1.0.2"
WORKFLOW_ID = "TCRM-PERMISSIONS-BACKUP-END-TO-END-V1.0.2-DIRTY-SAFE-PERMISSION-LIMIT"
BASELINE = "846cbdbf610bd6d118b05272db76b262c701be6b"
ROOT = Path.cwd()

PREEXISTING_DIRTY = {
    "client/src/pages/LeadProfile.tsx",
    "client/src/lead-profile-premium-v2.css",
    "client/src/contexts/PermissionContext.tsx",
    "client/src/pages/AdminSettings.tsx",
    "client/src/components/BackupTab.tsx",
    "client/src/components/DatabaseBackupSettingsTab.tsx",
    "server/security/corePermissionPolicy.ts",
    "server/routes/tcrmDatabaseBackup.ts",
    "server/_core/index.ts",
    "server/security/backupPermissionFinal.test.ts",
}

HOTFIX_EXPECTED = {
    "server/_core/systemRouter.ts",
    "server/security/effectivePermissionsInputLimitHotfix.test.ts",
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

# Replace the brittle fixed request-size ceiling with the canonical catalog size.
# This keeps effectivePermissions bounded while allowing the UI to request every
# permission currently defined in PHASE1_PERMISSION_CATALOG.
router_rel = "server/_core/systemRouter.ts"
router = read(router_rel)
old = "permissions: z.array(z.enum(PHASE1_PERMISSION_CATALOG)).min(1).max(64),"
new = "permissions: z.array(z.enum(PHASE1_PERMISSION_CATALOG)).min(1).max(PHASE1_PERMISSION_CATALOG.length),"
count = router.count(old)
if count != 1:
    fail(f"SYSTEM_ROUTER_ANCHOR_DRIFT:count={count}")
router = router.replace(old, new, 1)
write(router_rel, router)

# Focused regression test: no future permission module should break all protected
# routes merely because the frontend legitimately requests the full catalog.
test_rel = "server/security/effectivePermissionsInputLimitHotfix.test.ts"
if (ROOT / test_rel).exists():
    fail("HOTFIX_TEST_ALREADY_EXISTS")
test = r'''import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import path from "node:path";
import { PHASE1_PERMISSION_CATALOG } from "./permissionCatalog";

const source = readFileSync(path.resolve(process.cwd(), "server/_core/systemRouter.ts"), "utf8");

describe("effectivePermissions input limit hotfix", () => {
  it("bounds requests by the canonical permission catalog instead of a stale magic number", () => {
    expect(PHASE1_PERMISSION_CATALOG.length).toBeGreaterThanOrEqual(65);
    expect(source).toContain(".max(PHASE1_PERMISSION_CATALOG.length)");
    expect(source).not.toContain(".max(64)");
  });
});
'''
write(test_rel, test)

after_hashes = {rel: sha256_file(rel) for rel in sorted(PREEXISTING_DIRTY)}
changed_preexisting = [rel for rel in sorted(PREEXISTING_DIRTY) if before_hashes[rel] != after_hashes[rel]]
if changed_preexisting:
    fail(f"PREEXISTING_FILES_CHANGED:{changed_preexisting}")

final_dirty = dirty_paths()
expected_final = PREEXISTING_DIRTY | HOTFIX_EXPECTED
if final_dirty != expected_final:
    fail(f"FINAL_DIRTY_SET_MISMATCH:{sorted(final_dirty)}")

run("git", "diff", "--check", "--", router_rel)

print(f"VERSION={VERSION}")
print(f"WORKFLOW_ID={WORKFLOW_ID}")
print(f"BASELINE={BASELINE}")
print("PATCH_APPLIED=YES")
print("RECOVERY_MODE=DIRTY_SAFE_ALLOWLIST")
print("PREEXISTING_DIRTY_PRESERVED=YES")
print("PREEXISTING_LEAD_PROFILE_FILES_MODIFIED=NO")
print("PREEXISTING_BACKUP_FILES_MODIFIED=NO")
print("EFFECTIVE_PERMISSIONS_LIMIT=CATALOG_LENGTH")
print("MAGIC_MAX_64_REMOVED=YES")
print("HOTFIX_FILES_CHANGED=" + ",".join(sorted(HOTFIX_EXPECTED)))
print("PREEXISTING_DIRTY_FILES=" + ",".join(sorted(PREEXISTING_DIRTY)))
print("FINAL_DIRTY_SET=PASS")
print("READY_FOR_TESTS=YES")
