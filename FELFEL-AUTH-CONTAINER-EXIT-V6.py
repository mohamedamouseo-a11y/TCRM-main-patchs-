#!/usr/bin/env python3
# FELFEL-AUTH-CONTAINER-EXIT-V6
from pathlib import Path
import os

target = Path("/var/www/TCRM-MAIN/ai-staff/felfel/deploy/compose/bin/felfel-auth-identity")
if not target.exists():
    raise SystemExit("PATCH_FAIL=IDENTITY_PROVISIONER_MISSING")

s = target.read_text(encoding="utf-8")
old = "    node /app/core/meetings/modules/remote-browser/dist/provision-cli.js\n"
new = "    exec node /app/core/meetings/modules/remote-browser/dist/provision-cli.js\n"

if new not in s:
    if old not in s:
        raise SystemExit("PATCH_FAIL=PROVISION_EXIT_ANCHOR_MISSING")
    s = s.replace(old, new, 1)

target.write_text(s, encoding="utf-8")
os.chmod(target, 0o755)

print("PATCH=PASS")
print("AUTH_CONTAINER_EXIT=FIXED")
print("BUILD_REQUIRED=NO")
