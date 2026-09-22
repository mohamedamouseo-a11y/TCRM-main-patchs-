#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import os, shutil, textwrap

ROOT = Path(os.environ.get("TCRM_ROOT", "/var/www/TCRM-MAIN"))
MIGRATIONS = ROOT / "drizzle/migrations"
SCRIPTS = ROOT / "scripts"

if not ROOT.exists():
    raise SystemExit(f"ERROR=TCRM_ROOT_NOT_FOUND:{ROOT}")
if not MIGRATIONS.exists() or not SCRIPTS.exists():
    raise SystemExit("ERROR=TCRM_LAYOUT_INVALID")

migration = MIGRATIONS / "20260922_tdm_memory_vault_foundation_v1.sql"
runner = SCRIPTS / "apply-tdm-memory-vault-foundation-v1-migration.ts"
verify = SCRIPTS / "verify-tdm-memory-vault-foundation-v1.mjs"

backup = ROOT / ".patch-backups" / f"tdm-phase1-memory-vault-v1-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup.mkdir(parents=True, exist_ok=True)

for p in (migration, runner, verify):
    if p.exists():
        shutil.copy2(p, backup / p.name)

migration_sql = r"""
-- TDM PHASE 1 — MEMORY VAULT FOUNDATION V1
-- Foundation only: no reads from whatsapp_messages, no backfill, no runtime hooks.

CREATE TABLE IF NOT EXISTS `tdm_memory_records` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `source` VARCHAR(32) NOT NULL DEFAULT 'whatsapp',
  `source_session_id` INT NULL,
  `source_session_key` VARCHAR(120) NOT NULL,
  `source_account_phone` VARCHAR(50) NULL,
  `source_chat_id` INT NULL,
  `source_message_row_id` BIGINT UNSIGNED NULL,
  `source_message_id` VARCHAR(255) NOT NULL,
  `conversation_jid` VARCHAR(255) NOT NULL,
  `conversation_type` VARCHAR(32) NULL,
  `conversation_name` VARCHAR(255) NULL,
  `direction` ENUM('Inbound','Outbound') NOT NULL,
  `sender_jid` VARCHAR(255) NULL,
  `sender_name` VARCHAR(255) NULL,
  `recipient_jid` VARCHAR(255) NULL,
  `message_type` VARCHAR(50) NULL,
  `body` LONGTEXT NULL,
  `quoted_message_id` VARCHAR(255) NULL,
  `quoted_body` LONGTEXT NULL,
  `occurred_at` DATETIME(3) NULL,
  `source_created_at` DATETIME(3) NULL,
  `source_payload` JSON NULL,
  `source_payload_sha256` CHAR(64) NULL,
  `captured_via` ENUM('realtime','backfill','import') NOT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `tdm_memory_records_source_message_unique` (`source`,`source_session_key`,`source_message_id`),
  KEY `idx_tdm_memory_records_source_row` (`source_message_row_id`),
  KEY `idx_tdm_memory_records_session_time` (`source_session_key`,`occurred_at`,`id`),
  KEY `idx_tdm_memory_records_conversation_time` (`conversation_jid`,`occurred_at`,`id`),
  KEY `idx_tdm_memory_records_created` (`created_at`,`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
--> statement-breakpoint

CREATE TABLE IF NOT EXISTS `tdm_memory_media` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `memory_record_id` BIGINT UNSIGNED NOT NULL,
  `ordinal` INT NOT NULL DEFAULT 0,
  `media_kind` VARCHAR(32) NULL,
  `mime_type` VARCHAR(120) NULL,
  `file_name` VARCHAR(255) NULL,
  `file_size` BIGINT UNSIGNED NULL,
  `duration_seconds` INT NULL,
  `source_media_url` TEXT NULL,
  `source_drive_file_id` VARCHAR(255) NULL,
  `source_storage_account_id` INT NULL,
  `canonical_drive_file_id` VARCHAR(255) NULL,
  `canonical_storage_account_id` INT NULL,
  `content_sha256` CHAR(64) NULL,
  `archive_state` ENUM('pending','archived','failed') NOT NULL DEFAULT 'pending',
  `archive_error` VARCHAR(500) NULL,
  `archived_at` DATETIME(3) NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `tdm_memory_media_record_ordinal_unique` (`memory_record_id`,`ordinal`),
  KEY `idx_tdm_memory_media_archive_state` (`archive_state`,`id`),
  KEY `idx_tdm_memory_media_canonical_drive` (`canonical_drive_file_id`),
  KEY `idx_tdm_memory_media_source_drive` (`source_drive_file_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
--> statement-breakpoint

CREATE TABLE IF NOT EXISTS `tdm_archive_segments` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `source` VARCHAR(32) NOT NULL DEFAULT 'whatsapp',
  `source_session_key` VARCHAR(120) NOT NULL,
  `conversation_jid` VARCHAR(255) NOT NULL,
  `period_key` VARCHAR(16) NOT NULL,
  `segment_no` INT NOT NULL,
  `format` VARCHAR(32) NOT NULL DEFAULT 'ndjson',
  `state` ENUM('building','sealed','failed') NOT NULL DEFAULT 'building',
  `record_count` INT NOT NULL DEFAULT 0,
  `uncompressed_bytes` BIGINT UNSIGNED NOT NULL DEFAULT 0,
  `content_sha256` CHAR(64) NULL,
  `drive_file_id` VARCHAR(255) NULL,
  `storage_account_id` INT NULL,
  `first_occurred_at` DATETIME(3) NULL,
  `last_occurred_at` DATETIME(3) NULL,
  `sealed_at` DATETIME(3) NULL,
  `last_error` VARCHAR(500) NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `tdm_archive_segments_scope_unique` (`source`,`source_session_key`,`conversation_jid`,`period_key`,`segment_no`),
  KEY `idx_tdm_archive_segments_state` (`state`,`id`),
  KEY `idx_tdm_archive_segments_drive` (`drive_file_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
--> statement-breakpoint

CREATE TABLE IF NOT EXISTS `tdm_archive_memberships` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `memory_record_id` BIGINT UNSIGNED NOT NULL,
  `archive_segment_id` BIGINT UNSIGNED NOT NULL,
  `entry_no` INT NOT NULL,
  `entry_sha256` CHAR(64) NOT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `tdm_archive_memberships_record_unique` (`memory_record_id`),
  UNIQUE KEY `tdm_archive_memberships_segment_entry_unique` (`archive_segment_id`,`entry_no`),
  KEY `idx_tdm_archive_memberships_segment` (`archive_segment_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
--> statement-breakpoint

CREATE TABLE IF NOT EXISTS `tdm_archive_jobs` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `dedupe_key` VARCHAR(255) NOT NULL,
  `job_type` ENUM('message_manifest','media_archive','reconcile') NOT NULL,
  `memory_record_id` BIGINT UNSIGNED NULL,
  `media_id` BIGINT UNSIGNED NULL,
  `state` ENUM('queued','processing','retry','completed','dead') NOT NULL DEFAULT 'queued',
  `attempt_count` INT NOT NULL DEFAULT 0,
  `available_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `lease_token` VARCHAR(64) NULL,
  `lease_expires_at` DATETIME(3) NULL,
  `last_error` VARCHAR(1000) NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `tdm_archive_jobs_dedupe_unique` (`dedupe_key`),
  KEY `idx_tdm_archive_jobs_ready` (`state`,`available_at`,`id`),
  KEY `idx_tdm_archive_jobs_lease` (`state`,`lease_expires_at`,`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
--> statement-breakpoint

CREATE TABLE IF NOT EXISTS `tdm_checkpoints` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `source` VARCHAR(32) NOT NULL DEFAULT 'whatsapp',
  `source_session_key` VARCHAR(120) NOT NULL,
  `pipeline` ENUM('shadow_capture','historical_backfill','reconciliation') NOT NULL,
  `cursor_type` VARCHAR(32) NULL,
  `cursor_value` VARCHAR(512) NULL,
  `last_source_message_row_id` BIGINT UNSIGNED NULL,
  `last_source_message_id` VARCHAR(255) NULL,
  `last_occurred_at` DATETIME(3) NULL,
  `metadata` JSON NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `tdm_checkpoints_scope_unique` (`source`,`source_session_key`,`pipeline`),
  KEY `idx_tdm_checkpoints_pipeline` (`pipeline`,`updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
""".strip() + "\n"

runner_ts = r"""
import fs from "node:fs";
import path from "node:path";
import { config } from "dotenv";
import mysql, { type RowDataPacket } from "mysql2/promise";

config({ path: path.join(process.cwd(), ".env"), override: false });

const FILE = "drizzle/migrations/20260922_tdm_memory_vault_foundation_v1.sql";
const EXPECTED = [
  "tdm_memory_records",
  "tdm_memory_media",
  "tdm_archive_segments",
  "tdm_archive_memberships",
  "tdm_archive_jobs",
  "tdm_checkpoints",
];
const APPLY = process.argv.includes("--apply");
const CONFIRM = process.argv.includes("--confirm=APPLY_TDM_PHASE1");

if (!process.env.DATABASE_URL) throw new Error("DATABASE_URL is required");
if (APPLY && !CONFIRM) throw new Error("Use --confirm=APPLY_TDM_PHASE1 with --apply");

const sqlText = fs.readFileSync(path.join(process.cwd(), FILE), "utf8");
const statements = sqlText
  .split(/-->\s*statement-breakpoint/g)
  .map(s => s.split("\n").filter(line => !line.trim().startsWith("--")).join("\n").trim())
  .filter(Boolean);

if (statements.length !== EXPECTED.length) {
  throw new Error(`Expected ${EXPECTED.length} CREATE TABLE statements, got ${statements.length}`);
}

for (const [i, statement] of statements.entries()) {
  const normalized = statement.replace(/\s+/g, " ").trim();
  if (!/^CREATE TABLE IF NOT EXISTS `tdm_[a-z0-9_]+` \(/i.test(normalized)) {
    throw new Error(`Unsafe statement ${i + 1}`);
  }
  const forbidden = normalized.match(/\b(DROP|ALTER|INSERT|UPDATE|DELETE|TRUNCATE|REPLACE|GRANT|REVOKE)\b/i);
  if (forbidden) throw new Error(`Forbidden SQL keyword: ${forbidden[1]}`);
}

const db = await mysql.createConnection(process.env.DATABASE_URL);
try {
  const [beforeRows] = await db.query<RowDataPacket[]>(
    `SELECT TABLE_NAME FROM information_schema.TABLES
      WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME IN (${EXPECTED.map(() => "?").join(",")})`,
    EXPECTED,
  );
  const before = beforeRows.map(r => String(r.TABLE_NAME)).sort();
  console.log(`TDM_PHASE1_MODE=${APPLY ? "APPLY" : "DRY_RUN"}`);
  console.log(`STATEMENTS=${statements.length}`);
  console.log(`EXISTING_TABLES=${before.join(",") || "NONE"}`);

  if (!APPLY) {
    console.log("SAFE_DDL=YES");
    console.log("CHANGES=0");
    process.exit(0);
  }

  for (const statement of statements) await db.query(statement);

  const [afterRows] = await db.query<RowDataPacket[]>(
    `SELECT TABLE_NAME FROM information_schema.TABLES
      WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME IN (${EXPECTED.map(() => "?").join(",")})`,
    EXPECTED,
  );
  const after = afterRows.map(r => String(r.TABLE_NAME)).sort();
  const missing = EXPECTED.filter(t => !after.includes(t));
  if (missing.length) throw new Error(`Missing TDM tables: ${missing.join(",")}`);

  console.log("MIGRATION=PASS");
  console.log(`TDM_TABLES=${after.length}`);
  console.log("SOURCE_TABLES_TOUCHED=NO");
  console.log("RUNTIME_HOOKS=NO");
  console.log("BACKFILL=NO");
  console.log("ERROR=NONE");
} finally {
  await db.end();
}
""".strip() + "\n"

verify_js = r"""
import "dotenv/config";
import mysql from "mysql2/promise";

const EXPECTED = [
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
  const [tables] = await db.query(
    `SELECT TABLE_NAME
       FROM information_schema.TABLES
      WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME IN (${EXPECTED.map(() => "?").join(",")})`,
    EXPECTED,
  );
  const names = tables.map(r => String(r.TABLE_NAME)).sort();
  const missing = EXPECTED.filter(t => !names.includes(t));

  const counts = {};
  for (const table of EXPECTED) {
    const [rows] = await db.query(`SELECT COUNT(*) AS c FROM \`${table}\``);
    counts[table] = Number(rows[0]?.c || 0);
  }

  const [fkRows] = await db.query(
    `SELECT TABLE_NAME, REFERENCED_TABLE_NAME
       FROM information_schema.KEY_COLUMN_USAGE
      WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME LIKE 'tdm\\_%'
        AND REFERENCED_TABLE_NAME IS NOT NULL`
  );

  const [recordCols] = await db.query(
    `SELECT COLUMN_NAME
       FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'tdm_memory_records'
      ORDER BY ORDINAL_POSITION`
  );
  const recordColumnNames = recordCols.map(r => String(r.COLUMN_NAME));
  const immutableShape = !recordColumnNames.includes("updated_at");

  console.log(`TDM_PHASE1_VERIFY=${missing.length ? "FAIL" : "PASS"}`);
  console.log(`TABLES=${names.length}/${EXPECTED.length}`);
  console.log(`MISSING=${missing.join(",") || "NONE"}`);
  console.log(`EMPTY_FOUNDATION=${Object.values(counts).every(v => v === 0) ? "YES" : "NO"}`);
  console.log(`MEMORY_RECORD_APPEND_ONLY_SHAPE=${immutableShape ? "YES" : "NO"}`);
  console.log(`SOURCE_TABLE_FK_DEPENDENCY=${fkRows.length ? "YES" : "NO"}`);
  console.log(`COUNTS=${JSON.stringify(counts)}`);
  console.log(`ERROR=${missing.length ? "MISSING_TABLES" : "NONE"}`);
  if (missing.length) process.exitCode = 2;
} finally {
  await db.end();
}
""".strip() + "\n"

migration.write_text(migration_sql, encoding="utf-8")
runner.write_text(runner_ts, encoding="utf-8")
verify.write_text(verify_js, encoding="utf-8")

print("PATCH=PASS")
print("TDM_PHASE=1_MEMORY_VAULT_FOUNDATION")
print("TABLES=6")
print("WHATSAPP_FLOW_CHANGED=NO")
print("DARWISH_RUNTIME_CHANGED=NO")
print("BACKFILL=NO")
print("UI_CHANGED=NO")
print("FILES_CHANGED=3")
print(f"BACKUP={backup}")
print("ERROR=NONE")
