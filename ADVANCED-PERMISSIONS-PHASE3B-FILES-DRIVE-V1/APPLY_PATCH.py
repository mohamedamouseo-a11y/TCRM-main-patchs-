#!/usr/bin/env python3
from pathlib import Path
import shutil, sys, time

ROOT = Path(__file__).resolve().parent
TARGET = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TCRM-MAIN").resolve()
FILES = ROOT / "files"
TRPC = TARGET / "server/_core/trpc.ts"
ROUTERS = TARGET / "server/routers.ts"
VERIFY_SRC = FILES / "scripts/verify-advanced-permissions-phase3b-files-drive.ts"
VERIFY_DST = TARGET / "scripts/verify-advanced-permissions-phase3b-files-drive.ts"
BACKUP = TARGET / ".patch-backups" / f"advanced-permissions-phase3b-files-drive-{int(time.time())}"

for p in [TRPC, ROUTERS, VERIFY_SRC]:
    if not p.exists(): raise SystemExit(f"Missing required file: {p}")

routers_text = ROUTERS.read_text()
trpc_text = TRPC.read_text()
if "ADVANCED_PERMISSIONS_PHASE3B_REMAINING_CORE_V1" not in trpc_text:
    raise SystemExit("Expected Remaining Core V1 baseline marker in server/_core/trpc.ts")

BACKUP.mkdir(parents=True, exist_ok=True)
for p in [TRPC, ROUTERS]:
    dst = BACKUP / p.relative_to(TARGET)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, dst)

marker = '// ADVANCED_PERMISSIONS_PHASE3B_FILES_DRIVE_V1\n'
block = marker + '''export const filesViewScope = phase3Scope("files.view");\nexport const filesUploadScope = phase3Scope("files.upload");\nexport const filesEditScope = phase3Scope("files.edit");\nexport const filesDeleteScope = phase3Scope("files.delete");\nexport const filesShareScope = phase3Scope("files.share");\n'''
if marker not in trpc_text:
    anchor = 'export const auditExportScope = phase3Scope("audit.export");\n'
    if anchor not in trpc_text: raise SystemExit("Files/Drive scope anchor changed")
    trpc_text = trpc_text.replace(anchor, anchor + '\n' + block, 1)
    TRPC.write_text(trpc_text)

VERIFY_DST.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(VERIFY_SRC, VERIFY_DST)

print("Phase 3B Files/Drive V1 reusable scopes + verifier installed.")
print(f"Backup: {BACKUP}")
print("Now wire the actual CRM file routes in server/routers.ts per README; do not touch Google Drive technical settings.")
