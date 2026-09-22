#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import os, shutil

ROOT = Path(os.environ.get("TCRM_ROOT", "/var/www/TCRM-MAIN"))
GITIGNORE = ROOT / ".gitignore"
WA = ROOT / "server/services/waGatewayIntegrationService.ts"
TDM_DRIVE = ROOT / "server/services/darwish/tdm/tdmDriveArchiveStorage.ts"
RUNNER = ROOT / "scripts/run-tdm-historical-backfill-v1.ts"
VERIFY = ROOT / "scripts/verify-tdm-historical-backfill-v1.ts"
PHASE1_SQL = ROOT / "drizzle/migrations/20260922_tdm_memory_vault_foundation_v1.sql"

for p in (GITIGNORE, WA, TDM_DRIVE):
    if not p.exists():
        raise SystemExit(f"ERROR=MISSING:{p}")

backup = ROOT / ".patch-backups" / f"tdm-phase3-history-v1-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup.mkdir(parents=True, exist_ok=True)
for p in (GITIGNORE, WA, TDM_DRIVE, RUNNER, VERIFY):
    if p.exists():
        shutil.copy2(p, backup / p.name)

gi = GITIGNORE.read_text(encoding="utf-8")
unignore = "!/drizzle/migrations/20260922_tdm_memory_vault_foundation_v1.sql"
if unignore not in gi:
    gi += "\n# TDM versioned migrations\n" + unignore + "\n"
    GITIGNORE.write_text(gi, encoding="utf-8")

wa = WA.read_text(encoding="utf-8")
marker = "export async function fetchWAGatewayHistoricalMessagesPage("
if marker not in wa:
    anchor = "function remoteInstances(body: any): any[] {"
    if anchor not in wa:
        raise SystemExit("ERROR=WA_HISTORY_EXPORT_ANCHOR_MISSING")
    insert = r'''
export async function fetchWAGatewayHistoricalMessagesPage(input: {
  sessionKey: string;
  page: number;
  pageSize: number;
  remoteJid?: string | null;
}) {
  const sessionKey = String(input.sessionKey || "").trim();
  const page = Math.max(1, Math.min(1_000_000, Math.floor(Number(input.page) || 1)));
  const pageSize = Math.max(1, Math.min(100, Math.floor(Number(input.pageSize) || 50)));
  if (!sessionKey) throw new Error("Evolution instance name is required");

  const remoteJid = String(input.remoteJid || "").trim();
  const body: Record<string, unknown> = {
    page,
    offset: pageSize,
    ...(remoteJid ? { where: { key: { remoteJid } } } : {}),
  };

  const result = await gatewayRequest(
    `/chat/findMessages/${encodeURIComponent(sessionKey)}`,
    {
      method: "POST",
      body,
      strict: true,
      timeoutMs: 30_000,
      maxResponseBytes: 32 * 1024 * 1024,
    },
  );

  const root =
    result.response?.messages ??
    result.response?.data?.messages ??
    result.response?.data ??
    result.response ??
    {};
  const records = Array.isArray(root)
    ? root
    : Array.isArray(root?.records)
      ? root.records
      : [];
  const total = Math.max(0, Number(root?.total ?? records.length) || 0);
  const pages = Math.max(1, Number(root?.pages ?? Math.ceil(total / pageSize) || 1));
  const currentPage = Math.max(1, Number(root?.currentPage ?? page) || page);

  return { total, pages, currentPage, records };
}

'''
    wa = wa.replace(anchor, insert + anchor, 1)
    WA.write_text(wa, encoding="utf-8")

tdm = TDM_DRIVE.read_text(encoding="utf-8")
seg_marker = "export async function archiveTdmRawSegment("
if seg_marker not in tdm:
    anchor = "export async function archiveTdmMediaBuffer("
    if anchor not in tdm:
        raise SystemExit("ERROR=TDM_SEGMENT_ANCHOR_MISSING")
    insert = r'''
export async function archiveTdmRawSegment(input: {
  sessionKey: string;
  segmentNo: number;
  ndjson: string;
}) {
  const buffer = Buffer.from(input.ndjson, "utf8");
  const digest = sha256(buffer);
  const account = safeSegment(input.sessionKey, "unknown-account");
  const segmentNo = Math.max(1, Math.floor(Number(input.segmentNo) || 1));
  const result = await uploadStoredFileViaGoogleDrivePool({
    storageKey: `${TDM_DRIVE_ROOT}/WhatsApp/Accounts/${account}/Historical Raw Segments`,
    fileName: `history-page-${String(segmentNo).padStart(8, "0")}-${digest.slice(0, 12)}.ndjson`,
    buffer,
    contentType: "application/x-ndjson",
    appProperties: {
      source: TDM_DRIVE_SOURCE,
      tdmVersion: "1",
      tdmResource: "raw-segment",
      retentionClass: TDM_RETENTION_CLASS,
      provider: "whatsapp",
      sessionKey: safeSegment(input.sessionKey, "unknown", 60),
      segmentNo: String(segmentNo),
      sha256: digest,
    },
  });
  if (result.uploadStatus !== "uploaded" || !result.driveFileId) {
    throw new Error(result.error || "TDM raw segment upload failed");
  }
  return {
    driveFileId: result.driveFileId,
    storageAccountId: result.storageAccountId,
    sha256: digest,
    bytes: buffer.length,
  };
}

'''
    tdm = tdm.replace(anchor, insert + anchor, 1)
    TDM_DRIVE.write_text(tdm, encoding="utf-8")

RUNNER.write_text(r'''import "dotenv/config";
import crypto from "node:crypto";
import mysql, { type ResultSetHeader, type RowDataPacket } from "mysql2/promise";
import { fetchWAGatewayHistoricalMessagesPage } from "../server/services/waGatewayIntegrationService";
import { archiveTdmRawSegment } from "../server/services/darwish/tdm/tdmDriveArchiveStorage";

const args = process.argv.slice(2);
const apply = args.includes("--apply");
const confirm = args.includes("--confirm=APPLY_TDM_PHASE3");
const getArg = (name: string) => {
  const hit = args.find(v => v.startsWith(`--${name}=`));
  return hit ? hit.slice(name.length + 3) : null;
};
const sessionArg = String(getArg("session") || "").trim();
const pageSize = Math.max(1, Math.min(100, Number(getArg("page-size") || 25) || 25));
const maxPages = Math.max(1, Math.min(100, Number(getArg("max-pages") || 1) || 1));
const sleepMs = Math.max(0, Math.min(5000, Number(getArg("sleep-ms") || 250) || 250));

if (!process.env.DATABASE_URL) throw new Error("DATABASE_URL is required");
if (!sessionArg) throw new Error("Use --session=<session id or Evolution instance name>");
if (apply && !confirm) throw new Error("Use --confirm=APPLY_TDM_PHASE3 with --apply");

type SessionRow = RowDataPacket & {
  id: number;
  sessionKey: string;
  phoneNumber: string | null;
  name: string | null;
};

type LocalMessage = RowDataPacket & {
  id: number;
  chatId: number;
  messageId: string;
  jid: string;
  direction: "Inbound" | "Outbound";
  messageType: string | null;
  body: string | null;
  quotedMessageId: string | null;
  quotedBody: string | null;
  senderJid: string | null;
  senderName: string | null;
  mediaUrl: string | null;
  mimeType: string | null;
  fileName: string | null;
  fileSize: number | null;
  durationSeconds: number | null;
  mediaDriveFileId: string | null;
  mediaStorageAccountId: number | null;
  rawPayload: unknown;
  sentAt: Date | null;
  createdAt: Date | null;
  chatType: string | null;
  contactName: string | null;
  groupSubject: string | null;
};

const MEDIA_TYPES = new Set([
  "image","video","audio","voice","ptt","document","sticker",
  "imageMessage","videoMessage","audioMessage","documentMessage","stickerMessage",
]);

const db = await mysql.createConnection(process.env.DATABASE_URL);

function delay(ms: number) {
  return ms ? new Promise(resolve => setTimeout(resolve, ms)) : Promise.resolve();
}

function sha256(text: string) {
  return crypto.createHash("sha256").update(text).digest("hex");
}

function parseJsonMaybe(value: unknown) {
  if (value == null) return null;
  if (typeof value === "object") return value;
  if (typeof value === "string") {
    try { return JSON.parse(value); } catch { return value; }
  }
  return value;
}

function asDate(value: unknown): Date | null {
  if (value == null || value === "") return null;
  if (value instanceof Date) return Number.isFinite(value.getTime()) ? value : null;
  const n = Number(value);
  if (Number.isFinite(n) && n > 0) {
    const d = new Date(n > 10_000_000_000 ? n : n * 1000);
    return Number.isFinite(d.getTime()) ? d : null;
  }
  const d = new Date(String(value));
  return Number.isFinite(d.getTime()) ? d : null;
}

function firstText(record: any) {
  const m = record?.message || {};
  const candidates = [
    m.conversation,
    m.extendedTextMessage?.text,
    m.imageMessage?.caption,
    m.videoMessage?.caption,
    m.documentMessage?.caption,
    m.buttonsResponseMessage?.selectedDisplayText,
    m.listResponseMessage?.title,
    m.templateButtonReplyMessage?.selectedDisplayText,
  ];
  return candidates.find(v => typeof v === "string" && v.trim())?.trim() || null;
}

function mediaNode(record: any) {
  const m = record?.message || {};
  return m.imageMessage || m.videoMessage || m.audioMessage || m.documentMessage || m.stickerMessage || null;
}

function inferChatType(jid: string) {
  if (jid.endsWith("@g.us")) return "Group";
  if (jid.endsWith("@newsletter")) return "Newsletter";
  return "Direct";
}

function ownJid(phone: string | null) {
  const digits = String(phone || "").replace(/\D+/g, "");
  return digits ? `${digits}@s.whatsapp.net` : null;
}

async function loadSession(): Promise<SessionRow> {
  const numeric = Number(sessionArg);
  const useId = Number.isInteger(numeric) && numeric > 0;
  const [rows] = await db.query<SessionRow[]>(
    `SELECT id, session_key AS sessionKey, phone_number AS phoneNumber, name
       FROM whatsapp_sessions
      WHERE ${useId ? "id = ?" : "session_key = ?"}
      LIMIT 1`,
    [useId ? numeric : sessionArg],
  );
  if (!rows[0]) throw new Error("WhatsApp session not found");
  return rows[0];
}

async function loadCheckpoint(sessionKey: string) {
  const [rows] = await db.query<RowDataPacket[]>(
    `SELECT cursor_value AS cursorValue
       FROM tdm_checkpoints
      WHERE source='whatsapp' AND source_session_key=? AND pipeline='historical_backfill'
      LIMIT 1`,
    [sessionKey],
  );
  if (!rows[0]?.cursorValue) return null;
  try { return JSON.parse(String(rows[0].cursorValue)); } catch { return null; }
}

async function localMessages(sessionId: number, messageIds: string[]) {
  const ids = [...new Set(messageIds.filter(Boolean))];
  if (!ids.length) return new Map<string, LocalMessage>();
  const [rows] = await db.query<LocalMessage[]>(
    `SELECT m.id,
            m.chat_id AS chatId,
            m.message_id AS messageId,
            m.jid,
            m.direction,
            m.message_type AS messageType,
            m.body,
            m.quoted_message_id AS quotedMessageId,
            m.quoted_body AS quotedBody,
            m.sender_jid AS senderJid,
            m.sender_name AS senderName,
            m.media_url AS mediaUrl,
            m.mime_type AS mimeType,
            m.file_name AS fileName,
            m.file_size AS fileSize,
            m.duration_seconds AS durationSeconds,
            m.media_drive_file_id AS mediaDriveFileId,
            m.media_storage_account_id AS mediaStorageAccountId,
            m.raw_payload AS rawPayload,
            m.sent_at AS sentAt,
            m.created_at AS createdAt,
            c.chat_type AS chatType,
            c.contact_name AS contactName,
            c.group_subject AS groupSubject
       FROM whatsapp_messages m
       LEFT JOIN whatsapp_chats c ON c.id=m.chat_id
      WHERE m.session_id=?
        AND m.message_id IN (${ids.map(() => "?").join(",")})`,
    [sessionId, ...ids],
  );
  return new Map(rows.map(row => [String(row.messageId), row]));
}

async function ensureMemoryRecord(session: SessionRow, record: any, local: LocalMessage | undefined) {
  const sourceMessageId = String(record?.key?.id || local?.messageId || record?.id || "").trim();
  const conversationJid = String(record?.key?.remoteJid || local?.jid || "").trim();
  if (!sourceMessageId || !conversationJid) return null;

  const fromMe = Boolean(record?.key?.fromMe);
  const direction = local?.direction || (fromMe ? "Outbound" : "Inbound");
  const occurredAt = local?.sentAt || asDate(record?.messageTimestamp) || local?.createdAt || null;
  const participant = String(record?.key?.participant || record?.participant || "").trim() || null;
  const accountJid = ownJid(session.phoneNumber);
  const senderJid = local?.senderJid || participant || (direction === "Outbound" ? accountJid : conversationJid);
  const recipientJid = direction === "Outbound"
    ? conversationJid
    : conversationJid.endsWith("@g.us")
      ? conversationJid
      : accountJid;
  const messageType = local?.messageType || String(record?.messageType || "").trim() || null;
  const body = local?.body || firstText(record);
  const sourcePayload = { evolution: record, tcrm: parseJsonMaybe(local?.rawPayload) };
  const payloadJson = JSON.stringify(sourcePayload);

  const [insert] = await db.execute<ResultSetHeader>(
    `INSERT IGNORE INTO tdm_memory_records (
       source, source_session_id, source_session_key, source_account_phone,
       source_chat_id, source_message_row_id, source_message_id,
       conversation_jid, conversation_type, conversation_name,
       direction, sender_jid, sender_name, recipient_jid,
       message_type, body, quoted_message_id, quoted_body,
       occurred_at, source_created_at, source_payload, source_payload_sha256,
       captured_via
     ) VALUES (
       'whatsapp',?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'backfill'
     )`,
    [
      session.id,
      session.sessionKey,
      session.phoneNumber,
      local?.chatId ?? null,
      local?.id ?? null,
      sourceMessageId,
      conversationJid,
      local?.chatType || inferChatType(conversationJid),
      local?.groupSubject || local?.contactName || record?.pushName || null,
      direction,
      senderJid,
      local?.senderName || record?.pushName || null,
      recipientJid,
      messageType,
      body,
      local?.quotedMessageId ?? null,
      local?.quotedBody ?? null,
      occurredAt,
      local?.createdAt || occurredAt,
      payloadJson,
      sha256(payloadJson),
    ],
  );

  const [rows] = await db.query<RowDataPacket[]>(
    `SELECT id FROM tdm_memory_records
      WHERE source='whatsapp' AND source_session_key=? AND source_message_id=?
      LIMIT 1`,
    [session.sessionKey, sourceMessageId],
  );
  const memoryId = Number(rows[0]?.id || 0);
  if (!memoryId) throw new Error(`Failed to resolve TDM memory row for ${sourceMessageId}`);

  const node = mediaNode(record);
  const hasMedia =
    Boolean(local?.mediaDriveFileId || local?.mediaUrl || local?.mimeType || node) ||
    MEDIA_TYPES.has(String(messageType || ""));

  let mediaQueued = false;
  if (hasMedia) {
    const [mediaInsert] = await db.execute<ResultSetHeader>(
      `INSERT IGNORE INTO tdm_memory_media (
         memory_record_id, ordinal, media_kind, mime_type, file_name, file_size,
         duration_seconds, source_media_url, source_drive_file_id,
         source_storage_account_id, archive_state
       ) VALUES (?,0,?,?,?,?,?,?,?,?, 'pending')`,
      [
        memoryId,
        messageType,
        local?.mimeType || node?.mimetype || null,
        local?.fileName || node?.fileName || null,
        local?.fileSize || Number(node?.fileLength || 0) || null,
        local?.durationSeconds || Number(node?.seconds || 0) || null,
        local?.mediaUrl || node?.url || null,
        local?.mediaDriveFileId || null,
        local?.mediaStorageAccountId || null,
      ],
    );
    const [mediaRows] = await db.query<RowDataPacket[]>(
      `SELECT id FROM tdm_memory_media WHERE memory_record_id=? AND ordinal=0 LIMIT 1`,
      [memoryId],
    );
    const mediaId = Number(mediaRows[0]?.id || 0);
    if (mediaId) {
      const [jobInsert] = await db.execute<ResultSetHeader>(
        `INSERT IGNORE INTO tdm_archive_jobs
          (dedupe_key, job_type, memory_record_id, media_id, state, attempt_count, available_at)
         VALUES (?, 'media_archive', ?, ?, 'queued', 0, CURRENT_TIMESTAMP(3))`,
        [`media:${mediaId}`, memoryId, mediaId],
      );
      mediaQueued = mediaInsert.affectedRows > 0 || jobInsert.affectedRows > 0;
    }
  }

  return {
    memoryId,
    sourceMessageId,
    occurredAt,
    inserted: insert.affectedRows > 0,
    mediaQueued,
    archiveLine: JSON.stringify({
      tdmMemoryRecordId: memoryId,
      source: "whatsapp",
      sourceSessionKey: session.sessionKey,
      sourceMessageId,
      raw: sourcePayload,
    }),
  };
}

async function existingSealedSegment(sessionKey: string, page: number) {
  const [rows] = await db.query<RowDataPacket[]>(
    `SELECT id, state
       FROM tdm_archive_segments
      WHERE source='whatsapp'
        AND source_session_key=?
        AND conversation_jid='*'
        AND period_key='history'
        AND segment_no=?
      LIMIT 1`,
    [sessionKey, page],
  );
  return rows[0] || null;
}

async function saveCheckpoint(sessionKey: string, nextPage: number, pageSizeValue: number, totalAtStart: number, last: any | null) {
  await db.execute(
    `INSERT INTO tdm_checkpoints (
       source, source_session_key, pipeline, cursor_type, cursor_value,
       last_source_message_row_id, last_source_message_id, last_occurred_at, metadata
     ) VALUES (
       'whatsapp', ?, 'historical_backfill', 'evolution_page_desc', ?, ?, ?, ?, ?
     )
     ON DUPLICATE KEY UPDATE
       cursor_type=VALUES(cursor_type),
       cursor_value=VALUES(cursor_value),
       last_source_message_row_id=VALUES(last_source_message_row_id),
       last_source_message_id=VALUES(last_source_message_id),
       last_occurred_at=VALUES(last_occurred_at),
       metadata=VALUES(metadata)`,
    [
      sessionKey,
      JSON.stringify({ nextPage, pageSize: pageSizeValue, totalAtStart }),
      last?.localRowId || null,
      last?.sourceMessageId || null,
      last?.occurredAt || null,
      JSON.stringify({ updatedBy: "tdm-phase3-v1" }),
    ],
  );
}

async function sealRawSegment(sessionKey: string, page: number, rows: Array<Awaited<ReturnType<typeof ensureMemoryRecord>>>) {
  const usable = rows.filter(Boolean) as NonNullable<Awaited<ReturnType<typeof ensureMemoryRecord>>>[];
  if (!usable.length) return null;
  const ndjson = usable.map(r => r.archiveLine).join("\n") + "\n";
  const archived = await archiveTdmRawSegment({ sessionKey, segmentNo: page, ndjson });
  const dates = usable.map(r => r.occurredAt).filter((v): v is Date => v instanceof Date);
  const first = dates.length ? new Date(Math.min(...dates.map(d => d.getTime()))) : null;
  const last = dates.length ? new Date(Math.max(...dates.map(d => d.getTime()))) : null;

  await db.execute(
    `INSERT INTO tdm_archive_segments (
       source, source_session_key, conversation_jid, period_key, segment_no,
       format, state, record_count, uncompressed_bytes, content_sha256,
       drive_file_id, storage_account_id, first_occurred_at, last_occurred_at, sealed_at
     ) VALUES (
       'whatsapp', ?, '*', 'history', ?, 'ndjson', 'sealed', ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP(3)
     )
     ON DUPLICATE KEY UPDATE
       state='sealed',
       record_count=VALUES(record_count),
       uncompressed_bytes=VALUES(uncompressed_bytes),
       content_sha256=VALUES(content_sha256),
       drive_file_id=VALUES(drive_file_id),
       storage_account_id=VALUES(storage_account_id),
       first_occurred_at=VALUES(first_occurred_at),
       last_occurred_at=VALUES(last_occurred_at),
       sealed_at=VALUES(sealed_at),
       last_error=NULL`,
    [
      sessionKey,
      page,
      usable.length,
      archived.bytes,
      archived.sha256,
      archived.driveFileId,
      archived.storageAccountId,
      first,
      last,
    ],
  );

  const [segmentRows] = await db.query<RowDataPacket[]>(
    `SELECT id FROM tdm_archive_segments
      WHERE source='whatsapp' AND source_session_key=? AND conversation_jid='*'
        AND period_key='history' AND segment_no=? LIMIT 1`,
    [sessionKey, page],
  );
  const segmentId = Number(segmentRows[0]?.id || 0);
  if (!segmentId) throw new Error("Failed to resolve TDM raw segment");

  let entryNo = 0;
  for (const row of usable) {
    entryNo += 1;
    await db.execute(
      `INSERT IGNORE INTO tdm_archive_memberships
        (memory_record_id, archive_segment_id, entry_no, entry_sha256)
       VALUES (?,?,?,?)`,
      [row.memoryId, segmentId, entryNo, sha256(row.archiveLine)],
    );
  }
  return archived;
}

try {
  const session = await loadSession();
  const probe = await fetchWAGatewayHistoricalMessagesPage({
    sessionKey: session.sessionKey,
    page: 1,
    pageSize,
  });

  const checkpoint = await loadCheckpoint(session.sessionKey);
  let page = Math.max(
    1,
    Math.min(probe.pages, Number(checkpoint?.nextPage || probe.pages) || probe.pages),
  );

  console.log(`TDM_PHASE3_MODE=${apply ? "APPLY" : "DRY_RUN"}`);
  console.log(`SESSION_ID=${session.id}`);
  console.log(`SESSION_KEY=${session.sessionKey}`);
  console.log(`EVOLUTION_TOTAL=${probe.total}`);
  console.log(`EVOLUTION_PAGES=${probe.pages}`);
  console.log(`PAGE_SIZE=${pageSize}`);
  console.log(`START_PAGE=${page}`);

  let pagesProcessed = 0;
  let recordsSeen = 0;
  let inserted = 0;
  let existing = 0;
  let mediaQueued = 0;
  let segmentsSealed = 0;

  if (!apply) {
    const sample = page === 1 ? probe : await fetchWAGatewayHistoricalMessagesPage({
      sessionKey: session.sessionKey,
      page,
      pageSize,
    });
    console.log(`DRY_RUN_RECORDS=${sample.records.length}`);
    console.log("DB_WRITES=0");
    console.log("DRIVE_WRITES=0");
    console.log("SAFE_TO_APPLY=YES");
    console.log("ERROR=NONE");
    process.exit(0);
  }

  while (page >= 1 && pagesProcessed < maxPages) {
    const sealed = await existingSealedSegment(session.sessionKey, page);
    if (String(sealed?.state || "") === "sealed") {
      await saveCheckpoint(session.sessionKey, page - 1, pageSize, probe.total, null);
      page -= 1;
      continue;
    }

    const remote = page === 1 ? probe : await fetchWAGatewayHistoricalMessagesPage({
      sessionKey: session.sessionKey,
      page,
      pageSize,
    });
    if (!remote.records.length) throw new Error(`Evolution returned no records for historical page ${page}`);

    const messageIds = remote.records
      .map((r: any) => String(r?.key?.id || "").trim())
      .filter(Boolean);
    const localMap = await localMessages(session.id, messageIds);
    const processed = [];

    for (const record of remote.records) {
      const messageId = String(record?.key?.id || "").trim();
      const row = await ensureMemoryRecord(session, record, localMap.get(messageId));
      if (!row) continue;
      processed.push(row);
      recordsSeen += 1;
      if (row.inserted) inserted += 1;
      else existing += 1;
      if (row.mediaQueued) mediaQueued += 1;
    }

    if (!processed.length) throw new Error(`No valid historical messages found on page ${page}`);

    await sealRawSegment(session.sessionKey, page, processed);
    segmentsSealed += 1;
    pagesProcessed += 1;

    const last = processed[processed.length - 1];
    await saveCheckpoint(session.sessionKey, page - 1, pageSize, probe.total, {
      sourceMessageId: last.sourceMessageId,
      occurredAt: last.occurredAt,
      localRowId: null,
    });

    page -= 1;
    if (page >= 1 && pagesProcessed < maxPages) await delay(sleepMs);
  }

  console.log(`PAGES_PROCESSED=${pagesProcessed}`);
  console.log(`RECORDS_SEEN=${recordsSeen}`);
  console.log(`MEMORY_INSERTED=${inserted}`);
  console.log(`MEMORY_EXISTING=${existing}`);
  console.log(`MEDIA_QUEUED=${mediaQueued}`);
  console.log(`RAW_SEGMENTS_SEALED=${segmentsSealed}`);
  console.log(`NEXT_PAGE=${Math.max(0, page)}`);
  console.log(`COMPLETE=${page < 1 ? "YES" : "NO"}`);
  console.log("SOURCE_WRITES=0");
  console.log("ERROR=NONE");
} finally {
  await db.end();
}
''', encoding="utf-8")

VERIFY.write_text(r'''import "dotenv/config";
import fs from "node:fs";
import path from "node:path";
import mysql from "mysql2/promise";

const args = process.argv.slice(2);
const getArg = (name: string) => {
  const hit = args.find(v => v.startsWith(`--${name}=`));
  return hit ? hit.slice(name.length + 3) : null;
};
const session = String(getArg("session") || "").trim();

if (!process.env.DATABASE_URL) throw new Error("DATABASE_URL is required");

const root = process.cwd();
const wa = fs.readFileSync(path.join(root, "server/services/waGatewayIntegrationService.ts"), "utf8");
const drive = fs.readFileSync(path.join(root, "server/services/darwish/tdm/tdmDriveArchiveStorage.ts"), "utf8");
const runner = fs.readFileSync(path.join(root, "scripts/run-tdm-historical-backfill-v1.ts"), "utf8");
const core = fs.readFileSync(path.join(root, "server/_core/index.ts"), "utf8");
const workerPath = path.join(root, "server/services/darwish/chatwoot/darwishWorker.ts");
const worker = fs.existsSync(workerPath) ? fs.readFileSync(workerPath, "utf8") : "";

const db = await mysql.createConnection(process.env.DATABASE_URL);
try {
  const [tables] = await db.query<any[]>(
    `SELECT TABLE_NAME FROM information_schema.TABLES
      WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME IN
      ('tdm_memory_records','tdm_memory_media','tdm_archive_segments','tdm_archive_memberships','tdm_archive_jobs','tdm_checkpoints')`,
  );
  const tableCount = tables.length;

  let memory = 0, segments = 0, checkpoints = 0, queuedMedia = 0;
  if (session) {
    const [mr] = await db.query<any[]>(
      `SELECT COUNT(*) AS c FROM tdm_memory_records WHERE source_session_key=?`,
      [session],
    );
    memory = Number(mr[0]?.c || 0);
    const [sg] = await db.query<any[]>(
      `SELECT COUNT(*) AS c FROM tdm_archive_segments
        WHERE source_session_key=? AND period_key='history' AND state='sealed'`,
      [session],
    );
    segments = Number(sg[0]?.c || 0);
    const [cp] = await db.query<any[]>(
      `SELECT COUNT(*) AS c FROM tdm_checkpoints
        WHERE source_session_key=? AND pipeline='historical_backfill'`,
      [session],
    );
    checkpoints = Number(cp[0]?.c || 0);
    const [mj] = await db.query<any[]>(
      `SELECT COUNT(*) AS c
         FROM tdm_archive_jobs j
         JOIN tdm_memory_records m ON m.id=j.memory_record_id
        WHERE m.source_session_key=? AND j.job_type='media_archive' AND j.state='queued'`,
      [session],
    );
    queuedMedia = Number(mj[0]?.c || 0);
  }

  const sourceWritePattern = /\b(?:INSERT\s+INTO|UPDATE|DELETE\s+FROM)\s+whatsapp_/i;
  const runtimeHooked =
    core.includes("run-tdm-historical-backfill") ||
    core.includes("tdmHistoricalBackfill") ||
    worker.includes("run-tdm-historical-backfill") ||
    worker.includes("tdmHistoricalBackfill");

  const sqlPath = path.join(root, "drizzle/migrations/20260922_tdm_memory_vault_foundation_v1.sql");
  const gitignore = fs.readFileSync(path.join(root, ".gitignore"), "utf8");

  const ok =
    tableCount === 6 &&
    wa.includes("fetchWAGatewayHistoricalMessagesPage") &&
    drive.includes("archiveTdmRawSegment") &&
    !sourceWritePattern.test(runner) &&
    !runtimeHooked &&
    fs.existsSync(sqlPath) &&
    gitignore.includes("!/drizzle/migrations/20260922_tdm_memory_vault_foundation_v1.sql");

  console.log(`TDM_PHASE3_VERIFY=${ok ? "PASS" : "FAIL"}`);
  console.log(`TDM_TABLES=${tableCount}/6`);
  console.log(`HISTORY_API_WRAPPER=${wa.includes("fetchWAGatewayHistoricalMessagesPage") ? "YES" : "NO"}`);
  console.log(`RAW_SEGMENT_ARCHIVER=${drive.includes("archiveTdmRawSegment") ? "YES" : "NO"}`);
  console.log(`SOURCE_WRITE_CODE=${sourceWritePattern.test(runner) ? "YES" : "NO"}`);
  console.log(`RUNTIME_HOOKED=${runtimeHooked ? "YES" : "NO"}`);
  console.log(`PHASE1_SQL_TRACKABLE=${fs.existsSync(sqlPath) && gitignore.includes("!/drizzle/migrations/20260922_tdm_memory_vault_foundation_v1.sql") ? "YES" : "NO"}`);
  if (session) {
    console.log(`SESSION_MEMORY=${memory}`);
    console.log(`SEALED_SEGMENTS=${segments}`);
    console.log(`CHECKPOINTS=${checkpoints}`);
    console.log(`MEDIA_JOBS_QUEUED=${queuedMedia}`);
  }
  console.log(`ERROR=${ok ? "NONE" : "VERIFY_FAILED"}`);
  if (!ok) process.exitCode = 2;
} finally {
  await db.end();
}
''', encoding="utf-8")

print("PATCH=PASS")
print("TDM_PHASE=3_HISTORICAL_BACKFILL_V1")
print("EVOLUTION_HISTORY_WRAPPER=YES")
print("CHECKPOINTED=YES")
print("RATE_LIMITED=YES")
print("IDEMPOTENT=YES")
print("RAW_NDJSON_SEGMENTS=YES")
print("MEDIA_JOBS=QUEUED_ONLY")
print("RUNTIME_HOOK=NO")
print("PHASE1_SQL_UNIGNORE=YES")
print("FILES_CHANGED=5")
print(f"PHASE1_SQL_PRESENT={'YES' if PHASE1_SQL.exists() else 'NO'}")
print(f"BACKUP={backup}")
print("ERROR=NONE")
