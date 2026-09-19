#!/usr/bin/env python3
from pathlib import Path

ROOT = Path("/var/www/TCRM-MAIN")
changed = []

# -------------------------------------------------------------------
# 1) Replace recording player with preview + download + processing UI.
# -------------------------------------------------------------------
player = ROOT / "client/src/components/felfel/FelfelRecordingPlayer.tsx"
src = player.read_text()
if "FELFEL_RECORDING_PREVIEW_DOWNLOAD_V1" not in src:
    player.write_text(r'''// FELFEL_RECORDING_PREVIEW_DOWNLOAD_V1
import {
  CheckCircle2,
  CircleAlert,
  Download,
  ExternalLink,
  Headphones,
  Loader2,
  Video as VideoIcon,
} from "lucide-react";

type RecordingMedia = {
  mediaType?: string | null;
  protectedUrl?: string | null;
  driveUrl?: string | null;
  durationSec?: number | null;
  sizeBytes?: number | null;
};

function formatDuration(value: unknown) {
  const seconds = Number(value || 0);
  if (!Number.isFinite(seconds) || seconds <= 0) return null;
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainder = Math.round(seconds % 60).toString().padStart(2, "0");
  return hours > 0 ? `${hours}:${String(minutes).padStart(2, "0")}:${remainder}` : `${minutes}:${remainder}`;
}

function formatSize(value: unknown) {
  const bytes = Number(value || 0);
  if (!Number.isFinite(bytes) || bytes <= 0) return null;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function protectedUrl(value: unknown) {
  const url = String(value || "").trim();
  return url.startsWith("/api/crm-files/") ? url : null;
}

function previewUrl(value: unknown) {
  const url = protectedUrl(value);
  if (!url) return null;
  return url.replace(/\/download(?:\?.*)?$/, "/preview");
}

function statusLabel(status: string, isRTL: boolean) {
  if (["uploaded", "uploaded_audio_only"].includes(status)) return isRTL ? "جاهز للتشغيل" : "Ready to play";
  if (["pending", "processing"].includes(status)) return isRTL ? "جاري تجهيز التسجيل" : "Processing recording";
  if (status === "failed") return isRTL ? "تعذر تجهيز التسجيل" : "Recording failed";
  return isRTL ? "في انتظار التسجيل" : "Waiting for recording";
}

export default function FelfelRecordingPlayer({
  media,
  driveUrl,
  durationSec,
  sizeBytes,
  recordingStatus,
  meetingStatus,
  isRTL,
}: {
  media?: RecordingMedia[] | null;
  driveUrl?: string | null;
  durationSec?: number | null;
  sizeBytes?: number | null;
  recordingStatus?: string | null;
  meetingStatus?: string | null;
  isRTL: boolean;
}) {
  const entries = Array.isArray(media) ? media : [];
  const status = String(recordingStatus || "");
  const meetingLifecycle = String(meetingStatus || "");

  let video = entries.find((item) => item?.mediaType === "video" && protectedUrl(item?.protectedUrl));
  let audio = entries.find((item) => item?.mediaType === "audio" && protectedUrl(item?.protectedUrl));

  // Older/retried meetings may only expose the protected top-level URL.
  const topLevelProtected = protectedUrl(driveUrl);
  if (!video && !audio && topLevelProtected) {
    if (status === "uploaded_audio_only") {
      audio = { mediaType: "audio", protectedUrl: topLevelProtected, durationSec, sizeBytes };
    } else if (status === "uploaded") {
      video = { mediaType: "video", protectedUrl: topLevelProtected, durationSec, sizeBytes };
    }
  }

  const playable = video || audio;
  const resolvedDuration = formatDuration(playable?.durationSec ?? durationSec);
  const resolvedSize = formatSize(playable?.sizeBytes ?? sizeBytes);
  const isReady = Boolean(playable) || ["uploaded", "uploaded_audio_only"].includes(status);
  const isProcessing = ["pending", "processing"].includes(status) || meetingLifecycle === "processing";
  const isFailed = status === "failed";

  const videoDownload = protectedUrl(video?.protectedUrl);
  const audioDownload = protectedUrl(audio?.protectedUrl);
  const videoPreview = previewUrl(videoDownload);
  const audioPreview = previewUrl(audioDownload);

  if (!playable && !driveUrl) {
    return (
      <div className="flex min-h-40 items-center justify-center rounded-2xl border border-dashed border-border bg-muted/20 p-5 text-center">
        <div>
          <div className={`mx-auto grid h-11 w-11 place-items-center rounded-full ${isFailed ? "bg-red-500/10 text-red-600" : isProcessing ? "bg-orange-500/10 text-orange-600" : "bg-muted text-muted-foreground"}`}>
            {isProcessing ? <Loader2 className="h-5 w-5 animate-spin" /> : isFailed ? <CircleAlert className="h-5 w-5" /> : <Headphones className="h-5 w-5" />}
          </div>
          <p className="mt-2 text-sm font-bold">{statusLabel(status, isRTL)}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            {isProcessing
              ? (isRTL ? "فلفل يحفظ التسجيل ويجهزه للمعاينة." : "Felfel is saving and preparing the recording for preview.")
              : (isRTL ? "سيظهر المشغل هنا فور توفر ملف التسجيل." : "The player will appear here as soon as the recording is available.")}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-border/70 bg-muted/15" data-felfel-recording-player="preview-download-v1">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/60 px-3 py-2.5">
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-2 text-xs font-bold">
            {video ? <VideoIcon className="h-4 w-4 text-orange-500" /> : <Headphones className="h-4 w-4 text-orange-500" />}
            {video ? (isRTL ? "تسجيل الاجتماع — فيديو" : "Meeting recording — Video") : (isRTL ? "تسجيل الاجتماع — صوت" : "Meeting recording — Audio")}
          </span>
          <span className={`inline-flex items-center gap-1 rounded-full px-2 py-1 text-[10px] font-bold ${isReady ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300" : isFailed ? "bg-red-500/10 text-red-600" : "bg-orange-500/10 text-orange-700 dark:text-orange-300"}`}>
            {isReady ? <CheckCircle2 className="h-3 w-3" /> : isProcessing ? <Loader2 className="h-3 w-3 animate-spin" /> : null}
            {statusLabel(status, isRTL)}
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-2 text-[11px] text-muted-foreground">
          {resolvedDuration && <span>{isRTL ? "المدة" : "Duration"}: {resolvedDuration}</span>}
          {resolvedSize && <span>· {resolvedSize}</span>}

          {videoDownload && (
            <a href={videoDownload} download className="inline-flex items-center gap-1 rounded-lg border border-border bg-background px-2.5 py-1.5 font-bold text-foreground hover:bg-muted">
              <Download className="h-3.5 w-3.5" />{isRTL ? "تنزيل الفيديو" : "Download video"}
            </a>
          )}
          {audioDownload && (
            <a href={audioDownload} download className="inline-flex items-center gap-1 rounded-lg border border-border bg-background px-2.5 py-1.5 font-bold text-foreground hover:bg-muted">
              <Download className="h-3.5 w-3.5" />{isRTL ? "تنزيل الصوت" : "Download audio"}
            </a>
          )}
          {!videoDownload && !audioDownload && driveUrl && (
            <a href={driveUrl} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 font-semibold text-primary hover:underline">
              <ExternalLink className="h-3 w-3" />Drive
            </a>
          )}
        </div>
      </div>

      {videoPreview ? (
        <video controls playsInline preload="metadata" className="aspect-video w-full bg-black" src={videoPreview} />
      ) : audioPreview ? (
        <div className="p-4">
          <audio controls preload="metadata" className="w-full" src={audioPreview} />
        </div>
      ) : (
        <div className="p-4 text-center text-xs text-muted-foreground">
          {isRTL ? "التسجيل محفوظ، لكن المعاينة المباشرة غير متاحة لهذا الملف." : "The recording is stored, but direct preview is not available for this file."}
        </div>
      )}
    </div>
  );
}
''')
    changed.append(str(player.relative_to(ROOT)))

# -------------------------------------------------------------------
# 2) Dashboard service must expose media from successful retry events too.
# -------------------------------------------------------------------
dash = ROOT / "server/services/felfel/felfelDashboardService.ts"
s = dash.read_text()
old = '''function recordingMedia(auditData: unknown) {
  const audit = asRows(auditData);
  const finalized = [...audit].reverse().find((entry: any) => entry?.event === "recording_finalized");
  return asRows(finalized?.media).filter((item: any) => item?.protectedUrl || item?.driveUrl);
}'''
new = '''function recordingMedia(auditData: unknown) {
  const audit = asRows(auditData);
  const finalized = [...audit].reverse().find((entry: any) =>
    entry?.event === "recording_finalized" || entry?.event === "recording_retry_completed"
  );
  return asRows(finalized?.media).filter((item: any) => item?.protectedUrl || item?.driveUrl);
}'''
if new not in s:
    if old not in s:
        raise SystemExit("ANCHOR_NOT_FOUND:dashboard-recording-media")
    dash.write_text(s.replace(old,new,1))
    changed.append(str(dash.relative_to(ROOT)))

# -------------------------------------------------------------------
# 3) Linked-meeting hub must also recognize retry-completed media.
# -------------------------------------------------------------------
hub = ROOT / "client/src/components/FelfelMeetingsHub.tsx"
s = hub.read_text()
old = '''function recordingMedia(value: unknown) {
  const entries = list(value);
  const finalized = [...entries].reverse().find((entry: any) => entry?.event === "recording_finalized");
  return list(finalized?.media) as any[];
}'''
new = '''function recordingMedia(value: unknown) {
  const entries = list(value);
  const finalized = [...entries].reverse().find((entry: any) =>
    entry?.event === "recording_finalized" || entry?.event === "recording_retry_completed"
  );
  return list(finalized?.media) as any[];
}'''
if new not in s:
    if old not in s:
        raise SystemExit("ANCHOR_NOT_FOUND:hub-recording-media")
    s = s.replace(old,new,1)

old_call = '''              <FelfelRecordingPlayer
                media={media}
                driveUrl={meeting.recordingDriveUrl}
                durationSec={meeting.recordingDurationSec}
                sizeBytes={meeting.recordingSizeBytes}
                isRTL={isRTL}
              />'''
new_call = '''              <FelfelRecordingPlayer
                media={media}
                driveUrl={meeting.recordingDriveUrl}
                durationSec={meeting.recordingDurationSec}
                sizeBytes={meeting.recordingSizeBytes}
                recordingStatus={meeting.recordingStatus}
                meetingStatus={meeting.status}
                isRTL={isRTL}
              />'''
if new_call not in s:
    if old_call not in s:
        raise SystemExit("ANCHOR_NOT_FOUND:hub-player-call")
    s = s.replace(old_call,new_call,1)
hub.write_text(s)
if str(hub.relative_to(ROOT)) not in changed:
    changed.append(str(hub.relative_to(ROOT)))

# -------------------------------------------------------------------
# 4) Workspace card passes lifecycle/recording status to player.
# -------------------------------------------------------------------
card = ROOT / "client/src/components/felfel/FelfelMeetingWorkspaceCard.tsx"
s = card.read_text()
old = '''                  <FelfelRecordingPlayer media={meeting.recordingMedia} driveUrl={meeting.recordingDriveUrl} durationSec={meeting.recordingDurationSec} sizeBytes={meeting.recordingSizeBytes} isRTL={isRTL} />'''
new = '''                  <FelfelRecordingPlayer
                    media={meeting.recordingMedia}
                    driveUrl={meeting.recordingDriveUrl}
                    durationSec={meeting.recordingDurationSec}
                    sizeBytes={meeting.recordingSizeBytes}
                    recordingStatus={meeting.recordingStatus}
                    meetingStatus={meeting.status}
                    isRTL={isRTL}
                  />'''
if new not in s:
    if old not in s:
        raise SystemExit("ANCHOR_NOT_FOUND:workspace-player-call")
    card.write_text(s.replace(old,new,1))
    changed.append(str(card.relative_to(ROOT)))

print("PATCH_OK=" + ",".join(changed))
