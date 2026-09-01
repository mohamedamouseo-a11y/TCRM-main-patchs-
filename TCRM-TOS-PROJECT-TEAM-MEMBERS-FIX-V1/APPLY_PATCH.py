#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

PATCH_ID = "TCRM-TOS-PROJECT-TEAM-MEMBERS-FIX-V1"
REL_PATH = Path("client/src/components/TosProjectTeamSelector.tsx")

BLOCK_RE = re.compile(
    r"(?P<indent>^[ \t]*)const departmentMembersMap = React\.useMemo\(\(\) => \{\n"
    r".*?"
    r"^[ \t]*\}, \[projectMembers\]\);",
    re.MULTILINE | re.DOTALL,
)


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

    # Current canonical source already renders department.members directly.
    already_fixed_direct = (
        "Array.isArray(department.members) ? department.members.length : 0" in original
        and "(department.members || []).map((member: any) =>" in original
    )
    if already_fixed_direct and "const departmentMembersMap = React.useMemo" not in original:
        print(f"[OK] {PATCH_ID} is already present; no write needed.")
        print(f"[SHA256] {original_sha}  {REL_PATH}")
        return 0

    if "export function TosProjectTeamSelector" not in original:
        return fail("Unexpected target file: TosProjectTeamSelector export was not found.")

    match = BLOCK_RE.search(original)
    if not match:
        return fail(
            "Expected broken departmentMembersMap(projectMembers) block was not found. "
            "Refusing to replace an unknown version."
        )

    departments_decl = original.find("const departments =")
    if departments_decl < 0 or departments_decl > match.start():
        return fail(
            "The departments declaration is missing or appears after departmentMembersMap. "
            "Refusing to create a TDZ/runtime regression."
        )

    indent = match.group("indent")
    replacement = (
        f"{indent}const departmentMembersMap = React.useMemo(() => {{\n"
        f"{indent}  const map = new Map<string, TosProjectMembership[]>();\n"
        f"{indent}  for (const department of departments) {{\n"
        f"{indent}    const departmentKey = String(department?.key || department?.id || \"\").trim();\n"
        f"{indent}    if (!departmentKey) continue;\n"
        f"{indent}    const members = Array.isArray(department?.members) ? department.members : [];\n"
        f"{indent}    map.set(departmentKey, members);\n"
        f"{indent}  }}\n"
        f"{indent}  return map;\n"
        f"{indent}}}, [departments]);"
    )

    updated, count = BLOCK_RE.subn(replacement, original, count=1)
    if count != 1 or updated == original:
        return fail("Patch transformation did not produce exactly one change.")

    # Safety: selection/save behavior must remain in the file.
    required_markers = [
        "projectMemberById",
        "visibleSelectedIds",
        "locallySelectedIds",
        "tosUserId",
        "toggleMember",
    ]
    missing = [marker for marker in required_markers if marker not in updated]
    if missing:
        return fail(f"Safety markers missing after transformation: {', '.join(missing)}")

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
    print("[SCOPE] Frontend selector only; backend/TOS/database/save payload untouched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
