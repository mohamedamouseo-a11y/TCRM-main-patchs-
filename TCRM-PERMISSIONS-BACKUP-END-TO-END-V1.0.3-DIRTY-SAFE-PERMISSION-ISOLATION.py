#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

WORKFLOW_SERIES = "TCRM-PERMISSIONS"
MODULE = "BACKUP"
PHASE = "END-TO-END-DIRTY-SAFE-RUNTIME-RECOVERY"
VERSION = "V1.0.3"
WORKFLOW_ID = "TCRM-PERMISSIONS-BACKUP-END-TO-END-V1.0.3-DIRTY-SAFE-PERMISSION-ISOLATION"
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
    "server/_core/systemRouter.ts",
    "server/security/effectivePermissionsInputLimitHotfix.test.ts",
}

HOTFIX_EXPECTED = {
    "client/src/main.tsx",
    "server/security/effectivePermissionsBatchIsolationHotfix.test.ts",
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

main_rel = "client/src/main.tsx"
main = read(main_rel)

old_import = 'import { httpBatchLink, TRPCClientError } from "@trpc/client";'
new_import = 'import { httpBatchLink, httpLink, splitLink, TRPCClientError } from "@trpc/client";'
if main.count(old_import) != 1:
    fail(f"MAIN_IMPORT_ANCHOR_DRIFT:count={main.count(old_import)}")
main = main.replace(old_import, new_import, 1)

old_links = '''const trpcClient = trpc.createClient({\n  links: [\n    httpBatchLink({\n      url: "/api/trpc",\n      transformer: superjson,\n      async fetch(input, init) {\n        const rawMutation = parseRawCrmMutation(input, init);\n        if (rawMutation) return executeRawCrmMutation(rawMutation);\n        return browserFetch(input, {\n          ...(init ?? {}),\n          credentials: "include",\n        });\n      },\n    }),\n  ],\n});'''
new_links = '''// TCRM_EFFECTIVE_PERMISSIONS_BATCH_ISOLATION_V1\n// Authorization is critical infrastructure. Keep it out of the general tRPC\n// batch so an unrelated procedure failure can never erase permission decisions\n// and redirect every protected route to /404.\nconst trpcClient = trpc.createClient({\n  links: [\n    splitLink({\n      condition(op) {\n        return op.path === "system.effectivePermissions";\n      },\n      true: httpLink({\n        url: "/api/trpc",\n        transformer: superjson,\n        fetch(input, init) {\n          return browserFetch(input, {\n            ...(init ?? {}),\n            credentials: "include",\n          });\n        },\n      }),\n      false: httpBatchLink({\n        url: "/api/trpc",\n        transformer: superjson,\n        async fetch(input, init) {\n          const rawMutation = parseRawCrmMutation(input, init);\n          if (rawMutation) return executeRawCrmMutation(rawMutation);\n          return browserFetch(input, {\n            ...(init ?? {}),\n            credentials: "include",\n          });\n        },\n      }),\n    }),\n  ],\n});'''
if main.count(old_links) != 1:
    fail(f"TRPC_CLIENT_ANCHOR_DRIFT:count={main.count(old_links)}")
main = main.replace(old_links, new_links, 1)
write(main_rel, main)

test_rel = "server/security/effectivePermissionsBatchIsolationHotfix.test.ts"
if (ROOT / test_rel).exists():
    fail("HOTFIX_TEST_ALREADY_EXISTS")
test = r'''import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import path from "node:path";

const source = readFileSync(path.resolve(process.cwd(), "client/src/main.tsx"), "utf8");

describe("effectivePermissions batch isolation hotfix", () => {
  it("routes system.effectivePermissions through a dedicated non-batched link", () => {
    expect(source).toContain("httpBatchLink, httpLink, splitLink, TRPCClientError");
    expect(source).toContain("condition(op)");
    expect(source).toContain('op.path === "system.effectivePermissions"');
    expect(source).toContain("true: httpLink({");
    expect(source).toContain("false: httpBatchLink({");
    expect(source).toContain('credentials: "include"');
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

run("git", "diff", "--check", "--", main_rel)

print(f"VERSION={VERSION}")
print(f"WORKFLOW_ID={WORKFLOW_ID}")
print(f"BASELINE={BASELINE}")
print("PATCH_APPLIED=YES")
print("RECOVERY_MODE=DIRTY_SAFE_ALLOWLIST")
print("PREEXISTING_DIRTY_PRESERVED=YES")
print("PREEXISTING_LEAD_PROFILE_FILES_MODIFIED=NO")
print("PREEXISTING_BACKUP_FILES_MODIFIED=NO")
print("PREEXISTING_PERMISSION_LIMIT_HOTFIX_MODIFIED=NO")
print("EFFECTIVE_PERMISSIONS_BATCH_ISOLATED=YES")
print("GENERAL_TRPC_BATCH_PRESERVED=YES")
print("HOTFIX_FILES_CHANGED=" + ",".join(sorted(HOTFIX_EXPECTED)))
print("PREEXISTING_DIRTY_FILES=" + ",".join(sorted(PREEXISTING_DIRTY)))
print("FINAL_DIRTY_SET=PASS")
print("READY_FOR_TESTS=YES")
