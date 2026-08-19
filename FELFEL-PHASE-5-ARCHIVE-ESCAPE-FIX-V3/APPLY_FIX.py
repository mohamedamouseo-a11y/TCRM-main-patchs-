#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import subprocess
import sys

PATCH_ID = "FELFEL-PHASE-5-ARCHIVE-ESCAPE-FIX-V3"
BASELINE_SHA = "c8859eda1915af3d2abcdaf7261f62bc3ffd988e"
SERVICE = "server/services/felfel/felfelMeetingArchiveService.ts"
TEST = "server/services/felfel/felfelMeetingArchiveService.test.ts"
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()


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
    raise SystemExit("Run this fix from the canonical TCRM repository root.")

head = run("git", "rev-parse", "HEAD")
if head != BASELINE_SHA:
    raise SystemExit(f"Baseline mismatch: {PATCH_ID} requires HEAD {BASELINE_SHA}, found {head}.")

status = run("git", "status", "--short")
if status.strip():
    raise SystemExit("Refusing to apply V3 on a dirty worktree. Commit/review existing work first:\n" + status)

service = load(SERVICE)
test = load(TEST)

required_test_markers = [
    "escapes raw HTML and markdown control characters in archive content",
    'expect(escaped).toContain("&lt;script&gt;")',
]
for marker in required_test_markers:
    if marker not in test:
        raise SystemExit(f"Required regression-test marker missing: {marker}")

old = r'''export function escapeFelfelArchiveMarkdown(value: unknown, max = 12_000) {
  return cleanInline(value, max)
    .replace(/\\/g, "\\\\")
    .replace(/([`*_{}\[\]()#+\-.!|>])/g, "\\$1")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}
'''

new = r'''export function escapeFelfelArchiveMarkdown(value: unknown, max = 12_000) {
  // Encode raw HTML delimiters first, then escape Markdown control characters.
  // Escaping `>` first would produce `\\&gt;` after HTML encoding.
  return cleanInline(value, max)
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\\/g, "\\\\")
    .replace(/([`*_{}\[\]()#+\-.!|])/g, "\\$1");
}
'''

if service.count(old) != 1:
    raise SystemExit("Exact pre-fix escape function was not found exactly once; refusing approximate edit.")

service_after = service.replace(old, new, 1)
(root / SERVICE).write_text(service_after, encoding="utf-8")

# Test must remain unchanged.
if load(TEST) != test:
    raise SystemExit("Unexpected test-file modification detected.")

run("git", "diff", "--check", "--", SERVICE)
changed = run("git", "status", "--short")
expected_line = f" M {SERVICE}"
if changed.strip() != expected_line.strip():
    raise SystemExit(f"Unexpected worktree scope after fix. Expected only {SERVICE}; got:\n{changed}")

print(f"{PATCH_ID} applied.")
print(f"Modified exactly one file: {SERVICE}")
print(f"Regression test unchanged: {TEST}")
print("Fix: HTML-encode < and > before Markdown escaping.")
print("No DB schema/migration, router API, UI behavior, Google Drive settings, Vexa, Evolution, Tara, Zaghloul, or TOS logic modified.")
print("No build, restart, commit, push, fetch, pull, reset, merge, rebase, migration, or cleanup performed.")
