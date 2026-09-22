#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import os, shutil

ROOT = Path(os.environ.get("TCRM_ROOT", "/var/www/TCRM-MAIN"))
GDFS = ROOT / "server/services/googleDriveFileStorage.ts"
POOL = ROOT / "server/services/googleDriveStoragePool.ts"
TDM_DIR = ROOT / "server/services/darwish/tdm"
TDM = TDM_DIR / "tdmDriveArchiveStorage.ts"
VERIFY = ROOT / "scripts/verify-tdm-drive-archive-v1.ts"

for p in (GDFS, POOL):
    if not p.exists():
        raise SystemExit(f"ERROR=MISSING:{p}")

backup = ROOT / ".patch-backups" / f"tdm-phase2-drive-archive-v1-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup.mkdir(parents=True, exist_ok=True)
for p in (GDFS, POOL, TDM, VERIFY):
    if p.exists():
        shutil.copy2(p, backup / p.name)

g = GDFS.read_text(encoding="utf-8")
old_sig = '''    buffer: Buffer;
    contentType?: string | null;
    onProgress?: (uploadedBytes: number, totalBytes: number) => void | Promise<void>;
    uploadTimeoutMs?: number;
'''
new_sig = '''    buffer: Buffer;
    contentType?: string | null;
    appProperties?: Record<string, string>;
    onProgress?: (uploadedBytes: number, totalBytes: number) => void | Promise<void>;
    uploadTimeoutMs?: number;
'''
if "appProperties?: Record<string, string>;" not in g[g.find("export async function uploadStoredFileToGoogleDriveUnsafe"):g.find("export async function uploadStoredFileToGoogleDrive(", g.find("export async function uploadStoredFileToGoogleDriveUnsafe"))]:
    if old_sig not in g:
        raise SystemExit("ERROR=GDFS_UNSAFE_SIG_ANCHOR_MISSING")
    g = g.replace(old_sig, new_sig, 1)

unsafe_start = g.find("export async function uploadStoredFileToGoogleDriveUnsafe")
unsafe_end = g.find("export async function uploadStoredFileToGoogleDrive(", unsafe_start)
section = g[unsafe_start:unsafe_end]
old_req = '''    requestBody: {
      name: cleanFolderSegment(args.fileName),
      parents: folderId ? [folderId] : undefined,
    },'''
new_req = '''    requestBody: {
      name: cleanFolderSegment(args.fileName),
      parents: folderId ? [folderId] : undefined,
      ...(args.appProperties ? { appProperties: args.appProperties } : {}),
    },'''
if "appProperties: args.appProperties" not in section:
    if old_req not in section:
        raise SystemExit("ERROR=GDFS_REQUEST_BODY_ANCHOR_MISSING")
    section = section.replace(old_req, new_req, 1)
    g = g[:unsafe_start] + section + g[unsafe_end:]
GDFS.write_text(g, encoding="utf-8")

p = POOL.read_text(encoding="utf-8")
pool_start = p.find("export async function uploadStoredFileViaGoogleDrivePool")
pool_end = p.find("export async function getPoolAccountSettings", pool_start)
if pool_start < 0 or pool_end < 0:
    raise SystemExit("ERROR=POOL_UPLOAD_SECTION_MISSING")
section = p[pool_start:pool_end]
old_pool = '''  buffer: Buffer;
  contentType?: string | null;
  onProgress?: (uploadedBytes: number, totalBytes: number) => void | Promise<void>;
'''
new_pool = '''  buffer: Buffer;
  contentType?: string | null;
  appProperties?: Record<string, string>;
  onProgress?: (uploadedBytes: number, totalBytes: number) => void | Promise<void>;
'''
if "appProperties?: Record<string, string>;" not in section:
    if old_pool not in section:
        raise SystemExit("ERROR=POOL_SIG_ANCHOR_MISSING")
    section = section.replace(old_pool, new_pool, 1)
    p = p[:pool_start] + section + p[pool_end:]
POOL.write_text(p, encoding="utf-8")

TDM_DIR.mkdir(parents=True, exist_ok=True)
TDM.write_text(r'''import crypto from "node:crypto";
import { uploadStoredFileViaGoogleDrivePool } from "../../googleDriveStoragePool";

export const TDM_DRIVE_ROOT = "Tamiyouz Darwish Memory/TDM/v1";
export const TDM_DRIVE_SOURCE = "tcrm-tdm";
export const TDM_RETENTION_CLASS = "permanent";

type ArchiveScope = {
  sessionKey: string;
  conversationJid: string;
  messageId: string;
  occurredAt?: Date | string | null;
  memoryRecordId?: number | null;
};

function safeSegment(value: unknown, fallback: string, max = 96) {
  const text = String(value ?? "")
    .trim()
    .replace(/[^a-zA-Z0-9@._+-]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, max);
  return text || fallback;
}

function utcParts(value?: Date | string | null) {
  const parsed = value instanceof Date ? value : value ? new Date(value) : new Date();
  const date = Number.isFinite(parsed.getTime()) ? parsed : new Date();
  return {
    year: String(date.getUTCFullYear()),
    month: String(date.getUTCMonth() + 1).padStart(2, "0"),
  };
}

function sha256(buffer: Buffer) {
  return crypto.createHash("sha256").update(buffer).digest("hex");
}

export function buildTdmDriveStorageKey(scope: ArchiveScope, kind: "raw" | "media") {
  const { year, month } = utcParts(scope.occurredAt);
  const account = safeSegment(scope.sessionKey, "unknown-account");
  const conversation = safeSegment(scope.conversationJid, "unknown-conversation", 120);
  const bucket = kind === "raw" ? "Raw Messages" : "Media";
  return `${TDM_DRIVE_ROOT}/WhatsApp/Accounts/${account}/${year}/${month}/Conversations/${conversation}/${bucket}`;
}

export function buildTdmDriveAppProperties(
  scope: ArchiveScope,
  resource: "raw-message" | "media",
  contentSha256: string,
) {
  return {
    source: TDM_DRIVE_SOURCE,
    tdmVersion: "1",
    tdmResource: resource,
    retentionClass: TDM_RETENTION_CLASS,
    provider: "whatsapp",
    sessionKey: safeSegment(scope.sessionKey, "unknown", 60),
    messageId: safeSegment(scope.messageId, "unknown", 80),
    ...(scope.memoryRecordId ? { memoryRecordId: String(scope.memoryRecordId) } : {}),
    sha256: contentSha256,
  };
}

export async function archiveTdmRawJson(input: ArchiveScope & { rawJson: string }) {
  const buffer = Buffer.from(input.rawJson, "utf8");
  const digest = sha256(buffer);
  const result = await uploadStoredFileViaGoogleDrivePool({
    storageKey: buildTdmDriveStorageKey(input, "raw"),
    fileName: `${safeSegment(input.messageId, "message", 96)}-${digest.slice(0, 12)}.json`,
    buffer,
    contentType: "application/json",
    appProperties: buildTdmDriveAppProperties(input, "raw-message", digest),
  });
  if (result.uploadStatus !== "uploaded" || !result.driveFileId) {
    throw new Error(result.error || "TDM raw archive upload failed");
  }
  return {
    driveFileId: result.driveFileId,
    storageAccountId: result.storageAccountId,
    sha256: digest,
    bytes: buffer.length,
  };
}

export async function archiveTdmMediaBuffer(
  input: ArchiveScope & {
    buffer: Buffer;
    fileName: string;
    mimeType?: string | null;
  },
) {
  const digest = sha256(input.buffer);
  const result = await uploadStoredFileViaGoogleDrivePool({
    storageKey: buildTdmDriveStorageKey(input, "media"),
    fileName: safeSegment(input.fileName, `media-${safeSegment(input.messageId, "message", 60)}`, 140),
    buffer: input.buffer,
    contentType: input.mimeType || "application/octet-stream",
    appProperties: buildTdmDriveAppProperties(input, "media", digest),
  });
  if (result.uploadStatus !== "uploaded" || !result.driveFileId) {
    throw new Error(result.error || "TDM media archive upload failed");
  }
  return {
    driveFileId: result.driveFileId,
    storageAccountId: result.storageAccountId,
    sha256: digest,
    bytes: input.buffer.length,
  };
}

// Intentionally no delete/trash API here.
// TDM canonical archive objects are permanent and are not owned by WhatsApp retention cleanup.
''', encoding="utf-8")

VERIFY.write_text(r'''import fs from "node:fs";
import path from "node:path";
import mysql from "mysql2/promise";
import { getGoogleDrivePoolStatus } from "../server/services/googleDriveStoragePool";
import {
  TDM_DRIVE_ROOT,
  TDM_DRIVE_SOURCE,
  TDM_RETENTION_CLASS,
  buildTdmDriveAppProperties,
  buildTdmDriveStorageKey,
} from "../server/services/darwish/tdm/tdmDriveArchiveStorage";

const TABLES = [
  "tdm_memory_records",
  "tdm_memory_media",
  "tdm_archive_segments",
  "tdm_archive_memberships",
  "tdm_archive_jobs",
  "tdm_checkpoints",
];

if (!process.env.DATABASE_URL) throw new Error("DATABASE_URL is required");

const db = await mysql.createConnection(process.env.DATABASE_URL);
try {
  const [rows] = await db.query<any[]>(
    `SELECT TABLE_NAME FROM information_schema.TABLES
      WHERE TABLE_SCHEMA=DATABASE()
        AND TABLE_NAME IN (${TABLES.map(() => "?").join(",")})`,
    TABLES,
  );
  const found = rows.map(r => String(r.TABLE_NAME));
  const missing = TABLES.filter(t => !found.includes(t));

  const pool = await getGoogleDrivePoolStatus();
  const sample = {
    sessionKey: "verify-session",
    conversationJid: "201000000000@s.whatsapp.net",
    messageId: "verify-message",
    occurredAt: "2026-09-22T00:00:00Z",
  };
  const key = buildTdmDriveStorageKey(sample, "raw");
  const props = buildTdmDriveAppProperties(sample, "raw-message", "a".repeat(64));

  const indexPath = path.join(process.cwd(), "server/_core/index.ts");
  const workerPath = path.join(process.cwd(), "server/services/darwish/chatwoot/darwishWorker.ts");
  const runtimeText = [
    fs.existsSync(indexPath) ? fs.readFileSync(indexPath, "utf8") : "",
    fs.existsSync(workerPath) ? fs.readFileSync(workerPath, "utf8") : "",
  ].join("\n");
  const runtimeHooked = runtimeText.includes("tdmDriveArchiveStorage");

  const servicePath = path.join(process.cwd(), "server/services/darwish/tdm/tdmDriveArchiveStorage.ts");
  const serviceText = fs.readFileSync(servicePath, "utf8");
  const destructiveApi = /export\s+(?:async\s+)?function\s+[^\n]*(?:delete|trash)/i.test(serviceText);

  console.log(`TDM_PHASE2_VERIFY=${!missing.length && pool.ready && !runtimeHooked && !destructiveApi ? "PASS" : "FAIL"}`);
  console.log(`TDM_TABLES=${found.length}/${TABLES.length}`);
  console.log(`DRIVE_POOL_READY=${pool.ready ? "YES" : "NO"}`);
  console.log(`DRIVE_ACCOUNTS=${pool.accounts.length}`);
  console.log(`TDM_NAMESPACE=${key.startsWith(TDM_DRIVE_ROOT + "/") ? "PASS" : "FAIL"}`);
  console.log(`TDM_SOURCE=${props.source === TDM_DRIVE_SOURCE ? "PASS" : "FAIL"}`);
  console.log(`PERMANENT_RETENTION=${props.retentionClass === TDM_RETENTION_CLASS ? "PASS" : "FAIL"}`);
  console.log(`RUNTIME_HOOKED=${runtimeHooked ? "YES" : "NO"}`);
  console.log(`DELETE_API=${destructiveApi ? "YES" : "NO"}`);
  console.log("UPLOAD_SMOKE=NOT_RUN");
  console.log(`ERROR=${missing.length ? "MISSING_TDM_TABLES" : !pool.ready ? "DRIVE_POOL_NOT_READY" : runtimeHooked ? "UNEXPECTED_RUNTIME_HOOK" : destructiveApi ? "DESTRUCTIVE_API_PRESENT" : "NONE"}`);
  if (missing.length || !pool.ready || runtimeHooked || destructiveApi) process.exitCode = 2;
} finally {
  await db.end();
}
''', encoding="utf-8")

print("PATCH=PASS")
print("TDM_PHASE=2_DRIVE_ARCHIVE_FOUNDATION")
print("POOL_AWARE=YES")
print("APP_PROPERTIES=YES")
print("TDM_NAMESPACE=YES")
print("PERMANENT_RETENTION_CLASS=YES")
print("RUNTIME_HOOK=NO")
print("BACKFILL=NO")
print("UPLOADS_EXECUTED=0")
print("FILES_CHANGED=4")
print(f"BACKUP={backup}")
print("ERROR=NONE")
