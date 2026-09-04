#!/usr/bin/env python3
from pathlib import Path
import shutil, sys, time

ROOT = Path(__file__).resolve().parent
TARGET = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TCRM-MAIN").resolve()
FILES = ROOT / "files"
TRPC = TARGET / "server/_core/trpc.ts"
ROUTERS = TARGET / "server/routers.ts"
VERIFY_SRC = FILES / "scripts/verify-advanced-permissions-phase3b-backup-core-integrations.ts"
VERIFY_DST = TARGET / "scripts/verify-advanced-permissions-phase3b-backup-core-integrations.ts"
BACKUP = TARGET / ".patch-backups" / f"advanced-permissions-phase3b-backup-core-integrations-{int(time.time())}"

for p in [TRPC, ROUTERS, VERIFY_SRC]:
    if not p.exists():
        raise SystemExit(f"Missing required file: {p}")

trpc_text = TRPC.read_text()
if "ADVANCED_PERMISSIONS_PHASE3B_FILES_DRIVE_V1" not in trpc_text:
    raise SystemExit("Expected Files/Drive V1 baseline marker in server/_core/trpc.ts")

BACKUP.mkdir(parents=True, exist_ok=True)
for p in [TRPC, ROUTERS]:
    dst = BACKUP / p.relative_to(TARGET)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, dst)

marker = '// ADVANCED_PERMISSIONS_PHASE3B_BACKUP_CORE_INTEGRATIONS_V1\n'
block = marker + '''export const backupViewScope = phase3Scope("backup.view");\nexport const backupRunScope = phase3Scope("backup.run");\nexport const backupRestoreScope = phase3Scope("backup.restore");\nexport const backupManageScope = phase3Scope("backup.manage");\nexport const integrationsViewScope = phase3Scope("integrations.view");\nexport const integrationsManageScope = phase3Scope("integrations.manage");\n'''
if marker not in trpc_text:
    anchor = 'export const filesShareScope = phase3Scope("files.share");\n'
    if anchor not in trpc_text:
        raise SystemExit("Backup/Integrations scope anchor changed")
    trpc_text = trpc_text.replace(anchor, anchor + '\n' + block, 1)
    TRPC.write_text(trpc_text)

VERIFY_DST.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(VERIFY_SRC, VERIFY_DST)

print("Phase 3B Backup/Core Integrations reusable scopes + verifier installed.")
print(f"Backup: {BACKUP}")
print("Now wire only Backup Center + core TFS/TOS/Google Drive technical integration routes per README.")
