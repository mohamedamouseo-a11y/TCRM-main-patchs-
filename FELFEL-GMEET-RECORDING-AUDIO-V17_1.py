#!/usr/bin/env python3
# FELFEL-GMEET-RECORDING-AUDIO-V17_1
# Reproducible COPY-only version of V17.
# It patches the already-built browser-utils bundle from the current V12 base
# instead of trying to rebuild @vexa/record-chunker inside the runtime image.

from pathlib import Path
import subprocess, tempfile, shutil, sys

ROOT = Path("/var/www/TCRM-MAIN/ai-staff/felfel")
COMPOSE = ROOT / "deploy/compose"
COMPOSE.mkdir(parents=True, exist_ok=True)

BASE = "vexaai/vexa-bot:tcrm-authfix-v12"
OUT = COMPOSE / "browser-utils.felfel-audio-v17.js"
DOCKERFILE = COMPOSE / "Dockerfile.felfel-recording-audio-v17-copy"

# Also keep the checked-in TS source correct for any future full rebuild.
src = ROOT / "core/meetings/modules/record-chunker/src/index.ts"
if src.exists():
    s = src.read_text(encoding="utf-8")
    old = """  const ctx = new AudioContext();
  const dest = ctx.createMediaStreamDestination();"""
    new = """  const ctx = new AudioContext();
  // Headless Chromium can leave this mixer suspended; MediaRecorder then writes
  // a structurally valid but digitally silent track. Resume before wiring sources.
  try {
    if (ctx.state === "suspended") await ctx.resume();
    blog(`[record-chunker] mix AudioContext state=${ctx.state}`);
  } catch (e: any) {
    blog(`[record-chunker] mix AudioContext resume failed: ${e?.message || e}`);
  }
  const dest = ctx.createMediaStreamDestination();"""
    if new not in s:
        if old not in s:
            raise SystemExit("PATCH_FAIL=TS_AUDIOCONTEXT_ANCHOR_MISSING")
        src.write_text(s.replace(old, new, 1), encoding="utf-8")

# Extract the prebuilt browser bundle from the proven base image.
cid = subprocess.check_output(["docker", "create", BASE], text=True).strip()
try:
    with tempfile.TemporaryDirectory() as td:
        extracted = Path(td) / "browser-utils.global.js"
        subprocess.check_call(["docker", "cp", f"{cid}:/app/browser-utils.global.js", str(extracted)])
        js = extracted.read_text(encoding="utf-8")

        marker = 'mix AudioContext state='
        if marker not in js:
            old_js = """const ctx = new AudioContext();
    const dest = ctx.createMediaStreamDestination();"""
            new_js = """const ctx = new AudioContext();
    try {
      if (ctx.state === "suspended") await ctx.resume();
      blog(`[record-chunker] mix AudioContext state=${ctx.state}`);
    } catch (e) {
      blog(`[record-chunker] mix AudioContext resume failed: ${e?.message || e}`);
    }
    const dest = ctx.createMediaStreamDestination();"""
            if old_js not in js:
                old_js = """const ctx = new AudioContext();
  const dest = ctx.createMediaStreamDestination();"""
                new_js = """const ctx = new AudioContext();
  try {
    if (ctx.state === "suspended") await ctx.resume();
    blog(`[record-chunker] mix AudioContext state=${ctx.state}`);
  } catch (e) {
    blog(`[record-chunker] mix AudioContext resume failed: ${e?.message || e}`);
  }
  const dest = ctx.createMediaStreamDestination();"""
            if old_js not in js:
                raise SystemExit("PATCH_FAIL=BUNDLE_AUDIOCONTEXT_ANCHOR_MISSING")
            js = js.replace(old_js, new_js, 1)

        if js.count(marker) != 1:
            raise SystemExit(f"PATCH_FAIL=EXPECTED_ONE_AUDIO_RESUME_GOT_{js.count(marker)}")
        OUT.write_text(js, encoding="utf-8")
finally:
    subprocess.call(["docker", "rm", "-f", cid], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

DOCKERFILE.write_text(r'''ARG BASE_IMAGE=vexaai/vexa-bot:tcrm-authfix-v12
FROM ${BASE_IMAGE}

COPY deploy/compose/browser-utils.felfel-audio-v17.js /app/browser-utils.global.js
COPY deploy/compose/browser-utils.felfel-audio-v17.js /app/core/meetings/services/bot/dist/browser-utils.global.js

RUN grep -q "mix AudioContext state=" /app/browser-utils.global.js \
 && grep -q "mix AudioContext state=" /app/core/meetings/services/bot/dist/browser-utils.global.js \
 && echo "RECORDING_AUDIO_RESUME=PASS"
''', encoding="utf-8")

print("PATCH=PASS")
print("MODE=COPY_ONLY")
print("TS_SOURCE=FIXED")
print("BUNDLE=PATCHED")
print("DOCKERFILE=deploy/compose/Dockerfile.felfel-recording-audio-v17-copy")
print("FULL_VEXA_BUILD_REQUIRED=NO")
