#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import subprocess
import sys
import urllib.request
from pathlib import Path

WORKFLOW_SERIES = "TCRM-PERMISSIONS"
MODULE = "USERS"
PHASE = "END-TO-END-DIRTY-SAFE-RECOVERY"
VERSION = "V1.0.1"
WORKFLOW_ID = "TCRM-PERMISSIONS-USERS-END-TO-END-V1.0.1-DIRTY-SAFE"
BASELINE = "76147a3cc33efda0c54745bf68c639792c4c5a15"
SOURCE_PATCH_URL = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TCRM-main-patchs-/main/TCRM-PERMISSIONS-USERS-END-TO-END-V1.0.0.py"

ROOT = Path.cwd()
PREEXISTING_DIRTY = {
    "client/src/pages/LeadsList.tsx",
    "client/src/new-lead-premium-v1-3.css",
    "client/src/new-lead-premium-v1-4.css",
}
USERS_EXPECTED = {
    "client/src/contexts/PermissionContext.tsx",
    "client/src/pages/AdminSettings.tsx",
    "server/_core/trpc.ts",
    "server/security/corePermissionPolicy.ts",
    "server/security/usersPermissionFinal.test.ts",
}
FINAL_EXPECTED = PREEXISTING_DIRTY | USERS_EXPECTED


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


def digest(rel: str) -> str:
    p = ROOT / rel
    if not p.exists() or not p.is_file():
        fail(f"PREEXISTING_FILE_MISSING:{rel}")
    return hashlib.sha256(p.read_bytes()).hexdigest()


# Strict preflight: only the known New Lead working-tree files may already be dirty.
head = run("git", "rev-parse", "HEAD")
if head != BASELINE:
    fail(f"BASELINE_MISMATCH:{head}")
if run("git", "diff", "--cached", "--name-only"):
    fail("STAGED_CHANGES_PRESENT")
initial_dirty = dirty_paths()
if initial_dirty != PREEXISTING_DIRTY:
    fail(f"UNEXPECTED_PREEXISTING_DIRTY_STATE:{sorted(initial_dirty)}")

before_hashes = {rel: digest(rel) for rel in sorted(PREEXISTING_DIRTY)}

# Download the already-reviewed Users V1.0.0 patch. This recovery wrapper changes
# only its worktree-safety bookkeeping so the known New Lead files can coexist.
# The Users implementation itself remains byte-for-byte sourced from V1.0.0.
try:
    with urllib.request.urlopen(SOURCE_PATCH_URL, timeout=30) as response:
        source = response.read().decode("utf-8")
except Exception as exc:
    fail(f"SOURCE_PATCH_DOWNLOAD_FAILED:{exc}")

old_preflight = '''if dirty_paths():
    fail(f"WORKTREE_NOT_CLEAN:{sorted(dirty_paths())}")
'''
new_preflight = '''if dirty_paths() != {
    "client/src/pages/LeadsList.tsx",
    "client/src/new-lead-premium-v1-3.css",
    "client/src/new-lead-premium-v1-4.css",
}:
    fail(f"UNEXPECTED_PREEXISTING_DIRTY_STATE:{sorted(dirty_paths())}")
'''
if source.count(old_preflight) != 1:
    fail(f"SOURCE_PATCH_PREFLIGHT_ANCHOR_DRIFT:count={source.count(old_preflight)}")
source = source.replace(old_preflight, new_preflight, 1)

old_final = '''paths = dirty_paths()
if paths != EXPECTED:
    fail(f"FINAL_DIRTY_SET_MISMATCH:{sorted(paths)}")
run("git", "diff", "--check")
'''
new_final = '''paths = dirty_paths()
_expected_with_preexisting = EXPECTED | {
    "client/src/pages/LeadsList.tsx",
    "client/src/new-lead-premium-v1-3.css",
    "client/src/new-lead-premium-v1-4.css",
}
if paths != _expected_with_preexisting:
    fail(f"FINAL_DIRTY_SET_MISMATCH:{sorted(paths)}")
run("git", "diff", "--check", "--", *sorted(EXPECTED))
'''
if source.count(old_final) != 1:
    fail(f"SOURCE_PATCH_FINAL_ANCHOR_DRIFT:count={source.count(old_final)}")
source = source.replace(old_final, new_final, 1)

# Execute the reviewed Users implementation in an isolated namespace.
namespace = {"__name__": "__main__", "__file__": "/tmp/TCRM-PERMISSIONS-USERS-END-TO-END-V1.0.0.dirty-safe.py"}
exec(compile(source, namespace["__file__"], "exec"), namespace, namespace)

# Prove that the pre-existing New Lead work was not touched by this Users patch.
after_hashes = {rel: digest(rel) for rel in sorted(PREEXISTING_DIRTY)}
if after_hashes != before_hashes:
    changed = [rel for rel in sorted(PREEXISTING_DIRTY) if before_hashes.get(rel) != after_hashes.get(rel)]
    fail(f"PREEXISTING_NEW_LEAD_FILES_MODIFIED:{changed}")

final_dirty = dirty_paths()
if final_dirty != FINAL_EXPECTED:
    fail(f"RECOVERY_FINAL_DIRTY_SET_MISMATCH:{sorted(final_dirty)}")

# Scope diff-check to Users-owned tracked files only; unrelated pre-existing work
# must neither block this recovery nor be normalized by it.
tracked_users = sorted(rel for rel in USERS_EXPECTED if (ROOT / rel).exists())
run("git", "diff", "--check", "--", *tracked_users)

print(f"VERSION={VERSION}")
print(f"WORKFLOW_ID={WORKFLOW_ID}")
print(f"BASELINE={BASELINE}")
print("PATCH_APPLIED=YES")
print("RECOVERY_MODE=DIRTY_SAFE_ALLOWLIST")
print("PREEXISTING_DIRTY_PRESERVED=YES")
print("PREEXISTING_DIRTY_FILES=" + ",".join(sorted(PREEXISTING_DIRTY)))
print("USERS_PERMISSION_KEYS=users.view,users.create,users.edit,users.delete,users.assign_roles")
print("USERS_EXPECTED_FILES=" + ",".join(sorted(USERS_EXPECTED)))
print("FINAL_DIRTY_SET=PASS")
print("READY_FOR_TESTS=YES")
