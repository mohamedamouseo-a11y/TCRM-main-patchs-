#!/usr/bin/env python3
from pathlib import Path

P = Path("/var/www/TCRM-MAIN/server/routes/crmFilePreview.ts")
s = P.read_text(encoding="utf-8")

old = '''      const fileName = sanitizeCrmPreviewFileName(file.fileName || "contract");
      const descriptor = resolveCrmFilePreviewDescriptor(file.fileType, fileName);
      if (!descriptor.previewable || !descriptor.contentType) {'''

new = '''      const fileName = sanitizeCrmPreviewFileName(file.fileName || "contract");
      // FELFEL_LEGACY_PLAYBACK_FIX_V2:
      // Older Felfel/Vexa audio masters were WebM bytes but some CRM rows were
      // persisted as audio/wav + .wav before MIME normalization was fixed.
      // Only override the protected preview MIME for Felfel audio recordings.
      const storedFileType = String((file as any).fileType || "");
      const isLegacyFelfelAudio =
        String((file as any).category || "") === "felfel_recording"
        && String((file as any).fileCategory || "") === "audio"
        && (storedFileType === "audio/wav" || storedFileType === "application/octet-stream");
      const previewFileType = isLegacyFelfelAudio ? "audio/webm" : storedFileType;
      const descriptor = resolveCrmFilePreviewDescriptor(previewFileType, fileName);
      if (!descriptor.previewable || !descriptor.contentType) {'''

if new in s:
    print("PATCH=PASS")
    print("ALREADY=YES")
    raise SystemExit(0)

if old not in s:
    print("PATCH=FAIL")
    print("ERROR=anchor_missing")
    raise SystemExit(1)

P.write_text(s.replace(old, new, 1), encoding="utf-8")
print("PATCH=PASS")
print("FILES=1")
