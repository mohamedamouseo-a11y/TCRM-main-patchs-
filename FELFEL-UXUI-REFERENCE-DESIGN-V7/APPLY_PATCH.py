#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import subprocess
import sys

PATCH_ID = "FELFEL-UXUI-REFERENCE-DESIGN-V7"
BASELINE_HEAD = "90b1d4573626e0fad4c7629df1b062e939099e7e"
TARGET = "client/src/pages/FelfelPage.tsx"
AVATAR = "client/public/ai-staff/felfel-avatar.webp"
EXPECTED_V5_PARTIAL_BLOB = "92e551d63f9c3e68d2f2961f6f1783f076bcbbd9"
EXPECTED_AVATAR_BLOB = "21e7557ee99908b5a9893bb5503d0e662c23d7b1"
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()


def run(*args: str) -> str:
    p = subprocess.run(list(args), cwd=root, text=True, capture_output=True)
    if p.returncode != 0:
        sys.stdout.write(p.stdout)
        sys.stderr.write(p.stderr)
        raise SystemExit(f"Command failed ({p.returncode}): {' '.join(args)}")
    return p.stdout.rstrip("\n")


def untracked_paths() -> list[str]:
    p = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
        cwd=root,
        capture_output=True,
    )
    if p.returncode != 0:
        sys.stdout.buffer.write(p.stdout)
        sys.stderr.buffer.write(p.stderr)
        raise SystemExit("Unable to enumerate untracked files")
    return [x.decode("utf-8", errors="surrogateescape") for x in p.stdout.split(b"\0") if x]


if run("git", "rev-parse", "--show-toplevel") != str(root):
    raise SystemExit("Run from canonical TCRM repository root")

branch = run("git", "branch", "--show-current")
head = run("git", "rev-parse", "HEAD")
if branch != "main" or head != BASELINE_HEAD:
    raise SystemExit(f"{PATCH_ID} requires main at {BASELINE_HEAD}; found {branch} at {head}")

if run("git", "diff", "--cached", "--name-only"):
    raise SystemExit("Staged changes exist; refusing recovery")

tracked_dirty = [p for p in run("git", "diff", "--name-only").splitlines() if p.strip()]
if tracked_dirty != [TARGET]:
    raise SystemExit(f"Expected exactly one tracked dirty file ({TARGET}); found {tracked_dirty}")

page = root / TARGET
avatar = root / AVATAR
if not page.is_file():
    raise SystemExit(f"Missing {TARGET}")
if not avatar.is_file():
    raise SystemExit(f"Missing validated avatar {AVATAR}")

page_blob_before = run("git", "hash-object", TARGET)
if page_blob_before != EXPECTED_V5_PARTIAL_BLOB:
    raise SystemExit(
        f"Unexpected Felfel partial state: expected {EXPECTED_V5_PARTIAL_BLOB}, found {page_blob_before}"
    )

avatar_blob = run("git", "hash-object", AVATAR)
if avatar_blob != EXPECTED_AVATAR_BLOB:
    raise SystemExit(f"Avatar blob mismatch: expected {EXPECTED_AVATAR_BLOB}, found {avatar_blob}")

untracked_before = untracked_paths()
mautic_before = [p for p in untracked_before if p.startswith("external/mautic/")]
unexpected_untracked = [p for p in untracked_before if p != AVATAR and not p.startswith("external/mautic/")]
if unexpected_untracked:
    raise SystemExit("Unexpected untracked paths before recovery:\n" + "\n".join(unexpected_untracked[:50]))

text = page.read_text(encoding="utf-8")
required_markers = (
    'data-felfel-uxui="reference-v5"',
    '/ai-staff/felfel-avatar.webp',
    'object-[50%_18%]',
    'bg-gradient-to-r from-orange-600 to-orange-400',
    '<Puzzle className="h-5 w-5" />',
    'Meetings Processed',
    'Live Meeting Status',
    'Transcript & Intelligence',
    'Service capabilities',
)
for marker in required_markers:
    if marker not in text:
        raise SystemExit(f"Expected V5 partial marker missing: {marker}")

if text.count('data-felfel-uxui="reference-v5"') != 1:
    raise SystemExit("Expected exactly one V5 design marker")

updated = text.replace(
    'data-felfel-uxui="reference-v5"',
    'data-felfel-uxui="reference-v7"',
    1,
)
page.write_text(updated, encoding="utf-8")

run("git", "diff", "--check", "--", TARGET)
tracked_after = [p for p in run("git", "diff", "--name-only").splitlines() if p.strip()]
if tracked_after != [TARGET]:
    raise SystemExit(f"Unexpected tracked diff after recovery: {tracked_after}")

page_blob_after = run("git", "hash-object", TARGET)
if page_blob_after == page_blob_before:
    raise SystemExit("V7 marker transition did not change the page blob")

final_text = page.read_text(encoding="utf-8")
for marker in (
    'data-felfel-uxui="reference-v7"',
    'object-[50%_18%]',
    'bg-gradient-to-r from-orange-600 to-orange-400',
    '<Puzzle className="h-5 w-5" />',
):
    if marker not in final_text:
        raise SystemExit(f"V7 marker missing: {marker}")
if 'data-felfel-uxui="reference-v5"' in final_text:
    raise SystemExit("Old V5 marker remained after V7 recovery")

if run("git", "hash-object", AVATAR) != EXPECTED_AVATAR_BLOB:
    raise SystemExit("Avatar changed unexpectedly during V7 recovery")

untracked_after = untracked_paths()
mautic_after = [p for p in untracked_after if p.startswith("external/mautic/")]
unexpected_after = [p for p in untracked_after if p != AVATAR and not p.startswith("external/mautic/")]
if unexpected_after:
    raise SystemExit("Unexpected untracked paths after recovery:\n" + "\n".join(unexpected_after[:50]))
if len(mautic_after) != len(mautic_before):
    raise SystemExit(f"Mautic untracked count changed: {len(mautic_before)} -> {len(mautic_after)}")

print(f"{PATCH_ID} applied")
print(f"BRANCH={branch}")
print(f"HEAD={head}")
print(f"PAGE_STATE_BEFORE={page_blob_before}")
print(f"PAGE_STATE_AFTER={page_blob_after}")
print(f"AVATAR_BLOB={EXPECTED_AVATAR_BLOB}")
print(f"MAUTIC_UNTRACKED_COUNT_PRESERVED={len(mautic_after)}")
print("V5_PARTIAL_RECOVERY=YES")
print("TRACKED_SCOPE=client/src/pages/FelfelPage.tsx")
print("AVATAR_CHANGED=NO")
print("BACKEND_CHANGED=NO")
print("ROUTER_CHANGED=NO")
print("DB_SCHEMA_CHANGED=NO")
print("FUNCTIONAL_BEHAVIOR_CHANGED=NO")
print("EXTERNAL_MAUTIC_CHANGED=NO")
print("NO_CLEAN_STASH_RESET_SWITCH_FETCH_PULL_MERGE_REBASE_COMMIT_PUSH=YES")
