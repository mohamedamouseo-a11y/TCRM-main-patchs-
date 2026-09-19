import "dotenv/config";
import { eq } from "drizzle-orm";
import { getDb } from "./server/db";
import { crmMeetings } from "./drizzle/schema";
import { getGoogleDrivePoolStatus } from "./server/services/googleDriveStoragePool";
import { processLinkedFelfelMeeting, isRecordingComplete } from "./server/services/felfel/felfelCrmMeetingService";

const ids = [10, 11, 12];
const db = await getDb();
if (!db) throw new Error("DB_UNAVAILABLE");

const pool = await getGoogleDrivePoolStatus();
console.log("POOL=" + JSON.stringify({
  ready: pool.ready,
  accounts: pool.accounts.map((a:any) => ({ id:a.id, name:a.name, freeBytes:a.freeBytes, priority:a.priority })),
}));

for (const id of ids) {
  const before = (await db.select().from(crmMeetings).where(eq(crmMeetings.id, id)).limit(1))[0] as any;
  if (!before) {
    console.log(`MEETING_${id}=NOT_FOUND`);
    continue;
  }
  if (isRecordingComplete(String(before.recordingStatus || ""))) {
    console.log(`MEETING_${id}=SKIP_ALREADY_RECORDED status=${before.status} recording=${before.recordingStatus} account=${before.recordingStorageAccountId ?? "null"}`);
    continue;
  }

  // Clear only stale processing state; preserve transcript/analysis data exactly.
  await db.update(crmMeetings).set({
    status: "ended",
    processingLockUntil: null,
    processingAttempt: 0,
    failedAt: null,
    lastError: null,
  }).where(eq(crmMeetings.id, id));

  try {
    await processLinkedFelfelMeeting(id);
  } catch (e:any) {
    console.log(`MEETING_${id}_PROCESS_ERROR=${String(e?.message || e)}`);
  }

  const after = (await db.select().from(crmMeetings).where(eq(crmMeetings.id, id)).limit(1))[0] as any;
  console.log(`MEETING_${id}=status:${after?.status},recording:${after?.recordingStatus},account:${after?.recordingStorageAccountId ?? "null"},transcript:${after?.transcriptStatus},analysis:${after?.analysisStatus},recordingError:${after?.recordingError ?? "null"},lastError:${after?.lastError ?? "null"}`);
}
