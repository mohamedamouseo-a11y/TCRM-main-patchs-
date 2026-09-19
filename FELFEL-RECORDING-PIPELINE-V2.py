#!/usr/bin/env python3
# FELFEL-RECORDING-PIPELINE-V2
# Phase 2 completion:
# - new meetings require video+audio
# - final outputs: MP4 video+audio + MP3 audio
# - real ffmpeg processing progress
# - real Drive byte-stream progress
# - Drive metadata verification before Ready
# - temporary conversion cleanup
# - Vexa source cleanup after CRM processing completes

from pathlib import Path

ROOT = Path("/var/www/TCRM-MAIN")

def path(rel: str) -> Path:
    return ROOT / rel

def read(rel: str) -> str:
    p = path(rel)
    if not p.exists():
        raise SystemExit(f"PATCH_FAIL=missing:{rel}")
    return p.read_text(encoding="utf-8")

def write(rel: str, text: str) -> None:
    p = path(rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")

def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f"PATCH_FAIL={label}:anchor_missing")
    return text.replace(old, new, 1)

# ---------------------------------------------------------------------------
# 1) Media normalizer: real ffmpeg progress, MP4+MP3, temp cleanup.
# ---------------------------------------------------------------------------
helper = r'''// FELFEL_RECORDING_PIPELINE_V2
import { spawn } from "node:child_process";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import type { FelfelRecordingArtifact } from "./felfelAdapter";

type ProgressFn = (percent: number) => void | Promise<void>;

function extFor(artifact: FelfelRecordingArtifact) {
  const type = String(artifact.contentType || "").toLowerCase();
  if (type.includes("mp4")) return "mp4";
  if (type.includes("mpeg")) return "mp3";
  if (type.includes("ogg")) return "ogg";
  if (type.includes("wav")) return "wav";
  return "webm";
}

async function runFfmpeg(args: string[], durationSec: number, onProgress?: ProgressFn) {
  await new Promise<void>((resolve, reject) => {
    const proc = spawn("ffmpeg", ["-y", ...args, "-progress", "pipe:1", "-nostats"], {
      stdio: ["ignore", "pipe", "pipe"],
    });
    let stdout = "";
    let stderr = "";
    let lastPercent = -1;
    let lastEmitAt = 0;

    const emit = (raw: number) => {
      const percent = Math.max(0, Math.min(99, Math.floor(raw)));
      const now = Date.now();
      if (percent <= lastPercent || (percent < 99 && now - lastEmitAt < 750)) return;
      lastPercent = percent;
      lastEmitAt = now;
      void Promise.resolve(onProgress?.(percent)).catch(() => undefined);
    };

    proc.stdout.on("data", (chunk: Buffer) => {
      stdout += chunk.toString();
      const lines = stdout.split(/\r?\n/);
      stdout = lines.pop() || "";
      for (const line of lines) {
        const match = line.match(/^(?:out_time_us|out_time_ms)=(\d+)/);
        if (!match || !durationSec) continue;
        const seconds = Number(match[1]) / 1_000_000;
        if (Number.isFinite(seconds)) emit((seconds / durationSec) * 100);
      }
    });

    proc.stderr.on("data", (chunk: Buffer) => {
      stderr = (stderr + chunk.toString()).slice(-5000);
    });

    proc.once("error", reject);
    proc.once("exit", (code) => {
      if (code === 0) {
        void Promise.resolve(onProgress?.(100)).catch(() => undefined);
        resolve();
      } else {
        reject(new Error("ffmpeg recording conversion failed: " + stderr.slice(-1200)));
      }
    });
  });
}

export async function prepareFelfelDriveArtifacts(
  source: FelfelRecordingArtifact[],
  onProgress?: ProgressFn,
): Promise<FelfelRecordingArtifact[]> {
  const audio = source.find((item) => item.mediaType === "audio");
  const video = source.find((item) => item.mediaType === "video");
  if (!audio && !video) return [];

  const durationSec = Math.max(
    Number(audio?.durationSec || 0),
    Number(video?.durationSec || 0),
    1,
  );

  const tempDir = await mkdtemp(path.join(os.tmpdir(), "felfel-media-"));
  try {
    const audioIn = audio ? path.join(tempDir, "audio." + extFor(audio)) : null;
    const videoIn = video ? path.join(tempDir, "video." + extFor(video)) : null;
    const mp3Out = path.join(tempDir, "recording.mp3");
    const mp4Out = path.join(tempDir, "recording.mp4");

    if (audio && audioIn) await writeFile(audioIn, audio.buffer);
    if (video && videoIn) await writeFile(videoIn, video.buffer);

    if (video && videoIn && audio && audioIn) {
      const videoCodec = String(video.contentType || "").toLowerCase() === "video/mp4"
        ? ["-c:v", "copy"]
        : ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "28", "-pix_fmt", "yuv420p"];

      await runFfmpeg([
        "-i", videoIn,
        "-i", audioIn,
        "-map", "0:v:0",
        "-map", "1:a:0",
        ...videoCodec,
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-movflags", "+faststart",
        mp4Out,
        "-map", "1:a:0",
        "-vn",
        "-c:a", "libmp3lame",
        "-q:a", "4",
        mp3Out,
      ], durationSec, onProgress);

      const [mp4, mp3] = await Promise.all([readFile(mp4Out), readFile(mp3Out)]);
      return [
        {
          mediaType: "video",
          buffer: mp4,
          fileName: video.fileName.replace(/\.[^.]+$/, "") + ".mp4",
          contentType: "video/mp4",
          durationSec,
          sizeBytes: mp4.length,
        },
        {
          mediaType: "audio",
          buffer: mp3,
          fileName: audio.fileName.replace(/\.[^.]+$/, "") + ".mp3",
          contentType: "audio/mpeg",
          durationSec,
          sizeBytes: mp3.length,
        },
      ];
    }

    if (audio && audioIn) {
      await runFfmpeg([
        "-i", audioIn,
        "-vn",
        "-c:a", "libmp3lame",
        "-q:a", "4",
        mp3Out,
      ], durationSec, onProgress);
      const mp3 = await readFile(mp3Out);
      return [{
        mediaType: "audio",
        buffer: mp3,
        fileName: audio.fileName.replace(/\.[^.]+$/, "") + ".mp3",
        contentType: "audio/mpeg",
        durationSec,
        sizeBytes: mp3.length,
      }];
    }

    if (video && videoIn) {
      const videoCodec = String(video.contentType || "").toLowerCase() === "video/mp4"
        ? ["-c:v", "copy"]
        : ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "28", "-pix_fmt", "yuv420p"];
      await runFfmpeg([
        "-i", videoIn,
        "-an",
        ...videoCodec,
        "-movflags", "+faststart",
        mp4Out,
      ], durationSec, onProgress);
      const mp4 = await readFile(mp4Out);
      return [{
        mediaType: "video",
        buffer: mp4,
        fileName: video.fileName.replace(/\.[^.]+$/, "") + ".mp4",
        contentType: "video/mp4",
        durationSec,
        sizeBytes: mp4.length,
      }];
    }

    return [];
  } finally {
    await rm(tempDir, { recursive: true, force: true }).catch(() => undefined);
  }
}
'''
write("server/services/felfel/felfelRecordingMediaService.ts", helper)

rel = "server/services/felfel/felfelAdapter.ts"
s = read(rel)
s = replace_once(
    s,
    'signal: AbortSignal.timeout(Math.max(30_000, REQUEST_TIMEOUT_MS)),',
    'signal: AbortSignal.timeout(Math.max(10 * 60_000, REQUEST_TIMEOUT_MS)),',
    "adapter_binary_timeout",
)
anchor = 'export async function getFelfelRecording(platform: string, nativeId: string, felfelMeetingId?: string | null): Promise<FelfelRecordingResult> {'
delete_fn = r'''export async function deleteFelfelRecording(recordingId: string): Promise<void> {
  const id = String(recordingId || "").trim();
  if (!/^\d+$/.test(id)) throw new FelfelAdapterError("Invalid Felfel recording id");
  try {
    await requestJson<unknown>(
      FELFEL_GATEWAY_URL,
      "/recordings/" + encodeURIComponent(id),
      { method: "DELETE" },
    );
  } catch (error) {
    if (error instanceof FelfelAdapterError && error.status === 404) return;
    throw error;
  }
}

'''
if "export async function deleteFelfelRecording" not in s:
    if anchor not in s:
        raise SystemExit("PATCH_FAIL=adapter_delete_anchor_missing")
    s = s.replace(anchor, delete_fn + anchor, 1)
write(rel, s)

rel = "server/services/googleDriveFileStorage.ts"
s = read(rel)
s = replace_once(
    s,
    '''    contentType?: string | null;
  }
): Promise<StoredDriveUploadResult> {''',
    '''    contentType?: string | null;
    onProgress?: (uploadedBytes: number, totalBytes: number) => void | Promise<void>;
    uploadTimeoutMs?: number;
  }
): Promise<StoredDriveUploadResult> {''',
    "drive_unsafe_type",
)
s = replace_once(
    s,
    '''    media: {
      mimeType: args.contentType || "application/octet-stream",
      body: Readable.from(args.buffer),
    },''',
    '''    media: {
      mimeType: args.contentType || "application/octet-stream",
      body: Readable.from((async function* () {
        const total = args.buffer.length;
        const chunkSize = 512 * 1024;
        let sent = 0;
        for (let offset = 0; offset < total; offset += chunkSize) {
          const chunk = args.buffer.subarray(offset, Math.min(offset + chunkSize, total));
          sent += chunk.length;
          if (args.onProgress) await args.onProgress(sent, total);
          yield chunk;
        }
      })()),
    },''',
    "drive_stream_progress",
)
s = replace_once(
    s,
    '''  }, { timeout: getDriveUploadTimeoutMs() });''',
    '''  }, { timeout: Math.max(getDriveUploadTimeoutMs(), Number(args.uploadTimeoutMs || 0)) });''',
    "drive_upload_timeout",
)
write(rel, s)

rel = "server/services/googleDriveStoragePool.ts"
s = read(rel)
s = replace_once(
    s,
    '''  contentType?: string | null;
}): Promise<StoredDriveUploadResult & { storageAccountId: number | null }> {''',
    '''  contentType?: string | null;
  onProgress?: (uploadedBytes: number, totalBytes: number) => void | Promise<void>;
  uploadTimeoutMs?: number;
}): Promise<StoredDriveUploadResult & { storageAccountId: number | null }> {''',
    "pool_progress_type",
)
write(rel, s)

rel = "server/services/crmFileStorage.ts"
s = read(rel)
s = replace_once(
    s,
    '''import { deleteStoredFileFromGoogleDrive, queueStoredFileToGoogleDrive, trashStoredFileOnGoogleDriveViaPool, untrashStoredFileOnGoogleDriveViaPool } from "./googleDriveFileStorage";''',
    '''import { deleteStoredFileFromGoogleDrive, getStoredGoogleDriveFileMetadata, queueStoredFileToGoogleDrive, trashStoredFileOnGoogleDriveViaPool, untrashStoredFileOnGoogleDriveViaPool } from "./googleDriveFileStorage";''',
    "crm_metadata_import",
)
s = replace_once(
    s,
    '''  uploadStatus?: "active" | "pending";
  projectReferenceTaskId?: number | null;''',
    '''  uploadStatus?: "active" | "pending";
  verifyDrive?: boolean;
  onProgress?: (uploadedBytes: number, totalBytes: number) => void | Promise<void>;
  uploadTimeoutMs?: number;
  projectReferenceTaskId?: number | null;''',
    "crm_store_options",
)
s = replace_once(
    s,
    '''    buffer: Buffer.from(input.buffer),
    contentType: input.contentType || "application/octet-stream",
  });''',
    '''    buffer: Buffer.from(input.buffer),
    contentType: input.contentType || "application/octet-stream",
    onProgress: input.onProgress,
    uploadTimeoutMs: input.uploadTimeoutMs,
  });''',
    "crm_store_progress_pass",
)
verify_old = '''  if (driveResult.uploadStatus === "disabled" || driveResult.uploadStatus === "failed") {
    throw new CrmFileDriveOnlyError(
      driveResult.error ||
        "Google Drive is not connected. Enable and connect Drive in Admin Settings."
    );
  }
  const db = await getDb();'''
verify_new = '''  if (driveResult.uploadStatus === "disabled" || driveResult.uploadStatus === "failed") {
    throw new CrmFileDriveOnlyError(
      driveResult.error ||
        "Google Drive is not connected. Enable and connect Drive in Admin Settings."
    );
  }

  if (input.verifyDrive && driveResult.driveFileId) {
    try {
      const metadata = await getStoredGoogleDriveFileMetadata(
        String(driveResult.driveFileId),
        driveResult.storageAccountId ?? null,
      );
      if (Number(metadata.size) !== Number(input.buffer.length)) {
        throw new Error("Drive verification size mismatch");
      }
      const expectedType = String(input.contentType || "").toLowerCase();
      const actualType = String(metadata.mimeType || "").toLowerCase();
      if (
        expectedType &&
        expectedType !== "application/octet-stream" &&
        actualType &&
        expectedType !== actualType
      ) {
        throw new Error("Drive verification MIME mismatch");
      }
    } catch (error) {
      await deleteStoredFileFromGoogleDrive(
        String(driveResult.driveFileId),
        driveResult.storageAccountId ?? null,
      ).catch(() => undefined);
      throw new CrmFileDriveOnlyError(
        error instanceof Error ? error.message : "Google Drive upload verification failed"
      );
    }
  }

  const db = await getDb();'''
s = replace_once(s, verify_old, verify_new, "crm_drive_verify")
write(rel, s)

rel = "server/services/felfel/felfelCrmMeetingService.ts"
s = read(rel)
s = replace_once(
    s,
    '''  createFelfelMeeting,
  detectFelfelMeetingUrl,''',
    '''  createFelfelMeeting,
  deleteFelfelRecording,
  detectFelfelMeetingUrl,''',
    "meeting_delete_import",
)
if 'from "./felfelRecordingMediaService"' not in s:
    s = replace_once(
        s,
        'import { syncFelfelMeetingCalendar } from "./felfelCalendarService";',
        'import { syncFelfelMeetingCalendar } from "./felfelCalendarService";\nimport { prepareFelfelDriveArtifacts } from "./felfelRecordingMediaService";',
        "meeting_media_import",
    )

old_join_audit = '{ event: "bot_join_requested", botName: "Felfel", at: new Date().toISOString() }'
new_join_audit = '{ event: "bot_join_requested", botName: "Felfel", recordingMode: "video_audio", at: new Date().toISOString() }'
if new_join_audit not in s:
    if old_join_audit not in s:
        raise SystemExit("PATCH_FAIL=join_audit_anchor_missing")
    s = s.replace(old_join_audit, new_join_audit, 1)

progress_anchor = 'function lastRecordingRetryFailureAt(meeting: any) {'
progress_helpers = r'''function meetingExpectsVideo(meeting: any) {
  return meetingAuditTrail(meeting?.auditData).some((entry: any) =>
    entry?.event === "bot_join_requested" && entry?.recordingMode === "video_audio"
  );
}

function recordingCleanupState(meeting: any) {
  const audit = meetingAuditTrail(meeting?.auditData);
  for (let i = audit.length - 1; i >= 0; i -= 1) {
    const entry = audit[i];
    if (entry?.event === "recording_source_cleanup") return entry;
  }
  return null;
}

async function setRecordingProgress(
  meetingId: number,
  phase: "processing" | "uploading",
  percent: number,
) {
  try {
    const { db, meeting } = await loadMeeting(meetingId);
    const value = Math.max(0, Math.min(100, Math.floor(Number(percent || 0))));
    const audit = meetingAuditTrail(meeting.auditData)
      .filter((entry: any) => entry?.event !== "recording_progress_state");
    audit.push({
      event: "recording_progress_state",
      phase,
      percent: value,
      at: new Date().toISOString(),
    });
    await db.update(crmMeetings).set({
      recordingStatus: phase,
      auditData: jsonValue(audit),
      processingLockUntil: new Date(Date.now() + PROCESSING_LOCK_MS),
    }).where(eq(crmMeetings.id, meetingId));
  } catch {
  }
}

async function cleanupFelfelRecordingSource(
  meetingId: number,
  sourceRecordingId: string | null | undefined,
) {
  const id = String(sourceRecordingId || "").trim();
  if (!/^\d+$/.test(id)) return;

  const { meeting } = await loadMeeting(meetingId);
  const previous = recordingCleanupState(meeting);
  if (previous?.recordingId === id && previous?.status === "completed") return;

  let status = "completed";
  let error: string | null = null;
  try {
    await deleteFelfelRecording(id);
  } catch (cleanupError) {
    status = "pending";
    error = cleanupError instanceof Error ? cleanupError.message : "Vexa source cleanup failed";
  }

  const { db, meeting: fresh } = await loadMeeting(meetingId);
  const audit = meetingAuditTrail(fresh.auditData)
    .filter((entry: any) => entry?.event !== "recording_source_cleanup");
  audit.push({
    event: "recording_source_cleanup",
    recordingId: id,
    status,
    error,
    at: new Date().toISOString(),
  });
  await db.update(crmMeetings).set({ auditData: jsonValue(audit) })
    .where(eq(crmMeetings.id, meetingId));

  if (status !== "completed") {
    setTimeout(() => {
      void cleanupFelfelRecordingSource(meetingId, id).catch(() => undefined);
    }, 60_000);
  }
}

'''
if "function meetingExpectsVideo" not in s:
    if progress_anchor not in s:
        raise SystemExit("PATCH_FAIL=progress_helpers_anchor_missing")
    s = s.replace(progress_anchor, progress_helpers + progress_anchor, 1)

start = s.find("async function tryFinalizeRecording(meeting: any) {")
end = s.find("\nexport async function processLinkedFelfelMeeting", start)
if start < 0 or end < 0:
    raise SystemExit("PATCH_FAIL=try_finalize_bounds_missing")

new_finalize = r'''async function tryFinalizeRecording(meeting: any) {
  const recording = await getFelfelRecording(
    meeting.platform,
    meeting.nativeMeetingId,
    meeting.felfelMeetingId,
  );
  const sourceArtifacts = Array.isArray(recording.artifacts)
    ? recording.artifacts as FelfelRecordingArtifact[]
    : [];

  if (!sourceArtifacts.length) {
    return {
      status: recording.status,
      error: recording.error || "Recording media is not finalized yet",
      sourceRecordingId: recording.recordingId || null,
      driveFileId: null,
      driveUrl: null,
      durationSec: recording.durationSec || null,
      sizeBytes: recording.sizeBytes || null,
      audio: null,
      video: null,
      media: [],
    };
  }

  if (
    meetingExpectsVideo(meeting) &&
    !sourceArtifacts.some((item) => item.mediaType === "video")
  ) {
    return {
      status: "pending",
      error: "Video recording is still finalizing",
      sourceRecordingId: recording.recordingId || null,
      driveFileId: null,
      driveUrl: null,
      durationSec: recording.durationSec || null,
      sizeBytes: recording.sizeBytes || null,
      audio: null,
      video: null,
      media: [],
    };
  }

  await setRecordingProgress(Number(meeting.id), "processing", 0);
  const artifacts = await prepareFelfelDriveArtifacts(
    sourceArtifacts,
    (percent) => setRecordingProgress(Number(meeting.id), "processing", percent),
  );

  if (!artifacts.length) {
    return {
      status: "pending",
      error: "Recording conversion produced no media",
      sourceRecordingId: recording.recordingId || null,
      driveFileId: null,
      driveUrl: null,
      durationSec: recording.durationSec || null,
      sizeBytes: null,
      audio: null,
      video: null,
      media: [],
    };
  }

  await setRecordingProgress(Number(meeting.id), "uploading", 0);

  const uploadedBy = Number(meeting.ownerUserId || meeting.createdByUserId || 0) || 1;
  const totalBytes = artifacts.reduce((sum, item) => sum + Number(item.sizeBytes || 0), 0) || 1;
  let completedBytes = 0;
  let lastProgress = -1;
  let lastProgressAt = 0;
  const media: Array<Record<string, unknown>> = [];
  let uploadError: string | null = null;

  const reportUpload = async (bytes: number) => {
    const percent = Math.max(0, Math.min(100, Math.floor((bytes / totalBytes) * 100)));
    const now = Date.now();
    if (percent <= lastProgress || (percent < 100 && now - lastProgressAt < 750)) return;
    lastProgress = percent;
    lastProgressAt = now;
    await setRecordingProgress(Number(meeting.id), "uploading", percent);
  };

  for (const artifact of artifacts) {
    const entityKey = `felfel:meeting:${meeting.id}:recording:${artifact.mediaType}`;
    const existing = (await listCrmFiles({
      entityType: "general",
      entityId: meeting.id,
      entityKey,
      limit: 1,
    }))[0] as any;

    const reusable = existing?.driveFileId
      && existing?.driveUploadStatus === "uploaded"
      && String(existing?.fileType || "").toLowerCase() === String(artifact.contentType || "").toLowerCase();

    if (reusable) {
      completedBytes += Number(existing.fileSize || artifact.sizeBytes || 0);
      await reportUpload(completedBytes);
      media.push({
        mediaType: artifact.mediaType,
        crmFileId: Number(existing.id) || null,
        driveFileId: String(existing.driveFileId),
        storageAccountId: Number(existing.storageAccountId || 0) || null,
        driveUrl: existing.driveUrl || null,
        protectedUrl: existing.id ? `/api/crm-files/${Number(existing.id)}/download` : null,
        durationSec: artifact.durationSec,
        sizeBytes: Number(existing.fileSize || artifact.sizeBytes),
        contentType: artifact.contentType,
        fileName: existing.fileName || artifact.fileName,
      });
      continue;
    }

    try {
      const baseBytes = completedBytes;
      const stored = await storeCrmFileDriveOnly({
        entityType: "general",
        entityId: meeting.id,
        entityKey,
        category: "felfel_recording",
        fileCategory: artifact.mediaType,
        description: `Felfel meeting ${meeting.id} ${artifact.mediaType} recording`,
        previousFileId: existing?.id ? Number(existing.id) : null,
        storageKey: `felfel/meetings/${meeting.id}/recording-${artifact.mediaType}`,
        fileName: artifact.fileName,
        buffer: artifact.buffer,
        contentType: artifact.contentType,
        uploadedBy,
        verifyDrive: true,
        uploadTimeoutMs: 2 * 60 * 60_000,
        onProgress: async (sent) => {
          await reportUpload(baseBytes + sent);
        },
      });
      if (!stored.driveFileId) throw new Error("Drive did not return a file id");
      completedBytes += artifact.sizeBytes;
      await reportUpload(completedBytes);
      media.push({
        mediaType: artifact.mediaType,
        crmFileId: stored.crmFileId,
        driveFileId: stored.driveFileId,
        storageAccountId: Number(stored.storageAccountId || 0) || null,
        driveUrl: stored.driveUrl || null,
        protectedUrl: stored.protectedUrl || null,
        durationSec: artifact.durationSec,
        sizeBytes: artifact.sizeBytes,
        contentType: artifact.contentType,
        fileName: artifact.fileName,
      });
    } catch (error) {
      uploadError = error instanceof Error ? error.message : "Google Drive recording upload failed";
      break;
    }
  }

  const video = media.find((item) => item.mediaType === "video") || null;
  const audio = media.find((item) => item.mediaType === "audio") || null;
  const storageAccountId = Number(video?.storageAccountId || audio?.storageAccountId || 0) || null;
  const audioReady = Boolean(audio?.driveFileId);
  const videoReady = Boolean(video?.driveFileId);
  const complete = audioReady && (!meetingExpectsVideo(meeting) || videoReady);
  const recordingStatus = videoReady ? "uploaded" : "uploaded_audio_only";

  return {
    status: uploadError && !complete ? "failed" : complete ? recordingStatus : "pending",
    error: uploadError || (
      complete
        ? null
        : meetingExpectsVideo(meeting) && !videoReady
          ? "Video recording is not available yet"
          : "Audio recording is not available yet"
    ),
    sourceRecordingId: recording.recordingId || null,
    driveFileId: video?.driveFileId || audio?.driveFileId || null,
    storageAccountId,
    driveUrl: video?.protectedUrl || audio?.protectedUrl || null,
    durationSec: Math.max(
      Number(video?.durationSec || 0),
      Number(audio?.durationSec || 0),
    ) || recording.durationSec || null,
    sizeBytes: media.reduce((sum, item) => sum + Number(item.sizeBytes || 0), 0) || null,
    audio,
    video,
    media: media.map((item) => ({
      mediaType: item.mediaType,
      storageAccountId: item.storageAccountId || null,
      protectedUrl: item.protectedUrl || null,
      durationSec: item.durationSec || null,
      sizeBytes: item.sizeBytes || null,
      contentType: item.contentType || null,
      fileName: item.fileName || null,
    })),
  };
}
'''
s = s[:start] + new_finalize + s[end:]

s = replace_once(
    s,
    'new Promise<never>((_, reject) => setTimeout(() => reject(new Error("tryFinalizeRecording TIMEOUT after 120s")), 120_000))',
    'new Promise<never>((_, reject) => setTimeout(() => reject(new Error("tryFinalizeRecording TIMEOUT after 2h")), 7_200_000))',
    "finalize_timeout",
)

retry_return = '''      if (recordingComplete) {
        void syncFelfelMeetingCalendar(updated).catch((error) => {
          console.error(`[FelfelCalendar] sync failed for meeting ${id}:`, error instanceof Error ? error.message : error);
        });
      }
      return updated;'''
retry_return_new = '''      if (recordingComplete) {
        void syncFelfelMeetingCalendar(updated).catch((error) => {
          console.error(`[FelfelCalendar] sync failed for meeting ${id}:`, error instanceof Error ? error.message : error);
        });
        void cleanupFelfelRecordingSource(id, recording.sourceRecordingId).catch(() => undefined);
      }
      return updated;'''
s = replace_once(s, retry_return, retry_return_new, "cleanup_retry_branch")

normal_anchor = '''    await applySmartFelfelMeetingTitle(id, analysis);

    if (meeting.clientId) {'''
normal_new = '''    await applySmartFelfelMeetingTitle(id, analysis);

    if (isRecordingComplete(recording.status)) {
      void cleanupFelfelRecordingSource(id, recording.sourceRecordingId).catch(() => undefined);
    }

    if (meeting.clientId) {'''
s = replace_once(s, normal_anchor, normal_new, "cleanup_normal_branch")
write(rel, s)

rel = "server/services/felfel/felfelDashboardService.ts"
s = read(rel)
progress_fn = '''function recordingProgress(auditData: unknown) {
  const audit = asRows(auditData);
  const state = [...audit].reverse().find((entry: any) =>
    entry?.event === "recording_progress_state"
  );
  const percent = Number(state?.percent);
  return {
    phase: state?.phase || null,
    percent: Number.isFinite(percent)
      ? Math.max(0, Math.min(100, Math.floor(percent)))
      : null,
  };
}

'''
if "function recordingProgress(auditData" not in s:
    anchor = "function positiveInt(value: unknown) {"
    if anchor not in s:
        raise SystemExit("PATCH_FAIL=dashboard_progress_anchor_missing")
    s = s.replace(anchor, progress_fn + anchor, 1)
s = replace_once(
    s,
    '''      clientName: row.clientName || row.leadName || null,
      recordingMedia: recordingMedia(row.auditData),''',
    '''      clientName: row.clientName || row.leadName || null,
      recordingMedia: recordingMedia(row.auditData),
      recordingProgress: recordingProgress(row.auditData).percent,
      recordingProgressPhase: recordingProgress(row.auditData).phase,''',
    "dashboard_progress_map",
)
write(rel, s)

rel = "client/src/components/felfel/FelfelRecordingPlayer.tsx"
s = read(rel)
if 'from "react"' not in s:
    s = replace_once(
        s,
        "// FELFEL_RECORDING_PREVIEW_DOWNLOAD_V1\n",
        '// FELFEL_RECORDING_PREVIEW_DOWNLOAD_V1\nimport { useEffect, useState } from "react";\n',
        "player_react_import",
    )
s = replace_once(
    s,
    '''  recordingStatus,
  meetingStatus,
  isRTL,''',
    '''  recordingStatus,
  recordingProgress,
  meetingStartedAt,
  meetingStatus,
  isRTL,''',
    "player_props",
)
s = replace_once(
    s,
    '''  recordingStatus?: string | null;
  meetingStatus?: string | null;
  isRTL: boolean;''',
    '''  recordingStatus?: string | null;
  recordingProgress?: number | null;
  meetingStartedAt?: string | null;
  meetingStatus?: string | null;
  isRTL: boolean;''',
    "player_prop_types",
)
s = replace_once(
    s,
    '''  const meetingLifecycle = String(meetingStatus || "");''',
    '''  const meetingLifecycle = String(meetingStatus || "");
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    if (status !== "recording") return;
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [status]);

  const startedMs = meetingStartedAt ? new Date(meetingStartedAt).getTime() : NaN;
  const recordingElapsed =
    status === "recording" && Number.isFinite(startedMs) && now >= startedMs
      ? formatDuration(Math.floor((now - startedMs) / 1000))
      : null;
  const progressNumber = Number(recordingProgress);
  const progress = Number.isFinite(progressNumber)
    ? Math.max(0, Math.min(100, Math.floor(progressNumber)))
    : null;
  const showProgress =
    ["processing", "uploading"].includes(status) && progress !== null;''',
    "player_progress_state",
)
s = replace_once(
    s,
    '''          </p>
        </div>
      </div>''',
    '''          </p>

          {status === "recording" && recordingElapsed && (
            <p className="mt-2 text-sm font-black tabular-nums">{recordingElapsed}</p>
          )}

          {showProgress && (
            <div className="mx-auto mt-3 w-full max-w-sm">
              <div className="mb-1 flex items-center justify-between text-[11px] font-bold">
                <span>
                  {status === "uploading"
                    ? (isRTL ? "رفع إلى Google Drive" : "Uploading to Google Drive")
                    : (isRTL ? "معالجة التسجيل" : "Processing recording")}
                </span>
                <span>{progress}%</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-orange-500 transition-[width] duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </div>''',
    "player_progress_ui",
)
write(rel, s)

rel = "client/src/components/felfel/FelfelMeetingWorkspaceCard.tsx"
s = read(rel)
s = replace_once(
    s,
    '''                    recordingStatus={meeting.recordingStatus}
                    meetingStatus={meeting.status}''',
    '''                    recordingStatus={meeting.recordingStatus}
                    recordingProgress={meeting.recordingProgress}
                    meetingStartedAt={meeting.startedAt}
                    meetingStatus={meeting.status}''',
    "workspace_progress_props",
)
write(rel, s)

rel = "client/src/components/FelfelMeetingsHub.tsx"
s = read(rel)
if "function recordingProgress(value: unknown)" not in s:
    anchor = "function recordingMedia(value: unknown) {"
    helper2 = '''function recordingProgress(value: unknown) {
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
    if anchor not in s:
        raise SystemExit("PATCH_FAIL=hub_progress_anchor_missing")
    s = s.replace(anchor, helper2 + anchor, 1)
s = replace_once(
    s,
    '''                recordingStatus={meeting.recordingStatus}
                meetingStatus={meeting.status}''',
    '''                recordingStatus={meeting.recordingStatus}
                recordingProgress={recordingProgress(meeting.auditData)}
                meetingStartedAt={meeting.startedAt}
                meetingStatus={meeting.status}''',
    "hub_progress_props",
)
write(rel, s)

print("PATCH=PASS")
print("FILES=9")
print("PIPELINE=MP4+MP3+REAL_PROCESSING_PROGRESS+REAL_UPLOAD_PROGRESS+DRIVE_VERIFY+TEMP_CLEANUP+VEXA_CLEANUP")