#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

PATCH_ID = "TCRM-TOS-INTEGRATION-CONSOLE-WARN-SYNTAX-FIX-V1"
REL_PATH = Path("server/services/tosIntegrationService.ts")
BROKEN_RE = re.compile(r"console\.warn\s*\(\s*,\s*\)\s*;")
FIXED = "console.warn();"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fail(message: str, code: int = 2) -> int:
    print(f"[ABORT] {message}", file=sys.stderr)
    return code


def main() -> int:
    root = Path(sys.argv[1]).expanduser().resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
    target = root / REL_PATH

    if not target.is_file():
        return fail(f"Target file not found: {target}")

    original = target.read_text(encoding="utf-8")
    original_sha = sha256(target)
    matches = list(BROKEN_RE.finditer(original))

    if not matches:
        print(f"[OK] Broken console.warn(, ) syntax was not found; no write needed.")
        print(f"[SHA256] {original_sha}  {REL_PATH}")
        return 0

    if len(matches) != 1:
        return fail(f"Expected exactly one broken console.warn(, ) occurrence; found {len(matches)}. Refusing to modify unknown state.")

    updated = BROKEN_RE.sub(FIXED, original, count=1)
    if updated == original:
        return fail("Transformation produced no change.")

    if BROKEN_RE.search(updated):
        return fail("Broken syntax is still present after transformation.")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = root / ".patch-backups" / PATCH_ID / timestamp / REL_PATH
    backup.parent.mkdir(parents=True, exist_ok=False)
    shutil.copy2(target, backup)

    temp = target.with_name(target.name + f".{PATCH_ID}.tmp")
    try:
        temp.write_text(updated, encoding="utf-8")
        os.replace(temp, target)
    finally:
        if temp.exists():
            temp.unlink()

    post_sha = sha256(target)
    print(f"[APPLIED] {PATCH_ID}")
    print(f"[TARGET] {target}")
    print(f"[BACKUP] {backup}")
    print(f"[SHA256 BEFORE] {original_sha}")
    print(f"[SHA256 AFTER ] {post_sha}")
    print("[CHANGE] console.warn(, ); -> console.warn();")
    print("[SCOPE] Syntax-only repair in tosIntegrationService.ts; no logic/API/database changes intended.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
