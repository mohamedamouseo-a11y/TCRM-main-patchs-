from pathlib import Path

p = Path('/var/www/TCRM-MAIN/server/services/felfel/felfelCrmMeetingService.ts')
s = p.read_text()

MARKER = 'FELFEL_RECORDING_RETRY_V1'
if MARKER in s:
    print('already_applied')
    raise SystemExit(0)

def replace_once(old: str, new: str, label: str):
    global s
    if old not in s:
        raise SystemExit(f'PATCH_FAIL={label}_anchor_not_found')
    s = s.replace(old, new, 1)

replace_once(
    'const LIFECYCLE_POLL_MS = 10_000;\n',
    'const LIFECYCLE_POLL_MS = 10_000;\nconst RECORDING_RETRY_BACKOFF_MS = 10 * 60_000; // FELFEL_RECORDING_RETRY_V1\n',
    'constants',
)

replace_once(
'''function isMeetingProcessingComplete(meeting: any) {
  const segments = Array.isArray(meeting?.transcriptData?.segments) ? meeting.transcriptData.segments : [];
  return isRecordingComplete(meeting?.recordingStatus)
    && String(meeting?.transcriptStatus || "").toLowerCase() === "completed"
    && String(meeting?.analysisStatus || "").toLowerCase() === "completed"
    && segments.length > 0
    && Boolean(meeting?.analysisData);
}
''',
'''function isMeetingProcessingComplete(meeting: any) {
  const segments = Array.isArray(meeting?.transcriptData?.segments) ? meeting.transcriptData.segments : [];
  return isRecordingComplete(meeting?.recordingStatus)
    && String(meeting?.transcriptStatus || "").toLowerCase() === "completed"
    && String(meeting?.analysisStatus || "").toLowerCase() === "completed"
    && segments.length > 0
    && Boolean(meeting?.analysisData);
}

function isMeetingIntelligenceComplete(meeting: any) {
  const segments = Array.isArray(meeting?.transcriptData?.segments) ? meeting.transcriptData.segments : [];
  return String(meeting?.transcriptStatus || "").toLowerCase() === "completed"
    && String(meeting?.analysisStatus || "").toLowerCase() === "completed"
    && segments.length > 0
    && Boolean(meeting?.analysisData);
}

function lastRecordingRetryFailureAt(meeting: any) {
  const audit = Array.isArray(meeting?.auditData) ? meeting.auditData : [];
  for (let i = audit.length - 1; i >= 0; i -= 1) {
    const entry = audit[i];
    if (!["recording_retry_failed", "recording_retry_deferred"].includes(String(entry?.event || ""))) continue;
    const at = asDate(entry?.at);
    if (at && !Number.isNaN(at.getTime())) return at;
  }
  return null;
}
''',
    'intelligence_helpers',
)

replace_once(
'''    } catch {
      uploadError = "Google Drive recording upload failed";
    }
''',
'''    } catch (error) {
      uploadError = error instanceof Error ? error.message : "Google Drive recording upload failed";
    }
''',
    'drive_error_preserve',
)

replace_once(
'''  if (!meeting.platform || !meeting.nativeMeetingId) throw new Error("Felfel meeting identity is not available");
  let attempt = Number(meeting.processingAttempt || 0);
''',
'''  if (!meeting.platform || !meeting.nativeMeetingId) throw new Error("Felfel meeting identity is not available");
  const intelligenceAlreadyComplete = isMeetingIntelligenceComplete(meeting);
  const lastRecordingRetryFailure = lastRecordingRetryFailureAt(meeting);
  if (
    intelligenceAlreadyComplete
    && !isRecordingComplete(String(meeting.recordingStatus || ""))
    && lastRecordingRetryFailure
    && Date.now() - lastRecordingRetryFailure.getTime() < RECORDING_RETRY_BACKOFF_MS
  ) {
    console.log(`[FelfelDiag] RECORDING_RETRY_BACKOFF id=${id} until=${new Date(lastRecordingRetryFailure.getTime() + RECORDING_RETRY_BACKOFF_MS).toISOString()}`);
    return meeting;
  }
  let attempt = Number(meeting.processingAttempt || 0);
''',
    'retry_backoff',
)

replace_once(
'''    console.log(`[FelfelDiag] AFTER tryFinalizeRecording id=${id} status=${recording?.status} mediaCount=${Array.isArray(recording?.media) ? recording.media.length : 0} error=${recording?.error || "none"} at=${new Date().toISOString()}`);

    // Step 2: Obtain transcript segments — prefer post-meeting transcription of finalized audio
''',
'''    console.log(`[FelfelDiag] AFTER tryFinalizeRecording id=${id} status=${recording?.status} mediaCount=${Array.isArray(recording?.media) ? recording.media.length : 0} error=${recording?.error || "none"} at=${new Date().toISOString()}`);

    // If transcript + analysis are already complete, retry only recording/Drive.
    // Never spend transcription or AI analysis again just because storage failed.
    if (intelligenceAlreadyComplete) {
      const recordingComplete = isRecordingComplete(recording.status);
      const retryEvent = recordingComplete ? "recording_retry_completed" : (recording.status === "failed" ? "recording_retry_failed" : "recording_retry_deferred");
      const auditTrail = Array.isArray(meeting.auditData) ? meeting.auditData : [];
      await db.update(crmMeetings).set({
        status: lifecycleAfterRecording(recording.status),
        recordingStatus: recording.status,
        recordingDriveFileId: recording.driveFileId || null,
        recordingDriveUrl: recording.driveUrl || null,
        recordingDurationSec: recording.durationSec || null,
        recordingSizeBytes: recording.sizeBytes || null,
        recordingError: recording.error || null,
        auditData: jsonValue([...auditTrail, {
          event: retryEvent,
          recordingStatus: recording.status,
          error: recording.error || null,
          media: recording.media || [],
          at: new Date().toISOString(),
        }]),
        completedAt: recordingComplete ? (meeting.completedAt || new Date()) : meeting.completedAt,
        processingLockUntil: null,
        processingAttempt: 0,
        failedAt: null,
        lastError: null,
      }).where(eq(crmMeetings.id, id));

      const updated = (await loadMeeting(id)).meeting;
      console.log(`[FelfelDiag] RECORDING_ONLY_RETRY id=${id} status=${recording.status} error=${recording.error || "none"} at=${new Date().toISOString()}`);
      if (recordingComplete) {
        void syncFelfelMeetingCalendar(updated).catch((error) => {
          console.error(`[FelfelCalendar] sync failed for meeting ${id}:`, error instanceof Error ? error.message : error);
        });
      }
      return updated;
    }

    // Step 2: Obtain transcript segments — prefer post-meeting transcription of finalized audio
''',
    'recording_only_retry',
)

p.write_text(s)
print('PATCH_OK=FELFEL_RECORDING_RETRY_V1')
