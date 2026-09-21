#!/usr/bin/env python3
# FELFEL-GOOGLE-LISTACCOUNTS-VALIDATION-V4
# Fix V3's Google ListAccounts parser.
# Google standard ListAccounts rows are:
# [marker, ..., email@3, ..., valid_session@9, gaia_id@10, ..., signed_out@14, verified@15]

from pathlib import Path
import os

target = Path("/var/www/TCRM-MAIN/ai-staff/felfel/deploy/compose/bin/felfel-auth-identity")
if not target.exists():
    raise SystemExit("PATCH_FAIL=IDENTITY_PROVISIONER_MISSING")

s = target.read_text(encoding="utf-8")

old = '''      ok = accounts.some((account) =>
        Array.isArray(account) &&
        String(account[0] || "").trim().length > 0 &&
        String(account[1] || "").includes("@")
      );'''

new = '''      ok = accounts.some((account) => {
        if (!Array.isArray(account)) return false;
        const email = String(account[3] || "").trim();
        const validSession = account.length > 9 ? Number(account[9]) !== 0 : true;
        const gaiaId = String(account[10] || "").trim();
        const signedOut = account.length > 14 ? Number(account[14]) !== 0 : false;
        const verified = account.length > 15 ? Number(account[15]) !== 0 : true;
        return email.includes("@") && gaiaId.length > 0 && validSession && !signedOut && verified;
      });'''

if new not in s:
    if old not in s:
        raise SystemExit("PATCH_FAIL=V3_LISTACCOUNTS_ANCHOR_MISSING")
    s = s.replace(old, new, 1)

target.write_text(s, encoding="utf-8")
os.chmod(target, 0o755)

print("PATCH=PASS")
print("GOOGLE_VALIDATION=LISTACCOUNTS_FIELDS_FIXED")
print("BUILD_REQUIRED=NO")
