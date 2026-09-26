#!/usr/bin/env python3
# FELFEL-RECORDING-STATE-PROGRESS-FIX-V21
# Fixes:
# 1) stale Processing/Uploading UI states after a failed pipeline attempt
# 2) retry counter being reset to 0 in the failure path
# 3) recording progress visually going backwards when phase changes processing -> uploading

from pathlib import Path

ROOT = Path("/var/www/TCRM-MAIN")
SERVICE = ROOT / "server/services/felfel/felfelCrmMeetingService.ts"
HUB = ROOT / "client/src/components/FelfelMeetingsHub.tsx"
PLAYER = ROOT / "client/src/components/felfel/FelfelRecordingPlayer.tsx"

for p in (SERVICE, HUB, PLAYER):
    if not p.exists():
        raise SystemExit(f"PATCH_FAIL=MISSING_{p}")

# --- backend: preserve retry attempts and never leave recordingStatus in processing/uploading after failure
s = SERVICE.read_text(encoding="utf-8")
old_catch = '''  } catch (error) {
    console.error(`[FelfelDiag] CATCH processLinkedFelfelMeeting id=${id} error=${error instanceof Error ? error.message : String(error)} at=${new Date().toISOString()}`);
    if (error instanceof Error) console.error(`[FelfelDiag] STACK id=${id}`, error.stack);
    await db.update(crmMeetings).set({         status: Number(meeting.processingAttempt || 0) + 1 >= MAX_PROCESSING_ATTEMPTS ? "failed" : "ended",
        failedAt: Number(meeting.processingAttempt || 0) + 1 >= MAX_PROCESSING_ATTEMPTS ? new Date() : null,
        processingLockUntil: null,
    processingAttempt: 0,
    failedAt: null,
    lastError: null,
        transcriptStatus: "failed",
        analysisStatus: "failed",
        lastError: error instanceof Error ? error.message : "Felfel processing failed" }).where(eq(crmMeetings.id, id));
    throw error;
  }
'''
new_catch = '''  } catch (error) {
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
if new_catch not in s:
    if old_catch not in s:
        raise SystemExit("PATCH_FAIL=BACKEND_CATCH_ANCHOR_MISSING")
    s = s.replace(old_catch, new_catch, 1)
SERVICE.write_text(s, encoding="utf-8")

# --- frontend: convert phase-local percentages into one monotonic overall 0..100 bar.
h = HUB.read_text(encoding="utf-8")
old_progress = '''function recordingProgress(value: unknown) {
  const audit = Array.isArray(value) ? value : [];
  const state = [...audit].reverse().find((entry: any) =>
    entry?.event === "recording_progress_state"
  );
  const percent = Number(state?.percent);
  return Number.isFinite(percent)
    ? Math.max(0, Math.min(100, Math.floor(percent)))
    : null;
}
'''
new_progress = '''function recordingProgress(value: unknown) {
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
if new_progress not in h:
    if old_progress not in h:
        raise SystemExit("PATCH_FAIL=FRONTEND_PROGRESS_ANCHOR_MISSING")
    h = h.replace(old_progress, new_progress, 1)
HUB.write_text(h, encoding="utf-8")

# --- UI label: make it explicit that the displayed percentage is overall pipeline progress.
p = PLAYER.read_text(encoding="utf-8")
old_label = '''                <span>
                  {status === "uploading"
                    ? (isRTL ? "رفع إلى Google Drive" : "Uploading to Google Drive")
                    : (isRTL ? "معالجة التسجيل" : "Processing recording")}
                </span>
'''
new_label = '''                <span>
                  {isRTL ? "التقدم الإجمالي" : "Overall progress"} ·{" "}
                  {status === "uploading"
                    ? (isRTL ? "رفع إلى Google Drive" : "Uploading to Google Drive")
                    : (isRTL ? "معالجة التسجيل" : "Processing recording")}
                </span>
'''
if new_label not in p:
    if old_label not in p:
        raise SystemExit("PATCH_FAIL=PLAYER_LABEL_ANCHOR_MISSING")
    p = p.replace(old_label, new_label, 1)
PLAYER.write_text(p, encoding="utf-8")

print("PATCH=PASS")
print("BACKEND_STALE_STATE_FIX=YES")
print("RETRY_COUNTER_FIX=YES")
print("MONOTONIC_OVERALL_PROGRESS=YES")
print("FILES=3")
