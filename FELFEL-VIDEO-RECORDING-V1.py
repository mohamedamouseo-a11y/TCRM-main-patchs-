#!/usr/bin/env python3
# FELFEL-VIDEO-RECORDING-V1
# Enables real server-side meeting video capture in the bundled Vexa v0.12 runtime,
# then lets TCRM retrieve video first while keeping audio as fallback.
#
# Source implementation: Vexa maintainer videorec work
#   9d0de1f50f03d18930b82a25321bf4856aa5719a
#   a0a4b6b017b2ba502a87bceeb3cf976038f469e2

from __future__ import annotations

import json
import re
import subprocess
import tempfile
import urllib.request
from pathlib import Path

TCRM = Path("/var/www/TCRM-MAIN")
VEXA = TCRM / "ai-staff" / "felfel"
ADAPTER = TCRM / "server" / "services" / "felfel" / "felfelAdapter.ts"
COMPOSE = VEXA / "deploy" / "compose" / "docker-compose.yml"
SPAWN_SERVICE = VEXA / "core" / "meetings" / "services" / "meeting-api" / "src" / "meeting_api" / "bot_spawn" / "service.py"
BOT_DOCKERFILE = VEXA / "core" / "meetings" / "services" / "bot" / "Dockerfile"
BOT_INDEX = VEXA / "core" / "meetings" / "services" / "bot" / "src" / "index.ts"
BOT_PIPELINE = VEXA / "core" / "meetings" / "services" / "bot" / "src" / "pipeline.ts"
BOT_VIDEO = VEXA / "core" / "meetings" / "services" / "bot" / "src" / "video-recording.ts"
BROWSER_ARGS = VEXA / "core" / "meetings" / "modules" / "join" / "src" / "browser-args.ts"
VIDEO_SERVICE = VEXA / "core" / "meetings" / "modules" / "recording" / "src" / "video-recording.ts"
MARKER = TCRM / ".felfel_video_recording_v1"

VIDEO_COMMIT = "9d0de1f50f03d18930b82a25321bf4856aa5719a"
FULLSCREEN_COMMIT = "a0a4b6b017b2ba502a87bceeb3cf976038f469e2"

KEEP_VIDEO = {
    "core/meetings/services/bot/Dockerfile",
    "core/meetings/services/bot/src/index.ts",
    "core/meetings/services/bot/src/pipeline.ts",
    "core/meetings/services/bot/src/video-recording.ts",
    "core/meetings/services/meeting-api/src/meeting_api/bot_spawn/service.py",
}
KEEP_FULLSCREEN = {
    "core/meetings/modules/join/src/browser-args.ts",
}

def fail(msg: str) -> None:
    print(f"PATCH_FAIL={msg}")
    raise SystemExit(1)

def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        fail(f"read_failed:{path}:{e}")

def write(path: Path, value: str) -> None:
    try:
        path.write_text(value, encoding="utf-8")
    except Exception as e:
        fail(f"write_failed:{path}:{e}")

def download(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "TCRM-Felfel-Video-Patch/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
    except Exception as e:
        fail(f"download_failed:{url}:{e}")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as e:
        fail(f"patch_decode_failed:{e}")

def split_git_patch(text: str) -> dict[str, str]:
    starts = [m.start() for m in re.finditer(r"(?m)^diff --git a/", text)]
    out: dict[str, str] = {}
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(text)
        section = text[start:end]
        first = section.splitlines()[0]
        m = re.match(r"diff --git a/(.+?) b/(.+)$", first)
        if m:
            out[m.group(1)] = section
    return out

def run_patch(section: str, dry_run: bool) -> None:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".patch", delete=False) as f:
        f.write(section)
        temp = Path(f.name)
    try:
        cmd = ["patch", "-p1", "--batch", "-i", str(temp)]
        if dry_run:
            cmd.append("--dry-run")
        p = subprocess.run(cmd, cwd=VEXA, text=True, capture_output=True)
        if p.returncode != 0:
            tail = (p.stdout + "\n" + p.stderr).strip().replace("\n", " | ")[-1800:]
            fail(("dry_run_failed:" if dry_run else "apply_failed:") + tail)
    finally:
        temp.unlink(missing_ok=True)

def section_needed(path: str) -> bool:
    p = VEXA / path
    if path.endswith("bot/Dockerfile"):
        return "ffmpeg" not in read(p)
    if path.endswith("bot/src/index.ts"):
        return "startVideoRecording" not in read(p)
    if path.endswith("bot/src/pipeline.ts"):
        return "startVideoRecording" not in read(p)
    if path.endswith("bot/src/video-recording.ts"):
        return not p.exists() or "wantsVideoCapture" not in read(p)
    if path.endswith("bot_spawn/service.py"):
        txt = read(p)
        return not ("VIDEO_HWACCEL" in txt and "extra_env=video_env" in txt)
    if path.endswith("browser-args.ts"):
        return "--start-fullscreen" not in read(p)
    return True

# ---------------- preflight: no mutations before every required shape is known ----------------

for p in [TCRM, VEXA, ADAPTER, COMPOSE, SPAWN_SERVICE, BOT_DOCKERFILE, BOT_INDEX, BOT_PIPELINE, BROWSER_ARGS, VIDEO_SERVICE]:
    if not p.exists():
        fail(f"missing_path:{p}")

video_service_text = read(VIDEO_SERVICE)
if "class VideoRecordingService" not in video_service_text or "x11grab" not in video_service_text:
    fail("vexa_video_recording_service_missing")

adapter = read(ADAPTER)
old_loop = 'for (const kind of ["audio"] as const) {'
new_loop = 'for (const kind of ["video", "audio"] as const) {'
if old_loop not in adapter and new_loop not in adapter:
    fail("unknown_tcrm_recording_loop_shape")

old_status = '''    return {
      status: artifacts.some((artifact) => artifact.mediaType === "audio") ? "uploaded_audio_only" : "pending",
      recordingId,
      artifacts,
      durationSec,
      sizeBytes,
      error: artifacts.some((artifact) => artifact.mediaType === "audio") ? undefined : errors.join("; ") || "Felfel audio recording is partially finalized",
    };'''
new_status = '''    const hasVideo = artifacts.some((artifact) => artifact.mediaType === "video");
    const hasAudio = artifacts.some((artifact) => artifact.mediaType === "audio");
    return {
      status: hasVideo ? "uploaded" : hasAudio ? "uploaded_audio_only" : "pending",
      recordingId,
      artifacts,
      durationSec,
      sizeBytes,
      error: hasVideo || hasAudio ? undefined : errors.join("; ") || "Felfel recording is partially finalized",
    };'''
if old_status not in adapter and "const hasVideo = artifacts.some" not in adapter:
    fail("unknown_tcrm_recording_status_shape")

spawn = read(SPAWN_SERVICE)
capture_ready = bool(re.search(r'capture_modes\s*=.*\["audio"\s*,\s*"video"\]', spawn))
env_gated = "RECORD_VIDEO" in spawn and "record_video" in spawn
audio_only = bool(re.search(r'capture_modes\s*=.*\["audio"\]', spawn))
if not (capture_ready or env_gated or audio_only):
    fail("unknown_vexa_capture_modes_shape")

compose = read(COMPOSE)
if "meeting-api:" not in compose or "RECORDING_ENABLED=" not in compose:
    fail("compose_meeting_api_recording_anchor_missing")

video_patch = split_git_patch(download(f"https://github.com/jbschooley/vexa/commit/{VIDEO_COMMIT}.patch"))
fullscreen_patch = split_git_patch(download(f"https://github.com/jbschooley/vexa/commit/{FULLSCREEN_COMMIT}.patch"))

sections: list[tuple[str, str]] = []
for path in KEEP_VIDEO:
    if section_needed(path):
        section = video_patch.get(path)
        if not section:
            fail(f"upstream_patch_section_missing:{path}")
        sections.append((path, section))
for path in KEEP_FULLSCREEN:
    if section_needed(path):
        section = fullscreen_patch.get(path)
        if not section:
            fail(f"upstream_patch_section_missing:{path}")
        sections.append((path, section))

for path, section in sections:
    run_patch(section, dry_run=True)

# ---------------- apply official Vexa wiring ----------------
for path, section in sections:
    run_patch(section, dry_run=False)

# ---------------- force video capture for Felfel's deployment ----------------
spawn = read(SPAWN_SERVICE)
if re.search(r'capture_modes\s*=.*\["audio"\]', spawn) and not re.search(r'capture_modes\s*=.*\["audio"\s*,\s*"video"\]', spawn):
    spawn2, n = re.subn(
        r'(capture_modes\s*=\s*)\(\["audio"\](\s+if\s+recording_enabled\s+else\s+None)\)',
        r'\1(["audio", "video"]\2)',
        spawn,
        count=1,
    )
    if n != 1:
        fail("capture_modes_audio_only_replace_failed")
    write(SPAWN_SERVICE, spawn2)
    spawn = spawn2

compose = read(COMPOSE)
if "RECORD_VIDEO" in spawn and "RECORD_VIDEO=" not in compose:
    anchor = "      - RECORDING_ENABLED=${RECORDING_ENABLED:-true}\n"
    if anchor not in compose:
        fail("compose_recording_anchor_changed")
    compose = compose.replace(
        anchor,
        anchor + "      - RECORD_VIDEO=${RECORD_VIDEO:-true}\n",
        1,
    )

# CPU H.264: universally previewable MP4; no GPU dependency.
for env_line in [
    "      - VIDEO_HWACCEL=${VIDEO_HWACCEL:-none}\n",
    "      - ENCODE_H264=${ENCODE_H264:-true}\n",
]:
    key = env_line.strip().split("=", 1)[0].replace("- ", "")
    if key + "=" not in compose:
        anchor = "      - RECORDING_ENABLED=${RECORDING_ENABLED:-true}\n"
        if anchor not in compose:
            fail("compose_video_env_anchor_changed")
        compose = compose.replace(anchor, anchor + env_line, 1)

write(COMPOSE, compose)

# ---------------- TCRM: video primary, audio fallback ----------------
adapter = read(ADAPTER)
if old_loop in adapter:
    adapter = adapter.replace(old_loop, new_loop, 1)

adapter = adapter.replace(
'''    // The deployed Vexa bot composition root wires the audio-only browser tap.
    // Do not probe generic type=video routes: those routes assemble existing
    // media but do not create a video capture stream in this runtime.
''',
'''    // Video is the primary Felfel recording artifact; audio remains a fallback.
''',
1,
)

if old_status in adapter:
    adapter = adapter.replace(old_status, new_status, 1)

write(ADAPTER, adapter)

MARKER.write_text(json.dumps({
    "patch": "FELFEL-VIDEO-RECORDING-V1",
    "vexa_source_commits": [VIDEO_COMMIT, FULLSCREEN_COMMIT],
    "runtime": "server-side-x11grab",
    "video": "primary",
    "audio": "fallback",
    "codec_default": "h264-cpu",
}, indent=2) + "\n", encoding="utf-8")

print("PATCH_OK=video_runtime+tcrm_adapter")
print("VEXA_COMMITS=9d0de1f5,a0a4b6b0")
print("VIDEO=primary")
print("AUDIO=fallback")
