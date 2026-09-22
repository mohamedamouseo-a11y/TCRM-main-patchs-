#!/usr/bin/env python3
# FELFEL-AUTH-SESSION-POOL-V18
from pathlib import Path
import re

ROOT = Path("/var/www/TCRM-MAIN/ai-staff/felfel")
SERVICE = ROOT / "core/meetings/services/meeting-api/src/meeting_api/bot_spawn/service.py"
COMPOSE = ROOT / "deploy/compose/docker-compose.yml"
ENV = ROOT / "deploy/compose/.env"
BIN = ROOT / "deploy/compose/bin"
DOCKERFILE = ROOT / "deploy/compose/Dockerfile.felfel-session-pool-v18"

for p in (SERVICE, COMPOSE, ENV):
    if not p.exists():
        raise SystemExit(f"PATCH_FAIL=MISSING_{p.name}")

s = SERVICE.read_text(encoding="utf-8")

# In-process reservation closes the tiny race where two simultaneous POST /bots
# requests could both observe the same free S3 slot before either meeting row is
# inserted. Reservations expire automatically if a request aborts before insert.
if "\nimport time\n" not in s:
    if "import re\nimport uuid\n" not in s:
        raise SystemExit("PATCH_FAIL=IMPORT_ANCHOR_MISSING")
    s = s.replace("import re\nimport uuid\n", "import re\nimport time\nimport uuid\n", 1)

reservation_anchor = "_STT_VERDICT_MAX_AGE_S = 60.0\n"
reservation_block = """_STT_VERDICT_MAX_AGE_S = 60.0

# TCRM Felfel pool: transient reservation between slot selection and DB insert.
_AUTH_POOL_RESERVATIONS: dict[str, float] = {}
_AUTH_POOL_RESERVATION_TTL_S = 60.0
"""
if "_AUTH_POOL_RESERVATIONS" not in s:
    if reservation_anchor not in s:
        raise SystemExit("PATCH_FAIL=RESERVATION_ANCHOR_MISSING")
    s = s.replace(reservation_anchor, reservation_block, 1)

block_re = re.compile(
    r'    authenticated = env_flag\("BOT_AUTHENTICATED", False\)\n'
    r'    auth_userdata_path: Optional\[str\] = None\n'
    r'    auth_s3: dict\[str, Optional\[str\]\] = \{\}\n'
    r'    if authenticated:\n'
    r'(?:(?!\n    # 2c\.).)*',
    re.S,
)

new_auth = '''    authenticated = env_flag("BOT_AUTHENTICATED", False)
    auth_userdata_path: Optional[str] = None
    auth_userdata_paths: list[str] = []
    auth_s3: dict[str, Optional[str]] = {}
    if authenticated:
        pooled = [
            item.strip()
            for item in (os.getenv("BOT_USERDATA_S3_PATHS") or "").split(",")
            if item.strip()
        ]
        single = (os.getenv("BOT_USERDATA_S3_PATH") or "").strip()
        auth_userdata_paths = list(dict.fromkeys(pooled or ([single] if single else [])))
        auth_s3 = {
            "s3_endpoint": os.getenv("BOT_S3_ENDPOINT") or None,
            "s3_bucket": os.getenv("BOT_S3_BUCKET") or None,
            "s3_access_key": os.getenv("BOT_S3_ACCESS_KEY") or None,
            "s3_secret_key": os.getenv("BOT_S3_SECRET_KEY") or None,
        }
        if not (auth_userdata_paths and auth_s3["s3_endpoint"] and auth_s3["s3_bucket"]):
            raise AuthSessionNotConfigured(
                "BOT_AUTHENTICATED is set but the userdata pool/store is incomplete"
            )

        now = time.monotonic()
        for reserved_path, reserved_at in list(_AUTH_POOL_RESERVATIONS.items()):
            if now - reserved_at > _AUTH_POOL_RESERVATION_TTL_S:
                _AUTH_POOL_RESERVATIONS.pop(reserved_path, None)

        busy: list[dict] = []
        for candidate in auth_userdata_paths:
            if candidate in _AUTH_POOL_RESERVATIONS:
                busy.append({"id": "reserved"})
                continue
            conflict = await repo.find_active_by_userdata(candidate)
            if conflict is None:
                _AUTH_POOL_RESERVATIONS[candidate] = now
                auth_userdata_path = candidate
                break
            busy.append(conflict)

        if auth_userdata_path is None:
            first = busy[0] if busy else {"id": "unknown"}
            raise AuthSessionBusy(
                first.get("id"),
                f"Felfel auth pool exhausted ({len(auth_userdata_paths)} sessions)",
            )
'''

if "BOT_USERDATA_S3_PATHS" not in s:
    s, n = block_re.subn(new_auth, s, count=1)
    if n != 1:
        raise SystemExit("PATCH_FAIL=AUTH_BLOCK_ANCHOR_MISSING")
release_anchor = '    meeting_id = row["id"]\n'
if "TCRM_FELFEL_POOL_RELEASE" not in s:
    if release_anchor not in s:
        raise SystemExit("PATCH_FAIL=POOL_RELEASE_ANCHOR_MISSING")
    s = s.replace(
        release_anchor,
        release_anchor
        + "    # TCRM_FELFEL_POOL_RELEASE: the DB row now owns the selected slot.\n"
        + "    if auth_userdata_path:\n"
        + "        _AUTH_POOL_RESERVATIONS.pop(auth_userdata_path, None)\n",
        1,
    )

SERVICE.write_text(s, encoding="utf-8")

c = COMPOSE.read_text(encoding="utf-8")
env_anchor = '      - BOT_USERDATA_S3_PATH=${BOT_USERDATA_S3_PATH:-}\n'
if 'BOT_USERDATA_S3_PATHS=${BOT_USERDATA_S3_PATHS:-}' not in c:
    if env_anchor not in c:
        raise SystemExit("PATCH_FAIL=COMPOSE_AUTH_ENV_ANCHOR_MISSING")
    c = c.replace(env_anchor, env_anchor + '      - BOT_USERDATA_S3_PATHS=${BOT_USERDATA_S3_PATHS:-}\n', 1)

image_old = '    image: vexaai/v012-meeting-api:${IMAGE_TAG:-dev}\n'
image_new = '    image: vexaai/v012-meeting-api:tcrm-sessionpool-v18\n'
if image_new not in c:
    if image_old not in c:
        raise SystemExit("PATCH_FAIL=MEETING_API_IMAGE_ANCHOR_MISSING")
    c = c.replace(image_old, image_new, 1)
COMPOSE.write_text(c, encoding="utf-8")

e = ENV.read_text(encoding="utf-8")
m = re.search(r'(?m)^BOT_USERDATA_S3_PATH=(.*)$', e)
if not m:
    raise SystemExit("PATCH_FAIL=BOT_USERDATA_S3_PATH_MISSING")
canonical = m.group(1).strip().strip('"').strip("'")
if not canonical:
    raise SystemExit("PATCH_FAIL=BOT_USERDATA_S3_PATH_EMPTY")
pool = ",".join([canonical, canonical + "-slot-2", canonical + "-slot-3"])
if re.search(r'(?m)^BOT_USERDATA_S3_PATHS=', e):
    e = re.sub(r'(?m)^BOT_USERDATA_S3_PATHS=.*$', f'BOT_USERDATA_S3_PATHS={pool}', e)
else:
    e = e.rstrip() + f"\nBOT_USERDATA_S3_PATHS={pool}\n"
ENV.write_text(e, encoding="utf-8")

BIN.mkdir(parents=True, exist_ok=True)
helper = BIN / "felfel-clone-auth-pool-v18.py"
helper.write_text('''#!/usr/bin/env python3
import os
import boto3

def v(name):
    return (os.getenv(name) or "").strip()

source = v("BOT_USERDATA_S3_PATH").rstrip("/")
paths = [p.strip().rstrip("/") for p in v("BOT_USERDATA_S3_PATHS").split(",") if p.strip()]
endpoint = v("BOT_S3_ENDPOINT")
bucket = v("BOT_S3_BUCKET")
access = v("BOT_S3_ACCESS_KEY")
secret = v("BOT_S3_SECRET_KEY")
if not source or len(paths) < 2 or not endpoint or not bucket:
    raise SystemExit("POOL_CLONE=FAIL CONFIG_INCOMPLETE")
s3 = boto3.client("s3", endpoint_url=endpoint, aws_access_key_id=access or None, aws_secret_access_key=secret or None)

def keys(prefix):
    out = []
    token = None
    while True:
        kw = {"Bucket": bucket, "Prefix": prefix.rstrip("/") + "/"}
        if token:
            kw["ContinuationToken"] = token
        r = s3.list_objects_v2(**kw)
        out.extend([x["Key"] for x in r.get("Contents", [])])
        if not r.get("IsTruncated"):
            break
        token = r.get("NextContinuationToken")
    return out

source_keys = keys(source)
if not source_keys:
    raise SystemExit("POOL_CLONE=FAIL SOURCE_EMPTY")
names = [k[len(source.rstrip("/") + "/"):] for k in source_keys]
if not any("Local State" in n for n in names):
    raise SystemExit("POOL_CLONE=FAIL SOURCE_LOCAL_STATE_MISSING")
if not any(n.endswith("Cookies") or "/Cookies" in n for n in names):
    raise SystemExit("POOL_CLONE=FAIL SOURCE_COOKIES_MISSING")
print(f"SOURCE_OBJECTS={len(source_keys)}")
for target in paths:
    if target == source:
        print(f"SLOT={target} STATUS=CANONICAL OBJECTS={len(source_keys)}")
        continue
    existing = keys(target)
    if existing:
        print(f"SLOT={target} STATUS=EXISTS OBJECTS={len(existing)}")
        continue
    for key in source_keys:
        suffix = key[len(source.rstrip("/") + "/"):]
        s3.copy_object(Bucket=bucket, CopySource={"Bucket": bucket, "Key": key}, Key=target.rstrip("/") + "/" + suffix)
    cloned = keys(target)
    if len(cloned) != len(source_keys):
        raise SystemExit(f"POOL_CLONE=FAIL SLOT={target} EXPECTED={len(source_keys)} GOT={len(cloned)}")
    print(f"SLOT={target} STATUS=CLONED OBJECTS={len(cloned)}")
print(f"POOL_CLONE=PASS SLOTS={len(paths)}")
''', encoding="utf-8")
helper.chmod(0o755)

DOCKERFILE.write_text('''ARG BASE_IMAGE=vexaai/v012-meeting-api:dev
FROM ${BASE_IMAGE}
COPY core/meetings/services/meeting-api/src/meeting_api/bot_spawn/service.py /app/src/meeting_api/bot_spawn/service.py
RUN python -m py_compile /app/src/meeting_api/bot_spawn/service.py \\
 && grep -q "BOT_USERDATA_S3_PATHS" /app/src/meeting_api/bot_spawn/service.py \\
 && echo "FELFEL_SESSION_POOL=PASS"
''', encoding="utf-8")

print("PATCH=PASS")
print("POOL_SIZE=3")
print(f"POOL_PATHS={pool}")
print("MEETING_API_POOL=FIRST_FREE_SESSION")
print("QUEUE=NONE")
print("PER_SESSION_SERIALIZATION=PRESERVED")
print("CLONE_HELPER=deploy/compose/bin/felfel-clone-auth-pool-v18.py")
print("DERIVED_DOCKERFILE=deploy/compose/Dockerfile.felfel-session-pool-v18")
