#!/usr/bin/env python3
from pathlib import Path

ROOT = Path("/var/www/TCRM-MAIN")
ADAPTER = ROOT / "server/services/felfel/felfelAdapter.ts"
SEC = ROOT / "server/services/crmFilePreviewSecurity.ts"

def fail(msg):
    print("PATCH_FAIL=" + msg)
    raise SystemExit(1)

def patch_once(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        fail("anchor_missing:" + label)
    return text.replace(old, new, 1)

adapter = ADAPTER.read_text(encoding="utf-8")
adapter = patch_once(
    adapter,
    '''        const format = String(master.format ?? original?.format ?? (kind === "audio" ? "wav" : "webm")).replace(/[^A-Za-z0-9]/g, "") || (kind === "audio" ? "wav" : "webm");
        const contentType = downloaded.contentType?.split(";", 1)[0] || (kind === "audio" ? (format === "wav" ? "audio/wav" : "audio/webm") : "video/webm");''',
    '''        const reportedFormat = String(master.format ?? original?.format ?? (kind === "audio" ? "wav" : "webm")).replace(/[^A-Za-z0-9]/g, "") || (kind === "audio" ? "wav" : "webm");
        const responseContentType = String(downloaded.contentType?.split(";", 1)[0] || "").trim().toLowerCase();
        const contentType = responseContentType && responseContentType !== "application/octet-stream"
          ? responseContentType
          : (kind === "audio" ? (reportedFormat === "wav" ? "audio/wav" : "audio/webm") : (reportedFormat === "mp4" ? "video/mp4" : "video/webm"));
        const format = contentType === "audio/webm" || contentType === "video/webm"
          ? "webm"
          : contentType === "audio/wav"
            ? "wav"
            : contentType === "audio/mpeg"
              ? "mp3"
              : contentType === "audio/ogg"
                ? "ogg"
                : contentType === "video/mp4"
                  ? "mp4"
                  : reportedFormat;''',
    "adapter_mime"
)
ADAPTER.write_text(adapter, encoding="utf-8")

sec = SEC.read_text(encoding="utf-8")
sec = patch_once(
    sec,
    'export type CrmFilePreviewKind = "pdf" | "image" | "audio" | "unsupported";',
    'export type CrmFilePreviewKind = "pdf" | "image" | "audio" | "video" | "unsupported";',
    "preview_kind"
)
sec = patch_once(
    sec,
    '''const SAFE_AUDIO_CONTENT_TYPES = new Set([
  "audio/mpeg",
  "audio/wav",
  "audio/ogg",
]);''',
    '''const SAFE_AUDIO_CONTENT_TYPES = new Set([
  "audio/mpeg",
  "audio/wav",
  "audio/ogg",
  "audio/webm",
]);

const SAFE_VIDEO_CONTENT_TYPES = new Set([
  "video/webm",
  "video/mp4",
]);''',
    "safe_media_types"
)
sec = patch_once(
    sec,
    '''  ".mp3": "audio/mpeg",
  ".wav": "audio/wav",
  ".ogg": "audio/ogg",
};''',
    '''  ".mp3": "audio/mpeg",
  ".wav": "audio/wav",
  ".ogg": "audio/ogg",
  ".mp4": "video/mp4",
};''',
    "extension_map"
)
sec = patch_once(
    sec,
    '''  "audio/mpeg": new Set([".mp3"]),
  "audio/wav": new Set([".wav"]),
  "audio/ogg": new Set([".ogg"]),
};''',
    '''  "audio/mpeg": new Set([".mp3"]),
  "audio/wav": new Set([".wav"]),
  "audio/ogg": new Set([".ogg"]),
  // Legacy Felfel audio masters could be WebM bytes/MIME with a .wav filename.
  // Serving the trusted MIME is safe under nosniff and restores playback.
  "audio/webm": new Set([".webm", ".wav"]),
  "video/webm": new Set([".webm"]),
  "video/mp4": new Set([".mp4"]),
};''',
    "extension_allowlist"
)
sec = patch_once(
    sec,
    '''    contentType === "application/pdf" ||
    SAFE_IMAGE_CONTENT_TYPES.has(contentType) ||
    SAFE_AUDIO_CONTENT_TYPES.has(contentType)
      ? contentType''',
    '''    contentType === "application/pdf" ||
    SAFE_IMAGE_CONTENT_TYPES.has(contentType) ||
    SAFE_AUDIO_CONTENT_TYPES.has(contentType) ||
    SAFE_VIDEO_CONTENT_TYPES.has(contentType)
      ? contentType''',
    "known_by_type"
)
sec = patch_once(
    sec,
    '''  const kind: CrmFilePreviewKind = safeContentType === "application/pdf"
    ? "pdf"
    : SAFE_AUDIO_CONTENT_TYPES.has(safeContentType)
      ? "audio"
      : "image";''',
    '''  const kind: CrmFilePreviewKind = safeContentType === "application/pdf"
    ? "pdf"
    : SAFE_AUDIO_CONTENT_TYPES.has(safeContentType)
      ? "audio"
      : SAFE_VIDEO_CONTENT_TYPES.has(safeContentType)
        ? "video"
        : "image";''',
    "preview_kind_resolution"
)
SEC.write_text(sec, encoding="utf-8")

print("PATCH=PASS")
print("FILES=2")
