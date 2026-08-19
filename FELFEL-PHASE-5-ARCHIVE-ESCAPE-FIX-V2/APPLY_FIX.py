#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import subprocess
import sys

PATCH_ID = "FELFEL-PHASE-5-ARCHIVE-ESCAPE-FIX-V2"
BASELINE_SHA = "cd70a4898ff2b2f11e8b7c5e7c7e476d04fe4a2c"
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()

SERVICE = "server/services/felfel/felfelMeetingArchiveService.ts"
TEST = "server/services/felfel/felfelMeetingArchiveService.test.ts"
ROUTERS = "server/routers.ts"
PAGE = "client/src/pages/FelfelPage.tsx"

EXPECTED_STATUS = {
    PAGE: " M",
    ROUTERS: " M",
    TEST: "??",
    SERVICE: "??",
}


def run(*args: str) -> str:
    result = subprocess.run(list(args), cwd=root, text=True, capture_output=True)
    if result.returncode != 0:
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise SystemExit(f"Command failed ({result.returncode}): {' '.join(args)}")
    return result.stdout.strip()


def run_raw(*args: str) -> str:
    """Preserve leading spaces and NUL separators from Git porcelain output."""
    result = subprocess.run(list(args), cwd=root, text=True, capture_output=True)
    if result.returncode != 0:
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise SystemExit(f"Command failed ({result.returncode}): {' '.join(args)}")
    return result.stdout


def load(rel: str) -> str:
    path = root / rel
    if not path.is_file():
        raise SystemExit(f"Missing required Phase 5 file: {rel}")
    return path.read_text(encoding="utf-8")


def parse_porcelain_z(raw: str) -> dict[str, str]:
    records = [record for record in raw.split("\0") if record]
    parsed: dict[str, str] = {}
    for record in records:
        if len(record) < 4 or record[2] != " ":
            raise SystemExit(f"Unexpected git porcelain record shape: {record!r}")
        status = record[:2]
        path = record[3:]
        if status[0] in {"R", "C"} or status[1] in {"R", "C"}:
            raise SystemExit("Refusing to apply fix with rename/copy records present in the worktree.")
        if path in parsed:
            raise SystemExit(f"Duplicate worktree path in git status: {path}")
        parsed[path] = status
    return parsed


if run("git", "rev-parse", "--show-toplevel") != str(root):
    raise SystemExit("Run this fix from the canonical TCRM repository root.")

head = run("git", "rev-parse", "HEAD")
if head != BASELINE_SHA:
    raise SystemExit(
        f"Baseline mismatch: {PATCH_ID} requires uncommitted Phase 5 on HEAD {BASELINE_SHA}, found {head}."
    )

# IMPORTANT: do NOT call .strip() on porcelain output. A tracked unstaged file
# begins with a leading space (for example: ' M client/...'). V1 accidentally
# stripped that first character from the first status record before slicing,
# turning 'client/...' into 'lient/...'.
status_raw = run_raw("git", "status", "--porcelain=v1", "-z", "--untracked-files=all")
actual_status = parse_porcelain_z(status_raw)
if actual_status != EXPECTED_STATUS:
    raise SystemExit(
        "Refusing to apply Phase 5 fix because the worktree is not the exact expected uncommitted Phase 5 state.\n"
        f"Expected: {EXPECTED_STATUS}\n"
        f"Found: {actual_status}"
    )

service = load(SERVICE)
test = load(TEST)
routers = load(ROUTERS)
page = load(PAGE)

required_markers = [
    (service, "felfel-meeting-archive-v1", "Phase 5 archive service"),
    (test, "escapes raw HTML and markdown control characters in archive content", "archive escape regression test"),
    (test, 'expect(escaped).toContain("&lt;script&gt;")', "unchanged HTML entity expectation"),
    (routers, "archiveMeeting: felfelProcedure", "Phase 5 archive router"),
    (page, "Meeting Archive & Google Drive", "Phase 5 archive UI"),
]
for source, marker, label in required_markers:
    if marker not in source:
        raise SystemExit(f"Refusing to apply fix: missing {label} marker: {marker}")

old = r'''export function escapeFelfelArchiveMarkdown(value: unknown, max = 12_000) {
  return cleanInline(value, max)
    .replace(/\\/g, "\\\\")
    .replace(/([`*_{}\[\]()#+\-.!|>])/g, "\\$1")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}
'''

new = r'''export function escapeFelfelArchiveMarkdown(value: unknown, max = 12_000) {
  // Encode raw HTML delimiters before Markdown escaping. If `>` is Markdown-
  // escaped first, later HTML encoding produces `\\&gt;`, which is not the
  // intended safe entity representation and fails the Phase 5 regression test.
  return cleanInline(value, max)
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\\/g, "\\\\")
    .replace(/([`*_{}\[\]()#+\-.!|])/g, "\\$1");
}
'''

if service.count(old) != 1:
    raise SystemExit(
        "Refusing to apply fix: exact pre-fix escape function was not found exactly once. "
        "Do not patch by approximation."
    )

service_after = service.replace(old, new, 1)
(root / SERVICE).write_text(service_after, encoding="utf-8")

# The regression test is deliberately not modified.
if load(TEST) != test:
    raise SystemExit("Unexpected test-file modification detected; refusing to continue.")

run("git", "diff", "--check", "--", SERVICE)

# Recheck that the overall dirty-path set is still exactly the four Phase 5 files.
status_after = parse_porcelain_z(run_raw("git", "status", "--porcelain=v1", "-z", "--untracked-files=all"))
if set(status_after) != set(EXPECTED_STATUS):
    raise SystemExit(
        "Fix changed the worktree scope unexpectedly.\n"
        f"Expected paths: {sorted(EXPECTED_STATUS)}\n"
        f"Found paths: {sorted(status_after)}"
    )

print(f"{PATCH_ID} applied.")
print("V2 correction: preserves leading spaces in git porcelain status parsing.")
print("Application fix: HTML-encode < and > before Markdown escaping.")
print(f"Modified application source: {SERVICE}")
print(f"Regression test unchanged: {TEST}")
print("Overall dirty path set remains exactly the four approved Phase 5 paths.")
print("No DB schema/migration, router contract, UI behavior, Google Drive settings, Vexa, Evolution, Tara, Zaghloul, or TOS logic was modified by this fix.")
print("No build, restart, commit, push, fetch, pull, reset, merge, rebase, migration, or cleanup was performed.")
