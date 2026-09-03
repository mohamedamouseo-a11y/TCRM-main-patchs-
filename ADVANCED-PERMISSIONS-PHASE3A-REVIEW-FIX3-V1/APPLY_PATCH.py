#!/usr/bin/env python3
from pathlib import Path
import shutil
import sys
import time

PATCH_ROOT = Path(__file__).resolve().parent
SRC = PATCH_ROOT / "files/scripts/verify-advanced-permissions-phase3a-fix2.ts"

def die(msg: str):
    print(f"[Phase3A Fix3] ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)

def main():
    project = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    routers = project / "server/routers.ts"
    db = project / "server/db.ts"
    target = project / "scripts/verify-advanced-permissions-phase3a-fix2.ts"
    for p in [routers, db, target]:
        if not p.exists(): die(f"Missing required file: {p.relative_to(project)}")
    rt = routers.read_text(encoding="utf-8")
    dbt = db.read_text(encoding="utf-8")
    if "ADVANCED_PERMISSIONS_PHASE3A_FIX2_V1" not in rt:
        die("Fix2 marker missing; apply Fix2 first")
    if "getDealsScoped," not in rt or "export async function getDealsScoped" not in dbt:
        die("Fix2 code is not present")
    if not SRC.exists(): die("Patch payload missing verifier")
    backup = project / ".patch-backups" / f"advanced-permissions-phase3a-fix3-{int(time.time())}"
    backup.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target, backup / target.name)
    shutil.copy2(SRC, target)
    print("[Phase3A Fix3] Replaced verifier only.")
    print(f"[Phase3A Fix3] Backup: {backup}")
    print("[Phase3A Fix3] No production code, DB, or git operation was changed.")

if __name__ == "__main__":
    main()
