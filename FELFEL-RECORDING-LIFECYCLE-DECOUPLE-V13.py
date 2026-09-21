#!/usr/bin/env python3
# FELFEL-RECORDING-LIFECYCLE-DECOUPLE-V13
# Fix CRM recording state + make finalized recording independent from STT success.
#
# Facts from Vexa v0.12:
# - there is intentionally NO recordings table
# - recordings live in meetings.data['recordings'] JSONB
# - status "active" is the admitted/live bot state
#
# Changes:
# 1) Treat exact remote status "active" as live, without trusting active=true alone.
# 2) Persist completed Drive recording metadata immediately after recording finalization,
#    before transcription/analysis, so STT failure cannot hide/lose a valid recording.
# 3) Keep manual sync recordingStatus consistent with lifecycle monitor.

from pathlib import Path

target = Path("/var/www/TCRM-MAIN/server/services/felfel/felfelCrmMeetingService.ts")
if not target.exists():
    raise SystemExit("PATCH_FAIL=SERVICE_MISSING")

s = target.read_text(encoding="utf-8")

old_map = '''  if (["live", "in_call", "joined", "started", "recording"].some((v) => normalized.includes(v))) return "live";'''
new_map = '''  if (normalized === "active" || ["live", "in_call", "joined", "started", "recording"].some((v) => normalized.includes(v))) return "live";'''

if new_map not in s:
    if old_map not in s:
        raise SystemExit("PATCH_FAIL=MAP_LIFECYCLE_ANCHOR_MISSING")
    s = s.replace(old_map, new_map, 1)

old_sync = '''  const next = {
    status: lifecycle,
    felfelStatus: remote.status,
    startedAt: remote.startedAt ? asDate(remote.startedAt) : lifecycle === "live" ? new Date() : meeting.startedAt,
    endedAt: lifecycle === "ended" ? (meeting.endedAt || new Date()) : meeting.endedAt,
  };'''

new_sync = '''  const next = {
    status: lifecycle,
    felfelStatus: remote.status,
    recordingStatus: lifecycle === "live" && !isRecordingComplete(String(meeting.recordingStatus || ""))
      ? "recording"
      : meeting.recordingStatus,
    startedAt: remote.startedAt ? asDate(remote.startedAt) : lifecycle === "live" ? (meeting.startedAt || new Date()) : meeting.startedAt,
    endedAt: lifecycle === "ended" ? (meeting.endedAt || new Date()) : meeting.endedAt,
  };'''

if new_sync not in s:
    if old_sync not in s:
        raise SystemExit("PATCH_FAIL=SYNC_STATE_ANCHOR_MISSING")
    s = s.replace(old_sync, new_sync, 1)

anchor = '''    console.log(`[FelfelDiag] AFTER tryFinalizeRecording id=${id} status=${recording?.status} mediaCount=${Array.isArray(recording?.media) ? recording.media.length : 0} error=${recording?.error || "none"} at=${new Date().toISOString()}`);

    // If transcript + analysis are already complete, retry only recording/Drive.'''

insert = '''    console.log(`[FelfelDiag] AFTER tryFinalizeRecording id=${id} status=${recording?.status} mediaCount=${Array.isArray(recording?.media) ? recording.media.length : 0} error=${recording?.error || "none"} at=${new Date().toISOString()}`);

    // Recording is an independent deliverable. Persist it immediately after
    // Drive verification so a later STT/analysis failure cannot hide a valid
    // MP4/MP3 or force it through the recording pipeline again.
    if (isRecordingComplete(recording.status)) {
      await db.update(crmMeetings).set({
        recordingStatus: recording.status,
        recordingDriveFileId: recording.driveFileId || null,
        recordingStorageAccountId: recording.storageAccountId || null,
        recordingDriveUrl: recording.driveUrl || null,
        recordingDurationSec: recording.durationSec || null,
        recordingSizeBytes: recording.sizeBytes || null,
        recordingError: recording.error || null,
      }).where(eq(crmMeetings.id, id));
      console.log(`[FelfelDiag] RECORDING_PERSISTED_BEFORE_STT id=${id} status=${recording.status} at=${new Date().toISOString()}`);
    }

    // If transcript + analysis are already complete, retry only recording/Drive.'''

if insert not in s:
    if anchor not in s:
        raise SystemExit("PATCH_FAIL=RECORDING_PERSIST_ANCHOR_MISSING")
    s = s.replace(anchor, insert, 1)

target.write_text(s, encoding="utf-8")

print("PATCH=PASS")
print("FILES=1")
print("REMOTE_ACTIVE=LIVE")
print("RECORDING_STATUS=INDEPENDENT_FROM_STT")
print("RECORDINGS_TABLE=NOT_REQUIRED_JSONB_IS_CANONICAL")
