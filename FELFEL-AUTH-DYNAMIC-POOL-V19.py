#!/usr/bin/env python3
# FELFEL-AUTH-DYNAMIC-POOL-V19
# Makes the authenticated Felfel pool size configuration-driven.
from pathlib import Path
import re

ROOT = Path("/var/www/TCRM-MAIN/ai-staff/felfel")
SERVICE = ROOT / "core/meetings/services/meeting-api/src/meeting_api/bot_spawn/service.py"
COMPOSE = ROOT / "deploy/compose/docker-compose.yml"
ENV = ROOT / "deploy/compose/.env"
BIN = ROOT / "deploy/compose/bin"
DOCKERFILE = ROOT / "deploy/compose/Dockerfile.felfel-dynamic-pool-v19"

for p in (SERVICE, COMPOSE, ENV):
    if not p.exists():
        raise SystemExit(f"PATCH_FAIL=MISSING_{p.name}")

# 1) Runtime selector: derive N sibling auth-session paths from one canonical path.
s = SERVICE.read_text(encoding="utf-8")
old = '''        pooled = [
            item.strip()
            for item in (os.getenv("BOT_USERDATA_S3_PATHS") or "").split(",")
            if item.strip()
        ]
        single = (os.getenv("BOT_USERDATA_S3_PATH") or "").strip()
        auth_userdata_paths = list(dict.fromkeys(pooled or ([single] if single else [])))
'''
new = '''        pooled = [
            item.strip()
            for item in (os.getenv("BOT_USERDATA_S3_PATHS") or "").split(",")
            if item.strip()
        ]
        single = (os.getenv("BOT_USERDATA_S3_PATH") or "").strip().rstrip("/")
        raw_pool_size = (os.getenv("BOT_USERDATA_S3_POOL_SIZE") or "").strip()
        pool_size = 0
        if raw_pool_size:
            try:
                pool_size = int(raw_pool_size)
            except ValueError:
                raise AuthSessionNotConfigured("BOT_USERDATA_S3_POOL_SIZE must be a positive integer")
            if pool_size <= 0:
                raise AuthSessionNotConfigured("BOT_USERDATA_S3_POOL_SIZE must be a positive integer")
        if pool_size and single:
            generated = [single] + [f"{single}-slot-{i}" for i in range(2, pool_size + 1)]
            auth_userdata_paths = generated
        else:
            auth_userdata_paths = list(dict.fromkeys(pooled or ([single] if single else [])))
'''
if new not in s:
    if old not in s:
        raise SystemExit("PATCH_FAIL=POOL_SELECTOR_ANCHOR_MISSING")
    s = s.replace(old, new, 1)
SERVICE.write_text(s, encoding="utf-8")

# 2) Compose passes the dynamic pool-size knob and pins the V19 derived image.
c = COMPOSE.read_text(encoding="utf-8")
anchor = '      - BOT_USERDATA_S3_PATHS=${BOT_USERDATA_S3_PATHS:-}\\n'
line = '      - BOT_USERDATA_S3_POOL_SIZE=${BOT_USERDATA_S3_POOL_SIZE:-}\\n'
if "BOT_USERDATA_S3_POOL_SIZE=${BOT_USERDATA_S3_POOL_SIZE:-}" not in c:
    if anchor not in c:
        raise SystemExit("PATCH_FAIL=COMPOSE_POOL_ENV_ANCHOR_MISSING")
    c = c.replace(anchor, anchor + line, 1)
section_start = c.find("  meeting-api:")
section_end = c.find("\n  gateway:", section_start)
if section_start < 0 or section_end < 0:
    raise SystemExit("PATCH_FAIL=MEETING_API_SECTION_MISSING")
section = c[section_start:section_end]
section, n = re.subn(r"(?m)^    image: vexaai/v012-meeting-api:[^\\n]+$", "    image: vexaai/v012-meeting-api:tcrm-dynamicpool-v19", section, count=1)
if n != 1:
    raise SystemExit("PATCH_FAIL=MEETING_API_IMAGE_MISSING")
c = c[:section_start] + section + c[section_end:]
COMPOSE.write_text(c, encoding="utf-8")

# 3) Configure 10 concurrent authenticated slots now. Future scaling only changes this number.
e = ENV.read_text(encoding="utf-8")
if re.search(r"(?m)^BOT_USERDATA_S3_POOL_SIZE=", e):
    e = re.sub(r"(?m)^BOT_USERDATA_S3_POOL_SIZE=.*$", "BOT_USERDATA_S3_POOL_SIZE=10", e)
else:
    e = e.rstrip() + "\nBOT_USERDATA_S3_POOL_SIZE=10\n"
ENV.write_text(e, encoding="utf-8")

# 4) Expansion helper. It clones ONLY missing sibling slots and never overwrites an existing slot.
BIN.mkdir(parents=True, exist_ok=True)
clone = BIN / "felfel-expand-auth-pool-v19.py"
clone.write_text(r'''#!/usr/bin/env python3
import os
import re
import boto3

def v(name):
    return (os.getenv(name) or "").strip()

source = v("BOT_USERDATA_S3_PATH").rstrip("/")
raw_size = v("BOT_USERDATA_S3_POOL_SIZE")
endpoint = v("BOT_S3_ENDPOINT")
bucket = v("BOT_S3_BUCKET")
access = v("BOT_S3_ACCESS_KEY")
secret = v("BOT_S3_SECRET_KEY")
try:
    size = int(raw_size)
except Exception:
    raise SystemExit("POOL_EXPAND=FAIL BAD_POOL_SIZE")
if not source or size <= 0 or not endpoint or not bucket:
    raise SystemExit("POOL_EXPAND=FAIL CONFIG_INCOMPLETE")

paths = [source] + [f"{source}-slot-{i}" for i in range(2, size + 1)]
s3 = boto3.client("s3", endpoint_url=endpoint, aws_access_key_id=access or None, aws_secret_access_key=secret or None)

def keys(prefix):
    out = []
    token = None
    while True:
        kw = {"Bucket": bucket, "Prefix": prefix.rstrip("/") + "/"}
        if token:
            kw["ContinuationToken"] = token
        r = s3.list_objects_v2(**kw)
        out.extend(x["Key"] for x in r.get("Contents", []))
        if not r.get("IsTruncated"):
            return out
        token = r.get("NextContinuationToken")

all_source = keys(source)
base = source + "/"
source_keys = []
for key in all_source:
    rel = key[len(base):]
    if re.match(r"^slot-[0-9]+/", rel):
        continue
    source_keys.append(key)
if not source_keys:
    raise SystemExit("POOL_EXPAND=FAIL SOURCE_EMPTY")
rels = [k[len(base):] for k in source_keys]
if not any(rel == "Local State" or rel.endswith("/Local State") for rel in rels):
    raise SystemExit("POOL_EXPAND=FAIL LOCAL_STATE_MISSING")
if not any(rel.endswith("Cookies") for rel in rels):
    raise SystemExit("POOL_EXPAND=FAIL COOKIES_MISSING")

print(f"CANONICAL_OBJECTS={len(source_keys)}")
created = 0
for target in paths[1:]:
    existing = keys(target)
    if existing:
        print(f"SLOT={target} STATUS=PRESERVED OBJECTS={len(existing)}")
        continue
    for key in source_keys:
        rel = key[len(base):]
        s3.copy_object(Bucket=bucket, CopySource={"Bucket": bucket, "Key": key}, Key=target + "/" + rel)
    cloned = keys(target)
    if len(cloned) != len(source_keys):
        raise SystemExit(f"POOL_EXPAND=FAIL SLOT={target} EXPECTED={len(source_keys)} GOT={len(cloned)}")
    created += 1
    print(f"SLOT={target} STATUS=CREATED OBJECTS={len(cloned)}")
print(f"POOL_EXPAND=PASS SIZE={size} CREATED={created}")
''', encoding="utf-8")
clone.chmod(0o755)

# 5) Admin helper keeps the Vexa service-user concurrency cap equal to pool size.
admin = BIN / "felfel-sync-max-concurrency-v19.py"
admin.write_text(r'''#!/usr/bin/env python3
from pathlib import Path
import json
import urllib.parse
import urllib.request

ROOT = Path("/var/www/TCRM-MAIN/ai-staff/felfel")
ENV = ROOT / "deploy/compose/.env"

def envfile():
    out = {}
    for raw in ENV.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, value = line.split("=", 1)
        out[k.strip()] = value.strip().strip('"').strip("\'")
    return out

e = envfile()
token = e.get("ADMIN_TOKEN", "")
try:
    size = int(e.get("BOT_USERDATA_S3_POOL_SIZE", "0"))
except ValueError:
    raise SystemExit("MAX_SYNC=FAIL BAD_POOL_SIZE")
if not token or size <= 0:
    raise SystemExit("MAX_SYNC=FAIL CONFIG_INCOMPLETE")

base = "http://127.0.0.1:18057"
email = "tcrm-felfel-adapter@internal.local"
headers = {"X-Admin-API-Key": token, "Accept": "application/json"}
url = base + "/admin/users/email/" + urllib.parse.quote(email, safe="")
req = urllib.request.Request(url, headers=headers, method="GET")
with urllib.request.urlopen(req, timeout=10) as r:
    user = json.loads(r.read().decode("utf-8"))
uid = user.get("id")
if not uid:
    raise SystemExit("MAX_SYNC=FAIL USER_NOT_FOUND")
body = json.dumps({"max_concurrent_bots": size}).encode("utf-8")
headers2 = dict(headers)
headers2["Content-Type"] = "application/json"
req2 = urllib.request.Request(base + f"/admin/users/{uid}", data=body, headers=headers2, method="PATCH")
with urllib.request.urlopen(req2, timeout=10) as r:
    updated = json.loads(r.read().decode("utf-8"))
actual = int(updated.get("max_concurrent_bots", -1))
if actual != size:
    raise SystemExit(f"MAX_SYNC=FAIL EXPECTED={size} GOT={actual}")
print(f"MAX_SYNC=PASS USER_ID={uid} MAX_CONCURRENT_BOTS={actual}")
''', encoding="utf-8")
admin.chmod(0o755)

# 6) COPY-only derived meeting-api image over the proven V18 image.
DOCKERFILE.write_text(r'''ARG BASE_IMAGE=vexaai/v012-meeting-api:tcrm-sessionpool-v18
FROM ${BASE_IMAGE}
COPY core/meetings/services/meeting-api/src/meeting_api/bot_spawn/service.py /app/src/meeting_api/bot_spawn/service.py
RUN python -m py_compile /app/src/meeting_api/bot_spawn/service.py \\
 && grep -q "BOT_USERDATA_S3_POOL_SIZE" /app/src/meeting_api/bot_spawn/service.py \\
 && grep -q "_AUTH_POOL_RESERVATIONS" /app/src/meeting_api/bot_spawn/service.py \\
 && echo "FELFEL_DYNAMIC_POOL=PASS"
''', encoding="utf-8")

print("PATCH=PASS")
print("POOL_MODE=DYNAMIC")
print("POOL_SIZE=10")
print("QUEUE=NONE")
print("SELECTOR=FIRST_FREE")
print("RESERVATION_GUARD=PRESERVED")
print("EXPAND_HELPER=deploy/compose/bin/felfel-expand-auth-pool-v19.py")
print("MAX_SYNC_HELPER=deploy/compose/bin/felfel-sync-max-concurrency-v19.py")
print("DERIVED_DOCKERFILE=deploy/compose/Dockerfile.felfel-dynamic-pool-v19")