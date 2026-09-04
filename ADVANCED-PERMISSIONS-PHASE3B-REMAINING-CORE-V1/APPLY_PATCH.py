#!/usr/bin/env python3
from pathlib import Path
import shutil, sys, time

ROOT = Path(__file__).resolve().parent
TARGET = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TCRM-MAIN").resolve()
FILES = ROOT / "files"
BACKUP = TARGET / ".patch-backups" / f"advanced-permissions-phase3b-remaining-core-{int(time.time())}"

trpc_path = TARGET / "server/_core/trpc.ts"
routers_path = TARGET / "server/routers.ts"
if not trpc_path.exists() or not routers_path.exists():
    raise SystemExit("Missing TCRM server baseline files")

routers = routers_path.read_text()
if "ADVANCED_PERMISSIONS_PHASE3B_V1" not in routers:
    raise SystemExit("Phase 3B V1 baseline is required")
if "permissionsAdmin" not in routers:
    raise SystemExit("Phase 3B V2 baseline is required")

BACKUP.mkdir(parents=True, exist_ok=True)
for rel in ["server/_core/trpc.ts", "server/routers.ts"]:
    src = TARGET / rel
    dst = BACKUP / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

trpc = trpc_path.read_text()
marker = "// ADVANCED_PERMISSIONS_PHASE3B_REMAINING_CORE_V1"
if marker not in trpc:
    anchor = 'export const contractsExportScope = phase3Scope("contracts.export");\n'
    if anchor not in trpc:
        # Older/current Phase3B may not export contractsExportScope yet; anchor after contractsEditScope.
        anchor = 'export const contractsEditScope = phase3Scope("contracts.edit");\n'
    if anchor not in trpc:
        raise SystemExit("Could not find Phase3B scope export anchor in trpc.ts")
    addition = anchor + f'''\n{marker}\nexport const campaignsViewScope = phase3Scope("campaigns.view");\nexport const campaignsCreateScope = phase3Scope("campaigns.create");\nexport const campaignsEditScope = phase3Scope("campaigns.edit");\nexport const campaignsDeleteScope = phase3Scope("campaigns.delete");\nexport const campaignsExportScope = phase3Scope("campaigns.export");\nexport const reportsViewScope = phase3Scope("reports.view");\nexport const reportsExportScope = phase3Scope("reports.export");\nexport const notificationsViewScope = phase3Scope("notifications.view");\nexport const notificationsManageScope = phase3Scope("notifications.manage");\nexport const auditViewScope = phase3Scope("audit.view");\nexport const auditExportScope = phase3Scope("audit.export");\n'''
    trpc = trpc.replace(anchor, addition, 1)
    trpc_path.write_text(trpc)

# Install verifier. Router wiring is intentionally reviewed/manual because current routers.ts
# contains several campaign/report/notification/audit surfaces with legacy guards.
for rel in ["scripts/verify-advanced-permissions-phase3b-remaining-core.ts"]:
    src = FILES / rel
    dst = TARGET / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

print("Phase 3B Remaining Core reusable guards installed.")
print(f"Backup: {BACKUP}")
print("NEXT: wire server/routers.ts per README with smallest safe additive diff, then run verifier.")