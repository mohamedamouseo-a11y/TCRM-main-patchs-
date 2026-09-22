#!/usr/bin/env python3
# FELFEL-AUTH-SESSION-POOL-V18_1
# Repair V18 pool layout: use sibling S3 prefixes, never child prefixes under the canonical profile.
from pathlib import Path
import re

ROOT = Path("/var/www/TCRM-MAIN/ai-staff/felfel")
ENV = ROOT / "deploy/compose/.env"
BIN = ROOT / "deploy/compose/bin"

if not ENV.exists():
    raise SystemExit("PATCH_FAIL=ENV_MISSING")

e = ENV.read_text(encoding="utf-8")
m = re.search(r"(?m)^BOT_USERDATA_S3_PATH=(.*)$", e)
if not m:
    raise SystemExit("PATCH_FAIL=CANONICAL_PATH_MISSING")
canonical = m.group(1).strip().strip('"').strip("\'").rstrip("/")
if not canonical:
    raise SystemExit("PATCH_FAIL=CANONICAL_PATH_EMPTY")

# Slot 1 is the canonical profile itself. Extra slots are SIBLINGS, not children.
# Child prefixes caused recursive cloning (23 -> 46 -> 92 objects).
pool = ",".join([canonical, canonical + "-slot-2", canonical + "-slot-3"])
if re.search(r"(?m)^BOT_USERDATA_S3_PATHS=", e):
    e = re.sub(r"(?m)^BOT_USERDATA_S3_PATHS=.*$", "BOT_USERDATA_S3_PATHS=" + pool, e)
else:
    e = e.rstrip() + "\nBOT_USERDATA_S3_PATHS=" + pool + "\n"
ENV.write_text(e, encoding="utf-8")

BIN.mkdir(parents=True, exist_ok=True)
helper = BIN / "felfel-repair-auth-pool-v18_1.py"
helper.write_text(r'''#!/usr/bin/env python3
import os
import re
import boto3

def v(name):
    return (os.getenv(name) or "").strip()

source = v("BOT_USERDATA_S3_PATH").rstrip("/")
paths = [p.strip().rstrip("/") for p in v("BOT_USERDATA_S3_PATHS").split(",") if p.strip()]
endpoint = v("BOT_S3_ENDPOINT")
bucket = v("BOT_S3_BUCKET")
access = v("BOT_S3_ACCESS_KEY")
secret = v("BOT_S3_SECRET_KEY")

if not source or len(paths) != 3 or paths[0] != source:
    raise SystemExit("POOL_REPAIR=FAIL BAD_POOL_LAYOUT")
if any(p.startswith(source + "/") for p in paths[1:]):
    raise SystemExit("POOL_REPAIR=FAIL NESTED_TARGET_FORBIDDEN")
if not endpoint or not bucket:
    raise SystemExit("POOL_REPAIR=FAIL S3_CONFIG_INCOMPLETE")

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

def delete_prefix(prefix):
    ks = keys(prefix)
    for i in range(0, len(ks), 1000):
        batch = ks[i:i+1000]
        if batch:
            s3.delete_objects(Bucket=bucket, Delete={"Objects": [{"Key": k} for k in batch], "Quiet": True})
    return len(ks)

all_source = keys(source)
base = source + "/"
clean_source = []
legacy_nested = []
for k in all_source:
    rel = k[len(base):]
    if re.match(r"^slot-[0-9]+/", rel):
        legacy_nested.append(k)
    else:
        clean_source.append(k)

if not clean_source:
    raise SystemExit("POOL_REPAIR=FAIL CANONICAL_EMPTY")
rels = [k[len(base):] for k in clean_source]
if not any(rel == "Local State" or rel.endswith("/Local State") for rel in rels):
    raise SystemExit("POOL_REPAIR=FAIL LOCAL_STATE_MISSING")
if not any(rel.endswith("Cookies") for rel in rels):
    raise SystemExit("POOL_REPAIR=FAIL COOKIES_MISSING")

print(f"CANONICAL_OBJECTS={len(clean_source)}")
print(f"LEGACY_NESTED_OBJECTS={len(legacy_nested)}")

# Recreate only sibling clone slots. Canonical top-level profile is never deleted.
for target in paths[1:]:
    removed = delete_prefix(target)
    for key in clean_source:
        rel = key[len(base):]
        s3.copy_object(Bucket=bucket, CopySource={"Bucket": bucket, "Key": key}, Key=target + "/" + rel)
    cloned = keys(target)
    if len(cloned) != len(clean_source):
        raise SystemExit(f"POOL_REPAIR=FAIL SLOT={target} EXPECTED={len(clean_source)} GOT={len(cloned)}")
    print(f"SLOT={target} RESET_REMOVED={removed} OBJECTS={len(cloned)}")

# Remove only the malformed child slot prefixes created by V18.
for child in ("slot-1", "slot-2", "slot-3"):
    removed = delete_prefix(source + "/" + child)
    if removed:
        print(f"LEGACY_CHILD={child} REMOVED={removed}")

# Final invariant: each slot has exactly the same object count.
counts = [len(keys(p)) for p in paths]
if len(set(counts)) != 1:
    raise SystemExit("POOL_REPAIR=FAIL COUNT_MISMATCH " + ",".join(map(str, counts)))
print("POOL_REPAIR=PASS COUNTS=" + ",".join(map(str, counts)))
''', encoding="utf-8")
helper.chmod(0o755)

print("PATCH=PASS")
print("POOL_LAYOUT=SIBLING_PREFIXES")
print("POOL_SIZE=3")
print("POOL_PATHS=" + pool)
print("REPAIR_HELPER=deploy/compose/bin/felfel-repair-auth-pool-v18_1.py")