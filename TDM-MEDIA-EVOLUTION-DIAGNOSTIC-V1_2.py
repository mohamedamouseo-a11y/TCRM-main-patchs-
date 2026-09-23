#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import os, shutil

ROOT = Path(os.environ.get("TCRM_ROOT", "/var/www/TCRM-MAIN"))
WA = ROOT / "server/services/waGatewayIntegrationService.ts"
DIAG = ROOT / "scripts/diagnose-tdm-media-evolution-v1.ts"

if not WA.exists():
    raise SystemExit(f"ERROR=MISSING:{WA}")

backup = ROOT / ".patch-backups" / f"tdm-media-evolution-diagnostic-v1-2-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup.mkdir(parents=True, exist_ok=True)
shutil.copy2(WA, backup / WA.name)
if DIAG.exists():
    shutil.copy2(DIAG, backup / DIAG.name)

w = WA.read_text(encoding="utf-8")

old = '''      const result = await gatewayRequest(
        `/chat/getBase64FromMediaMessage/${encodeURIComponent(sessionKey)}`,
        {
          method: "POST",
          strict: true,
          timeoutMs: 90_000,
          maxBodyBytes: 4 * 1024 * 1024,
          maxResponseBytes: Math.ceil(maxBytes * 1.5) + 2 * 1024 * 1024,
          body: { message: candidates[index], convertToMp4: false },
        },
      );

      const encoded = extractEvolutionBase64(result.response);'''

new = '''      const result = await gatewayRequest(
        `/chat/getBase64FromMediaMessage/${encodeURIComponent(sessionKey)}`,
        {
          method: "POST",
          strict: false,
          timeoutMs: 90_000,
          maxBodyBytes: 4 * 1024 * 1024,
          maxResponseBytes: Math.ceil(maxBytes * 1.5) + 2 * 1024 * 1024,
          body: { message: candidates[index], convertToMp4: false },
        },
      );

      if (!result.success) {
        const rawDetail =
          result.response?.response?.message ??
          result.response?.message ??
          result.response?.error ??
          result.error ??
          `HTTP ${result.status}`;
        const detail = Array.isArray(rawDetail)
          ? rawDetail.map(v => String(v)).join(" | ")
          : typeof rawDetail === "object"
            ? JSON.stringify(rawDetail)
            : String(rawDetail);
        throw new Error(
          `HTTP_${Number(result.status || 0)} ${detail.replace(/[\\r\\n\\t]+/g, " ").slice(0, 300)}`,
        );
      }

      const encoded = extractEvolutionBase64(result.response);'''

if old not in w:
    raise SystemExit("ERROR=V1_1_GATEWAY_BLOCK_NOT_FOUND")

w = w.replace(old, new, 1)
WA.write_text(w, encoding="utf-8")

DIAG.write_text(r'''import "dotenv/config";
import mysql, { type RowDataPacket } from "mysql2/promise";
import { fetchWAGatewayHistoricalMediaBuffer } from "../server/services/waGatewayIntegrationService";

const argv = process.argv.slice(2);
const arg = (name: string) => {
  const hit = argv.find(v => v.startsWith(`--${name}=`));
  return hit ? hit.slice(name.length + 3) : null;
};

const sessionArg = String(arg("session") || "").trim();
const messageIdArg = String(arg("message-id") || "").trim();

if (!process.env.DATABASE_URL) throw new Error("DATABASE_URL is required");
if (!sessionArg) throw new Error("Use --session=<session id or key>");

function parseJson(value: unknown): any {
  if (value && typeof value === "object") return value;
  if (typeof value === "string") {
    try { return JSON.parse(value); } catch { return null; }
  }
  return null;
}

function mediaNode(record: any) {
  const m = record?.message || {};
  const keys = [
    "imageMessage",
    "videoMessage",
    "audioMessage",
    "documentMessage",
    "stickerMessage",
    "ptvMessage",
  ];
  return keys.find(k => m?.[k]) || null;
}

async function main() {
  const db = await mysql.createConnection(process.env.DATABASE_URL!);
  try {
    const numeric = Number(sessionArg);
    const useId = Number.isInteger(numeric) && numeric > 0;
    const [sessions] = await db.query<RowDataPacket[]>(
      `SELECT id, session_key AS sessionKey
         FROM whatsapp_sessions
        WHERE ${useId ? "id=?" : "session_key=?"}
        LIMIT 1`,
      [useId ? numeric : sessionArg],
    );
    const session = sessions[0];
    if (!session) throw new Error("WhatsApp session not found");

    const params: unknown[] = [String(session.sessionKey)];
    let messageFilter = "";
    if (messageIdArg) {
      messageFilter = " AND mr.source_message_id=?";
      params.push(messageIdArg);
    }

    const [rows] = await db.query<RowDataPacket[]>(
      `SELECT
         j.id AS jobId,
         j.state,
         j.attempt_count AS attemptCount,
         mm.id AS mediaId,
         mm.file_size AS fileSize,
         mm.mime_type AS mimeType,
         mm.source_drive_file_id AS sourceDriveFileId,
         mr.source_message_id AS sourceMessageId,
         mr.source_payload AS sourcePayload
       FROM tdm_archive_jobs j
       JOIN tdm_memory_media mm ON mm.id=j.media_id
       JOIN tdm_memory_records mr ON mr.id=j.memory_record_id
      WHERE j.job_type='media_archive'
        AND mr.source_session_key=?
        ${messageFilter}
      ORDER BY j.id ASC
      LIMIT 1`,
      params,
    );
    const row = rows[0];
    if (!row) throw new Error("No TDM media job found");

    const payload = parseJson(row.sourcePayload);
    const raw = payload?.evolution || null;
    const key = raw?.key || {};
    const node = mediaNode(raw);

    console.log(`JOB_ID=${Number(row.jobId)}`);
    console.log(`JOB_STATE=${String(row.state || "")}`);
    console.log(`ATTEMPTS=${Number(row.attemptCount || 0)}`);
    console.log(`MESSAGE_ID=${String(row.sourceMessageId || "")}`);
    console.log(`MESSAGE_TYPE=${String(raw?.messageType || "")}`);
    console.log(`REMOTE_JID=${String(key?.remoteJid || "")}`);
    console.log(`FROM_ME=${typeof key?.fromMe === "boolean" ? String(key.fromMe).toUpperCase() : "UNKNOWN"}`);
    console.log(`HAS_MESSAGE=${raw?.message && typeof raw.message === "object" ? "YES" : "NO"}`);
    console.log(`MEDIA_NODE=${node || "NONE"}`);
    console.log(`SOURCE_DRIVE=${row.sourceDriveFileId ? "YES" : "NO"}`);
    console.log(`MIME=${String(row.mimeType || "")}`);
    console.log(`FILE_SIZE=${Number(row.fileSize || 0)}`);

    try {
      const result = await fetchWAGatewayHistoricalMediaBuffer({
        sessionKey: String(session.sessionKey),
        rawMessage: raw,
        messageId: String(row.sourceMessageId),
        maxBytes: Math.min(
          64 * 1024 * 1024,
          Math.max(8 * 1024 * 1024, Number(row.fileSize || 0) + 1024 * 1024),
        ),
      });
      console.log("RECOVERY=PASS");
      console.log(`RECOVERED_BYTES=${result.buffer.length}`);
      console.log(`RECOVERED_MIME=${String(result.mimeType || "")}`);
      console.log(`RECOVERY_CANDIDATE=${Number((result as any).recoveryCandidate || 0)}`);
      console.log("ERROR=NONE");
    } catch (error: any) {
      console.log("RECOVERY=FAIL");
      console.log(`DETAIL=${String(error?.message || error).replace(/[\\r\\n\\t]+/g, " ").slice(0, 1200)}`);
      console.log("ERROR=EVOLUTION_MEDIA_RECOVERY_FAILED");
    }

    console.log("DB_WRITES=0");
    console.log("DRIVE_WRITES=0");
    console.log("SOURCE_WRITES=0");
  } finally {
    await db.end();
  }
}

main().catch(error => {
  console.error("DIAGNOSTIC_ERROR=" + String(error?.message || error));
  process.exitCode = 1;
});
''', encoding="utf-8")

print("PATCH=PASS")
print("TDM_MEDIA_DIAGNOSTIC=V1_2")
print("DETAILED_EVOLUTION_ERROR=YES")
print("READ_ONLY_DIAGNOSTIC=YES")
print("SOURCE_WRITES=0")
print("DRIVE_WRITES=0")
print("FILES_CHANGED=2")
print(f"BACKUP={backup}")
print("ERROR=NONE")
