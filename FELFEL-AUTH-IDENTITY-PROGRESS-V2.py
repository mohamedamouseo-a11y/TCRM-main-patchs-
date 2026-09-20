#!/usr/bin/env python3
# FELFEL-AUTH-IDENTITY-PROGRESS-V2
# V1 already applied. This tiny follow-up removes the minio/mc image dependency
# from the one-time identity provisioner and reuses the existing Vexa MinIO
# credentials already present in deploy/compose/.env.

from pathlib import Path
import os

target = Path("/var/www/TCRM-MAIN/ai-staff/felfel/deploy/compose/bin/felfel-auth-identity")
if not target.exists():
    raise SystemExit("PATCH_FAIL=IDENTITY_PROVISIONER_MISSING")

s = target.read_text(encoding="utf-8")

start = 'BOT_ACCESS="$(get_env BOT_S3_ACCESS_KEY)"'
end = 'set_env BOT_USERDATA_S3_PATH "$PREFIX"'

if 'FELFEL_AUTH_MINIO_ROOT_FALLBACK_V2' not in s:
    a = s.find(start)
    b = s.find(end, a)
    if a < 0 or b < 0:
        raise SystemExit("PATCH_FAIL=MINIO_BLOCK_ANCHOR_MISSING")

    replacement = '''# FELFEL_AUTH_MINIO_ROOT_FALLBACK_V2
# Reuse the already-configured Vexa MinIO credentials. This avoids pulling
# minio/mc just to create a second scoped user; the browser-session prefix is
# still isolated by BOT_USERDATA_S3_PATH.
BOT_ACCESS="$ROOT_USER"
BOT_SECRET="$ROOT_PASS"
[ -n "$BOT_ACCESS" ] && [ -n "$BOT_SECRET" ] || {
  echo "RESULT=MINIO_CREDENTIALS_MISSING"
  exit 1
}

'''
    s = s[:a] + replacement + s[b:]

marker = 'echo "RESULT=LOGIN_REQUIRED"'
if 'echo "AUTH_STORAGE=EXISTING_VEXA_MINIO"' not in s:
    if marker not in s:
        raise SystemExit("PATCH_FAIL=RESULT_ANCHOR_MISSING")
    s = s.replace(marker, 'echo "AUTH_STORAGE=EXISTING_VEXA_MINIO"\n' + marker, 1)

target.write_text(s, encoding="utf-8")
os.chmod(target, 0o755)

print("PATCH=PASS")
print("MINIO_MC_DEPENDENCY=REMOVED")
print("AUTH_STORAGE=EXISTING_VEXA_MINIO")
