#!/usr/bin/env python3
# FELFEL-GOOGLE-LISTACCOUNTS-VALIDATION-V5
# Fix V4 validation: Google ListAccounts is nested and account rows are marked
# with "gaia.l.a"; email is field index 3. Do not assume parsed[1] or fixed
# session/gaia indexes.

from pathlib import Path
import os

target = Path("/var/www/TCRM-MAIN/ai-staff/felfel/deploy/compose/bin/felfel-auth-identity")
if not target.exists():
    raise SystemExit("PATCH_FAIL=IDENTITY_PROVISIONER_MISSING")

s = target.read_text(encoding="utf-8")

old = '''      const parsed = JSON.parse(body);
      const accounts = Array.isArray(parsed) && Array.isArray(parsed[1]) ? parsed[1] : [];
      ok = accounts.some((account) => {
        if (!Array.isArray(account)) return false;
        const email = String(account[3] || "").trim();
        const validSession = account.length > 9 ? Number(account[9]) !== 0 : true;
        const gaiaId = String(account[10] || "").trim();
        const signedOut = account.length > 14 ? Number(account[14]) !== 0 : false;
        const verified = account.length > 15 ? Number(account[15]) !== 0 : true;
        return email.includes("@") && gaiaId.length > 0 && validSession && !signedOut && verified;
      });'''

new = '''      const parsed = JSON.parse(body);
      const accounts = [];
      const walk = (value) => {
        if (!Array.isArray(value)) return;
        if (value[0] === "gaia.l.a" && String(value[3] || "").includes("@")) {
          accounts.push(value);
          return;
        }
        for (const child of value) walk(child);
      };
      walk(parsed);
      ok = accounts.length > 0;'''

if new not in s:
    if old not in s:
        raise SystemExit("PATCH_FAIL=V4_LISTACCOUNTS_ANCHOR_MISSING")
    s = s.replace(old, new, 1)

target.write_text(s, encoding="utf-8")
os.chmod(target, 0o755)

print("PATCH=PASS")
print("GOOGLE_VALIDATION=LISTACCOUNTS_RECURSIVE_GAIA_MARKER")
print("BUILD_REQUIRED=NO")
