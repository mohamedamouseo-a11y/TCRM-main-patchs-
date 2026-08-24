#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys

PATCH_ID = "FELFEL-VIDEO-AUDIO-RECORDING-DRIVE-V1"
BASELINE_SHA = "90b1d4573626e0fad4c7629df1b062e939099e7e"
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
assets = pathlib.Path(__file__).resolve().parent

ADAPTER = "server/services/felfel/felfelAdapter.ts"
STORAGE = "server/services/crmFileStorage.ts"
SERVICE = "server/services/felfel/felfelRecordingDriveService.ts"
TEST = "server/services/felfel/felfelRecordingDriveService.test.ts"
ROUTERS = "server/routers.ts"
PAGE = "client/src/pages/FelfelPage.tsx"
OVERLAY_README = "server/services/felfel/vexa-video-overlay/README.md"
VEXA_INDEX_REL = "core/meetings/services/bot/src/index.ts"
VEXA_VIDEO_REL = "core/meetings/modules/recording/src/video-recording.ts"


def run(*args: str, cwd: pathlib.Path | None = None) -> str:
    p = subprocess.run(list(args), cwd=cwd or root, text=True, capture_output=True)
    if p.returncode != 0:
        sys.stdout.write(p.stdout)
        sys.stderr.write(p.stderr)
        raise SystemExit(f"Command failed ({p.returncode}): {' '.join(args)}")
    return p.stdout.strip()


def read(rel: str) -> str:
    p = root / rel
    if not p.is_file():
        raise SystemExit(f"Missing required file: {rel}")
    return p.read_text(encoding="utf-8")


def replace_once(source: str, old: str, new: str, label: str) -> str:
    n = source.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected anchor exactly once, found {n}")
    return source.replace(old, new, 1)


def asset(name: str) -> pathlib.Path:
    p = assets / name
    if not p.is_file():
        raise SystemExit(f"Missing approved patch asset: {name}")
    return p


def find_vexa_root() -> pathlib.Path:
    candidates = [
        root / "ai-staff/felfel/vexa",
        root / "ai-staff/felfel/vexa-main",
        root / "ai-staff/felfel",
    ]
    for candidate in candidates:
        if (candidate / VEXA_INDEX_REL).is_file() and (candidate / VEXA_VIDEO_REL).is_file():
            return candidate
    raise SystemExit(
        "Vexa source checkout not found under /var/www/TCRM-MAIN/ai-staff/felfel; "
        "video recording cannot be wired safely without the v0.12 source tree"
    )


if run("git", "rev-parse", "--show-toplevel") != str(root):
    raise SystemExit("Run this patch from the canonical TCRM repository root")
if run("git", "rev-parse", "HEAD") != BASELINE_SHA:
    raise SystemExit(f"{PATCH_ID} requires baseline {BASELINE_SHA}")
if run("git", "status", "--short"):
    raise SystemExit("Refusing to apply on a dirty TCRM worktree")

for rel in (SERVICE, TEST, OVERLAY_README):
    if (root / rel).exists():
        raise SystemExit(f"Refusing to overwrite existing recording integration file: {rel}")

for name in ("felfelRecordingDriveService.ts", "felfelRecordingDriveService.test.ts", "README.md", "docker-compose.video-recording.yml"):
    asset(name)

vexa_root = find_vexa_root()
vexa_index_path = vexa_root / VEXA_INDEX_REL
vexa_video_path = vexa_root / VEXA_VIDEO_REL
vexa_index = vexa_index_path.read_text(encoding="utf-8")
vexa_video = vexa_video_path.read_text(encoding="utf-8")
for marker in (
    "import { createBotRecordingSink } from './recording.js';",
    "const recording = inv.recordingEnabled ? createBotRecordingSink",
    "startCapture: () => startCaptureBridge",
    "await pipeline.stop().catch",
):
    if marker not in vexa_index:
        raise SystemExit(f"Unexpected Vexa v0.12 bot source; marker missing: {marker}")
for marker in ("export class VideoRecordingService", "x11grab", "media_type: 'video'", "ffmpeg"):
    if marker not in vexa_video:
        raise SystemExit(f"Existing Vexa video recorder marker missing: {marker}")

adapter = read(ADAPTER)
storage = read(STORAGE)
routers = read(ROUTERS)
page = read(PAGE)
for source, marker in (
    (adapter, "export async function createFelfelMeeting"),
    (adapter, "export async function listFelfelMeetings"),
    (storage, "export async function storeCrmFileDriveOnly"),
    (routers, "createFollowUp: felfelProcedure"),
    (page, "Follow-up Planner"),
    (page, "Meeting Archive & Google Drive"),
):
    if marker not in source:
        raise SystemExit(f"Required TCRM baseline marker missing: {marker}")

# ---- felfelAdapter.ts -------------------------------------------------------
adapter = replace_once(
    adapter,
    'import { promisify } from "node:util";\n',
    'import { promisify } from "node:util";\nimport { Readable } from "node:stream";\n',
    "Readable import",
)

transcript_iface = '''export interface FelfelTranscript {
  platform: FelfelPlatform | string;
  nativeId: string;
  segments: FelfelTranscriptSegment[];
}
'''
recording_ifaces = transcript_iface + '''
export interface FelfelRecordingMedia {
  id: string;
  type: string;
  format: string;
  durationSeconds: number | null;
  fileSize: number | null;
  isFinal: boolean;
}

export interface FelfelRecording {
  id: string;
  meetingId: string;
  sessionUid: string | null;
  status: string;
  mediaFiles: FelfelRecordingMedia[];
}

export interface FelfelRecordingMaster {
  recordingId: string;
  mediaType: "audio" | "video";
  mediaFileId: string;
  rawUrl: string;
  durationSeconds: number | null;
}

export interface FelfelRecordingStream {
  stream: Readable;
  contentType: string;
  contentLength: number | null;
  master: FelfelRecordingMaster;
}
'''
adapter = replace_once(adapter, transcript_iface, recording_ifaces, "recording interfaces")

as_record_anchor = '''function asRecord(value: unknown): Record<string, unknown> {
'''
stream_helper = '''async function requestRecordingStream(path: string, retry = true): Promise<{
  stream: Readable;
  contentType: string;
  contentLength: number | null;
}> {
  const headers = new Headers();
  headers.set("Accept", "*/*");
  headers.set("X-API-Key", await getUserApiKey());
  let response: Response;
  try {
    response = await fetch(`${FELFEL_GATEWAY_URL}${path}`, {
      headers,
      signal: AbortSignal.timeout(30_000),
    });
  } catch {
    throw new FelfelAdapterError("Felfel recording stream is unavailable");
  }
  if (!response.ok) {
    if (retry && (response.status === 401 || response.status === 403)) {
      cachedUserApiKey = null;
      return requestRecordingStream(path, false);
    }
    const text = await response.text().catch(() => "");
    let detail: string | undefined;
    if (text) {
      try { detail = safeErrorMessage(JSON.parse(text)); } catch { /* non-JSON */ }
    }
    throw new FelfelAdapterError(detail || `Felfel recording download failed (${response.status})`, response.status);
  }
  if (!response.body) throw new FelfelAdapterError("Felfel recording response had no body");
  const lengthHeader = response.headers.get("content-length");
  const parsedLength = lengthHeader ? Number(lengthHeader) : NaN;
  return {
    stream: Readable.fromWeb(response.body as any),
    contentType: response.headers.get("content-type") || "application/octet-stream",
    contentLength: Number.isFinite(parsedLength) && parsedLength >= 0 ? parsedLength : null,
  };
}

''' + as_record_anchor
adapter = replace_once(adapter, as_record_anchor, stream_helper, "recording stream helper")

health_anchor = '''export async function getFelfelHealth(): Promise<FelfelHealth> {
'''
normalize_recording = '''function normalizeRecording(value: unknown): FelfelRecording {
  const record = asRecord(value);
  const rawMedia = Array.isArray(record.media_files) ? record.media_files
    : Array.isArray(record.mediaFiles) ? record.mediaFiles
    : [];
  return {
    id: asString(record.id) || "",
    meetingId: asString(record.meeting_id ?? record.meetingId) || "",
    sessionUid: asString(record.session_uid ?? record.sessionUid),
    status: asString(record.status) || "unknown",
    mediaFiles: rawMedia.map((value) => {
      const media = asRecord(value);
      const duration = Number(media.duration_seconds ?? media.durationSeconds);
      const fileSize = Number(media.file_size ?? media.fileSize ?? media.file_size_bytes);
      return {
        id: asString(media.id) || "",
        type: asString(media.type ?? media.media_type) || "",
        format: (asString(media.format ?? media.media_format) || "").toLowerCase(),
        durationSeconds: Number.isFinite(duration) ? duration : null,
        fileSize: Number.isFinite(fileSize) ? fileSize : null,
        isFinal: Boolean(media.is_final ?? media.isFinal),
      };
    }).filter((media) => media.id && media.type),
  };
}

''' + health_anchor
adapter = replace_once(adapter, health_anchor, normalize_recording, "recording normalizer")

platform_anchor = '''  const platform = ensureSupportedPlatform(parsed.platform);
  const payload = await requestJson<unknown>(FELFEL_GATEWAY_URL, "/bots", {
'''
platform_replacement = '''  const platform = ensureSupportedPlatform(parsed.platform);

  // Privacy guard: Vexa Lite shares one Xvfb display between bot child processes.
  // A second concurrent TCRM Felfel bot could cross-capture another meeting's screen.
  const activeStatuses = new Set(["requested", "joining", "awaiting_admission", "needs_help", "active", "stopping"]);
  const activeMeeting = (await listFelfelMeetings().catch(() => []))
    .find((meeting) => activeStatuses.has(String(meeting.status || "").toLowerCase()));
  if (activeMeeting) {
    throw new FelfelAdapterError(
      "Felfel video recording mode allows one active meeting at a time to prevent cross-meeting screen capture"
    );
  }

  const payload = await requestJson<unknown>(FELFEL_GATEWAY_URL, "/bots", {
'''
adapter = replace_once(adapter, platform_anchor, platform_replacement, "single meeting privacy guard")

bot_name_anchor = '''      bot_name: (botName || "Felfel").trim().slice(0, 100) || "Felfel",
'''
bot_name_replacement = bot_name_anchor + '''      recording_enabled: true,
      transcribe_enabled: true,
'''
adapter = replace_once(adapter, bot_name_anchor, bot_name_replacement, "recording flags")

reset_anchor = '''export function __resetFelfelAdapterForTests() {
'''
recording_api = '''export async function listFelfelRecordings(): Promise<FelfelRecording[]> {
  const payload = asRecord(await requestJson<unknown>(FELFEL_GATEWAY_URL, "/recordings"));
  const recordings = Array.isArray(payload.recordings) ? payload.recordings : [];
  return recordings.map(normalizeRecording).filter((recording) => recording.id && recording.meetingId);
}

export async function getFelfelRecordingMaster(
  recordingId: string | number,
  mediaType: "audio" | "video",
): Promise<FelfelRecordingMaster> {
  const safeId = String(recordingId).trim();
  if (!/^\\d+$/.test(safeId)) throw new FelfelAdapterError("Invalid recording id");
  const payload = asRecord(await requestJson<unknown>(
    FELFEL_GATEWAY_URL,
    `/recordings/${encodeURIComponent(safeId)}/master?type=${encodeURIComponent(mediaType)}`,
  ));
  const mediaFileId = asString(payload.media_file_id ?? payload.mediaFileId);
  const rawUrl = asString(payload.raw_url ?? payload.rawUrl);
  const duration = Number(payload.duration_seconds ?? payload.durationSeconds);
  if (!mediaFileId || !rawUrl || !rawUrl.startsWith("/recordings/")) {
    throw new FelfelAdapterError(`Felfel ${mediaType} recording master is not ready`);
  }
  return {
    recordingId: safeId,
    mediaType,
    mediaFileId,
    rawUrl,
    durationSeconds: Number.isFinite(duration) ? duration : null,
  };
}

export async function openFelfelRecordingStream(
  recordingId: string | number,
  mediaType: "audio" | "video",
): Promise<FelfelRecordingStream> {
  const master = await getFelfelRecordingMaster(recordingId, mediaType);
  const opened = await requestRecordingStream(master.rawUrl);
  return { ...opened, master };
}

''' + reset_anchor
adapter = replace_once(adapter, reset_anchor, recording_api, "recording API exports")
(root / ADAPTER).write_text(adapter, encoding="utf-8")

# ---- crmFileStorage.ts ------------------------------------------------------
storage = replace_once(
    storage,
    'import { promises as fs } from "node:fs";\n',
    'import { promises as fs } from "node:fs";\nimport type { Readable } from "node:stream";\n',
    "storage Readable import",
)
input_anchor = '''export type StoreCrmFileInput = {
  entityType: CrmFileEntityType | string;
  entityId?: string | number | null;
  entityKey?: string | null;
  category: string;
  fileCategory?: string | null;
  description?: string | null;
  previousFileId?: number | null;
  storageKey: string;
  fileName: string;
  buffer: Buffer;
  contentType?: string | null;
  uploadedBy: number;
  uploadStatus?: "active" | "pending";
  projectReferenceTaskId?: number | null;
  projectReferenceClientId?: number | null;
};
'''
input_replacement = input_anchor + '''
export type StoreCrmFileStreamInput = Omit<StoreCrmFileInput, "buffer"> & {
  stream: Readable;
  fileSize?: number | null;
  appProperties?: Record<string, string>;
};
'''
storage = replace_once(storage, input_anchor, input_replacement, "stream storage input")

drive_anchor = '''export async function storeCrmFileDriveOnly(input: StoreCrmFileInput) {
'''
stream_store = '''export async function storeCrmFileStreamDriveOnly(input: StoreCrmFileStreamInput) {
  const { uploadStoredStreamToGoogleDrive } = await import("./googleDriveFileStorage");
  const driveResult = await uploadStoredStreamToGoogleDrive({
    storageKey: input.storageKey,
    fileName: input.fileName,
    stream: input.stream,
    contentType: input.contentType || "application/octet-stream",
    appProperties: input.appProperties,
  });
  if (driveResult.uploadStatus !== "uploaded" || !driveResult.driveFileId) {
    throw new CrmFileDriveOnlyError(driveResult.error || "Google Drive recording upload failed");
  }
  const db = await getDb();
  if (!db) throw new Error("Database connection failed");
  const [inserted] = await db.insert(crmFiles).values({
    entityType: input.entityType,
    entityId: input.entityId === undefined || input.entityId === null ? null : String(input.entityId),
    entityKey: input.entityKey ?? null,
    category: input.category,
    fileCategory: input.fileCategory ?? null,
    description: input.description ?? null,
    fileName: input.fileName,
    fileUrl: null,
    localUrl: null,
    storageKey: input.storageKey,
    driveFileId: driveResult.driveFileId,
    driveUrl: driveResult.driveUrl ?? null,
    driveUploadStatus: "uploaded",
    driveUploadError: null,
    fileSize: input.fileSize ?? null,
    fileType: input.contentType || "application/octet-stream",
    projectReferenceTaskId: input.projectReferenceTaskId ?? null,
    projectReferenceClientId: input.projectReferenceClientId ?? null,
    uploadStatus: input.uploadStatus ?? "active",
    previousFileId: input.previousFileId ?? null,
    replacedByFileId: null,
    uploadedBy: input.uploadedBy,
  } as any).$returningId();
  const crmFileId = Number((inserted as any)?.id ?? (inserted as any)?.insertId ?? 0) || null;
  return {
    crmFileId,
    fileName: input.fileName,
    fileCategory: input.fileCategory ?? null,
    description: input.description ?? null,
    fileSize: input.fileSize ?? null,
    fileType: input.contentType || "application/octet-stream",
    projectReferenceClientId: input.projectReferenceClientId ?? null,
    protectedUrl: buildProtectedCrmFileUrl(crmFileId),
    storageKey: input.storageKey,
    driveFileId: driveResult.driveFileId,
    driveUrl: driveResult.driveUrl ?? null,
    driveUploadStatus: "uploaded" as const,
    driveUploadError: null,
  };
}


''' + drive_anchor
storage = replace_once(storage, drive_anchor, stream_store, "stream Drive-only helper")
(root / STORAGE).write_text(storage, encoding="utf-8")

# ---- new TCRM service/test/overlay doc --------------------------------------
service_dest = root / SERVICE
service_dest.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(asset("felfelRecordingDriveService.ts"), service_dest)
shutil.copyfile(asset("felfelRecordingDriveService.test.ts"), root / TEST)
readme_dest = root / OVERLAY_README
readme_dest.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(asset("README.md"), readme_dest)

# ---- routers.ts -------------------------------------------------------------
followup_import = '''import {
  createFelfelCrmFollowUp,
  listFelfelCrmFollowUps,
} from "./services/felfel/felfelFollowUpService";
'''
routers = replace_once(
    routers,
    followup_import,
    followup_import + '''import {
  getFelfelRecordingStatus,
  listFelfelRecordingExports,
  saveFelfelRecordingToDrive,
} from "./services/felfel/felfelRecordingDriveService";
''',
    "recording router import",
)
archive_router_anchor = '''    listArchives: felfelProcedure
      .input(z.object({ clientId: z.number().int().positive() }).strict())
'''
recording_routes = '''    recordingStatus: felfelProcedure
      .input(z.object({ meetingId: z.string().trim().regex(/^\\d+$/) }).strict())
      .query(({ input }) => getFelfelRecordingStatus(input.meetingId)),
    recordingExports: felfelProcedure
      .input(z.object({ clientId: z.number().int().positive() }).strict())
      .query(({ input }) => listFelfelRecordingExports(input.clientId)),
    saveRecordingToDrive: felfelProcedure
      .input(z.object({
        clientId: z.number().int().positive(),
        dealId: z.number().int().positive().optional().nullable(),
        platform: z.enum(["google_meet", "teams", "zoom", "jitsi"]),
        nativeId: z.string().trim().min(1).max(255),
        meetingId: z.string().trim().regex(/^\\d+$/),
        confirm: z.literal(true),
      }).strict())
      .mutation(({ input, ctx }) => saveFelfelRecordingToDrive({
        ...input,
        actorUserId: Number(ctx.user.id),
      })),
''' + archive_router_anchor
routers = replace_once(routers, archive_router_anchor, recording_routes, "recording router procedures")
(root / ROUTERS).write_text(routers, encoding="utf-8")

# ---- FelfelPage.tsx ---------------------------------------------------------
archive_query_anchor = '''  const archivesQ = trpc.felfel.listArchives.useQuery(
'''
recording_queries = '''  const recordingStatusQ = trpc.felfel.recordingStatus.useQuery(
    { meetingId: String(meeting?.meetingId || "0") },
    { enabled: Boolean(meeting?.meetingId), refetchInterval: 5_000, refetchOnWindowFocus: false },
  );
  const recordingExportsQ = trpc.felfel.recordingExports.useQuery(
    { clientId: crmClientId || 1 },
    { enabled: Boolean(intelligence && crmClientId), refetchOnWindowFocus: false },
  );
  const saveRecordingM = trpc.felfel.saveRecordingToDrive.useMutation({
    onSuccess: (data) => {
      toast.success(ar
        ? `تم حفظ تسجيل فلفل على Google Drive (${data.savedCount} جديد${data.duplicateCount ? `، ${data.duplicateCount} موجود` : ""})`
        : `Felfel recording saved to Google Drive (${data.savedCount} new${data.duplicateCount ? `, ${data.duplicateCount} existing` : ""})`);
      void utils.felfel.recordingExports.invalidate({ clientId: crmClientId || 1 });
      void utils.felfel.recordingStatus.invalidate({ meetingId: String(meeting?.meetingId || "0") });
    },
    onError: (error) => toast.error(error.message),
  });

''' + archive_query_anchor
page = replace_once(page, archive_query_anchor, recording_queries, "recording UI queries")

followup_function_anchor = '''  const createCurrentFollowUp = () => {
'''
save_function = '''  const saveCurrentRecording = () => {
    if (!meeting || !crmClientId || !meeting.meetingId) return;
    saveRecordingM.mutate({
      clientId: crmClientId,
      dealId: crmDealId,
      platform: meeting.platform as "google_meet" | "teams" | "zoom" | "jitsi",
      nativeId: meeting.nativeId,
      meetingId: String(meeting.meetingId),
      confirm: true,
    });
  };

''' + followup_function_anchor
page = replace_once(page, followup_function_anchor, save_function, "recording save UI function")

archive_card_anchor = '''                          <Card className="border-emerald-500/30 bg-emerald-500/5">
                            <CardHeader className="pb-3">
                              <CardTitle className="text-base">{ar ? "أرشيف الاجتماع وGoogle Drive" : "Meeting Archive & Google Drive"}</CardTitle>
'''
recording_card = '''                          <Card className="border-sky-500/30 bg-sky-500/5">
                            <CardHeader className="pb-3">
                              <CardTitle className="text-base">{ar ? "تسجيل الفيديو والصوت" : "Video + Audio Recording"}</CardTitle>
                              <CardDescription>{ar ? "فلفل يبدأ تسجيل الفيديو والصوت تلقائيًا عند دخول الاجتماع. بعد انتهاء التسجيل احفظ ملف الفيديو وملف الصوت داخل CRM وGoogle Drive الحالي." : "Felfel starts video and audio recording automatically when it joins. After finalization, save both files through the existing CRM + Google Drive storage."}</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                              <div className="grid gap-3 sm:grid-cols-2">
                                <div className="rounded-xl border bg-background/70 p-3"><p className="text-xs text-muted-foreground">{ar ? "الفيديو" : "Video"}</p><p className="mt-1 text-sm font-bold">{recordingStatusQ.data?.videoReady ? (ar ? "جاهز للحفظ" : "Ready") : (ar ? "جار التسجيل / التجهيز" : "Recording / finalizing")}</p></div>
                                <div className="rounded-xl border bg-background/70 p-3"><p className="text-xs text-muted-foreground">{ar ? "الصوت" : "Audio"}</p><p className="mt-1 text-sm font-bold">{recordingStatusQ.data?.audioReady ? (ar ? "جاهز للحفظ" : "Ready") : (ar ? "جار التسجيل / التجهيز" : "Recording / finalizing")}</p></div>
                              </div>
                              <div className="flex flex-wrap items-center gap-3">
                                <Button variant="outline" className="gap-2" onClick={saveCurrentRecording} disabled={!crmClientId || !meeting?.meetingId || !recordingStatusQ.data?.videoReady || !recordingStatusQ.data?.audioReady || saveRecordingM.isPending}>
                                  {saveRecordingM.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <ExternalLink className="h-4 w-4" />}
                                  {ar ? "حفظ الفيديو + الصوت على Google Drive" : "Save video + audio to Google Drive"}
                                </Button>
                                <span className="text-xs text-muted-foreground">{ar ? "يتطلب اختيار العميل. يستخدم Google Drive المرتبط بـ TCRM ولا ينشئ تكامل Drive جديد." : "Requires a selected client and reuses TCRM's connected Google Drive."}</span>
                              </div>
                              <p className="text-xs text-amber-600 dark:text-amber-400">{ar ? "حماية الخصوصية: تسجيل الفيديو يسمح باجتماع فلفل نشط واحد في نفس الوقت لأن Vexa Lite يستخدم شاشة افتراضية مشتركة." : "Privacy guard: video mode permits one active Felfel meeting at a time because Vexa Lite uses a shared virtual display."}</p>
                              {crmClientId && <div className="space-y-2"><p className="text-sm font-bold">{ar ? "تسجيلات العميل المحفوظة" : "Saved client recordings"}</p>{recordingExportsQ.isLoading ? <p className="text-sm text-muted-foreground">{ar ? "جار التحميل..." : "Loading..."}</p> : recordingExportsQ.error ? <p className="text-sm text-destructive">{recordingExportsQ.error.message}</p> : !(recordingExportsQ.data || []).length ? <p className="text-sm text-muted-foreground">{ar ? "لا توجد تسجيلات محفوظة لهذا العميل حتى الآن." : "No saved Felfel recordings for this client yet."}</p> : <div className="space-y-2">{(recordingExportsQ.data || []).slice(0, 8).map((file: any) => <div key={file.id} className="flex flex-col gap-2 rounded-xl border bg-background/70 p-3 sm:flex-row sm:items-center sm:justify-between"><div className="min-w-0"><p className="truncate text-sm font-medium" dir="ltr">{file.fileName}</p><p className="text-xs text-muted-foreground">{file.fileCategory} • {file.driveUploadStatus}</p></div>{file.protectedUrl && <Button asChild size="sm" variant="ghost"><a href={file.protectedUrl} target="_blank" rel="noreferrer">{ar ? "فتح" : "Open"}</a></Button>}</div>)}</div>}</div>}
                            </CardContent>
                          </Card>

''' + archive_card_anchor
page = replace_once(page, archive_card_anchor, recording_card, "recording UI card")
(root / PAGE).write_text(page, encoding="utf-8")

# ---- Vexa bot composition root ---------------------------------------------
vexa_index = replace_once(
    vexa_index,
    "import { createBotRecordingSink } from './recording.js';\n",
    "import { createBotRecordingSink } from './recording.js';\nimport { VideoRecordingService } from '@vexa/recording';\n",
    "Vexa video recorder import",
)
audio_recording_anchor = '''  const recording = inv.recordingEnabled ? createBotRecordingSink({ inv, log: (m) => console.log(`[bot] ${m}`) }) : undefined;
'''
vexa_index = replace_once(
    vexa_index,
    audio_recording_anchor,
    audio_recording_anchor + '''  // TCRM/Felfel overlay: wire the existing Vexa x11grab video brick beside audio recording.v1.
  const videoRecording = inv.recordingEnabled && inv.meeting_id && inv.connectionId
    ? new VideoRecordingService(Number(inv.meeting_id), String(inv.connectionId))
    : null;
  let videoRecordingStarted = false;
''',
    "Vexa video recorder construction",
)
start_anchor = '''      startCapture: () => startCaptureBridge(sess.page, inv, bp, signalRecorder?.sink, publishChat, remoteAudioActivity),   // on the live meeting page
'''
start_replacement = '''      startCapture: async () => {
        if (videoRecording && !videoRecordingStarted) {
          videoRecording.start();
          videoRecordingStarted = true;
        }
        return startCaptureBridge(sess.page, inv, bp, signalRecorder?.sink, publishChat, remoteAudioActivity);
      },   // live meeting page; video begins only after admission
'''
vexa_index = replace_once(vexa_index, start_anchor, start_replacement, "Vexa video start hook")
teardown_anchor = '''    await pipeline.stop().catch(() => { /* best-effort */ });
    await signalRecorder?.close().catch(() => { /* best-effort */ });
'''
teardown_replacement = '''    await pipeline.stop().catch(() => { /* best-effort */ });
    if (videoRecording && videoRecordingStarted) {
      try {
        await videoRecording.stop();
        if (inv.recordingUploadUrl && inv.internalSecret) {
          await videoRecording.upload(inv.recordingUploadUrl, inv.internalSecret);
        } else {
          console.error("[bot] video recording finalized but upload configuration is missing");
        }
      } catch (e) {
        console.error(`[bot] video recording finalization/upload failed: ${String(e)}`);
      } finally {
        await videoRecording.cleanup().catch(() => { /* best-effort */ });
      }
    }
    await signalRecorder?.close().catch(() => { /* best-effort */ });
'''
vexa_index = replace_once(vexa_index, teardown_anchor, teardown_replacement, "Vexa video teardown")
vexa_index_path.write_text(vexa_index, encoding="utf-8")

# Copy compose override into the ignored Felfel deployment directory.
compose_override = root / "ai-staff/felfel/docker-compose.video-recording.yml"
shutil.copyfile(asset("docker-compose.video-recording.yml"), compose_override)

tracked = [ADAPTER, STORAGE, SERVICE, TEST, ROUTERS, PAGE, OVERLAY_README]
run("git", "diff", "--check", "--", *tracked)
status = run("git", "status", "--short")
for rel in tracked:
    if rel not in status:
        raise SystemExit(f"Expected TCRM path missing from final worktree: {rel}")

print(f"{PATCH_ID} applied")
print(f"BASELINE={BASELINE_SHA}")
print(f"VEXA_SOURCE_ROOT={vexa_root}")
print(f"VEXA_INDEX_MODIFIED={vexa_index_path}")
print(f"COMPOSE_OVERRIDE={compose_override}")
print("RECORDING_ENABLED_FOR_FELFEL=YES")
print("AUDIO_RECORDING=EXISTING_VEXA_RECORDING_V1")
print("VIDEO_RECORDING=VEXA_VIDEO_RECORDING_SERVICE_X11GRAB")
print("VIDEO_UPLOAD_MEDIA_TYPE=video")
print("DRIVE_UPLOAD=EXISTING_TCRM_STREAMED_GOOGLE_DRIVE_STORAGE")
print("CRM_FILES_REGISTRATION=YES")
print("CLIENT_LINK_REQUIRED_FOR_DRIVE_SAVE=YES")
print("ONE_ACTIVE_MEETING_PRIVACY_GUARD=YES")
print("DB_SCHEMA_CHANGED=NO")
print("DB_MIGRATION_RUN=NO")
print("NEW_GOOGLE_OAUTH_INTEGRATION=NO")
print("CUSTOM_VEXA_IMAGE=tcrm-vexa-lite:video-audio-drive-v1")
print("NO_BUILD_OR_RESTART_OR_REAL_RECORDING_OR_DRIVE_UPLOAD_OR_GIT_PUSH_PERFORMED_BY_PATCH=YES")
