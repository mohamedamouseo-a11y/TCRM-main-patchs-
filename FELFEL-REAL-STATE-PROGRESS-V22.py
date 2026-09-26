#!/usr/bin/env python3
# FELFEL-REAL-STATE-PROGRESS-V22
# Truthful recording telemetry patch.
#
# Goals:
# 1) Remove V21's synthetic 70/30 overall-progress mapping.
# 2) Never show a numeric Processing percentage unless it is objectively measurable.
#    With the current pipeline, numeric progress is exposed only for Uploading because
#    that percentage is derived from streamed bytes / total bytes.
# 3) Reserve Uploading=100 for confirmed + metadata-verified durable storage.
# 4) Do not let a later transcript/analysis failure invalidate an already durable recording.
# 5) Never touch waGatewayIntegrationService.ts or historical meeting rows.

from pathlib import Path
import hashlib
import re

ROOT = Path("/var/www/TCRM-MAIN")
SERVICE = ROOT / "server/services/felfel/felfelCrmMeetingService.ts"
HUB = ROOT / "client/src/components/FelfelMeetingsHub.tsx"
PLAYER = ROOT / "client/src/components/felfel/FelfelRecordingPlayer.tsx"
WAGATEWAY = ROOT / "server/services/waGatewayIntegrationService.ts"

TARGETS = (SERVICE, HUB, PLAYER)
for p in TARGETS:
    if not p.exists():
        raise SystemExit(f"PATCH_FAIL=MISSING_{p}")


def sha256(path: Path):
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


wa_before = sha256(WAGATEWAY)
changed = []

# ---------------------------------------------------------------------------
# BACKEND A: Preserve a recording that is already durably uploaded even when
# transcript/analysis processing fails later. For a dead in-flight recording
# with no durable object, resolve the stale processing/uploading state to failed.
# ---------------------------------------------------------------------------
s = SERVICE.read_text(encoding="utf-8")

v21_catch = '''  } catch (error) {
    const message = error instanceof Error ? error.message : "Felfel processing failed";
    console.error(`[FelfelDiag] CATCH processLinkedFelfelMeeting id=${id} error=${message} at=${new Date().toISOString()}`);
    if (error instanceof Error) console.error(`[FelfelDiag] STACK id=${id}`, error.stack);

    // Reload after the failed attempt because recording/transcript state may have
    // advanced inside this run. Never leave a dead job visually stuck as
    // "processing"/"uploading", and never reset the retry counter to zero.
    const latest = (await loadMeeting(id)).meeting;
    const nextAttempt = Math.max(Number(latest.processingAttempt || 0), attempt + 1);
    const exhausted = nextAttempt >= MAX_PROCESSING_ATTEMPTS;
    const currentRecordingStatus = String(latest.recordingStatus || "").toLowerCase();
    const recordingWasInFlight = ["processing", "uploading"].includes(currentRecordingStatus);
    const intelligenceNowComplete = isMeetingIntelligenceComplete(latest);
    const auditTrail = Array.isArray(latest.auditData) ? latest.auditData : [];

    await db.update(crmMeetings).set({
      status: exhausted ? "failed" : "ended",
      failedAt: exhausted ? (latest.failedAt || new Date()) : null,
      processingLockUntil: null,
      processingAttempt: nextAttempt,
      recordingStatus: recordingWasInFlight ? "failed" : latest.recordingStatus,
      recordingError: recordingWasInFlight ? message : latest.recordingError,
      transcriptStatus: intelligenceNowComplete ? latest.transcriptStatus : "failed",
      analysisStatus: intelligenceNowComplete ? latest.analysisStatus : "failed",
      lastError: message,
      auditData: jsonValue([...auditTrail, {
        event: "processing_attempt_failed_v21",
        attempt: nextAttempt,
        exhausted,
        recordingStatus: currentRecordingStatus || null,
        error: message,
        at: new Date().toISOString(),
      }]),
    }).where(eq(crmMeetings.id, id));
    throw error;
  }
'''

v22_catch = '''  } catch (error) {
    const message = error instanceof Error ? error.message : "Felfel processing failed";
    console.error(`[FelfelDiag] CATCH processLinkedFelfelMeeting id=${id} error=${message} at=${new Date().toISOString()}`);
    if (error instanceof Error) console.error(`[FelfelDiag] STACK id=${id}`, error.stack);

    // Reload after the failed attempt because recording/transcript state may have
    // advanced inside this run. Backend state is authoritative: a recording that
    // is already durable must survive a later transcript/analysis failure.
    const latest = (await loadMeeting(id)).meeting;
    const nextAttempt = Math.max(Number(latest.processingAttempt || 0), attempt + 1);
    const exhausted = nextAttempt >= MAX_PROCESSING_ATTEMPTS;
    const currentRecordingStatus = String(latest.recordingStatus || "").toLowerCase();
    const recordingWasInFlight = ["processing", "uploading"].includes(currentRecordingStatus);
    const durableRecording = ["uploaded", "uploaded_audio_only", "ready"].includes(currentRecordingStatus)
      || Boolean((latest as any).recordingDriveFileId);
    const intelligenceNowComplete = isMeetingIntelligenceComplete(latest);
    const auditTrail = Array.isArray(latest.auditData) ? latest.auditData : [];

    // Only a recording pipeline that died before durable persistence is marked
    // failed. A durable recording is never downgraded because transcript/analysis
    // work failed afterwards.
    const nextRecordingStatus = durableRecording
      ? latest.recordingStatus
      : (recordingWasInFlight ? "failed" : latest.recordingStatus);
    const nextRecordingError = durableRecording
      ? latest.recordingError
      : (recordingWasInFlight ? message : latest.recordingError);

    await db.update(crmMeetings).set({
      status: exhausted ? "failed" : "ended",
      failedAt: exhausted ? (latest.failedAt || new Date()) : null,
      processingLockUntil: null,
      processingAttempt: nextAttempt,
      recordingStatus: nextRecordingStatus,
      recordingError: nextRecordingError,
      transcriptStatus: intelligenceNowComplete ? latest.transcriptStatus : "failed",
      analysisStatus: intelligenceNowComplete ? latest.analysisStatus : "failed",
      lastError: message,
      auditData: jsonValue([...auditTrail, {
        event: "processing_attempt_failed_v22",
        attempt: nextAttempt,
        exhausted,
        recordingStatus: currentRecordingStatus || null,
        durableRecording,
        error: message,
        at: new Date().toISOString(),
      }]),
    }).where(eq(crmMeetings.id, id));
    throw error;
  }
'''

if v22_catch not in s:
    if v21_catch not in s:
        raise SystemExit("PATCH_FAIL=BACKEND_V21_CATCH_ANCHOR_MISSING")
    s = s.replace(v21_catch, v22_catch, 1)
    changed.append(str(SERVICE.relative_to(ROOT)))

# ---------------------------------------------------------------------------
# BACKEND B: Make upload percent truthfully byte-derived. Reading the last body
# byte is not durable-storage confirmation, so 100 is emitted only after the
# existing Drive metadata verification completes successfully.
# ---------------------------------------------------------------------------
old_report_upload = '''  const reportUpload = async (bytes: number) => {
    const percent = Math.max(0, Math.min(100, Math.floor((bytes / totalBytes) * 100)));
    const now = Date.now();
    if (percent <= lastProgress || (percent < 100 && now - lastProgressAt < 750)) return;
    lastProgress = percent;
    lastProgressAt = now;
    await setRecordingProgress(Number(meeting.id), "uploading", percent);
  };'''

verified_report_upload = '''  const reportUpload = async (bytes: number) => {
    const rawPercent = Math.max(0, Math.min(100, Math.floor((bytes / totalBytes) * 100)));
    // Reading the final request-body byte is not the same as Google Drive
    // acknowledging + persisting the object. Keep 100 reserved for the
    // post-upload metadata verification below.
    const percent = Math.min(98, rawPercent);
    const now = Date.now();
    if (percent <= lastProgress || (percent < 98 && now - lastProgressAt < 750)) return;
    lastProgress = percent;
    lastProgressAt = now;
    await setRecordingProgress(Number(meeting.id), "uploading", percent);
  };'''

if old_report_upload in s:
    s = s.replace(old_report_upload, verified_report_upload, 1)
    if str(SERVICE.relative_to(ROOT)) not in changed:
        changed.append(str(SERVICE.relative_to(ROOT)))
elif verified_report_upload not in s:
    raise SystemExit("PATCH_FAIL=UPLOAD_BYTE_PROGRESS_ANCHOR_MISSING")

verified_100_anchor = '''  const recordingStatus = videoReady ? "uploaded" : "uploaded_audio_only";

  return {'''
verified_100_replacement = '''  const recordingStatus = videoReady ? "uploaded" : "uploaded_audio_only";

  // 100 means the required recording artifacts completed upload and the
  // durable-object metadata verification succeeded.
  if (complete) {
    await setRecordingProgress(Number(meeting.id), "uploading", 100);
  }

  return {'''

if verified_100_replacement not in s:
    if verified_100_anchor not in s:
        raise SystemExit("PATCH_FAIL=UPLOAD_VERIFIED_100_ANCHOR_MISSING")
    s = s.replace(verified_100_anchor, verified_100_replacement, 1)
    if str(SERVICE.relative_to(ROOT)) not in changed:
        changed.append(str(SERVICE.relative_to(ROOT)))

SERVICE.write_text(s, encoding="utf-8")

# ---------------------------------------------------------------------------
# FRONTEND A: Remove V21's synthetic 70/30 overall mapping completely.
# Only Uploading gets a numeric percentage, because the current backend upload
# percentage is objectively measured from streamed bytes. Processing remains
# an honest indeterminate stage instead of showing a made-up number.
# ---------------------------------------------------------------------------
h = HUB.read_text(encoding="utf-8")

v21_progress = '''function recordingProgress(value: unknown) {
  const audit = Array.isArray(value) ? value : [];
  const state = [...audit].reverse().find((entry: any) =>
    entry?.event === "recording_progress_state"
  );
  const raw = Number(state?.percent);
  if (!Number.isFinite(raw)) return null;

  const percent = Math.max(0, Math.min(100, Math.floor(raw)));
  const phase = String(state?.phase || "").toLowerCase();

  // The backend reports phase-local progress. Map it to one overall bar so
  // processing -> uploading never appears to jump backwards (e.g. 86% -> 0%).
  if (phase === "processing") return Math.floor(percent * 0.70);
  if (phase === "uploading") return Math.min(100, 70 + Math.floor(percent * 0.30));
  return percent;
}
'''

v22_progress = '''function recordingProgress(value: unknown) {
  const audit = Array.isArray(value) ? value : [];
  const state = [...audit].reverse().find((entry: any) =>
    entry?.event === "recording_progress_state"
  );
  const phase = String(state?.phase || "").toLowerCase();

  // V22 truth rule: numeric progress is shown only for an objectively
  // measurable phase. Uploading percent is emitted by the backend from actual
  // streamed bytes. Processing has no reliable scalar measurement today, so it
  // intentionally renders as indeterminate instead of inventing a percentage.
  if (phase !== "uploading") return null;

  const percent = Number(state?.percent);
  return Number.isFinite(percent)
    ? Math.max(0, Math.min(100, Math.floor(percent)))
    : null;
}
'''

if v22_progress not in h:
    if v21_progress not in h:
        raise SystemExit("PATCH_FAIL=FRONTEND_V21_PROGRESS_ANCHOR_MISSING")
    h = h.replace(v21_progress, v22_progress, 1)
    changed.append(str(HUB.relative_to(ROOT)))

HUB.write_text(h, encoding="utf-8")

# ---------------------------------------------------------------------------
# FRONTEND B: Remove the misleading "Overall progress" wording introduced by
# V21. The label reflects the backend phase; a percentage is rendered only when
# the supplied progress is real/measurable.
# ---------------------------------------------------------------------------
p = PLAYER.read_text(encoding="utf-8")

v21_label = '''                <span>
                  {isRTL ? "التقدم الإجمالي" : "Overall progress"} ·{" "}
                  {status === "uploading"
                    ? (isRTL ? "رفع إلى Google Drive" : "Uploading to Google Drive")
                    : (isRTL ? "معالجة التسجيل" : "Processing recording")}
                </span>
'''

v22_label = '''                <span>
                  {status === "uploading"
                    ? (isRTL ? "رفع التسجيل إلى Google Drive" : "Uploading recording to Google Drive")
                    : (isRTL ? "معالجة التسجيل" : "Processing recording")}
                </span>
'''

if v22_label not in p:
    if v21_label not in p:
        raise SystemExit("PATCH_FAIL=PLAYER_V21_LABEL_ANCHOR_MISSING")
    p = p.replace(v21_label, v22_label, 1)
    changed.append(str(PLAYER.relative_to(ROOT)))

PLAYER.write_text(p, encoding="utf-8")

# ---------------------------------------------------------------------------
# SAFETY / VERIFICATION
# ---------------------------------------------------------------------------
# The V21 70/30 synthetic mapping must be gone.
h_after = HUB.read_text(encoding="utf-8")
if "percent * 0.70" in h_after or "70 + Math.floor(percent * 0.30)" in h_after:
    raise SystemExit("PATCH_FAIL=SYNTHETIC_70_30_PROGRESS_STILL_PRESENT")

# Do not silently accept known timer-driven recording progress in the two UI
# surfaces. We only fail when a timer block itself mentions recording progress.
for ui_path in (HUB, PLAYER):
    text = ui_path.read_text(encoding="utf-8")
    timer_patterns = [
        r"setInterval\([\s\S]{0,500}recordingProgress",
        r"setTimeout\([\s\S]{0,500}recordingProgress",
        r"setInterval\([\s\S]{0,500}progress[^\n]{0,120}(?:\+|Math\.min)",
    ]
    for pattern in timer_patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            raise SystemExit(f"PATCH_FAIL=SUSPECT_SYNTHETIC_TIMER_PROGRESS:{ui_path.name}")

# Upload progress must still be byte-derived in backend source.
s_after = SERVICE.read_text(encoding="utf-8")
if "(bytes / totalBytes) * 100" not in s_after:
    raise SystemExit("PATCH_FAIL=UPLOAD_PROGRESS_NOT_BYTE_DERIVED")
if 'setRecordingProgress(Number(meeting.id), "uploading", 100)' not in s_after:
    raise SystemExit("PATCH_FAIL=VERIFIED_UPLOAD_100_MISSING")

# Never alter unrelated WhatsApp worktree changes.
wa_after = sha256(WAGATEWAY)
if wa_before != wa_after:
    raise SystemExit("PATCH_FAIL=WAGATEWAY_CHANGED")

print("PATCH=PASS")
print("VERSION=V22")
print("FILES=" + ",".join(changed if changed else ["ALREADY_APPLIED"]))
print("FAKE_70_30_PROGRESS_REMOVED=YES")
print("PROCESSING_PERCENT=INDETERMINATE")
print("UPLOAD_PERCENT_SOURCE=REAL_STREAMED_BYTES")
print("UPLOAD_100=AFTER_DURABLE_METADATA_VERIFY")
print("DURABLE_RECORDING_SURVIVES_TRANSCRIPT_FAILURE=YES")
print("WAGATEWAY_UNTOUCHED=YES")
