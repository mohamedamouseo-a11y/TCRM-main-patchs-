#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import subprocess
import sys

BASELINE_SHA = "3d6a67c61dd0abce01d803469f81bcbf45c730a6"
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()

targets = [
    "server/services/developerHubRepositoryRoot.test.ts",
    "server/services/developerHubGitHubRuntime.test.ts",
]


def run(*args: str) -> str:
    result = subprocess.run(list(args), cwd=root, text=True, capture_output=True)
    if result.returncode != 0:
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise SystemExit(f"Command failed ({result.returncode}): {' '.join(args)}")
    return result.stdout.strip()


def load(rel: str) -> str:
    path = root / rel
    if not path.is_file():
        raise SystemExit(f"Missing required file: {rel}")
    return path.read_text(encoding="utf-8")


if run("git", "rev-parse", "--show-toplevel") != str(root):
    raise SystemExit("Run this patch from the canonical TCRM repository root.")

head = run("git", "rev-parse", "HEAD")
if head != BASELINE_SHA:
    raise SystemExit(
        f"Baseline mismatch: expected {BASELINE_SHA}, found {head}. Re-review before applying V2.1."
    )

runtime_test_path = root / targets[1]
repo_test_path = root / targets[0]
runtime_test = load(targets[1])
repo_test = load(targets[0])

# V2 must already be present. This repair only fixes generated test source.
required_runtime_markers = [
    "injects only the canonical repository as sandbox safe.directory",
    "createSafeGitEnvironment(repo)",
]
for marker in required_runtime_markers:
    if marker not in runtime_test:
        raise SystemExit(f"V2 runtime-test marker missing: {marker}")

required_repo_markers = [
    "accepts a canonical Git root while keeping the isolated probe policy",
    "subprocessGitInit(root)",
]
for marker in required_repo_markers:
    if marker not in repo_test:
        raise SystemExit(f"V2 repository-test marker missing: {marker}")

# Repair the exact malformed string emitted by V2. The source currently contains
# a literal newline between '*'' and the closing quote.
malformed = '      expect(stdout).not.toContain("*\n");\n'
fixed = '      expect(stdout.trim().split("\\n")).not.toContain("*");\n'

if fixed not in runtime_test:
    if malformed not in runtime_test:
        # Be explicit about the two-line form for easier diagnostics.
        alt_malformed = '      expect(stdout).not.toContain("*\n");'
        if alt_malformed not in runtime_test:
            raise SystemExit(
                "Refusing to repair runtime test: expected V2 malformed safe.directory assertion was not found."
            )
    runtime_test = runtime_test.replace(malformed, fixed, 1)
    runtime_test_path.write_text(runtime_test, encoding="utf-8")
    print("[repaired] server/services/developerHubGitHubRuntime.test.ts safe.directory assertion")
else:
    print("[already] runtime safe.directory assertion is repaired")

# V2 used require() inside an ESM TypeScript test helper. Replace it with a normal
# node:child_process import so the test cannot fail later under package type=module.
repo_test = repo_test_path.read_text(encoding="utf-8")
if 'import { spawnSync } from "node:child_process";' not in repo_test:
    anchor = 'import path from "node:path";\n'
    if anchor not in repo_test:
        raise SystemExit("Refusing to repair repository test: import anchor not found.")
    repo_test = repo_test.replace(
        anchor,
        anchor + 'import { spawnSync } from "node:child_process";\n',
        1,
    )

old_spawn = 'const result = require("node:child_process").spawnSync("git", ["init", root], {'
new_spawn = 'const result = spawnSync("git", ["init", root], {'
if old_spawn in repo_test:
    repo_test = repo_test.replace(old_spawn, new_spawn, 1)
elif new_spawn not in repo_test:
    raise SystemExit("Refusing to repair repository test: subprocessGitInit implementation not recognized.")

repo_test_path.write_text(repo_test, encoding="utf-8")
print("[repaired] server/services/developerHubRepositoryRoot.test.ts ESM child_process helper")

run("git", "diff", "--check", "--", *targets)

print("")
print("Developer Hub Safe Directory V2.1 test repair applied.")
print("Only the two V2 test files were repaired.")
print("No production implementation source was changed by V2.1.")
print("No build, restart, push, pull, reset, merge, cleanup, or deployment was performed.")
print("Run focused tests next:")
print(
    "  pnpm exec vitest run "
    "server/services/developerHubRepositoryRoot.test.ts "
    "server/services/developerHubGitHubRuntime.test.ts"
)
