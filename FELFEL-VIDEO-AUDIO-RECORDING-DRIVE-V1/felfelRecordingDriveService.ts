import { and, eq, isNull } from "drizzle-orm";
import { clients, deals } from "../../../drizzle/schema";
import { getDb } from "../../db";
import {
  buildProtectedCrmFileUrl,
  listCrmFiles,
  storeCrmFileStreamDriveOnly,
} from "../crmFileStorage";
import {
  listFelfelRecordings,
  openFelfelRecordingStream,
  type FelfelRecording,
  type FelfelRecordingMedia,
  type FelfelPlatform,
} from "./felfelAdapter";

const RECORDING_CATEGORY = "felfel_meeting_recording";
const VIDEO_FILE_CATEGORY = "meeting_recording_video";
const AUDIO_FILE_CATEGORY = "meeting_recording_audio";
const EXPORT_LIMIT = 100;

function cleanSegment(value: unknown, max = 120) {
  return String(value ?? "")
    .replace(/[^A-Za-z0-9._-]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, max) || "meeting";
}

function normalizeMediaType(value: string): "audio" | "video" | null {
  const lower = String(value || "").toLowerCase();
  return lower === "audio" || lower === "video" ? lower : null;
}

function extensionForMedia(media: FelfelRecordingMedia) {
  const format = cleanSegment(media.format || "", 12).toLowerCase();
  if (format && format !== "meeting") return format;
  return normalizeMediaType(media.type) === "video" ? "webm" : "wav";
}

export function buildFelfelRecordingEntityKey(input: {
  platform: string;
  nativeId: string;
  mediaType: "audio" | "video";
}) {
  return `felfel-recording:${cleanSegment(input.platform, 40)}:${cleanSegment(input.nativeId, 120)}:${input.mediaType}`;
}

export function selectFelfelRecordingForMeeting(
  recordings: FelfelRecording[],
  meetingId: string | number,
): FelfelRecording | null {
  const wanted = String(meetingId);
  const candidates = recordings.filter((recording) => String(recording.meetingId) === wanted);
  if (!candidates.length) return null;
  return candidates.slice().sort((a, b) => Number(b.id) - Number(a.id))[0] || null;
}

export function summarizeFelfelRecording(recording: FelfelRecording | null) {
  const media = recording?.mediaFiles || [];
  const audio = media.find((item) => normalizeMediaType(item.type) === "audio") || null;
  const video = media.find((item) => normalizeMediaType(item.type) === "video") || null;
  return {
    recordingId: recording?.id || null,
    meetingId: recording?.meetingId || null,
    status: recording?.status || "not_found",
    audioReady: Boolean(audio?.id),
    videoReady: Boolean(video?.id),
    audio,
    video,
  };
}

async function requireCrmContext(clientId: number, dealId?: number | null) {
  const db = await getDb();
  if (!db) throw new Error("Database is not available");

  const clientRows = await db.select({
    id: clients.id,
    leadId: clients.leadId,
    dealId: clients.dealId,
  }).from(clients)
    .where(and(eq(clients.id, clientId), isNull(clients.deletedAt)))
    .limit(1);
  const client = clientRows[0];
  if (!client) throw new Error("Selected CRM client was not found or is inactive");

  if (dealId) {
    const dealRows = await db.select({ id: deals.id, leadId: deals.leadId })
      .from(deals)
      .where(and(eq(deals.id, dealId), isNull(deals.deletedAt)))
      .limit(1);
    const deal = dealRows[0];
    if (!deal) throw new Error("Selected CRM deal was not found or is inactive");
    const directMatch = Number(client.dealId || 0) === Number(deal.id);
    const leadMatch = Number(client.leadId || 0) > 0 && Number(client.leadId) === Number(deal.leadId || 0);
    if (!directMatch && !leadMatch) {
      throw new Error("Selected deal does not belong to the selected client");
    }
  }
}

export async function getFelfelRecordingStatus(meetingId: string | number) {
  const safeMeetingId = String(meetingId).trim();
  if (!/^\d+$/.test(safeMeetingId)) throw new Error("A valid Felfel meeting id is required");
  const recording = selectFelfelRecordingForMeeting(await listFelfelRecordings(), safeMeetingId);
  return summarizeFelfelRecording(recording);
}

export async function listFelfelRecordingExports(clientId: number) {
  await requireCrmContext(clientId);
  const rows = await listCrmFiles({
    entityType: "client",
    entityId: clientId,
    includeDeleted: false,
    limit: EXPORT_LIMIT,
  });
  return rows
    .filter((row: any) => String(row.category || "") === RECORDING_CATEGORY)
    .map((row: any) => ({
      id: Number(row.id),
      entityKey: row.entityKey || null,
      fileName: row.fileName,
      fileCategory: row.fileCategory || null,
      fileSize: row.fileSize == null ? null : Number(row.fileSize),
      fileType: row.fileType || null,
      protectedUrl: buildProtectedCrmFileUrl(Number(row.id)),
      driveFileId: row.driveFileId || null,
      driveUrl: row.driveUrl || null,
      driveUploadStatus: row.driveUploadStatus || null,
      createdAt: row.createdAt,
    }));
}

export async function saveFelfelRecordingToDrive(input: {
  clientId: number;
  dealId?: number | null;
  platform: FelfelPlatform;
  nativeId: string;
  meetingId: string;
  actorUserId: number;
  confirm: boolean;
}) {
  if (input.confirm !== true) throw new Error("Explicit confirmation is required");
  if (!Number.isInteger(input.clientId) || input.clientId <= 0) throw new Error("A valid CRM client is required");
  if (!Number.isInteger(input.actorUserId) || input.actorUserId <= 0) throw new Error("A valid acting user is required");
  if (!/^\d+$/.test(String(input.meetingId).trim())) throw new Error("A valid Felfel meeting id is required");
  await requireCrmContext(input.clientId, input.dealId);

  const recording = selectFelfelRecordingForMeeting(await listFelfelRecordings(), input.meetingId);
  const status = summarizeFelfelRecording(recording);
  if (!recording || !status.audioReady || !status.videoReady) {
    throw new Error("Felfel recording is not ready yet; both video and audio are required before Drive export");
  }

  const results: any[] = [];
  for (const mediaType of ["video", "audio"] as const) {
    const media = recording.mediaFiles.find((item) => normalizeMediaType(item.type) === mediaType);
    if (!media) throw new Error(`Felfel ${mediaType} recording media is missing`);

    const entityKey = buildFelfelRecordingEntityKey({
      platform: input.platform,
      nativeId: input.nativeId,
      mediaType,
    });
    const existing = await listCrmFiles({
      entityType: "client",
      entityId: input.clientId,
      entityKey,
      includeDeleted: false,
      limit: 2,
    });
    if (existing[0]) {
      results.push({
        mediaType,
        duplicate: true,
        file: {
          id: Number((existing[0] as any).id),
          fileName: (existing[0] as any).fileName,
          protectedUrl: buildProtectedCrmFileUrl(Number((existing[0] as any).id)),
          driveFileId: (existing[0] as any).driveFileId || null,
          driveUploadStatus: (existing[0] as any).driveUploadStatus || null,
        },
      });
      continue;
    }

    const opened = await openFelfelRecordingStream(recording.id, mediaType);
    const ext = extensionForMedia(media);
    const safePlatform = cleanSegment(input.platform, 40);
    const safeNativeId = cleanSegment(input.nativeId, 120);
    const fileName = `Felfel_${safePlatform}_${safeNativeId}_${mediaType}.${ext}`;
    const storageKey = `felfel/recordings/client-${input.clientId}/${safePlatform}-${safeNativeId}/${fileName}`;
    const stored = await storeCrmFileStreamDriveOnly({
      entityType: "client",
      entityId: input.clientId,
      entityKey,
      category: RECORDING_CATEGORY,
      fileCategory: mediaType === "video" ? VIDEO_FILE_CATEGORY : AUDIO_FILE_CATEGORY,
      description: [
        `Felfel ${mediaType} recording`,
        `platform=${input.platform}`,
        `nativeId=${input.nativeId}`,
        `meetingId=${input.meetingId}`,
        `recordingId=${recording.id}`,
        `dealId=${input.dealId || "none"}`,
      ].join(" | "),
      storageKey,
      fileName,
      stream: opened.stream,
      fileSize: opened.contentLength ?? media.fileSize,
      contentType: opened.contentType,
      uploadedBy: input.actorUserId,
      projectReferenceClientId: input.clientId,
      appProperties: {
        source: "felfel",
        meetingId: String(input.meetingId),
        recordingId: String(recording.id),
        mediaType,
        platform: String(input.platform),
      },
    });

    results.push({ mediaType, duplicate: false, file: stored });
  }

  return {
    recordingId: recording.id,
    meetingId: recording.meetingId,
    savedCount: results.filter((item) => !item.duplicate).length,
    duplicateCount: results.filter((item) => item.duplicate).length,
    files: results,
  };
}
