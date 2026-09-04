#!/usr/bin/env python3
from pathlib import Path
import shutil, sys, time

ROOT = Path(__file__).resolve().parent
TARGET = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TCRM-MAIN").resolve()
SRC = ROOT / "files/scripts/verify-advanced-permissions-phase3b-v2.ts"
DST = TARGET / "scripts/verify-advanced-permissions-phase3b-v2.ts"

for required in [
    TARGET / "server/security/phase3bScope.ts",
    TARGET / "server/security/permissionUserOverrideAdmin.ts",
    TARGET / "client/src/pages/RolesPermissions.tsx",
]:
    if not required.exists():
        raise SystemExit(f"Missing Phase3B V2 working-tree file: {required}")

if not SRC.exists():
    raise SystemExit(f"Missing package verifier: {SRC}")

if DST.exists():
    backup = TARGET / ".patch-backups" / f"phase3b-v2-package-fix1-{int(time.time())}" / "scripts/verify-advanced-permissions-phase3b-v2.ts"
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(DST, backup)

DST.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(SRC, DST)
print("Phase 3B V2 Package Fix 1 applied: verifier-only, no production code changed.")
