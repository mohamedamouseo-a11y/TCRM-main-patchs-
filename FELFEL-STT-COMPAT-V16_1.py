#!/usr/bin/env python3
# FELFEL-STT-COMPAT-V16_1
# Robust follow-up to V16: avoids fragile multipart anchors and patches the
# current live function by semantic markers.

from pathlib import Path
import re

adapter = Path("/var/www/TCRM-MAIN/server/services/felfel/felfelAdapter.ts")
service = Path("/var/www/TCRM-MAIN/server/services/felfel/felfelCrmMeetingService.ts")

if not adapter.exists() or not service.exists():
    raise SystemExit("PATCH_FAIL=FELFEL_FILES_MISSING")

s = adapter.read_text(encoding="utf-8")

# 1) Function signature: add optional language argument.
sig_re = re.compile(
    r'export async function transcribeFelfelRecording\(\s*'
    r'buffer: Buffer,\s*'
    r'contentType: string,\s*'
    r'\): Promise<\{ segments: FelfelTranscriptSegment\[\]; language: string; duration: number \}> \{'
)
sig_new = '''export async function transcribeFelfelRecording(
  buffer: Buffer,
  contentType: string,
  language?: "ar" | "en" | null,
): Promise<{ segments: FelfelTranscriptSegment[]; language: string; duration: number }> {'''
s, n = sig_re.subn(sig_new, s, count=1)
if n != 1 and 'language?: "ar" | "en" | null' not in s:
    raise SystemExit("PATCH_FAIL=SIGNATURE_NOT_FOUND")

# 2) Normalize base URL to the OpenAI-compatible endpoint.
url_old_re = re.compile(
    r'  const url = process\.env\.FELFEL_TRANSCRIPTION_URL;\s*'
    r'  if \(!url\) throw new FelfelAdapterError\("FELFEL_TRANSCRIPTION_URL is not configured"\);'
)
url_new = '''  const configuredUrl = String(process.env.FELFEL_TRANSCRIPTION_URL || "").trim();
  if (!configuredUrl) throw new FelfelAdapterError("FELFEL_TRANSCRIPTION_URL is not configured");
  const url = /\\/v1\\/audio\\/transcriptions\\/?$/i.test(configuredUrl)
    ? configuredUrl.replace(/\\/$/, "")
    : configuredUrl.replace(/\\/$/, "") + "/v1/audio/transcriptions";'''
s, n = url_old_re.subn(url_new, s, count=1)
if n != 1 and 'configuredUrl' not in s:
    raise SystemExit("PATCH_FAIL=URL_BLOCK_NOT_FOUND")

# 3) Add language multipart part immediately before the file part.
file_marker = '  parts.push(Buffer.from(`--${boundary}\\r\\nContent-Disposition: form-data; name=\\\"file\\\"; filename=\\\"recording.webm\\\"\\r\\nContent-Type: ${contentType}\\r\\n\\r\\n`));'
if file_marker not in s:
    # Some live revisions use unescaped quote characters inside the template literal.
    file_marker = '  parts.push(Buffer.from(`--${boundary}\\r\\nContent-Disposition: form-data; name="file"; filename="recording.webm"\\r\\nContent-Type: ${contentType}\\r\\n\\r\\n`));'
if file_marker not in s:
    raise SystemExit("PATCH_FAIL=FILE_MULTIPART_MARKER_NOT_FOUND")
lang_block = '''  if (language) {
    parts.push(Buffer.from(`--${boundary}\\r\\nContent-Disposition: form-data; name="language"\\r\\n\\r\\n${language}\\r\\n`));
  }
'''
if 'name="language"' not in s and 'name=\\"language\\"' not in s:
    s = s.replace(file_marker, lang_block + file_marker, 1)

# 4) Send both standard Bearer and bundled-service X-API-Key auth.
auth_old = '  if (token) headers["X-API-Key"] = token;'
auth_new = '''  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
    headers["X-API-Key"] = token;
  }'''
if auth_new not in s:
    if auth_old not in s:
        raise SystemExit("PATCH_FAIL=AUTH_MARKER_NOT_FOUND")
    s = s.replace(auth_old, auth_new, 1)

# 5) Normalize successful text-only responses into one segment.
result_start = s.find('  const result = (await response.json()) as Record<string, unknown>;')
func_end_marker = '\n}\n\nexport { FelfelAdapterError }'
func_end = s.find(func_end_marker, result_start)
if result_start < 0 or func_end < 0:
    raise SystemExit("PATCH_FAIL=RESULT_BLOCK_NOT_FOUND")

result_new = '''  const result = (await response.json()) as Record<string, unknown>;
  const rawSegments = Array.isArray(result.segments) ? (result.segments as Record<string, unknown>[]) : [];
  let segments: FelfelTranscriptSegment[] = rawSegments
    .map((seg, index) => ({
      id: asString(seg.id) || String(index),
      speaker: asString(seg.speaker ?? seg.speaker_name) || "Unknown",
      timestamp: (seg.timestamp as string | number | null) ?? null,
      start: typeof seg.start === "number" ? seg.start : typeof seg.start_time === "number" ? seg.start_time : null,
      end: typeof seg.end === "number" ? seg.end : typeof seg.end_time === "number" ? seg.end_time : null,
      text: asString(seg.text ?? seg.transcript) || "",
    }))
    .filter((seg) => seg.text.length > 0);

  const fallbackText = asString(result.text)?.trim() || "";
  const duration = Number(result.duration || 0);
  if (!segments.length && fallbackText) {
    segments = [{
      id: "0",
      speaker: "Unknown",
      timestamp: 0,
      start: 0,
      end: Number.isFinite(duration) && duration > 0 ? duration : null,
      text: fallbackText,
    }];
  }

  return {
    segments,
    language: String(result.language || language || "unknown"),
    duration: Number.isFinite(duration) ? duration : 0,
  };'''

s = s[:result_start] + result_new + s[func_end:]

adapter.write_text(s, encoding="utf-8")

# 6) Pass requested processing language from CRM worker.
t = service.read_text(encoding="utf-8")
call_old = 'transcribeFelfelRecording(audioBuffer.buffer, audioBuffer.contentType)'
call_new = 'transcribeFelfelRecording(audioBuffer.buffer, audioBuffer.contentType, language)'
if call_new not in t:
    if call_old not in t:
        raise SystemExit("PATCH_FAIL=CALL_SITE_NOT_FOUND")
    t = t.replace(call_old, call_new, 1)
service.write_text(t, encoding="utf-8")

print("PATCH=PASS")
print("FILES=2")
print("STT_URL=NORMALIZED")
print("STT_AUTH=BEARER+X_API_KEY")
print("STT_LANGUAGE=PASSED")
print("TEXT_ONLY_RESPONSE=SUPPORTED")
