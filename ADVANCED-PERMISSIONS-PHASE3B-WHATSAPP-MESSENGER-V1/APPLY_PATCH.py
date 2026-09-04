#!/usr/bin/env python3
from pathlib import Path
import shutil, sys, time

ROOT = Path(__file__).resolve().parent
TARGET = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TCRM-MAIN").resolve()
FILES = ROOT / "files"
TRPC = TARGET / "server/_core/trpc.ts"
ROUTERS = TARGET / "server/routers.ts"
MESSENGER = TARGET / "server/modules/messenger/router.messenger.ts"
VERIFY_SRC = FILES / "scripts/verify-advanced-permissions-phase3b-whatsapp-messenger.ts"
VERIFY_DST = TARGET / "scripts/verify-advanced-permissions-phase3b-whatsapp-messenger.ts"
BACKUP = TARGET / ".patch-backups" / f"advanced-permissions-phase3b-whatsapp-messenger-{int(time.time())}"

for p in [TRPC, ROUTERS, MESSENGER, VERIFY_SRC]:
    if not p.exists(): raise SystemExit(f"Missing required file: {p}")

trpc = TRPC.read_text()
if "ADVANCED_PERMISSIONS_PHASE3B_BACKUP_CORE_INTEGRATIONS_V1" not in trpc:
    raise SystemExit("Expected Backup/Core Integrations V1 baseline marker")

BACKUP.mkdir(parents=True, exist_ok=True)
for p in [TRPC, ROUTERS, MESSENGER]:
    dst = BACKUP / p.relative_to(TARGET)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, dst)

marker = '// ADVANCED_PERMISSIONS_PHASE3B_WHATSAPP_MESSENGER_V1\n'
block = marker + '''export const whatsappViewScope = phase3Scope("whatsapp.view");\nexport const whatsappSendScope = phase3Scope("whatsapp.send");\nexport const whatsappManageScope = phase3Scope("whatsapp.manage");\nexport const messengerViewScope = phase3Scope("messenger.view");\nexport const messengerSendScope = phase3Scope("messenger.send");\nexport const messengerManageScope = phase3Scope("messenger.manage");\n'''
if marker not in trpc:
    anchor = 'export const integrationsManageScope = phase3Scope("integrations.manage");\n'
    if anchor not in trpc: raise SystemExit("WhatsApp/Messenger scope anchor changed")
    trpc = trpc.replace(anchor, anchor + '\n' + block, 1)
    TRPC.write_text(trpc)

VERIFY_DST.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(VERIFY_SRC, VERIFY_DST)

print("Phase 3B WhatsApp/Messenger reusable scopes + verifier installed.")
print(f"Backup: {BACKUP}")
print("Now wire WhatsApp gateway routes in server/routers.ts and Messenger routes in server/modules/messenger/router.messenger.ts per README. Tara remains excluded.")