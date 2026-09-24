#!/usr/bin/env python3
from __future__ import annotations

import base64
import hashlib
import json
import shutil
import subprocess
import zlib
from pathlib import Path

PATCH_NAME = "TCRM_SYSTEM_TIMEZONE_RIYADH_V1"
EXPECTED_MAIN_COMMIT = "fb7a06de47aaf242d374c356a30fa9b84a8051d0"
BACKUP_DIR = Path(".tcrm-patch-backups") / PATCH_NAME

PAYLOAD = json.loads(zlib.decompress(base64.b64decode("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")).decode("utf-8"))
EXPECTED_BLOBS = PAYLOAD["expected"]
NEW_FILES = PAYLOAD["new_files"]
REPLACEMENTS = PAYLOAD["replacements"]
TARGETS = tuple(EXPECTED_BLOBS)

def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("utf-8")
    return hashlib.sha1(header + data).hexdigest()

def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"ANCHOR_FAIL={label}:expected_1_found_{count}")
    return text.replace(old, new, 1)

def run_git_diff_check(paths: list[str]) -> None:
    proc = subprocess.run(
        ["git", "diff", "--check", "--", *paths],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if proc.returncode != 0:
        raise RuntimeError("GIT_DIFF_CHECK_FAIL=" + proc.stdout.strip().replace("\n", " | "))

def restore_backups() -> None:
    for rel in TARGETS:
        src = BACKUP_DIR / rel
        dst = Path(rel)
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    for rel in NEW_FILES:
        path = Path(rel)
        backup = BACKUP_DIR / rel
        if backup.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup, path)
        elif path.exists():
            path.unlink()

def already_present() -> bool:
    markers = {
        "server/_core/systemRouter.ts": "TCRM_SYSTEM_TIMEZONE_RIYADH_V1",
        "client/src/pages/AdminSettings.tsx": "SystemTimeSettingsCard",
        "client/src/components/NotificationCenter.tsx": "parseUtcTimestamp(date)",
        "client/src/pages/LeadProfile.tsx": "systemTimezone={systemTimezone}",
        "client/src/pages/AuditLogPage.tsx": "systemTimezone",
    }
    if not all(Path(rel).is_file() and marker in Path(rel).read_text(encoding="utf-8") for rel, marker in markers.items()):
        return False
    return all(Path(rel).is_file() for rel in NEW_FILES)

def main() -> int:
    root = Path.cwd()

    if already_present():
        print("PATCH=ALREADY_PRESENT")
        print("PATCH_NAME=" + PATCH_NAME)
        print("SYSTEM_TIMEZONE=Asia/Riyadh")
        print("UTC_STORAGE_POLICY=PRESERVED")
        print("ERROR=NONE")
        return 0

    originals: dict[str, str] = {}
    for rel, expected in EXPECTED_BLOBS.items():
        path = root / rel
        if not path.is_file():
            print("PATCH=FAIL")
            print(f"ERROR=MISSING_SOURCE:{rel}")
            return 2
        raw = path.read_bytes()
        actual = git_blob_sha(raw)
        if actual != expected:
            print("PATCH=STOP")
            print(f"SOURCE_GUARD_FAIL={rel}")
            print(f"EXPECTED_BLOB={expected}")
            print(f"ACTUAL_BLOB={actual}")
            print("ERROR=SOURCE_CHANGED_DO_NOT_FORCE")
            return 3
        originals[rel] = raw.decode("utf-8")

    for rel in NEW_FILES:
        path = root / rel
        if path.exists():
            print("PATCH=STOP")
            print(f"ERROR=NEW_FILE_ALREADY_EXISTS:{rel}")
            return 4

    updated = dict(originals)
    for rel, replacements in REPLACEMENTS.items():
        for idx, pair in enumerate(replacements, start=1):
            old, new = pair
            updated[rel] = replace_once(updated[rel], old, new, f"{rel}#{idx}")

    if BACKUP_DIR.exists():
        shutil.rmtree(BACKUP_DIR)
    for rel in TARGETS:
        src = root / rel
        dst = root / BACKUP_DIR / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    try:
        for rel, file_content in updated.items():
            (root / rel).write_text(file_content, encoding="utf-8")
        for rel, file_content in NEW_FILES.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(file_content, encoding="utf-8")
        run_git_diff_check([*TARGETS, *NEW_FILES.keys()])
    except Exception:
        restore_backups()
        raise

    print("PATCH=PASS")
    print("PATCH_NAME=" + PATCH_NAME)
    print("BASE_MAIN_COMMIT=" + EXPECTED_MAIN_COMMIT)
    print("FILES_CHANGED=" + ";".join([*TARGETS, *NEW_FILES.keys()]))
    print("SYSTEM_TIMEZONE_DEFAULT=Asia/Riyadh")
    print("UTC_STORAGE_POLICY=PRESERVED")
    print("TIMEZONE_SETTINGS_UI=ACTIVE")
    print("NOTIFICATIONS_UTC_PARSE_FIX=ACTIVE")
    print("ACTIVITY_SAVE_SYSTEM_TZ_TO_UTC=ACTIVE")
    print("ACTIVITY_DISPLAY_SYSTEM_TZ=ACTIVE")
    print("AUDIT_DISPLAY_SYSTEM_TZ=ACTIVE")
    print("DB_DIAGNOSTICS=ACTIVE")
    print("MIGRATION_REQUIRED=scripts/apply-system-timezone-riyadh-v1-migration.ts --apply")
    print("BACKUP=" + str(BACKUP_DIR))
    print("GIT_DIFF_CHECK=PASS")
    print("ERROR=NONE")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("PATCH=FAIL")
        print("ERROR=" + str(exc).replace("\n", " | "))
        raise SystemExit(1)
