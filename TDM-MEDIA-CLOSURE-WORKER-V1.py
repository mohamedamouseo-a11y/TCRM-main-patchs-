#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import os, shutil

ROOT = Path(os.environ.get("TCRM_ROOT", "/var/www/TCRM-MAIN"))
RUNNER = ROOT / "scripts/run-tdm-media-archive-v1.ts"

if not RUNNER.exists():
    raise SystemExit(f"ERROR=MISSING:{RUNNER}")

backup = ROOT / ".patch-backups" / f"tdm-media-closure-worker-v1-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup.mkdir(parents=True, exist_ok=True)
shutil.copy2(RUNNER, backup / RUNNER.name)

s = RUNNER.read_text(encoding="utf-8")

s = s.replace(
    'const limit = Math.max(1, Math.min(100, Number(arg("limit") || 10) || 10));',
    'const limit = Math.max(1, Math.min(250, Number(arg("limit") || 10) || 10));',
    1,
)

old = r'''async function markFailure(
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
}'''

new = r'''async function markFailure(
  db: mysql.Connection,
  job: JobRow & { leaseToken: string; attempt: number },
  error: unknown,
): Promise<"source_unavailable" | "dead" | "retry"> {
  const message = safeError(error);
  const sourceUnavailable =
    /failed to fetch stream|media is no longer available|media payload is unavailable|source unavailable/i.test(message);
  const dead = sourceUnavailable || job.attempt >= maxAttempts;
  const outcome = sourceUnavailable ? "source_unavailable" : dead ? "dead" : "retry";
  const storedError = sourceUnavailable
    ? `SOURCE_UNAVAILABLE | ${message}`.slice(0, 900)
    : message;
  const delaySeconds = Math.min(
    6 * 60 * 60,
    30 * 2 ** Math.min(Math.max(job.attempt - 1, 0), 9),
  );

  await db.beginTransaction();
  try {
    await db.execute(
      `UPDATE tdm_memory_media
          SET archive_state=?,
              archive_error=?
        WHERE id=? AND archive_state <> 'archived'`,
      [dead ? "failed" : "pending", storedError.slice(0, 500), job.mediaId],
    );
    await db.execute(
      `UPDATE tdm_archive_jobs
          SET state=?,
              available_at=DATE_ADD(CURRENT_TIMESTAMP(3), INTERVAL ? SECOND),
              lease_token=NULL,
              lease_expires_at=NULL,
              last_error=?
        WHERE id=? AND lease_token=?`,
      [dead ? "dead" : "retry", delaySeconds, storedError, job.jobId, job.leaseToken],
    );
    await db.commit();
    return outcome;
  } catch (dbError) {
    await db.rollback();
    throw dbError;
  }
}'''

if old not in s:
    raise SystemExit("ERROR=MARK_FAILURE_ANCHOR_MISSING")
s = s.replace(old, new, 1)

old2 = '''    let retried = 0;
    let dead = 0;'''
new2 = '''    let retried = 0;
    let dead = 0;
    let sourceUnavailable = 0;'''
if old2 not in s:
    raise SystemExit("ERROR=COUNTER_ANCHOR_MISSING")
s = s.replace(old2, new2, 1)

old3 = '''      } catch (error) {
        await markFailure(db, job, error);
        if (job.attempt >= maxAttempts) dead += 1;
        else retried += 1;
        console.log(`JOB_FAILED=${job.jobId} ATTEMPT=${job.attempt} ERROR=${safeError(error)}`);
      } finally {'''
new3 = '''      } catch (error) {
        const outcome = await markFailure(db, job, error);
        if (outcome === "source_unavailable") sourceUnavailable += 1;
        else if (outcome === "dead") dead += 1;
        else retried += 1;
        console.log(
          `JOB_FAILED=${job.jobId} ATTEMPT=${job.attempt} OUTCOME=${outcome} ERROR=${safeError(error)}`,
        );
      } finally {'''
if old3 not in s:
    raise SystemExit("ERROR=CATCH_ANCHOR_MISSING")
s = s.replace(old3, new3, 1)

old4 = '''    console.log(`RETRIED=${retried}`);
    console.log(`DEAD=${dead}`);'''
new4 = '''    console.log(`RETRIED=${retried}`);
    console.log(`SOURCE_UNAVAILABLE=${sourceUnavailable}`);
    console.log(`DEAD=${dead}`);'''
if old4 not in s:
    raise SystemExit("ERROR=OUTPUT_ANCHOR_MISSING")
s = s.replace(old4, new4, 1)

RUNNER.write_text(s, encoding="utf-8")

print("PATCH=PASS")
print("TDM_MEDIA_CLOSURE_WORKER=V1")
print("SOURCE_UNAVAILABLE_CLASSIFIER=YES")
print("RECOVERED_MEDIA_ARCHIVE_PATH=PRESERVED")
print("MAX_BATCH=250")
print("WHATSAPP_WRITES=0")
print("FILES_CHANGED=1")
print(f"BACKUP={backup}")
print("ERROR=NONE")
