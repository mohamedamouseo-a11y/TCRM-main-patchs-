#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import os, shutil

ROOT = Path(os.environ.get("TCRM_ROOT", "/var/www/TCRM-MAIN"))
GDFS = ROOT / "server/services/googleDriveFileStorage.ts"
POOL = ROOT / "server/services/googleDriveStoragePool.ts"
TDM = ROOT / "server/services/darwish/tdm/tdmDriveArchiveStorage.ts"
WA = ROOT / "server/services/waGatewayIntegrationService.ts"
RUNNER = ROOT / "scripts/run-tdm-media-archive-v1.ts"
VERIFY = ROOT / "scripts/verify-tdm-media-archive-v1.ts"

for p in (GDFS, POOL, TDM, WA):
    if not p.exists():
        raise SystemExit(f"ERROR=MISSING:{p}")

backup = ROOT / ".patch-backups" / f"tdm-media-archive-v1-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup.mkdir(parents=True, exist_ok=True)
for p in (GDFS, POOL, TDM, WA, RUNNER, VERIFY):
    if p.exists():
        shutil.copy2(p, backup / p.name)

# 1) Pool-aware streaming upload primitive.
g = GDFS.read_text(encoding="utf-8")
marker = "export async function uploadStoredStreamToGoogleDriveUnsafe("
if marker not in g:
    anchor = "export async function uploadStoredStreamToGoogleDrive(args: {"
    if anchor not in g:
        raise SystemExit("ERROR=GDFS_STREAM_ANCHOR_MISSING")
    insert = r'''
export async function uploadStoredStreamToGoogleDriveUnsafe(
  settings: GoogleDriveFileStorageSettings,
  args: {
    storageKey: string;
    fileName: string;
    stream: Readable;
    contentType?: string | null;
    appProperties?: Record<string, string>;
    signal?: AbortSignal;
    uploadTimeoutMs?: number;
  },
): Promise<StoredDriveUploadResult> {
  const controller = new AbortController();
  const timeoutMs = Math.max(
    getDriveStreamUploadTimeoutMs(),
    Number(args.uploadTimeoutMs || 0),
  );
  const onExternalAbort = () =>
    controller.abort(args.signal?.reason || new Error("Google Drive upload was cancelled"));
  if (args.signal?.aborted) onExternalAbort();
  else args.signal?.addEventListener("abort", onExternalAbort, { once: true });
  const timeout = setTimeout(
    () => controller.abort(new Error(`Google Drive streamed upload timed out after ${timeoutMs}ms`)),
    timeoutMs,
  );
  timeout.unref?.();

  try {
    const drive = await getDriveClient(settings);
    const folderId = await getTargetFolderId(drive, settings, args.storageKey);
    const created = await drive.files.create({
      requestBody: {
        name: cleanFolderSegment(args.fileName),
        parents: folderId ? [folderId] : undefined,
        ...(args.appProperties ? { appProperties: args.appProperties } : {}),
      },
      media: {
        mimeType: args.contentType || "application/octet-stream",
        body: args.stream,
      },
      fields: "id,name",
      supportsAllDrives: true,
    }, { timeout: timeoutMs, signal: controller.signal });
    const driveFileId = String(created.data.id || "").trim();
    if (!driveFileId) throw new Error("Google Drive streamed upload completed without a file id");
    return { driveFileId, driveUrl: null, uploadStatus: "uploaded" };
  } finally {
    clearTimeout(timeout);
    args.signal?.removeEventListener("abort", onExternalAbort);
  }
}

'''
    g = g.replace(anchor, insert + anchor, 1)
    GDFS.write_text(g, encoding="utf-8")

# 2) Google Drive pool streaming upload with streamFactory so retries get a fresh stream.
p = POOL.read_text(encoding="utf-8")
if 'import { Readable } from "node:stream";' not in p:
    p = 'import { Readable } from "node:stream";\n' + p
if "uploadStoredStreamToGoogleDriveUnsafe," not in p:
    needle = "  uploadStoredFileToGoogleDriveUnsafe,\n"
    if needle not in p:
        raise SystemExit("ERROR=POOL_IMPORT_ANCHOR_MISSING")
    p = p.replace(needle, needle + "  uploadStoredStreamToGoogleDriveUnsafe,\n", 1)

marker = "export async function uploadStoredStreamViaGoogleDrivePool("
if marker not in p:
    anchor = "export async function getPoolAccountSettings("
    if anchor not in p:
        raise SystemExit("ERROR=POOL_STREAM_ANCHOR_MISSING")
    insert = r'''
export async function uploadStoredStreamViaGoogleDrivePool(args: {
  storageKey: string;
  fileName: string;
  requiredBytes: number;
  streamFactory: () => Readable;
  contentType?: string | null;
  appProperties?: Record<string, string>;
  uploadTimeoutMs?: number;
}): Promise<StoredDriveUploadResult & { storageAccountId: number | null }> {
  const requiredBytes = Math.max(0, Number(args.requiredBytes || 0));
  const candidates = await getGoogleDriveStoragePoolCandidates(requiredBytes);
  if (!candidates.length) {
    return {
      driveFileId: null,
      driveUrl: null,
      uploadStatus: "failed",
      storageAccountId: null,
      error: "No writable Google Drive storage account is available",
    };
  }

  let lastError = "Google Drive streamed upload failed";
  for (const candidate of candidates) {
    const stream = args.streamFactory();
    try {
      const result = await uploadStoredStreamToGoogleDriveUnsafe(candidate.settings, {
        storageKey: args.storageKey,
        fileName: args.fileName,
        stream,
        contentType: args.contentType,
        appProperties: args.appProperties,
        uploadTimeoutMs: args.uploadTimeoutMs,
      });
      return { ...result, storageAccountId: candidate.id };
    } catch (error: any) {
      stream.destroy();
      lastError = String(error?.message || lastError);
      const status = Number(error?.response?.status || error?.code || 0);
      const reason = String(error?.response?.data?.error?.errors?.[0]?.reason || "");
      const quotaLimited =
        /storage\s*quota|storage.*full|insufficient.*storage/i.test(`${lastError} ${reason}`) ||
        ["storageQuotaExceeded", "quotaExceeded", "insufficientStorage"].includes(reason) ||
        status === 507;
      if (!quotaLimited) break;
    }
  }

  return {
    driveFileId: null,
    driveUrl: null,
    uploadStatus: "failed",
    storageAccountId: null,
    error: lastError,
  };
}

'''
    p = p.replace(anchor, insert + anchor, 1)
    POOL.write_text(p, encoding="utf-8")

# 3) TDM permanent media file uploader (streamed from a temp file, no memory-sized upload).
t = TDM.read_text(encoding="utf-8")
if 'import { createReadStream } from "node:fs";' not in t:
    t = t.replace('import crypto from "node:crypto";\n', 'import crypto from "node:crypto";\nimport { createReadStream } from "node:fs";\n', 1)
old_import = 'import { uploadStoredFileViaGoogleDrivePool } from "../../googleDriveStoragePool";'
new_import = 'import { uploadStoredFileViaGoogleDrivePool, uploadStoredStreamViaGoogleDrivePool } from "../../googleDriveStoragePool";'
if old_import in t:
    t = t.replace(old_import, new_import, 1)
elif "uploadStoredStreamViaGoogleDrivePool" not in t:
    raise SystemExit("ERROR=TDM_POOL_IMPORT_ANCHOR_MISSING")

marker = "export async function archiveTdmMediaFile("
if marker not in t:
    anchor = "export async function archiveTdmMediaBuffer("
    if anchor not in t:
        raise SystemExit("ERROR=TDM_MEDIA_FILE_ANCHOR_MISSING")
    insert = r'''
export async function archiveTdmMediaFile(
  input: ArchiveScope & {
    filePath: string;
    fileName: string;
    mimeType?: string | null;
    bytes: number;
    contentSha256: string;
  },
) {
  const bytes = Math.max(1, Number(input.bytes || 0));
  const digest = String(input.contentSha256 || "").trim().toLowerCase();
  if (!/^[a-f0-9]{64}$/.test(digest)) throw new Error("Invalid TDM media SHA-256");

  const result = await uploadStoredStreamViaGoogleDrivePool({
    storageKey: buildTdmDriveStorageKey(input, "media"),
    fileName: safeSegment(
      input.fileName,
      `media-${safeSegment(input.messageId, "message", 60)}`,
      140,
    ),
    requiredBytes: bytes,
    streamFactory: () => createReadStream(input.filePath),
    contentType: input.mimeType || "application/octet-stream",
    appProperties: buildTdmDriveAppProperties(input, "media", digest),
  });

  if (result.uploadStatus !== "uploaded" || !result.driveFileId) {
    throw new Error(result.error || "TDM streamed media archive upload failed");
  }

  return {
    driveFileId: result.driveFileId,
    storageAccountId: result.storageAccountId,
    sha256: digest,
    bytes,
  };
}

'''
    t = t.replace(anchor, insert + anchor, 1)
    TDM.write_text(t, encoding="utf-8")

# 4) Read-only Evolution fallback for media that is not already on operational Drive.
w = WA.read_text(encoding="utf-8")
marker = "export async function fetchWAGatewayHistoricalMediaBuffer("
if marker not in w:
    anchor = "function remoteInstances(body: any): any[] {"
    if anchor not in w:
        raise SystemExit("ERROR=WA_HISTORICAL_MEDIA_ANCHOR_MISSING")
    insert = r'''
export async function fetchWAGatewayHistoricalMediaBuffer(input: {
  sessionKey: string;
  rawMessage: unknown;
  maxBytes?: number;
}) {
  const sessionKey = String(input.sessionKey || "").trim();
  if (!sessionKey) throw new Error("Evolution instance name is required");
  if (!input.rawMessage || typeof input.rawMessage !== "object") {
    throw new Error("Evolution raw media message is required");
  }

  const maxBytes = Math.max(
    1024,
    Math.min(64 * 1024 * 1024, Math.floor(Number(input.maxBytes || 32 * 1024 * 1024))),
  );
  const result = await gatewayRequest(
    `/chat/getBase64FromMediaMessage/${encodeURIComponent(sessionKey)}`,
    {
      method: "POST",
      strict: true,
      timeoutMs: 90_000,
      maxBodyBytes: 4 * 1024 * 1024,
      maxResponseBytes: Math.ceil(maxBytes * 1.5) + 2 * 1024 * 1024,
      body: { message: input.rawMessage, convertToMp4: false },
    },
  );

  const encoded = extractEvolutionBase64(result.response);
  if (!encoded) throw new Error("Evolution media payload is unavailable");
  const decoded = decodeWAGatewayBase64Media(encoded, maxBytes);
  if (!decoded?.length) throw new Error("Evolution media payload could not be decoded");

  return {
    buffer: decoded,
    mimeType: String(
      result.response?.mimetype ||
      result.response?.mimeType ||
      result.response?.data?.mimetype ||
      result.response?.data?.mimeType ||
      "",
    ).trim() || null,
  };
}

'''
    w = w.replace(anchor, insert + anchor, 1)
    WA.write_text(w, encoding="utf-8")

# 5) Durable media archive worker.
RUNNER.write_text(r'''import "dotenv/config";
import crypto from "node:crypto";
import os from "node:os";
import path from "node:path";
import fs from "node:fs/promises";
import { createWriteStream } from "node:fs";
import { Transform } from "node:stream";
import { pipeline } from "node:stream/promises";
import mysql, { type RowDataPacket } from "mysql2/promise";
import {
  getStoredGoogleDriveFileMetadata,
  streamStoredFileFromGoogleDrive,
} from "../server/services/googleDriveFileStorage";
import {
  archiveTdmMediaFile,
  TDM_DRIVE_SOURCE,
  TDM_RETENTION_CLASS,
} from "../server/services/darwish/tdm/tdmDriveArchiveStorage";
import { fetchWAGatewayHistoricalMediaBuffer } from "../server/services/waGatewayIntegrationService";

const argv = process.argv.slice(2);
const apply = argv.includes("--apply");
const confirm = argv.includes("--confirm=APPLY_TDM_MEDIA_ARCHIVE_V1");
const arg = (name: string) => {
  const hit = argv.find(v => v.startsWith(`--${name}=`));
  return hit ? hit.slice(name.length + 3) : null;
};

const sessionArg = String(arg("session") || "").trim();
const limit = Math.max(1, Math.min(100, Number(arg("limit") || 10) || 10));
const maxAttempts = Math.max(1, Math.min(10, Number(arg("max-attempts") || 5) || 5));
const leaseSeconds = Math.max(60, Math.min(1800, Number(arg("lease-seconds") || 600) || 600));
const sleepMs = Math.max(0, Math.min(5000, Number(arg("sleep-ms") || 100) || 100));

if (!process.env.DATABASE_URL) throw new Error("DATABASE_URL is required");
if (!sessionArg) throw new Error("Use --session=<session id or session key>");
if (apply && !confirm) throw new Error("Use --confirm=APPLY_TDM_MEDIA_ARCHIVE_V1 with --apply");

type JobRow = RowDataPacket & {
  jobId: number;
  attemptCount: number;
  mediaId: number;
  memoryRecordId: number;
  sourceDriveFileId: string | null;
  sourceStorageAccountId: number | null;
  canonicalDriveFileId: string | null;
  canonicalStorageAccountId: number | null;
  archiveState: string;
  fileName: string | null;
  mimeType: string | null;
  fileSize: number | null;
  sourcePayload: unknown;
  sessionKey: string;
  conversationJid: string;
  sourceMessageId: string;
  occurredAt: Date | null;
};

function safeError(error: unknown) {
  return String(error instanceof Error ? error.message : error || "TDM media archive failed")
    .replace(/[\r\n\t]+/g, " ")
    .replace(/\s{2,}/g, " ")
    .slice(0, 900);
}

function parsePayload(value: unknown) {
  if (value && typeof value === "object") return value as any;
  if (typeof value === "string") {
    try { return JSON.parse(value); } catch { return null; }
  }
  return null;
}

function delay(ms: number) {
  return ms ? new Promise(resolve => setTimeout(resolve, ms)) : Promise.resolve();
}

async function resolveSession(db: mysql.Connection) {
  const numeric = Number(sessionArg);
  const useId = Number.isInteger(numeric) && numeric > 0;
  const [rows] = await db.query<RowDataPacket[]>(
    `SELECT id, session_key AS sessionKey
       FROM whatsapp_sessions
      WHERE ${useId ? "id=?" : "session_key=?"}
      LIMIT 1`,
    [useId ? numeric : sessionArg],
  );
  if (!rows[0]) throw new Error("WhatsApp session not found");
  return { id: Number(rows[0].id), sessionKey: String(rows[0].sessionKey) };
}

async function queueStats(db: mysql.Connection, sessionKey: string) {
  const [rows] = await db.query<RowDataPacket[]>(
    `SELECT
       SUM(j.state='queued') AS queued,
       SUM(j.state='retry') AS retryJobs,
       SUM(j.state='processing') AS processing,
       SUM(j.state='completed') AS completed,
       SUM(j.state='dead') AS deadJobs,
       SUM(mm.archive_state='archived') AS archivedMedia,
       SUM(mm.canonical_drive_file_id IS NOT NULL) AS canonicalMedia,
       SUM(mm.source_drive_file_id IS NOT NULL AND j.state IN ('queued','retry')) AS sourceDriveReady,
       SUM(mm.source_drive_file_id IS NULL AND j.state IN ('queued','retry')) AS evolutionFallback
     FROM tdm_archive_jobs j
     JOIN tdm_memory_media mm ON mm.id=j.media_id
     JOIN tdm_memory_records mr ON mr.id=j.memory_record_id
    WHERE j.job_type='media_archive'
      AND mr.source_session_key=?`,
    [sessionKey],
  );
  const r = rows[0] || {};
  return {
    queued: Number(r.queued || 0),
    retry: Number(r.retryJobs || 0),
    processing: Number(r.processing || 0),
    completed: Number(r.completed || 0),
    dead: Number(r.deadJobs || 0),
    archived: Number(r.archivedMedia || 0),
    canonical: Number(r.canonicalMedia || 0),
    sourceDriveReady: Number(r.sourceDriveReady || 0),
    evolutionFallback: Number(r.evolutionFallback || 0),
  };
}

async function recoverExpiredLeases(db: mysql.Connection, sessionKey: string) {
  await db.execute(
    `UPDATE tdm_archive_jobs j
      JOIN tdm_memory_records mr ON mr.id=j.memory_record_id
       SET j.state='retry',
           j.available_at=CURRENT_TIMESTAMP(3),
           j.lease_token=NULL,
           j.lease_expires_at=NULL,
           j.last_error=COALESCE(j.last_error,'Recovered expired TDM media lease')
     WHERE j.job_type='media_archive'
       AND mr.source_session_key=?
       AND j.state='processing'
       AND j.lease_expires_at IS NOT NULL
       AND j.lease_expires_at < CURRENT_TIMESTAMP(3)`,
    [sessionKey],
  );
}

async function claimOne(db: mysql.Connection, sessionKey: string): Promise<(JobRow & { leaseToken: string; attempt: number }) | null> {
  const leaseToken = crypto.randomBytes(24).toString("hex");
  await db.beginTransaction();
  try {
    const [rows] = await db.query<JobRow[]>(
      `SELECT
         j.id AS jobId,
         j.attempt_count AS attemptCount,
         mm.id AS mediaId,
         mr.id AS memoryRecordId,
         mm.source_drive_file_id AS sourceDriveFileId,
         mm.source_storage_account_id AS sourceStorageAccountId,
         mm.canonical_drive_file_id AS canonicalDriveFileId,
         mm.canonical_storage_account_id AS canonicalStorageAccountId,
         mm.archive_state AS archiveState,
         mm.file_name AS fileName,
         mm.mime_type AS mimeType,
         mm.file_size AS fileSize,
         mr.source_payload AS sourcePayload,
         mr.source_session_key AS sessionKey,
         mr.conversation_jid AS conversationJid,
         mr.source_message_id AS sourceMessageId,
         mr.occurred_at AS occurredAt
       FROM tdm_archive_jobs j
       JOIN tdm_memory_media mm ON mm.id=j.media_id
       JOIN tdm_memory_records mr ON mr.id=j.memory_record_id
      WHERE j.job_type='media_archive'
        AND mr.source_session_key=?
        AND j.state IN ('queued','retry')
        AND j.available_at <= CURRENT_TIMESTAMP(3)
      ORDER BY (mm.source_drive_file_id IS NULL) ASC, j.id ASC
      LIMIT 1
      FOR UPDATE SKIP LOCKED`,
      [sessionKey],
    );
    const row = rows[0];
    if (!row) {
      await db.commit();
      return null;
    }
    const attempt = Number(row.attemptCount || 0) + 1;
    await db.execute(
      `UPDATE tdm_archive_jobs
          SET state='processing',
              attempt_count=?,
              lease_token=?,
              lease_expires_at=DATE_ADD(CURRENT_TIMESTAMP(3), INTERVAL ? SECOND),
              last_error=NULL
        WHERE id=?`,
      [attempt, leaseToken, leaseSeconds, row.jobId],
    );
    await db.commit();
    return { ...row, leaseToken, attempt };
  } catch (error) {
    await db.rollback();
    throw error;
  }
}

async function renewLease(db: mysql.Connection, jobId: number, leaseToken: string) {
  await db.execute(
    `UPDATE tdm_archive_jobs
        SET lease_expires_at=DATE_ADD(CURRENT_TIMESTAMP(3), INTERVAL ? SECOND)
      WHERE id=? AND state='processing' AND lease_token=?`,
    [leaseSeconds, jobId, leaseToken],
  );
}

async function writeDriveSourceToTemp(job: JobRow, tempPath: string) {
  const fileId = String(job.sourceDriveFileId || "").trim();
  if (!fileId) throw new Error("Source Drive file is missing");
  const source = await streamStoredFileFromGoogleDrive(
    fileId,
    undefined,
    Number(job.sourceStorageAccountId || 0) || null,
  );
  const hash = crypto.createHash("sha256");
  let bytes = 0;
  const meter = new Transform({
    transform(chunk, _encoding, callback) {
      const data = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk);
      bytes += data.length;
      hash.update(data);
      callback(null, data);
    },
  });
  await pipeline(source.stream, meter, createWriteStream(tempPath, { flags: "wx" }));
  if (!bytes) throw new Error("Source Drive media is empty");
  if (Number(source.size || 0) > 0 && bytes !== Number(source.size)) {
    throw new Error("Source Drive media byte count mismatch");
  }
  return {
    bytes,
    sha256: hash.digest("hex"),
    mimeType: job.mimeType || source.mimeType || "application/octet-stream",
    fileName: job.fileName || source.name || `whatsapp-${job.sourceMessageId}`,
    source: "drive",
  };
}

async function writeEvolutionSourceToTemp(job: JobRow, tempPath: string) {
  const payload = parsePayload(job.sourcePayload);
  const rawMessage = payload?.evolution;
  if (!rawMessage) throw new Error("No Evolution raw payload is available for media recovery");

  const declared = Math.max(0, Number(job.fileSize || 0));
  const maxBytes = Math.min(
    64 * 1024 * 1024,
    Math.max(8 * 1024 * 1024, declared > 0 ? declared + 1024 * 1024 : 32 * 1024 * 1024),
  );
  const fetched = await fetchWAGatewayHistoricalMediaBuffer({
    sessionKey: job.sessionKey,
    rawMessage,
    maxBytes,
  });
  if (!fetched.buffer.length) throw new Error("Evolution media is empty");
  await fs.writeFile(tempPath, fetched.buffer, { flag: "wx" });
  return {
    bytes: fetched.buffer.length,
    sha256: crypto.createHash("sha256").update(fetched.buffer).digest("hex"),
    mimeType: job.mimeType || fetched.mimeType || "application/octet-stream",
    fileName: job.fileName || `whatsapp-${job.sourceMessageId}`,
    source: "evolution",
  };
}

async function markCompleted(
  db: mysql.Connection,
  job: JobRow & { leaseToken: string },
  archived: { driveFileId: string; storageAccountId: number | null; sha256: string; bytes: number },
) {
  const metadata = await getStoredGoogleDriveFileMetadata(
    archived.driveFileId,
    archived.storageAccountId,
  );
  if (
    metadata.appProperties?.source !== TDM_DRIVE_SOURCE ||
    metadata.appProperties?.retentionClass !== TDM_RETENTION_CLASS ||
    metadata.appProperties?.tdmResource !== "media"
  ) {
    throw new Error("Canonical TDM Drive ownership verification failed");
  }
  if (metadata.size !== archived.bytes) {
    throw new Error("Canonical TDM Drive size verification failed");
  }

  await db.beginTransaction();
  try {
    await db.execute(
      `UPDATE tdm_memory_media
          SET canonical_drive_file_id=?,
              canonical_storage_account_id=?,
              content_sha256=?,
              file_size=COALESCE(file_size, ?),
              archive_state='archived',
              archive_error=NULL,
              archived_at=CURRENT_TIMESTAMP(3)
        WHERE id=?`,
      [
        archived.driveFileId,
        archived.storageAccountId,
        archived.sha256,
        archived.bytes,
        job.mediaId,
      ],
    );
    await db.execute(
      `UPDATE tdm_archive_jobs
          SET state='completed',
              lease_token=NULL,
              lease_expires_at=NULL,
              last_error=NULL
        WHERE id=? AND lease_token=?`,
      [job.jobId, job.leaseToken],
    );
    await db.commit();
  } catch (error) {
    await db.rollback();
    throw error;
  }
}

async function markAlreadyArchived(db: mysql.Connection, job: JobRow & { leaseToken: string }) {
  await db.execute(
    `UPDATE tdm_archive_jobs
        SET state='completed', lease_token=NULL, lease_expires_at=NULL, last_error=NULL
      WHERE id=? AND lease_token=?`,
    [job.jobId, job.leaseToken],
  );
}

async function markFailure(
  db: mysql.Connection,
  job: JobRow & { leaseToken: string; attempt: number },
  error: unknown,
) {
  const message = safeError(error);
  const dead = job.attempt >= maxAttempts;
  const delaySeconds = Math.min(6 * 60 * 60, 30 * 2 ** Math.min(Math.max(job.attempt - 1, 0), 9));
  await db.beginTransaction();
  try {
    await db.execute(
      `UPDATE tdm_memory_media
          SET archive_state=?,
              archive_error=?
        WHERE id=? AND archive_state <> 'archived'`,
      [dead ? "failed" : "pending", message.slice(0, 500), job.mediaId],
    );
    await db.execute(
      `UPDATE tdm_archive_jobs
          SET state=?,
              available_at=DATE_ADD(CURRENT_TIMESTAMP(3), INTERVAL ? SECOND),
              lease_token=NULL,
              lease_expires_at=NULL,
              last_error=?
        WHERE id=? AND lease_token=?`,
      [dead ? "dead" : "retry", delaySeconds, message, job.jobId, job.leaseToken],
    );
    await db.commit();
  } catch (dbError) {
    await db.rollback();
    throw dbError;
  }
}

async function main() {
  const db = await mysql.createConnection(process.env.DATABASE_URL!);
  let lockHeld = false;
  let lockName = "";

  try {
    const session = await resolveSession(db);
    lockName = `tdm:media:${session.sessionKey}`.slice(0, 64);

    const before = await queueStats(db, session.sessionKey);
    console.log(`TDM_MEDIA_MODE=${apply ? "APPLY" : "DRY_RUN"}`);
    console.log(`SESSION_ID=${session.id}`);
    console.log(`SESSION_KEY=${session.sessionKey}`);
    console.log(`LIMIT=${limit}`);
    console.log(`QUEUED_BEFORE=${before.queued}`);
    console.log(`RETRY_BEFORE=${before.retry}`);
    console.log(`SOURCE_DRIVE_READY=${before.sourceDriveReady}`);
    console.log(`EVOLUTION_FALLBACK=${before.evolutionFallback}`);

    if (!apply) {
      console.log("DB_WRITES=0");
      console.log("DRIVE_WRITES=0");
      console.log("SAFE_TO_APPLY=YES");
      console.log("ERROR=NONE");
      return;
    }

    const [lockRows] = await db.query<RowDataPacket[]>("SELECT GET_LOCK(?,0) AS got", [lockName]);
    lockHeld = Number(lockRows[0]?.got || 0) === 1;
    if (!lockHeld) throw new Error("Another TDM media archive worker already holds this session lock");

    await recoverExpiredLeases(db, session.sessionKey);

    let claimed = 0;
    let archived = 0;
    let alreadyArchived = 0;
    let driveSources = 0;
    let evolutionSources = 0;
    let retried = 0;
    let dead = 0;

    while (claimed < limit) {
      const job = await claimOne(db, session.sessionKey);
      if (!job) break;
      claimed += 1;

      if (job.archiveState === "archived" && job.canonicalDriveFileId) {
        await markAlreadyArchived(db, job);
        alreadyArchived += 1;
        continue;
      }

      const tempPath = path.join(
        os.tmpdir(),
        `tdm-media-${job.mediaId}-${crypto.randomBytes(8).toString("hex")}.bin`,
      );

      try {
        await renewLease(db, job.jobId, job.leaseToken);
        const source = job.sourceDriveFileId
          ? await writeDriveSourceToTemp(job, tempPath)
          : await writeEvolutionSourceToTemp(job, tempPath);

        if (source.source === "drive") driveSources += 1;
        else evolutionSources += 1;

        await renewLease(db, job.jobId, job.leaseToken);
        const result = await archiveTdmMediaFile({
          sessionKey: job.sessionKey,
          conversationJid: job.conversationJid,
          messageId: job.sourceMessageId,
          occurredAt: job.occurredAt,
          memoryRecordId: job.memoryRecordId,
          filePath: tempPath,
          fileName: source.fileName,
          mimeType: source.mimeType,
          bytes: source.bytes,
          contentSha256: source.sha256,
        });
        await renewLease(db, job.jobId, job.leaseToken);
        await markCompleted(db, job, result);
        archived += 1;
        console.log(`JOB_DONE=${job.jobId} MEDIA_ID=${job.mediaId} SOURCE=${source.source} BYTES=${source.bytes}`);
      } catch (error) {
        await markFailure(db, job, error);
        if (job.attempt >= maxAttempts) dead += 1;
        else retried += 1;
        console.log(`JOB_FAILED=${job.jobId} ATTEMPT=${job.attempt} ERROR=${safeError(error)}`);
      } finally {
        await fs.unlink(tempPath).catch(() => undefined);
      }

      if (claimed < limit) await delay(sleepMs);
    }

    const after = await queueStats(db, session.sessionKey);
    console.log(`JOBS_CLAIMED=${claimed}`);
    console.log(`MEDIA_ARCHIVED=${archived}`);
    console.log(`ALREADY_ARCHIVED=${alreadyArchived}`);
    console.log(`DRIVE_SOURCES=${driveSources}`);
    console.log(`EVOLUTION_SOURCES=${evolutionSources}`);
    console.log(`RETRIED=${retried}`);
    console.log(`DEAD=${dead}`);
    console.log(`QUEUED_AFTER=${after.queued}`);
    console.log(`RETRY_AFTER=${after.retry}`);
    console.log(`COMPLETED_TOTAL=${after.completed}`);
    console.log(`ARCHIVED_MEDIA_TOTAL=${after.archived}`);
    console.log("SOURCE_WRITES=0");
    console.log("ERROR=NONE");
  } finally {
    if (lockHeld && lockName) {
      await db.query("SELECT RELEASE_LOCK(?)", [lockName]).catch(() => undefined);
    }
    await db.end();
  }
}

main().catch(error => {
  console.error("TDM_MEDIA_ARCHIVE_ERROR=" + safeError(error));
  process.exitCode = 1;
});
''', encoding="utf-8")

# 6) Verifier.
VERIFY.write_text(r'''import "dotenv/config";
import fs from "node:fs";
import path from "node:path";
import mysql from "mysql2/promise";

const argv = process.argv.slice(2);
const arg = (name: string) => {
  const hit = argv.find(v => v.startsWith(`--${name}=`));
  return hit ? hit.slice(name.length + 3) : null;
};
const session = String(arg("session") || "").trim();

if (!process.env.DATABASE_URL) throw new Error("DATABASE_URL is required");
if (!session) throw new Error("Use --session=<session key>");

const root = process.cwd();
const gdfs = fs.readFileSync(path.join(root, "server/services/googleDriveFileStorage.ts"), "utf8");
const pool = fs.readFileSync(path.join(root, "server/services/googleDriveStoragePool.ts"), "utf8");
const tdm = fs.readFileSync(path.join(root, "server/services/darwish/tdm/tdmDriveArchiveStorage.ts"), "utf8");
const wa = fs.readFileSync(path.join(root, "server/services/waGatewayIntegrationService.ts"), "utf8");
const runner = fs.readFileSync(path.join(root, "scripts/run-tdm-media-archive-v1.ts"), "utf8");
const core = fs.readFileSync(path.join(root, "server/_core/index.ts"), "utf8");
const workerPath = path.join(root, "server/services/darwish/chatwoot/darwishWorker.ts");
const darwishWorker = fs.existsSync(workerPath) ? fs.readFileSync(workerPath, "utf8") : "";

const sourceWritePattern = /\b(?:INSERT\s+INTO|UPDATE|DELETE\s+FROM)\s+whatsapp_/i;
const runtimeHooked =
  core.includes("run-tdm-media-archive-v1") ||
  core.includes("tdmMediaArchiveWorker") ||
  darwishWorker.includes("run-tdm-media-archive-v1") ||
  darwishWorker.includes("tdmMediaArchiveWorker");

const db = await mysql.createConnection(process.env.DATABASE_URL);
try {
  const [rows] = await db.query<any[]>(
    `SELECT
       SUM(j.state='queued') AS queued,
       SUM(j.state='retry') AS retryJobs,
       SUM(j.state='processing') AS processing,
       SUM(j.state='completed') AS completed,
       SUM(j.state='dead') AS deadJobs,
       SUM(mm.archive_state='archived') AS archivedMedia,
       SUM(mm.archive_state='failed') AS failedMedia,
       SUM(mm.canonical_drive_file_id IS NOT NULL) AS canonicalMedia,
       SUM(mm.source_drive_file_id IS NOT NULL AND j.state IN ('queued','retry')) AS sourceDriveReady,
       SUM(mm.source_drive_file_id IS NULL AND j.state IN ('queued','retry')) AS evolutionFallback
     FROM tdm_archive_jobs j
     JOIN tdm_memory_media mm ON mm.id=j.media_id
     JOIN tdm_memory_records mr ON mr.id=j.memory_record_id
    WHERE j.job_type='media_archive'
      AND mr.source_session_key=?`,
    [session],
  );
  const r = rows[0] || {};

  const [badRows] = await db.query<any[]>(
    `SELECT COUNT(*) AS c
       FROM tdm_memory_media mm
       JOIN tdm_memory_records mr ON mr.id=mm.memory_record_id
      WHERE mr.source_session_key=?
        AND mm.archive_state='archived'
        AND (
          mm.canonical_drive_file_id IS NULL OR
          mm.content_sha256 IS NULL OR
          mm.archived_at IS NULL
        )`,
    [session],
  );
  const invalidArchived = Number(badRows[0]?.c || 0);

  const checks = {
    STREAM_UNSAFE: gdfs.includes("uploadStoredStreamToGoogleDriveUnsafe"),
    POOL_STREAM: pool.includes("uploadStoredStreamViaGoogleDrivePool"),
    TDM_MEDIA_FILE: tdm.includes("archiveTdmMediaFile"),
    EVOLUTION_FALLBACK: wa.includes("fetchWAGatewayHistoricalMediaBuffer"),
    LEASES: runner.includes("lease_token") && runner.includes("lease_expires_at"),
    SESSION_LOCK: runner.includes("GET_LOCK"),
    SOURCE_WRITES: sourceWritePattern.test(runner),
    RUNTIME_HOOKED: runtimeHooked,
    INVALID_ARCHIVED: invalidArchived,
  };
  const ok =
    checks.STREAM_UNSAFE &&
    checks.POOL_STREAM &&
    checks.TDM_MEDIA_FILE &&
    checks.EVOLUTION_FALLBACK &&
    checks.LEASES &&
    checks.SESSION_LOCK &&
    !checks.SOURCE_WRITES &&
    !checks.RUNTIME_HOOKED &&
    invalidArchived === 0;

  console.log(`TDM_MEDIA_VERIFY=${ok ? "PASS" : "FAIL"}`);
  console.log(`POOL_STREAM=${checks.POOL_STREAM ? "YES" : "NO"}`);
  console.log(`PERMANENT_MEDIA_ARCHIVE=${checks.TDM_MEDIA_FILE ? "YES" : "NO"}`);
  console.log(`EVOLUTION_FALLBACK=${checks.EVOLUTION_FALLBACK ? "YES" : "NO"}`);
  console.log(`LEASES=${checks.LEASES ? "YES" : "NO"}`);
  console.log(`SESSION_LOCK=${checks.SESSION_LOCK ? "YES" : "NO"}`);
  console.log(`SOURCE_WRITE_CODE=${checks.SOURCE_WRITES ? "YES" : "NO"}`);
  console.log(`RUNTIME_HOOKED=${checks.RUNTIME_HOOKED ? "YES" : "NO"}`);
  console.log(`QUEUED=${Number(r.queued || 0)}`);
  console.log(`RETRY=${Number(r.retryJobs || 0)}`);
  console.log(`PROCESSING=${Number(r.processing || 0)}`);
  console.log(`COMPLETED=${Number(r.completed || 0)}`);
  console.log(`DEAD=${Number(r.deadJobs || 0)}`);
  console.log(`ARCHIVED_MEDIA=${Number(r.archivedMedia || 0)}`);
  console.log(`FAILED_MEDIA=${Number(r.failedMedia || 0)}`);
  console.log(`CANONICAL_MEDIA=${Number(r.canonicalMedia || 0)}`);
  console.log(`SOURCE_DRIVE_READY=${Number(r.sourceDriveReady || 0)}`);
  console.log(`EVOLUTION_FALLBACK_PENDING=${Number(r.evolutionFallback || 0)}`);
  console.log(`INVALID_ARCHIVED=${invalidArchived}`);
  console.log(`ERROR=${ok ? "NONE" : "VERIFY_FAILED"}`);
  if (!ok) process.exitCode = 2;
} finally {
  await db.end();
}
''', encoding="utf-8")

print("PATCH=PASS")
print("TDM_COMPONENT=MEDIA_ARCHIVE_WORKER_V1")
print("POOL_STREAMING=YES")
print("SOURCE_DRIVE_COPY=YES")
print("EVOLUTION_FALLBACK=YES")
print("LEASES=YES")
print("SESSION_LOCK=YES")
print("PERMANENT_TDM_OWNERSHIP=YES")
print("SOURCE_WRITES=0")
print("RUNTIME_HOOK=NO")
print("FILES_CHANGED=6")
print(f"BACKUP={backup}")
print("ERROR=NONE")
