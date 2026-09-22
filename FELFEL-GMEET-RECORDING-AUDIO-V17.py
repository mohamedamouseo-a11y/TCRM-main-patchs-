#!/usr/bin/env python3
# FELFEL-GMEET-RECORDING-AUDIO-V17
# Root cause: @vexa/record-chunker creates an AudioContext for the combined
# Google Meet recording mix but never resumes it. In headless Chromium the
# context can remain suspended by autoplay policy, yielding valid containers
# filled with digital silence (~ -91 dB).
#
# Fix source + prepare a small derived image that rebuilds only record-chunker
# and browser-utils.global.js (NOT the full Vexa image).

from pathlib import Path

ROOT = Path("/var/www/TCRM-MAIN/ai-staff/felfel")
src = ROOT / "core/meetings/modules/record-chunker/src/index.ts"

if not src.exists():
    raise SystemExit("PATCH_FAIL=RECORD_CHUNKER_SOURCE_MISSING")

s = src.read_text(encoding="utf-8")

old = '''  const ctx = new AudioContext();
  const dest = ctx.createMediaStreamDestination();'''

new = '''  const ctx = new AudioContext();
  // Headless Chromium may create this context suspended because there is no
  // user gesture. A suspended mixer still gives MediaRecorder a valid track,
  // but that track contains digital silence. Resume before wiring sources.
  try {
    if (ctx.state === "suspended") await ctx.resume();
    blog(`[record-chunker] mix AudioContext state=${ctx.state}`);
  } catch (e: any) {
    blog(`[record-chunker] mix AudioContext resume failed: ${e?.message || e}`);
  }
  const dest = ctx.createMediaStreamDestination();'''

if new not in s:
    if old not in s:
        raise SystemExit("PATCH_FAIL=AUDIOCONTEXT_ANCHOR_MISSING")
    s = s.replace(old, new, 1)
    src.write_text(s, encoding="utf-8")

compose = ROOT / "deploy/compose"
compose.mkdir(parents=True, exist_ok=True)

dockerfile = compose / "Dockerfile.felfel-recording-audio-v17"
dockerfile.write_text(r'''ARG BASE_IMAGE=vexaai/vexa-bot:tcrm-authfix-v12
FROM ${BASE_IMAGE}

WORKDIR /app

# Bring in only the patched source file from the existing Vexa tree.
COPY core/meetings/modules/record-chunker/src/index.ts /app/core/meetings/modules/record-chunker/src/index.ts

# Rebuild ONLY the browser recording brick, then regenerate the bot's browser bundle.
# No dependency install, no browser download, no full bot/Vexa rebuild.
RUN corepack pnpm --dir /app --filter "@vexa/record-chunker" run build \
 && cd /app/core/meetings/services/bot \
 && node build-browser-utils.mjs \
 && cp dist/browser-utils.global.js /app/browser-utils.global.js \
 && grep -q "mix AudioContext state=" /app/browser-utils.global.js \
 && echo "RECORDING_AUDIO_RESUME=PASS"
''', encoding="utf-8")

print("PATCH=PASS")
print("FILES=2")
print("AUDIO_CONTEXT_RESUME=ADDED")
print("DERIVED_DOCKERFILE=deploy/compose/Dockerfile.felfel-recording-audio-v17")
print("FULL_VEXA_BUILD_REQUIRED=NO")
