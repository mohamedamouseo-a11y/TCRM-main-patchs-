#!/usr/bin/env python3
from pathlib import Path

ROOT = Path("/var/www/TCRM-MAIN")
BACK = ROOT / "server/services/felfel/felfelCrmMeetingService.ts"
PLAYER = ROOT / "client/src/components/felfel/FelfelRecordingPlayer.tsx"
CARD = ROOT / "client/src/components/felfel/FelfelMeetingWorkspaceCard.tsx"
HUB = ROOT / "client/src/components/FelfelMeetingsHub.tsx"
DASH = ROOT / "client/src/components/felfel/FelfelOperationalDashboard.tsx"

def fail(msg):
    print("PATCH=FAIL")
    print("ERROR=" + msg)
    raise SystemExit(1)

def rep(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        fail("anchor_missing:" + label)
    return text.replace(old, new, 1)

# ---------------- BACKEND LIVE PHASES ----------------
s = BACK.read_text(encoding="utf-8")

s = rep(s,
'''        await db.update(crmMeetings).set({
          status: "ended",
          felfelStatus: historical?.status || remote.status || "ended",
          startedAt: meeting.startedAt || (remote.startedAt ? asDate(remote.startedAt) : null),
          endedAt: meeting.endedAt || new Date(),
        }).where(eq(crmMeetings.id, id));''',
'''        await db.update(crmMeetings).set({
          status: "ended",
          felfelStatus: historical?.status || remote.status || "ended",
          recordingStatus: isRecordingComplete(String(meeting.recordingStatus || ""))
            ? meeting.recordingStatus
            : "processing",
          startedAt: meeting.startedAt || (remote.startedAt ? asDate(remote.startedAt) : null),
          endedAt: meeting.endedAt || new Date(),
        }).where(eq(crmMeetings.id, id));''',
"ended_recording_phase")

s = rep(s,
'''        await db.update(crmMeetings).set({
          status: lifecycle,
          felfelStatus: remote.status,
          startedAt: remote.startedAt ? asDate(remote.startedAt) : lifecycle === "live" ? (meeting.startedAt || new Date()) : meeting.startedAt,
        }).where(eq(crmMeetings.id, id));''',
'''        await db.update(crmMeetings).set({
          status: lifecycle,
          felfelStatus: remote.status,
          recordingStatus: lifecycle === "live" && !isRecordingComplete(String(meeting.recordingStatus || ""))
            ? "recording"
            : meeting.recordingStatus,
          startedAt: remote.startedAt ? asDate(remote.startedAt) : lifecycle === "live" ? (meeting.startedAt || new Date()) : meeting.startedAt,
        }).where(eq(crmMeetings.id, id));''',
"live_recording_phase")

s = rep(s,
'''  const locked = await db.update(crmMeetings).set({ status: "processing", processingAttempt: attempt + 1, processingLockUntil: lockUntil, lastError: null })''',
'''  const locked = await db.update(crmMeetings).set({
    status: "processing",
    recordingStatus: isRecordingComplete(String(meeting.recordingStatus || "")) ? meeting.recordingStatus : "processing",
    processingAttempt: attempt + 1,
    processingLockUntil: lockUntil,
    lastError: null,
  })''',
"processing_recording_phase")

s = rep(s,
'''  const uploadedBy = Number(meeting.ownerUserId || meeting.createdByUserId || 0) || 1;
  const media: Array<Record<string, unknown>> = [];''',
'''  const uploadedBy = Number(meeting.ownerUserId || meeting.createdByUserId || 0) || 1;

  // FELFEL_RECORDING_LIVE_PHASES_V1
  // Artifacts exist and the next real backend action is Drive persistence.
  // Expose that phase to the frontend while upload is in progress.
  try {
    const phaseDb = await getDb();
    if (phaseDb && !isRecordingComplete(String(meeting.recordingStatus || ""))) {
      await phaseDb.update(crmMeetings)
        .set({ recordingStatus: "uploading" })
        .where(eq(crmMeetings.id, Number(meeting.id)));
    }
  } catch {
    // Phase telemetry must never block recording finalization.
  }

  const media: Array<Record<string, unknown>> = [];''',
"uploading_recording_phase")

BACK.write_text(s, encoding="utf-8")

# ---------------- PLAYER LABELS ----------------
s = PLAYER.read_text(encoding="utf-8")
s = rep(s,
'''function statusLabel(status: string, isRTL: boolean) {
  if (["uploaded", "uploaded_audio_only"].includes(status)) return isRTL ? "جاهز للتشغيل" : "Ready to play";
  if (["pending", "processing"].includes(status)) return isRTL ? "جاري تجهيز التسجيل" : "Processing recording";
  if (status === "failed") return isRTL ? "تعذر تجهيز التسجيل" : "Recording failed";
  return isRTL ? "في انتظار التسجيل" : "Waiting for recording";
}''',
'''function statusLabel(status: string, isRTL: boolean) {
  if (["uploaded", "uploaded_audio_only"].includes(status)) return isRTL ? "جاهز للتشغيل" : "Ready to play";
  if (status === "recording") return isRTL ? "جاري التسجيل الآن" : "Recording now";
  if (status === "uploading") return isRTL ? "جاري رفع التسجيل" : "Uploading recording";
  if (["pending", "processing"].includes(status)) return isRTL ? "جاري معالجة التسجيل" : "Processing recording";
  if (status === "failed") return isRTL ? "تعذر تجهيز التسجيل" : "Recording failed";
  return isRTL ? "في انتظار التسجيل" : "Waiting for recording";
}''',
"player_status_labels")

s = rep(s,
'''  const isProcessing = ["pending", "processing"].includes(status) || meetingLifecycle === "processing";''',
'''  const isProcessing = ["recording", "pending", "processing", "uploading"].includes(status) || meetingLifecycle === "processing";''',
"player_processing_states")

s = rep(s,
'''            {isProcessing
              ? (isRTL ? "فلفل يحفظ التسجيل ويجهزه للمعاينة." : "Felfel is saving and preparing the recording for preview.")
              : (isRTL ? "سيظهر المشغل هنا فور توفر ملف التسجيل." : "The player will appear here as soon as the recording is available.")}''',
'''            {status === "recording"
              ? (isRTL ? "فلفل يسجل الاجتماع الآن. سيظهر الملف بعد انتهاء الاجتماع." : "Felfel is recording the meeting now. The file will appear after the meeting ends.")
              : status === "uploading"
                ? (isRTL ? "تم تجهيز التسجيل ويتم رفعه الآن إلى Google Drive." : "The recording is prepared and is uploading to Google Drive.")
                : isProcessing
                  ? (isRTL ? "فلفل يعالج التسجيل ويجهزه للمعاينة." : "Felfel is processing and preparing the recording for preview.")
                  : (isRTL ? "سيظهر المشغل هنا فور توفر ملف التسجيل." : "The player will appear here as soon as the recording is available.")}''',
"player_phase_message")

PLAYER.write_text(s, encoding="utf-8")

# ---------------- WORKSPACE BADGE ----------------
s = CARD.read_text(encoding="utf-8")
anchor = '''function statusDot(status: string) {
  if (status === "completed") return "bg-emerald-500";
  if (status === "failed") return "bg-red-500";
  if (["live", "processing", "joining", "waiting"].includes(status)) return "bg-orange-500";
  return "bg-slate-400";
}'''
insert = anchor + '''

function recordingPhaseLabel(status: unknown, ar: boolean) {
  const value = String(status || "not_started");
  if (value === "recording") return ar ? "جاري التسجيل" : "Recording now";
  if (value === "processing" || value === "pending") return ar ? "جاري المعالجة" : "Processing";
  if (value === "uploading") return ar ? "جاري الرفع" : "Uploading";
  if (value === "uploaded") return ar ? "فيديو جاهز" : "Video ready";
  if (value === "uploaded_audio_only") return ar ? "صوت جاهز" : "Audio ready";
  if (value === "failed") return ar ? "فشل التسجيل" : "Failed";
  return ar ? "لم يبدأ" : "Not started";
}

function recordingPhaseClass(status: unknown) {
  const value = String(status || "");
  if (value === "failed") return "rounded-full border-red-500/25 bg-red-500/5 text-red-600";
  if (["recording", "processing", "pending", "uploading"].includes(value)) return "rounded-full border-orange-500/25 bg-orange-500/5 text-orange-700 dark:text-orange-300";
  if (["uploaded", "uploaded_audio_only"].includes(value)) return "rounded-full border-emerald-500/20 bg-emerald-500/5 text-emerald-700 dark:text-emerald-300";
  return "rounded-full border-border bg-muted/40 text-muted-foreground";
}'''
if "function recordingPhaseLabel(" not in s:
    if anchor not in s: fail("anchor_missing:workspace_helpers")
    s = s.replace(anchor, insert, 1)

s = rep(s,
'''          <Badge variant="outline" className={recordingFailed ? "rounded-full border-red-500/25 bg-red-500/5 text-red-600" : "rounded-full border-emerald-500/20 bg-emerald-500/5 text-emerald-700 dark:text-emerald-300"}>{ar ? "التسجيل" : "Recording"}: {meeting.recordingStatus || "not_started"}</Badge>''',
'''          <Badge variant="outline" className={recordingPhaseClass(meeting.recordingStatus)}>{ar ? "التسجيل" : "Recording"}: {recordingPhaseLabel(meeting.recordingStatus, ar)}</Badge>''',
"workspace_recording_badge")

CARD.write_text(s, encoding="utf-8")

# ---------------- LINKED MEETINGS VIEW ----------------
s = HUB.read_text(encoding="utf-8")

helper_anchor = '''function formatRecordingDuration(value: unknown) {
  const seconds = Number(value || 0);
  if (!Number.isFinite(seconds) || seconds <= 0) return null;
  const minutes = Math.floor(seconds / 60);
  const remainder = Math.round(seconds % 60).toString().padStart(2, "0");
  return `${minutes}:${remainder}`;
}'''
helper_new = helper_anchor + '''

function recordingPhaseLabel(status: unknown, isRTL: boolean) {
  const value = String(status || "not_started");
  if (value === "recording") return isRTL ? "جاري التسجيل" : "Recording now";
  if (value === "processing" || value === "pending") return isRTL ? "جاري المعالجة" : "Processing";
  if (value === "uploading") return isRTL ? "جاري الرفع" : "Uploading";
  if (value === "uploaded") return isRTL ? "فيديو جاهز" : "Video ready";
  if (value === "uploaded_audio_only") return isRTL ? "صوت جاهز" : "Audio ready";
  if (value === "failed") return isRTL ? "فشل التسجيل" : "Failed";
  return isRTL ? "لم يبدأ" : "Not started";
}'''
if "function recordingPhaseLabel(status: unknown, isRTL: boolean)" not in s:
    if helper_anchor not in s: fail("anchor_missing:hub_helper")
    s = s.replace(helper_anchor, helper_new, 1)

s = s.replace("refetchInterval: 15000", "refetchInterval: 5000", 1)
s = rep(s,
'''<div className="mt-1 text-sm font-medium">{meeting.recordingStatus || "not_started"}</div>''',
'''<div className="mt-1 text-sm font-medium">{recordingPhaseLabel(meeting.recordingStatus, isRTL)}</div>''',
"hub_recording_label")
HUB.write_text(s, encoding="utf-8")

# ---------------- OPERATIONAL DASHBOARD POLLING/FILTER ----------------
s = DASH.read_text(encoding="utf-8")
s = s.replace("refetchInterval: 15_000", "refetchInterval: 5_000", 1)
s = rep(s,
'''{["not_started","pending","uploaded","uploaded_audio_only","failed"].map((value) => <option key={value} value={value}>{value}</option>)}''',
'''{["not_started","recording","processing","uploading","pending","uploaded","uploaded_audio_only","failed"].map((value) => <option key={value} value={value}>{value}</option>)}''',
"dashboard_recording_filter")
DASH.write_text(s, encoding="utf-8")

print("PATCH=PASS")
print("FILES=5")
print("PHASES=recording,processing,uploading,ready,failed")
