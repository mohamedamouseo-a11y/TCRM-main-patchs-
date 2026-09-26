#!/usr/bin/env python3
# FELFEL-SESSION-PERSISTENCE-V20
# Root cause: authenticated browser session write-back runs after non-critical
# signal-tape upload during teardown. The SIGTERM watchdog can force-exit first,
# leaving S3 userdata empty. Prioritize session.close() before telemetry upload.
#
# Deployment image is derived COPY-only from the proven V17 bot image.

from pathlib import Path
import subprocess
import tempfile

ROOT = Path("/var/www/TCRM-MAIN/ai-staff/felfel")
SRC = ROOT / "core/meetings/services/bot/src/index.ts"
COMPOSE = ROOT / "deploy/compose"
OUT = COMPOSE / "bot-index.felfel-sessionpersist-v20.js"
DOCKERFILE = COMPOSE / "Dockerfile.felfel-session-persistence-v20"

BASE_IMAGE = "vexaai/vexa-bot:tcrm-audiofix-v17"
TARGET_IMAGE = "vexaai/vexa-bot:tcrm-sessionpersist-v20"
MARKER = "TCRM_FELFEL_SESSION_PERSISTENCE_V20"

if not SRC.exists():
    raise SystemExit("PATCH_FAIL=BOT_INDEX_SOURCE_MISSING")

def reorder_close_before_tape(text: str, label: str) -> str:
    lines = text.splitlines(keepends=True)
    upload_i = next((i for i, line in enumerate(lines) if "await uploadSignalTapes(signalRecorder" in line), None)
    close_i = next((i for i, line in enumerate(lines) if "if (session) await session.close()" in line), None)

    if upload_i is None or close_i is None:
        raise SystemExit(f"PATCH_FAIL={label}_TEARDOWN_ANCHOR_MISSING")

    if close_i < upload_i:
        if MARKER not in text:
            indent = lines[close_i][:len(lines[close_i]) - len(lines[close_i].lstrip())]
            lines.insert(close_i, f"{indent}// {MARKER}: persist auth before non-critical telemetry upload.\n")
        return "".join(lines)

    if close_i != upload_i + 1:
        raise SystemExit(f"PATCH_FAIL={label}_UNEXPECTED_TEARDOWN_ORDER")

    close_line = lines.pop(close_i)
    indent = lines[upload_i][:len(lines[upload_i]) - len(lines[upload_i].lstrip())]
    lines.insert(upload_i, close_line)
    lines.insert(upload_i, f"{indent}// {MARKER}: persist auth before non-critical telemetry upload.\n")
    return "".join(lines)

# 1) Keep canonical TS source correct for future full rebuilds.
src_text = SRC.read_text(encoding="utf-8")
SRC.write_text(reorder_close_before_tape(src_text, "SOURCE"), encoding="utf-8")

# 2) Patch the already-built bot entrypoint from the current proven image.
COMPOSE.mkdir(parents=True, exist_ok=True)
cid = subprocess.check_output(["docker", "create", BASE_IMAGE], text=True).strip()
try:
    with tempfile.TemporaryDirectory() as td:
        extracted = Path(td) / "index.js"
        subprocess.check_call([
            "docker", "cp",
            f"{cid}:/app/core/meetings/services/bot/dist/index.js",
            str(extracted),
        ])
        js = extracted.read_text(encoding="utf-8")
        OUT.write_text(reorder_close_before_tape(js, "BUNDLE"), encoding="utf-8")
finally:
    subprocess.call(
        ["docker", "rm", "-f", cid],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

# 3) Build a tiny derived image; no dependency install / full Vexa rebuild.
DOCKERFILE.write_text(f'''ARG BASE_IMAGE={BASE_IMAGE}
FROM {BASE_IMAGE}

COPY deploy/compose/{OUT.name} /app/core/meetings/services/bot/dist/index.js

RUN grep -q "{MARKER}" /app/core/meetings/services/bot/dist/index.js \\
 && python - <<'PY'
from pathlib import Path
s = Path("/app/core/meetings/services/bot/dist/index.js").read_text()
a = s.index("if (session) await session.close()")
b = s.index("await uploadSignalTapes(signalRecorder")
assert a < b, "session.close must precede signal tape upload"
print("FELFEL_SESSION_PERSISTENCE=PASS")
PY
''', encoding="utf-8")

print("PATCH=PASS")
print(f"BASE_IMAGE={BASE_IMAGE}")
print(f"TARGET_IMAGE={TARGET_IMAGE}")
print("TEARDOWN_ORDER=SESSION_CLOSE_BEFORE_SIGNAL_UPLOAD")
print("GRACE_UNCHANGED=YES")
print(f"DOCKERFILE={DOCKERFILE.relative_to(ROOT)}")
print(f"BUNDLE={OUT.relative_to(ROOT)}")
print("FULL_VEXA_BUILD_REQUIRED=NO")
