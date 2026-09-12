#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import subprocess
import sys
import urllib.request
from pathlib import Path

WORKFLOW_SERIES = "TCRM-PERMISSIONS"
MODULE = "BACKUP"
PHASE = "END-TO-END-DIRTY-SAFE-RECOVERY"
VERSION = "V1.0.1"
WORKFLOW_ID = "TCRM-PERMISSIONS-BACKUP-END-TO-END-V1.0.1-DIRTY-SAFE"
BASELINE = "846cbdbf610bd6d118b05272db76b262c701be6b"
ROOT = Path.cwd()
ORIGINAL_PATCH_URL = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TCRM-main-patchs-/main/TCRM-PERMISSIONS-BACKUP-END-TO-END-V1.0.0.py"

PREEXISTING_DIRTY = {
    "client/src/pages/LeadProfile.tsx",
    "client/src/lead-profile-premium-v2.css",
}

BACKUP_EXPECTED = {
    "client/src/contexts/PermissionContext.tsx",
    "client/src/pages/AdminSettings.tsx",
    "client/src/components/BackupTab.tsx",
    "client/src/components/DatabaseBackupSettingsTab.tsx",
    "server/security/corePermissionPolicy.ts",
    "server/routes/tcrmDatabaseBackup.ts",
    "server/_core/index.ts",
    "server/security/backupPermissionFinal.test.ts",
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


# Strict preflight: exact baseline, no staged changes, and ONLY the two already-
# validated Lead Profile Premium V2 files may be dirty before Backup work.
head = run("git", "rev-parse", "HEAD")
if head != BASELINE:
    fail(f"BASELINE_MISMATCH:{head}")
if run("git", "diff", "--cached", "--name-only"):
    fail("STAGED_CHANGES_PRESENT")
initial_dirty = dirty_paths()
if initial_dirty != PREEXISTING_DIRTY:
    fail(f"PREEXISTING_DIRTY_SET_MISMATCH:{sorted(initial_dirty)}")

before_hashes = {rel: sha256_file(rel) for rel in sorted(PREEXISTING_DIRTY)}

# Reuse the already-reviewed Backup V1.0.0 implementation. Only its safety
# bookkeeping is adapted in-memory so it can coexist with the exact preexisting
# Lead Profile Premium V2 dirty set. No Backup product logic is rewritten here.
try:
    with urllib.request.urlopen(ORIGINAL_PATCH_URL, timeout=30) as response:
        source = response.read().decode("utf-8")
except Exception as exc:
    fail(f"ORIGINAL_PATCH_DOWNLOAD_FAILED:{type(exc).__name__}:{exc}")

replacements = [
    (
        'PHASE = "END-TO-END"',
        'PHASE = "END-TO-END-DIRTY-SAFE-RECOVERY"',
        "phase",
    ),
    (
        'VERSION = "V1.0.0"',
        'VERSION = "V1.0.1"',
        "version",
    ),
    (
        'WORKFLOW_ID = "TCRM-PERMISSIONS-BACKUP-END-TO-END-V1.0.0"',
        'WORKFLOW_ID = "TCRM-PERMISSIONS-BACKUP-END-TO-END-V1.0.1-DIRTY-SAFE"',
        "workflow-id",
    ),
    (
        'if dirty_paths():\n    fail(f"WORKTREE_NOT_CLEAN:{sorted(dirty_paths())}")',
        'ALLOWED_PREEXISTING_DIRTY = {"client/src/pages/LeadProfile.tsx", "client/src/lead-profile-premium-v2.css"}\nif dirty_paths() != ALLOWED_PREEXISTING_DIRTY:\n    fail(f"PREEXISTING_DIRTY_SET_MISMATCH:{sorted(dirty_paths())}")',
        "preflight-dirty-check",
    ),
    (
        'if dirty_paths() != EXPECTED:\n    fail(f"FINAL_DIRTY_SET_MISMATCH:{sorted(dirty_paths())}")\nrun("git", "diff", "--check")',
        'if dirty_paths() != (EXPECTED | ALLOWED_PREEXISTING_DIRTY):\n    fail(f"FINAL_DIRTY_SET_MISMATCH:{sorted(dirty_paths())}")\nrun("git", "diff", "--check", "--", *sorted(EXPECTED - {"server/security/backupPermissionFinal.test.ts"}))',
        "final-dirty-check",
    ),
]

for old, new, label in replacements:
    count = source.count(old)
    if count != 1:
        fail(f"RECOVERY_SOURCE_DRIFT:{label}:count={count}")
    source = source.replace(old, new, 1)

namespace = {"__name__": "__main__", "__file__": "/tmp/TCRM-PERMISSIONS-BACKUP-END-TO-END-V1.0.0.py"}
try:
    exec(compile(source, namespace["__file__"], "exec"), namespace, namespace)
except SystemExit:
    raise
except Exception as exc:
    fail(f"ORIGINAL_PATCH_EXECUTION_FAILED:{type(exc).__name__}:{exc}")

# Byte-for-byte preservation check for unrelated Lead Profile Premium V2 work.
after_hashes = {rel: sha256_file(rel) for rel in sorted(PREEXISTING_DIRTY)}
changed_preexisting = [rel for rel in sorted(PREEXISTING_DIRTY) if before_hashes[rel] != after_hashes[rel]]
if changed_preexisting:
    fail(f"PREEXISTING_LEAD_PROFILE_FILES_CHANGED:{changed_preexisting}")

final_dirty = dirty_paths()
expected_final = PREEXISTING_DIRTY | BACKUP_EXPECTED
if final_dirty != expected_final:
    fail(f"RECOVERY_FINAL_DIRTY_SET_MISMATCH:{sorted(final_dirty)}")

tracked_backup = sorted(BACKUP_EXPECTED - {"server/security/backupPermissionFinal.test.ts"})
run("git", "diff", "--check", "--", *tracked_backup)

print("RECOVERY_MODE=DIRTY_SAFE_ALLOWLIST")
print("PREEXISTING_DIRTY_PRESERVED=YES")
print("PREEXISTING_LEAD_PROFILE_FILES_MODIFIED=NO")
print("LEAD_PROFILE_PREMIUM_V2_PRESERVED=YES")
print("PREEXISTING_DIRTY_FILES=" + ",".join(sorted(PREEXISTING_DIRTY)))
print("BACKUP_FILES_EXPECTED=" + ",".join(sorted(BACKUP_EXPECTED)))
print("FINAL_DIRTY_SET=PASS")
print("READY_FOR_TESTS=YES")
