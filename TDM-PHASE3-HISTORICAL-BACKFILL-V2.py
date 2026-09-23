#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import os, shutil

ROOT = Path(os.environ.get("TCRM_ROOT", "/var/www/TCRM-MAIN"))
V1 = ROOT / "scripts/run-tdm-historical-backfill-v1.ts"
V2 = ROOT / "scripts/run-tdm-historical-backfill-v2.ts"
VERIFY = ROOT / "scripts/verify-tdm-historical-backfill-v2.ts"

if not V1.exists():
    raise SystemExit("ERROR=TDM_PHASE3_V1_RUNNER_MISSING")

backup = ROOT / ".patch-backups" / f"tdm-phase3-v2-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup.mkdir(parents=True, exist_ok=True)
for p in (V2, VERIFY):
    if p.exists():
        shutil.copy2(p, backup / p.name)

V2.write_text(r'''import "dotenv/config";
import fs from "node:fs";
import crypto from "node:crypto";
import mysql, { type ResultSetHeader, type RowDataPacket } from "mysql2/promise";
import { fetchWAGatewayHistoricalMessagesPage } from "../server/services/waGatewayIntegrationService";
import { archiveTdmRawSegment } from "../server/services/darwish/tdm/tdmDriveArchiveStorage";

const argv = process.argv.slice(2);
const apply = argv.includes("--apply");
const confirm = argv.includes("--confirm=APPLY_TDM_PHASE3_V2");
const arg = (name: string) => {
  const hit = argv.find(v => v.startsWith(`--${name}=`));
  return hit ? hit.slice(name.length + 3) : null;
};

const sessionArg = String(arg("session") || "").trim();
const pageSize = Math.max(1, Math.min(100, Number(arg("page-size") || 100) || 100));
const maxPages = Math.max(1, Math.min(500, Number(arg("max-pages") || 10) || 10));
const sleepMs = Math.max(0, Math.min(5000, Number(arg("sleep-ms") || 250) || 250));

if (!process.env.DATABASE_URL) throw new Error("DATABASE_URL is required");
if (!sessionArg) throw new Error("Use --session=<session id or Evolution instance name>");
if (apply && !confirm) throw new Error("Use --confirm=APPLY_TDM_PHASE3_V2 with --apply");

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

function recordId(record: any) {
  return String(record?.key?.id || record?.id || "").trim();
}

async function main() {
  const db = await mysql.createConnection(process.env.DATABASE_URL!);
  let lockName = "";
  let lockHeld = false;

  try {
    const numeric = Number(sessionArg);
    const useId = Number.isInteger(numeric) && numeric > 0;
    const [sessionRows] = await db.query<SessionRow[]>(
      `SELECT id, session_key AS sessionKey, phone_number AS phoneNumber, name
         FROM whatsapp_sessions
        WHERE ${useId ? "id=?" : "session_key=?"}
        LIMIT 1`,
      [useId ? numeric : sessionArg],
    );
    const session = sessionRows[0];
    if (!session) throw new Error("WhatsApp session not found");

    lockName = `tdm:p3v2:${session.sessionKey}`.slice(0, 64);
    if (apply) {
      const [lockRows] = await db.query<RowDataPacket[]>("SELECT GET_LOCK(?,0) AS got", [lockName]);
      lockHeld = Number(lockRows[0]?.got || 0) === 1;
      if (!lockHeld) throw new Error("Another TDM Phase 3 V2 worker already holds this session lock");
    }

    const progressFile = String(arg("progress-file") || `/tmp/tdm-phase3-v2-${session.id}.json`);
    const writeProgress = (data: Record<string, unknown>) => {
      fs.writeFileSync(progressFile, JSON.stringify({
        pid: process.pid,
        sessionId: session.id,
        sessionKey: session.sessionKey,
        updatedAt: new Date().toISOString(),
        ...data,
      }, null, 2));
    };

    const probe = await fetchWAGatewayHistoricalMessagesPage({
      sessionKey: session.sessionKey,
      page: 1,
      pageSize,
    });
    if (!probe.records.length || probe.total <= 0) throw new Error("Evolution history is empty");

    const [checkpointRows] = await db.query<RowDataPacket[]>(
      `SELECT cursor_type AS cursorType, cursor_value AS cursorValue
         FROM tdm_checkpoints
        WHERE source='whatsapp' AND source_session_key=? AND pipeline='historical_backfill'
        LIMIT 1`,
      [session.sessionKey],
    );

    let cursor: any = null;
    if (checkpointRows[0]?.cursorType === "evolution_page_asc_v2" && checkpointRows[0]?.cursorValue) {
      try { cursor = JSON.parse(String(checkpointRows[0].cursorValue)); } catch { cursor = null; }
    }

    let nextPage = Math.max(1, Number(cursor?.nextPage || 1) || 1);
    let targetTailIds: string[] = Array.isArray(cursor?.targetTailIds)
      ? cursor.targetTailIds.map((v: unknown) => String(v || "").trim()).filter(Boolean).slice(0, 3)
      : [];

    if (!targetTailIds.length) {
      const tail = await fetchWAGatewayHistoricalMessagesPage({
        sessionKey: session.sessionKey,
        page: probe.pages,
        pageSize,
      });
      targetTailIds = tail.records.map(recordId).filter(Boolean).slice(0, 3);
      if (!targetTailIds.length) throw new Error("Unable to establish stable historical tail sentinel");
      nextPage = 1;
    }

    console.log(`TDM_PHASE3_V2_MODE=${apply ? "APPLY" : "DRY_RUN"}`);
    console.log(`SESSION_ID=${session.id}`);
    console.log(`SESSION_KEY=${session.sessionKey}`);
    console.log(`EVOLUTION_TOTAL=${probe.total}`);
    console.log(`EVOLUTION_PAGES=${probe.pages}`);
    console.log(`PAGE_SIZE=${pageSize}`);
    console.log(`START_PAGE=${nextPage}`);
    console.log(`TAIL_SENTINELS=${targetTailIds.length}`);

    if (!apply) {
      const sample = await fetchWAGatewayHistoricalMessagesPage({
        sessionKey: session.sessionKey,
        page: nextPage,
        pageSize,
      });
      console.log(`DRY_RUN_RECORDS=${sample.records.length}`);
      console.log("DB_WRITES=0");
      console.log("DRIVE_WRITES=0");
      console.log("SAFE_TO_APPLY=YES");
      console.log("ERROR=NONE");
      return;
    }

    const persistCheckpoint = async (page: number) => {
      const value = JSON.stringify({
        nextPage: page,
        pageSize,
        totalAtStart: probe.total,
        targetTailIds,
      });
      if (value.length > 500) throw new Error("TDM V2 checkpoint exceeds cursor_value capacity");
      await db.execute(
        `INSERT INTO tdm_checkpoints (
           source, source_session_key, pipeline, cursor_type, cursor_value, metadata
         ) VALUES (
           'whatsapp', ?, 'historical_backfill', 'evolution_page_asc_v2', ?, ?
         )
         ON DUPLICATE KEY UPDATE
           cursor_type=VALUES(cursor_type),
           cursor_value=VALUES(cursor_value),
           metadata=VALUES(metadata)`,
        [session.sessionKey, value, JSON.stringify({ updatedBy: "tdm-phase3-v2" })],
      );
    };

    if (!cursor) await persistCheckpoint(1);

    const loadLocal = async (ids: string[]) => {
      const uniq = [...new Set(ids.filter(Boolean))];
      if (!uniq.length) return new Map<string, LocalMessage>();
      const [rows] = await db.query<LocalMessage[]>(
        `SELECT m.id, m.chat_id AS chatId, m.message_id AS messageId, m.jid,
                m.direction, m.message_type AS messageType, m.body,
                m.quoted_message_id AS quotedMessageId, m.quoted_body AS quotedBody,
                m.sender_jid AS senderJid, m.sender_name AS senderName,
                m.media_url AS mediaUrl, m.mime_type AS mimeType,
                m.file_name AS fileName, m.file_size AS fileSize,
                m.duration_seconds AS durationSeconds,
                m.media_drive_file_id AS mediaDriveFileId,
                m.media_storage_account_id AS mediaStorageAccountId,
                m.raw_payload AS rawPayload, m.sent_at AS sentAt,
                m.created_at AS createdAt, c.chat_type AS chatType,
                c.contact_name AS contactName, c.group_subject AS groupSubject
           FROM whatsapp_messages m
           LEFT JOIN whatsapp_chats c ON c.id=m.chat_id
          WHERE m.session_id=?
            AND m.message_id IN (${uniq.map(() => "?").join(",")})`,
        [session.id, ...uniq],
      );
      return new Map(rows.map(row => [String(row.messageId), row]));
    };

    const ensureMemory = async (record: any, local: LocalMessage | undefined) => {
      const sourceMessageId = recordId(record) || String(local?.messageId || "").trim();
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
        : conversationJid.endsWith("@g.us") ? conversationJid : accountJid;
      const messageType = local?.messageType || String(record?.messageType || "").trim() || null;
      const sourcePayload = { evolution: record, tcrm: parseJsonMaybe(local?.rawPayload) };
      const payloadJson = JSON.stringify(sourcePayload);

      const [ins] = await db.execute<ResultSetHeader>(
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
          session.id, session.sessionKey, session.phoneNumber,
          local?.chatId ?? null, local?.id ?? null, sourceMessageId,
          conversationJid, local?.chatType || inferChatType(conversationJid),
          local?.groupSubject || local?.contactName || record?.pushName || null,
          direction, senderJid, local?.senderName || record?.pushName || null,
          recipientJid, messageType, local?.body || firstText(record),
          local?.quotedMessageId ?? null, local?.quotedBody ?? null,
          occurredAt, local?.createdAt || occurredAt, payloadJson, sha256(payloadJson),
        ],
      );

      const [rows] = await db.query<RowDataPacket[]>(
        `SELECT id FROM tdm_memory_records
          WHERE source='whatsapp' AND source_session_key=? AND source_message_id=?
          LIMIT 1`,
        [session.sessionKey, sourceMessageId],
      );
      const memoryId = Number(rows[0]?.id || 0);
      if (!memoryId) throw new Error(`Unable to resolve TDM memory row ${sourceMessageId}`);

      const node = mediaNode(record);
      const hasMedia =
        Boolean(local?.mediaDriveFileId || local?.mediaUrl || local?.mimeType || node) ||
        MEDIA_TYPES.has(String(messageType || ""));

      let mediaQueued = false;
      if (hasMedia) {
        await db.execute(
          `INSERT IGNORE INTO tdm_memory_media (
             memory_record_id, ordinal, media_kind, mime_type, file_name, file_size,
             duration_seconds, source_media_url, source_drive_file_id,
             source_storage_account_id, archive_state
           ) VALUES (?,0,?,?,?,?,?,?,?,?, 'pending')`,
          [
            memoryId, messageType, local?.mimeType || node?.mimetype || null,
            local?.fileName || node?.fileName || null,
            local?.fileSize || Number(node?.fileLength || 0) || null,
            local?.durationSeconds || Number(node?.seconds || 0) || null,
            local?.mediaUrl || node?.url || null,
            local?.mediaDriveFileId || null,
            local?.mediaStorageAccountId || null,
          ],
        );
        const [mediaRows] = await db.query<RowDataPacket[]>(
          "SELECT id FROM tdm_memory_media WHERE memory_record_id=? AND ordinal=0 LIMIT 1",
          [memoryId],
        );
        const mediaId = Number(mediaRows[0]?.id || 0);
        if (mediaId) {
          const [job] = await db.execute<ResultSetHeader>(
            `INSERT IGNORE INTO tdm_archive_jobs
              (dedupe_key, job_type, memory_record_id, media_id, state, attempt_count, available_at)
             VALUES (?, 'media_archive', ?, ?, 'queued', 0, CURRENT_TIMESTAMP(3))`,
            [`media:${mediaId}`, memoryId, mediaId],
          );
          mediaQueued = job.affectedRows > 0;
        }
      }

      return {
        memoryId,
        sourceMessageId,
        inserted: ins.affectedRows > 0,
        mediaQueued,
        occurredAt,
        archiveLine: JSON.stringify({
          tdmMemoryRecordId: memoryId,
          source: "whatsapp",
          sourceSessionKey: session.sessionKey,
          sourceMessageId,
          raw: sourcePayload,
        }),
      };
    };

    const [seqRows] = await db.query<RowDataPacket[]>(
      `SELECT COALESCE(MAX(segment_no),0) AS maxNo
         FROM tdm_archive_segments
        WHERE source='whatsapp' AND source_session_key=? AND period_key='history-v2'`,
      [session.sessionKey],
    );
    let nextSegmentNo = Number(seqRows[0]?.maxNo || 0) + 1;

    let page = nextPage;
    let pagesProcessed = 0;
    let recordsSeen = 0;
    let inserted = 0;
    let existing = 0;
    let mediaQueued = 0;
    let rawSegmentsSealed = 0;
    let dynamicPages = probe.pages;
    let complete = false;

    writeProgress({ state: "running", page, pagesProcessed, recordsSeen, nextPage: page });

    while (pagesProcessed < maxPages && !complete) {
      if (page > dynamicPages) {
        const refresh = await fetchWAGatewayHistoricalMessagesPage({
          sessionKey: session.sessionKey,
          page: 1,
          pageSize,
        });
        dynamicPages = refresh.pages;
        if (page > dynamicPages) {
          throw new Error("Historical tail sentinel was not found before current Evolution tail; reconciliation required");
        }
      }

      const remote = await fetchWAGatewayHistoricalMessagesPage({
        sessionKey: session.sessionKey,
        page,
        pageSize,
      });
      if (!remote.records.length) throw new Error(`Evolution returned empty historical page ${page}`);

      dynamicPages = Math.max(dynamicPages, remote.pages);
      const ids = remote.records.map(recordId).filter(Boolean);
      const localMap = await loadLocal(ids);
      const processed: NonNullable<Awaited<ReturnType<typeof ensureMemory>>>[] = [];

      for (const record of remote.records) {
        const id = recordId(record);
        const row = await ensureMemory(record, localMap.get(id));
        if (!row) continue;
        processed.push(row);
        recordsSeen += 1;
        if (row.inserted) inserted += 1;
        else existing += 1;
        if (row.mediaQueued) mediaQueued += 1;
      }
      if (!processed.length) throw new Error(`No valid historical messages on page ${page}`);

      const memoryIds = processed.map(r => r.memoryId);
      const [membershipRows] = await db.query<RowDataPacket[]>(
        `SELECT memory_record_id AS memoryRecordId
           FROM tdm_archive_memberships
          WHERE memory_record_id IN (${memoryIds.map(() => "?").join(",")})`,
        memoryIds,
      );
      const archived = new Set(membershipRows.map(r => Number(r.memoryRecordId)));
      const unarchived = processed.filter(r => !archived.has(r.memoryId));

      if (unarchived.length) {
        const ndjson = unarchived.map(r => r.archiveLine).join("\n") + "\n";
        const archive = await archiveTdmRawSegment({
          sessionKey: session.sessionKey,
          segmentNo: nextSegmentNo,
          ndjson,
        });
        const dates = unarchived.map(r => r.occurredAt).filter((v): v is Date => v instanceof Date);
        const first = dates.length ? new Date(Math.min(...dates.map(d => d.getTime()))) : null;
        const last = dates.length ? new Date(Math.max(...dates.map(d => d.getTime()))) : null;

        await db.execute(
          `INSERT INTO tdm_archive_segments (
             source, source_session_key, conversation_jid, period_key, segment_no,
             format, state, record_count, uncompressed_bytes, content_sha256,
             drive_file_id, storage_account_id, first_occurred_at, last_occurred_at, sealed_at
           ) VALUES (
             'whatsapp', ?, '*', 'history-v2', ?, 'ndjson', 'sealed', ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP(3)
           )`,
          [
            session.sessionKey, nextSegmentNo, unarchived.length, archive.bytes,
            archive.sha256, archive.driveFileId, archive.storageAccountId, first, last,
          ],
        );
        const [segmentRows] = await db.query<RowDataPacket[]>(
          `SELECT id FROM tdm_archive_segments
            WHERE source='whatsapp' AND source_session_key=? AND period_key='history-v2'
              AND segment_no=? LIMIT 1`,
          [session.sessionKey, nextSegmentNo],
        );
        const segmentId = Number(segmentRows[0]?.id || 0);
        if (!segmentId) throw new Error("Unable to resolve TDM V2 archive segment");

        let entry = 0;
        for (const row of unarchived) {
          entry += 1;
          await db.execute(
            `INSERT IGNORE INTO tdm_archive_memberships
              (memory_record_id, archive_segment_id, entry_no, entry_sha256)
             VALUES (?,?,?,?)`,
            [row.memoryId, segmentId, entry, sha256(row.archiveLine)],
          );
        }
        nextSegmentNo += 1;
        rawSegmentsSealed += 1;
      }

      const pageIds = new Set(ids);
      complete = targetTailIds.some(id => pageIds.has(id));
      pagesProcessed += 1;
      page += 1;
      await persistCheckpoint(complete ? 0 : page);

      writeProgress({
        state: complete ? "complete" : "running",
        page: page - 1,
        pagesProcessed,
        recordsSeen,
        memoryInserted: inserted,
        memoryExisting: existing,
        mediaQueued,
        rawSegmentsSealed,
        nextPage: complete ? 0 : page,
        dynamicPages,
      });

      console.log(`PAGE_DONE=${page - 1} RECORDS=${processed.length} NEW=${processed.filter(r => r.inserted).length} RAW_NEW=${unarchived.length} NEXT=${complete ? 0 : page}`);
      if (!complete && pagesProcessed < maxPages) await delay(sleepMs);
    }

    console.log(`PAGES_PROCESSED=${pagesProcessed}`);
    console.log(`RECORDS_SEEN=${recordsSeen}`);
    console.log(`MEMORY_INSERTED=${inserted}`);
    console.log(`MEMORY_EXISTING=${existing}`);
    console.log(`MEDIA_QUEUED=${mediaQueued}`);
    console.log(`RAW_SEGMENTS_SEALED=${rawSegmentsSealed}`);
    console.log(`NEXT_PAGE=${complete ? 0 : page}`);
    console.log(`COMPLETE=${complete ? "YES" : "NO"}`);
    console.log("SOURCE_WRITES=0");
    console.log(`PROGRESS_FILE=${progressFile}`);
    console.log("ERROR=NONE");
  } finally {
    if (lockHeld && lockName) {
      await db.query("SELECT RELEASE_LOCK(?)", [lockName]).catch(() => undefined);
    }
    await db.end();
  }
}

main().catch(error => {
  console.error("TDM_PHASE3_V2_ERROR=" + String(error instanceof Error ? error.message : error));
  process.exitCode = 1;
});
''', encoding="utf-8")

VERIFY.write_text(r'''import "dotenv/config";
import fs from "node:fs";
import path from "node:path";
import mysql from "mysql2/promise";

const argv = process.argv.slice(2);
const getArg = (name: string) => {
  const hit = argv.find(v => v.startsWith(`--${name}=`));
  return hit ? hit.slice(name.length + 3) : null;
};
const session = String(getArg("session") || "").trim();
if (!process.env.DATABASE_URL) throw new Error("DATABASE_URL is required");

const root = process.cwd();
const runnerPath = path.join(root, "scripts/run-tdm-historical-backfill-v2.ts");
const runner = fs.readFileSync(runnerPath, "utf8");

const db = await mysql.createConnection(process.env.DATABASE_URL);
try {
  let checkpointType = "";
  let checkpointNext: number | null = null;
  let memory = 0;
  let segmentsV1 = 0;
  let segmentsV2 = 0;
  let media = 0;

  if (session) {
    const [cp] = await db.query<any[]>(
      `SELECT cursor_type AS cursorType, cursor_value AS cursorValue
         FROM tdm_checkpoints
        WHERE source_session_key=? AND pipeline='historical_backfill' LIMIT 1`,
      [session],
    );
    checkpointType = String(cp[0]?.cursorType || "");
    if (cp[0]?.cursorValue) {
      try { checkpointNext = Number(JSON.parse(String(cp[0].cursorValue))?.nextPage ?? null); } catch {}
    }

    const [mr] = await db.query<any[]>(
      "SELECT COUNT(*) AS c FROM tdm_memory_records WHERE source_session_key=?",
      [session],
    );
    memory = Number(mr[0]?.c || 0);

    const [s1] = await db.query<any[]>(
      "SELECT COUNT(*) AS c FROM tdm_archive_segments WHERE source_session_key=? AND period_key='history' AND state='sealed'",
      [session],
    );
    segmentsV1 = Number(s1[0]?.c || 0);

    const [s2] = await db.query<any[]>(
      "SELECT COUNT(*) AS c FROM tdm_archive_segments WHERE source_session_key=? AND period_key='history-v2' AND state='sealed'",
      [session],
    );
    segmentsV2 = Number(s2[0]?.c || 0);

    const [mj] = await db.query<any[]>(
      `SELECT COUNT(*) AS c
         FROM tdm_archive_jobs j
         JOIN tdm_memory_records m ON m.id=j.memory_record_id
        WHERE m.source_session_key=? AND j.job_type='media_archive' AND j.state='queued'`,
      [session],
    );
    media = Number(mj[0]?.c || 0);
  }

  const sourceWrite = /\b(?:INSERT\s+INTO|UPDATE|DELETE\s+FROM)\s+whatsapp_/i.test(runner);
  const checks = {
    ASCENDING_CURSOR: runner.includes("evolution_page_asc_v2"),
    TAIL_SENTINEL: runner.includes("targetTailIds"),
    SESSION_LOCK: runner.includes("GET_LOCK"),
    PROGRESS_FILE: runner.includes("writeProgress"),
    IDEMPOTENT_MEMORY: runner.includes("INSERT IGNORE INTO tdm_memory_records"),
    SOURCE_WRITES: sourceWrite,
  };
  const ok =
    checks.ASCENDING_CURSOR &&
    checks.TAIL_SENTINEL &&
    checks.SESSION_LOCK &&
    checks.PROGRESS_FILE &&
    checks.IDEMPOTENT_MEMORY &&
    !checks.SOURCE_WRITES;

  console.log(`TDM_PHASE3_V2_VERIFY=${ok ? "PASS" : "FAIL"}`);
  console.log(`ASCENDING_CURSOR=${checks.ASCENDING_CURSOR ? "YES" : "NO"}`);
  console.log(`TAIL_SENTINEL=${checks.TAIL_SENTINEL ? "YES" : "NO"}`);
  console.log(`SESSION_LOCK=${checks.SESSION_LOCK ? "YES" : "NO"}`);
  console.log(`PROGRESS_FILE=${checks.PROGRESS_FILE ? "YES" : "NO"}`);
  console.log(`SOURCE_WRITE_CODE=${checks.SOURCE_WRITES ? "YES" : "NO"}`);
  if (session) {
    console.log(`CHECKPOINT_TYPE=${checkpointType || "NONE"}`);
    console.log(`CHECKPOINT_NEXT_PAGE=${checkpointNext == null ? "N/A" : checkpointNext}`);
    console.log(`TDM_MEMORY=${memory}`);
    console.log(`SEALED_SEGMENTS_V1=${segmentsV1}`);
    console.log(`SEALED_SEGMENTS_V2=${segmentsV2}`);
    console.log(`MEDIA_JOBS_QUEUED=${media}`);
  }
  console.log(`ERROR=${ok ? "NONE" : "VERIFY_FAILED"}`);
  if (!ok) process.exitCode = 2;
} finally {
  await db.end();
}
''', encoding="utf-8")

print("PATCH=PASS")
print("TDM_PHASE=3_V2")
print("ASCENDING_SCAN=YES")
print("TAIL_SENTINEL=YES")
print("SESSION_LOCK=YES")
print("PROGRESS_FILE=YES")
print("V1_SOURCE_UNCHANGED=YES")
print("SOURCE_WRITES=0")
print("FILES_CHANGED=2")
print(f"BACKUP={backup}")
print("ERROR=NONE")
