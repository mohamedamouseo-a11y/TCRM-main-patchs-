#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TCRM-MAIN").resolve()
ui_path = root / "client/src/pages/RolesPermissions.tsx"
engine_path = root / "server/security/permissionEngine.ts"

ui = ui_path.read_text()
engine = engine_path.read_text()

checks = {
    "ui-marker": "ADVANCED_PERMISSIONS_PHASE4B_TEMPORARY_ACCESS_UI" in ui,
    "draft-preserves-start": "startsAt?: string | null" in ui,
    "draft-preserves-expiry": "expiresAt?: string | null" in ui,
    "draft-preserves-reason": "reason?: string | null" in ui,
    "hydrate-start": "startsAt: toDateTimeLocalInput(item.startsAt)" in ui,
    "hydrate-expiry": "expiresAt: toDateTimeLocalInput(item.expiresAt)" in ui,
    "save-start-expiry-reason": all(token in ui for token in ["startsAt,", "expiresAt,", "reason: v.reason?.trim() || null"]),
    "datetime-inputs": ui.count('type="datetime-local"') >= 2,
    "engine-marker": "ADVANCED_PERMISSIONS_PHASE4B_TEMPORARY_ACCESS_ENGINE" in engine,
    "engine-honors-start": "AND (upo.starts_at IS NULL OR upo.starts_at <= NOW())" in engine,
    "engine-honors-expiry": "AND (upo.expires_at IS NULL OR upo.expires_at > NOW())" in engine,
}

try:
    changed = subprocess.check_output(["git", "-C", str(root), "diff", "--name-only"], text=True).splitlines()
    untracked = subprocess.check_output(["git", "-C", str(root), "ls-files", "--others", "--exclude-standard"], text=True).splitlines()
except Exception:
    changed, untracked = [], []

expected = {"client/src/pages/RolesPermissions.tsx", "server/security/permissionEngine.ts"}
checks["expected-files-only"] = set(changed) == expected
checks["no-untracked-files"] = len(untracked) == 0
checks["no-db-migration-files"] = not any("migration" in p.lower() or p.lower().endswith("schema.ts") for p in changed)

ok = all(checks.values())
print(json.dumps({
    "ok": ok,
    "phase": "4B-temporary-access-v1",
    "checks": checks,
    "modifiedFiles": changed,
    "untrackedFiles": untracked,
}, indent=2))
raise SystemExit(0 if ok else 1)
