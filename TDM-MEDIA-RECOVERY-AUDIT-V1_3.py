#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import os, shutil

ROOT = Path(os.environ.get("TCRM_ROOT", "/var/www/TCRM-MAIN"))
SCRIPT = ROOT / "scripts/audit-tdm-media-recovery-v1.ts"
GDFS = ROOT / "server/services/googleDriveFileStorage.ts"

if not GDFS.exists():
    raise SystemExit(f"ERROR=MISSING:{GDFS}")

backup = ROOT / ".patch-backups" / f"tdm-media-recovery-audit-v1-3-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup.mkdir(parents=True, exist_ok=True)
if SCRIPT.exists():
    shutil.copy2(SCRIPT, backup / SCRIPT.name)

SCRIPT.write_text(r'''import "dotenv/config";
import mysql, { type RowDataPacket } from "mysql2/promise";
import { listStoredGoogleDriveFilesByAppPropertiesPage } from "../server/services/googleDriveFileStorage";

const argv = process.argv.slice(2);
const arg = (name: string) => {
  const hit = argv.find(v => v.startsWith(`--${name}=`));
  return hit ? hit.slice(name.length + 3) : null;
};

const sessionArg = String(arg("session") || "").trim();
const failedMessageId = String(arg("message-id") || "").trim();

if (!process.env.DATABASE_URL) throw new Error("DATABASE_URL is required");
if (!sessionArg) throw new Error("Use --session=<session id or session key>");

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
    const sessionId = Number(session.id);
    const sessionKey = String(session.sessionKey);

    const [queueRows] = await db.query<RowDataPacket[]>(
      `SELECT
         COUNT(*) AS totalJobs,
         SUM(j.state='queued') AS queued,
         SUM(j.state='retry') AS retryJobs,
         SUM(j.state='processing') AS processing,
         SUM(j.state='completed') AS completed,
         SUM(j.state='dead') AS deadJobs,
         SUM(mm.source_drive_file_id IS NOT NULL) AS sourceDrivePointers,
         SUM(mm.canonical_drive_file_id IS NOT NULL) AS canonicalPointers
       FROM tdm_archive_jobs j
       JOIN tdm_memory_media mm ON mm.id=j.media_id
       JOIN tdm_memory_records mr ON mr.id=j.memory_record_id
      WHERE j.job_type='media_archive'
        AND mr.source_session_key=?`,
      [sessionKey],
    );

    const [localRows] = await db.query<RowDataPacket[]>(
      `SELECT
         COUNT(*) AS localMatches,
         SUM(wm.media_drive_file_id IS NOT NULL) AS localDrivePointers,
         SUM(wm.media_url IS NOT NULL AND wm.media_url <> '') AS localMediaUrls,
         SUM(wm.raw_payload IS NOT NULL) AS localRawPayloads
       FROM tdm_archive_jobs j
       JOIN tdm_memory_media mm ON mm.id=j.media_id
       JOIN tdm_memory_records mr ON mr.id=j.memory_record_id
       JOIN whatsapp_messages wm
         ON wm.session_id=?
        AND wm.message_id=mr.source_message_id
      WHERE j.job_type='media_archive'
        AND mr.source_session_key=?
        AND j.state IN ('queued','retry','processing')`,
      [sessionId, sessionKey],
    );

    const [pendingRows] = await db.query<RowDataPacket[]>(
      `SELECT mr.source_message_id AS messageId
       FROM tdm_archive_jobs j
       JOIN tdm_memory_media mm ON mm.id=j.media_id
       JOIN tdm_memory_records mr ON mr.id=j.memory_record_id
      WHERE j.job_type='media_archive'
        AND mr.source_session_key=?
        AND j.state IN ('queued','retry','processing')
        AND mm.canonical_drive_file_id IS NULL`,
      [sessionKey],
    );
    const pendingIds = new Set(
      pendingRows.map(row => String(row.messageId || "").trim()).filter(Boolean),
    );

    let pageToken: string | null = null;
    let pages = 0;
    let driveFiles = 0;
    let driveFilesWithMessageId = 0;
    let matchedPending = 0;
    let failedMessageDriveMatch = false;
    const matchedIds = new Set<string>();

    do {
      const page = await listStoredGoogleDriveFilesByAppPropertiesPage(
        { source: "tcrm-whatsapp", sessionId: String(sessionId) },
        { limit: 200, pageToken },
      );
      pages += 1;
      driveFiles += page.files.length;
      for (const file of page.files) {
        const messageId = String(file.appProperties?.messageId || "").trim();
        if (!messageId) continue;
        driveFilesWithMessageId += 1;
        if (pendingIds.has(messageId)) {
          matchedIds.add(messageId);
        }
        if (failedMessageId && messageId === failedMessageId) {
          failedMessageDriveMatch = true;
        }
      }
      pageToken = page.nextPageToken;
      if (pages >= 100) throw new Error("Drive audit exceeded 100 pages; stop and review scope");
    } while (pageToken);

    matchedPending = matchedIds.size;
    const queue = queueRows[0] || {};
    const local = localRows[0] || {};
    const pendingTotal = pendingIds.size;
    const evolutionOnly = Math.max(0, pendingTotal - matchedPending);

    console.log("TDM_MEDIA_RECOVERY_AUDIT=PASS");
    console.log(`SESSION_ID=${sessionId}`);
    console.log(`SESSION_KEY=${sessionKey}`);
    console.log(`TOTAL_MEDIA_JOBS=${Number(queue.totalJobs || 0)}`);
    console.log(`QUEUED=${Number(queue.queued || 0)}`);
    console.log(`RETRY=${Number(queue.retryJobs || 0)}`);
    console.log(`PROCESSING=${Number(queue.processing || 0)}`);
    console.log(`COMPLETED=${Number(queue.completed || 0)}`);
    console.log(`DEAD=${Number(queue.deadJobs || 0)}`);
    console.log(`TDM_SOURCE_DRIVE_POINTERS=${Number(queue.sourceDrivePointers || 0)}`);
    console.log(`TDM_CANONICAL_POINTERS=${Number(queue.canonicalPointers || 0)}`);
    console.log(`LOCAL_DB_MATCHES=${Number(local.localMatches || 0)}`);
    console.log(`LOCAL_DB_DRIVE_POINTERS=${Number(local.localDrivePointers || 0)}`);
    console.log(`LOCAL_DB_MEDIA_URLS=${Number(local.localMediaUrls || 0)}`);
    console.log(`LOCAL_DB_RAW_PAYLOADS=${Number(local.localRawPayloads || 0)}`);
    console.log(`PENDING_UNIQUE_MESSAGE_IDS=${pendingTotal}`);
    console.log(`DRIVE_SCAN_PAGES=${pages}`);
    console.log(`DRIVE_SCAN_FILES=${driveFiles}`);
    console.log(`DRIVE_FILES_WITH_MESSAGE_ID=${driveFilesWithMessageId}`);
    console.log(`DRIVE_MATCHED_PENDING=${matchedPending}`);
    console.log(`EVOLUTION_ONLY_PENDING=${evolutionOnly}`);
    console.log(`FAILED_MESSAGE_DRIVE_MATCH=${failedMessageDriveMatch ? "YES" : "NO"}`);
    console.log("DB_WRITES=0");
    console.log("DRIVE_WRITES=0");
    console.log("SOURCE_WRITES=0");
    console.log("ERROR=NONE");
  } finally {
    await db.end();
  }
}

main().catch(error => {
  console.error("TDM_MEDIA_RECOVERY_AUDIT=FAIL");
  console.error("ERROR=" + String(error?.message || error).replace(/[\\r\\n\\t]+/g, " ").slice(0, 1000));
  process.exitCode = 1;
});
''', encoding="utf-8")

print("PATCH=PASS")
print("TDM_MEDIA_RECOVERY_AUDIT=V1_3")
print("READ_ONLY=YES")
print("DB_WRITES=0")
print("DRIVE_WRITES=0")
print("SOURCE_WRITES=0")
print("FILES_CHANGED=1")
print(f"BACKUP={backup}")
print("ERROR=NONE")
