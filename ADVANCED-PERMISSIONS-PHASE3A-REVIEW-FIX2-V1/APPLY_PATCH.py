#!/usr/bin/env python3
from pathlib import Path
import shutil
import sys
import time

MARKER = "ADVANCED_PERMISSIONS_PHASE3A_FIX2_V1"


def die(msg: str):
    print(f"[Phase3A-Fix2] ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)


def main():
    project = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    routers = project / "server/routers.ts"
    db = project / "server/db.ts"
    scope = project / "server/security/phase3ScopeFilters.ts"
    if not routers.exists() or not db.exists() or not scope.exists():
        die("Compatible Phase 3A checkout required")

    routers_text = routers.read_text(encoding="utf-8")
    db_text = db.read_text(encoding="utf-8")
    scope_text = scope.read_text(encoding="utf-8")

    if "TCRM Advanced Permissions — Phase 3A" not in scope_text:
        die("Phase 3A scope filters are not present")
    if "export async function getDealsScoped" not in db_text:
        die("Expected Phase 3A getDealsScoped export is missing from server/db.ts")
    if "getDealsScoped(" not in routers_text:
        die("Expected Phase 3A getDealsScoped usage is missing from server/routers.ts")

    if f"// {MARKER}" in routers_text:
        print("[Phase3A-Fix2] already applied")
        return

    # Narrow anchor inside the existing large ./db import block.
    anchor = "  getDealsByUser,\n"
    if routers_text.count(anchor) != 1:
        die(f"Expected one getDealsByUser import anchor; found {routers_text.count(anchor)}")
    if "  getDealsScoped,\n" in routers_text:
        routers_text = routers_text.replace(anchor, f"  // {MARKER}\n" + anchor, 1)
    else:
        routers_text = routers_text.replace(anchor, f"  // {MARKER}\n  getDealsScoped,\n" + anchor, 1)

    backup_root = project / ".patch-backups" / f"advanced-permissions-phase3a-fix2-{int(time.time())}"
    backup = backup_root / "server/routers.ts"
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(routers, backup)
    routers.write_text(routers_text, encoding="utf-8")

    verifier_src = Path(__file__).resolve().parent / "files/scripts/verify-advanced-permissions-phase3a-fix2.ts"
    verifier_dst = project / "scripts/verify-advanced-permissions-phase3a-fix2.ts"
    if not verifier_src.exists():
        die("Patch package missing verifier")
    verifier_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(verifier_src, verifier_dst)

    print("[Phase3A-Fix2] applied successfully")
    print(f"[Phase3A-Fix2] backup: {backup_root}")
    print("[Phase3A-Fix2] changed server/routers.ts import only; no DB or git operations")


if __name__ == "__main__":
    main()
