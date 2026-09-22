#!/usr/bin/env python3
# FELFEL-STT-COMPAT-V16
# Make post-meeting STT compatible with Vexa/OpenAI-compatible endpoints:
# - accept base URL or full /v1/audio/transcriptions URL
# - send Bearer auth + X-API-Key for bundled compatibility
# - pass requested language
# - accept providers that return text without segments

from pathlib import Path

adapter = Path("/var/www/TCRM-MAIN/server/services/felfel/felfelAdapter.ts")
service = Path("/var/www/TCRM-MAIN/server/services/felfel/felfelCrmMeetingService.ts")
if not adapter.exists() or not service.exists():
    raise SystemExit("PATCH_FAIL=FELFEL_FILES_MISSING")

s = adapter.read_text(encoding="utf-8")

old_sig = '''export async function transcribeFelfelRecording(
  buffer: Buffer,
  contentType: string,
): Promise<{ segments: FelfelTranscriptSegment[]; language: string; duration: number }> {
  const url = process.env.FELFEL_TRANSCRIPTION_URL;
  if (!url) throw new FelfelAdapterError("FELFEL_TRANSCRIPTION_URL is not configured");
'''

new_sig = '''export async function transcribeFelfelRecording(
  buffer: Buffer,
  contentType: string,
  language?: "ar" | "en" | null,
): Promise<{ segments: FelfelTranscriptSegment[]; language: string; duration: number }> {
  const configuredUrl = String(process.env.FELFEL_TRANSCRIPTION_URL || "").trim();
  if (!configuredUrl) throw new FelfelAdapterError("FELFEL_TRANSCRIPTION_URL is not configured");
  const url = /\/v1\/audio\/transcriptions\/?$/i.test(configuredUrl)
    ? configuredUrl.replace(/\/$/, "")
    : configuredUrl.replace(/\/$/, "") + "/v1/audio/transcriptions";
'''

if new_sig not in s:
    if old_sig not in s:
        raise SystemExit("PATCH_FAIL=STT_SIGNATURE_ANCHOR_MISSING")
    s = s.replace(old_sig, new_sig, 1)

old_parts = '''  parts.push(Buffer.from(`--${boundary}\\r\\nContent-Disposition: form-data; name="transcription_tier"\\r\\n\\r\\ndeferred\\r\\n`));
  parts.push(Buffer.from(`--${boundary}\\r\\nContent-Disposition: form-data; name="file"; filename="recording.webm"\\r\\nContent-Type: ${contentType}\\r\\n\\r\\n`));
'''

new_parts = '''  parts.push(Buffer.from(`--${boundary}\\r\\nContent-Disposition: form-data; name="transcription_tier"\\r\\n\\r\\ndeferred\\r\\n`));
  if (language) {
    parts.push(Buffer.from(`--${boundary}\\r\\nContent-Disposition: form-data; name="language"\\r\\n\\r\\n${language}\\r\\n`));
  }
  parts.push(Buffer.from(`--${boundary}\\r\\nContent-Disposition: form-data; name="file"; filename="recording.webm"\\r\\nContent-Type: ${contentType}\\r\\n\\r\\n`));
'''

if new_parts not in s:
    if old_parts not in s:
        raise SystemExit("PATCH_FAIL=STT_MULTIPART_ANCHOR_MISSING")
    s = s.replace(old_parts, new_parts, 1)

old_auth = '''  const token = process.env.FELFEL_TRANSCRIPTION_TOKEN;
  if (token) headers["X-API-Key"] = token;
'''

new_auth = '''  const token = process.env.FELFEL_TRANSCRIPTION_TOKEN;
  if (token) {
    // Vexa/OpenAI-compatible STT uses Bearer; bundled Vexa also accepts X-API-Key.
    headers["Authorization"] = `Bearer ${token}`;
    headers["X-API-Key"] = token;
  }
'''

if new_auth not in s:
    if old_auth not in s:
        raise SystemExit("PATCH_FAIL=STT_AUTH_ANCHOR_MISSING")
    s = s.replace(old_auth, new_auth, 1)

old_norm = '''  const result = (await response.json()) as Record<string, unknown>;
  const rawSegments = Array.isArray(result.segments) ? (result.segments as Record<string, unknown>[]) : [];
  const segments: FelfelTranscriptSegment[] = rawSegments
    .map((seg, index) => ({
      id: asString(seg.id) || String(index),
      speaker: asString(seg.speaker ?? seg.speaker_name) || "Unknown",
      timestamp: (seg.timestamp as string | number | null) ?? null,
      start: typeof seg.start === "number" ? seg.start : typeof seg.start_time === "number" ? seg.start_time : null,
      end: typeof seg.end === "number" ? seg.end : typeof seg.end_time === "number" ? seg.end_time : null,
      text: asString(seg.text ?? seg.transcript) || "",
    }))
    .filter((seg) => seg.text.length > 0);

  return {
    segments,
    language: String(result.language || "unknown"),
    duration: Number(result.duration || 0),
  };
'''

new_norm = '''  const result = (await response.json()) as Record<string, unknown>;
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

  // Some OpenAI-compatible providers ignore verbose_json and return only {text}.
  // Preserve a successful transcript instead of misclassifying it as "0 segments".
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
  };
'''

if new_norm not in s:
    if old_norm not in s:
        raise SystemExit("PATCH_FAIL=STT_NORMALIZE_ANCHOR_MISSING")
    s = s.replace(old_norm, new_norm, 1)

adapter.write_text(s, encoding="utf-8")

t = service.read_text(encoding="utf-8")
old_call = '''          transcribeFelfelRecording(audioBuffer.buffer, audioBuffer.contentType),'''
new_call = '''          transcribeFelfelRecording(audioBuffer.buffer, audioBuffer.contentType, language),'''
if new_call not in t:
    if old_call not in t:
        raise SystemExit("PATCH_FAIL=STT_CALL_ANCHOR_MISSING")
    t = t.replace(old_call, new_call, 1)
service.write_text(t, encoding="utf-8")

print("PATCH=PASS")
print("FILES=2")
print("STT_URL=NORMALIZED")
print("STT_AUTH=BEARER+X_API_KEY")
print("STT_LANGUAGE=PASSED")
print("TEXT_ONLY_RESPONSE=SUPPORTED")
