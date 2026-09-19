#!/usr/bin/env python3
from pathlib import Path
from urllib.request import urlopen

ROOT = Path("/var/www/TCRM-MAIN/ai-staff/felfel")
TARGET = ROOT / "core/meetings/modules/record-chunker/src/index.ts"
URL = "https://raw.githubusercontent.com/Vexa-ai/vexa/dba990b413bd0f888b02d46a24f802db492addbb/core/meetings/modules/record-chunker/src/index.ts"

if not TARGET.exists():
    print("PATCH=FAIL")
    print("ERROR=record_chunker_not_found")
    raise SystemExit(1)

current = TARGET.read_text(encoding="utf-8", errors="replace")
markers = ("initSegmentDelivered", "EBML_MAGIC", "re-attached EBML init segment")
if all(m in current for m in markers):
    print("PATCH=PASS")
    print("ALREADY=YES")
    raise SystemExit(0)

try:
    official = urlopen(URL, timeout=30).read().decode("utf-8")
except Exception as e:
    print("PATCH=FAIL")
    print("ERROR=official_source_download_failed")
    raise SystemExit(1)

if not all(m in official for m in markers):
    print("PATCH=FAIL")
    print("ERROR=official_source_validation_failed")
    raise SystemExit(1)

backup = TARGET.with_suffix(TARGET.suffix + ".pre-ebml-v1.bak")
if not backup.exists():
    backup.write_text(current, encoding="utf-8")

TARGET.write_text(official, encoding="utf-8")

print("PATCH=PASS")
print("ALREADY=NO")
print("FILES=1")
