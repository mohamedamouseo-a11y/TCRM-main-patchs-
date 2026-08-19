#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import subprocess
import sys

PATCH_ID = "FELFEL-PHASE-5-ARCHIVE-ESCAPE-FIX-V1"
BASELINE_SHA = "cd70a4898ff2b2f11e8b7c5e7c7e476d04fe4a2c"
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()

SERVICE = "server/services/felfel/felfelMeetingArchiveService.ts"
TEST = "server/services/felfel/felfelMeetingArchiveService.test.ts"
ROUTERS = "server/routers.ts"
PAGE = "client/src/pages/FelfelPage.tsx"
EXPECTED_STATUS_PATHS = {
    SERVICE,
    TEST,
    ROUTERS,
    PAGE,
}


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
        raise SystemExit(f"Missing required Phase 5 file: {rel}")
    return path.read_text(encoding="utf-8")


if run("git", "rev-parse", "--show-toplevel") != str(root):
    raise SystemExit("Run this fix from the canonical TCRM repository root.")

head = run("git", "rev-parse", "HEAD")
if head != BASELINE_SHA:
    raise SystemExit(
        f"Baseline mismatch: {PATCH_ID} requires uncommitted Phase 5 on HEAD {BASELINE_SHA}, found {head}."
    )

status_lines = [line for line in run("git", "status", "--porcelain").splitlines() if line.strip()]
seen_paths = set()
for line in status_lines:
    path = line[3:].strip()
    if " -> " in path:
        path = path.split(" -> ", 1)[1].strip()
    seen_paths.add(path)

if seen_paths != EXPECTED_STATUS_PATHS:
    raise SystemExit(
        "Refusing to apply Phase 5 fix because the worktree does not contain exactly the four expected Phase 5 paths.\n"
        f"Expected: {sorted(EXPECTED_STATUS_PATHS)}\n"
        f"Found: {sorted(seen_paths)}"
    )

service = load(SERVICE)
test = load(TEST)
routers = load(ROUTERS)
page = load(PAGE)

required_markers = [
    (service, "FELFEL_ACTION" if False else "felfel-meeting-archive-v1", "Phase 5 archive service"),
    (test, "escapes raw HTML and markdown control characters in archive content", "failing archive escape test"),
    (test, 'expect(escaped).toContain("&lt;script&gt;")', "expected HTML entity assertion"),
    (routers, "archiveMeeting: felfelProcedure", "Phase 5 archive router"),
    (page, "Meeting Archive & Google Drive", "Phase 5 archive UI"),
]
for source, marker, label in required_markers:
    if marker not in source:
        raise SystemExit(f"Refusing to apply fix: missing {label} marker: {marker}")

old = '''export function escapeFelfelArchiveMarkdown(value: unknown, max = 12_000) {
  return cleanInline(value, max)
    .replace(/\\\\/g, "\\\\\\\\")
    .replace(/([`*_{}\\[\\]()#+\\-.!|>])/g, "\\\\$1")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}
'''
new = '''export function escapeFelfelArchiveMarkdown(value: unknown, max = 12_000) {
  // Encode raw HTML delimiters first, then escape Markdown control characters.
  // Doing Markdown escaping first turns `>` into `\\>` and later HTML encoding
  // produces the undesirable `\\&gt;` sequence that Phase 5 validation caught.
  return cleanInline(value, max)
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\\\\/g, "\\\\\\\\")
    .replace(/([`*_{}\\[\\]()#+\\-.!|])/g, "\\\\$1");
}
'''

if old not in service:
    raise SystemExit("Refusing to apply fix: exact pre-fix escape function was not found. Do not patch by approximation.")
if service.count(old) != 1:
    raise SystemExit("Refusing to apply fix: pre-fix escape function is not unique.")

service = service.replace(old, new, 1)
(root / SERVICE).write_text(service, encoding="utf-8")

# The existing test is intentionally NOT changed. It describes the desired output.
run("git", "diff", "--check", "--", SERVICE)

print(f"{PATCH_ID} applied.")
print("Modified exactly one already-uncommitted Phase 5 source file:")
print(f"  {SERVICE}")
print("The Phase 5 test expectation was not changed.")
print("Fix: HTML-encode < and > before Markdown escaping, preventing \\&gt; output.")
print("No DB schema/migration, router API, UI behavior, Google Drive settings, Vexa, Evolution, Tara, Zaghloul, or TOS logic was modified.")
print("No build, restart, commit, push, fetch, pull, reset, merge, rebase, migration, or cleanup was performed.")
