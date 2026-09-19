#!/usr/bin/env python3
from pathlib import Path

ROOT = Path("/var/www/TCRM-MAIN")
changed = []

def replace_once(rel, old, new, label):
    p = ROOT / rel
    s = p.read_text()
    if new in s:
        return
    if old not in s:
        raise SystemExit(f"ANCHOR_NOT_FOUND:{label}:{rel}")
    p.write_text(s.replace(old, new, 1))
    if rel not in changed:
        changed.append(rel)

# 1) Drive-only CRM file insert: fileUrl is NOT NULL while Drive URLs are intentionally hidden/null.
p = ROOT / "server/services/crmFileStorage.ts"
s = p.read_text()

old = '''  const db = await getDb();
  if (!db) throw new Error("Database connection failed");
  const [inserted] = await db.insert(crmFiles).values({
    entityType: input.entityType,
    entityId: input.entityId === undefined || input.entityId === null ? null : String(input.entityId),
    entityKey: input.entityKey ?? null,
    category: input.category,
    fileCategory: input.fileCategory ?? null,
    description: input.description ?? null,
    fileName: input.fileName,
    fileUrl: driveResult.driveUrl ?? null,
    localUrl: null,
    storageKey: input.storageKey,
    driveFileId: driveResult.driveFileId ?? null,
    storageAccountId: driveResult.storageAccountId ?? null,
    driveUrl: driveResult.driveUrl ?? null,
    driveUploadStatus: "uploaded",
    driveUploadError: null,
    fileSize: input.buffer.length,
    fileType: input.contentType || "application/octet-stream",
    projectReferenceTaskId: input.projectReferenceTaskId ?? null,
    projectReferenceClientId: input.projectReferenceClientId ?? null,
    uploadStatus: input.uploadStatus ?? "active",
    previousFileId: input.previousFileId ?? null,
    replacedByFileId: null,
    uploadedBy: input.uploadedBy,
  } as any).$returningId();
  const crmFileId = Number((inserted as any)?.id ?? (inserted as any)?.insertId ?? 0) || null;
  return {
'''
new = '''  const db = await getDb();
  if (!db) throw new Error("Database connection failed");

  // FELFEL_MULTIDRIVE_RECORDING_V2_2
  // crm_files.fileUrl is NOT NULL, while Drive links are intentionally hidden.
  // Insert a private internal placeholder first, then replace it with the
  // authenticated CRM download URL once the row id is known.
  const internalFileUrl = driveResult.driveFileId
    ? `gdrive://${driveResult.storageAccountId ?? "legacy"}/${driveResult.driveFileId}`
    : `gdrive://pending/${input.storageKey}`;

  let crmFileId: number | null = null;
  try {
    const [inserted] = await db.insert(crmFiles).values({
      entityType: input.entityType,
      entityId: input.entityId === undefined || input.entityId === null ? null : String(input.entityId),
      entityKey: input.entityKey ?? null,
      category: input.category,
      fileCategory: input.fileCategory ?? null,
      description: input.description ?? null,
      fileName: input.fileName,
      fileUrl: internalFileUrl,
      localUrl: null,
      storageKey: input.storageKey,
      driveFileId: driveResult.driveFileId ?? null,
      storageAccountId: driveResult.storageAccountId ?? null,
      driveUrl: driveResult.driveUrl ?? null,
      driveUploadStatus: "uploaded",
      driveUploadError: null,
      fileSize: input.buffer.length,
      fileType: input.contentType || "application/octet-stream",
      projectReferenceTaskId: input.projectReferenceTaskId ?? null,
      projectReferenceClientId: input.projectReferenceClientId ?? null,
      uploadStatus: input.uploadStatus ?? "active",
      previousFileId: input.previousFileId ?? null,
      replacedByFileId: null,
      uploadedBy: input.uploadedBy,
    } as any).$returningId();

    crmFileId = Number((inserted as any)?.id ?? (inserted as any)?.insertId ?? 0) || null;
    if (!crmFileId && driveResult.driveFileId) {
      const rows = await db.select({ id: crmFiles.id })
        .from(crmFiles)
        .where(eq(crmFiles.driveFileId, String(driveResult.driveFileId)))
        .orderBy(desc(crmFiles.id))
        .limit(1);
      crmFileId = Number(rows[0]?.id ?? 0) || null;
    }
    if (!crmFileId) {
      const rows = await db.select({ id: crmFiles.id })
        .from(crmFiles)
        .where(eq(crmFiles.storageKey, input.storageKey))
        .orderBy(desc(crmFiles.id))
        .limit(1);
      crmFileId = Number(rows[0]?.id ?? 0) || null;
    }
    if (!crmFileId) throw new Error("Drive upload succeeded but CRM file row id could not be resolved");

    await db.update(crmFiles)
      .set({ fileUrl: buildProtectedCrmFileUrl(crmFileId) || internalFileUrl } as any)
      .where(eq(crmFiles.id, crmFileId));
  } catch (error) {
    if (driveResult.driveFileId) {
      await deleteStoredFileFromGoogleDrive(
        String(driveResult.driveFileId),
        driveResult.storageAccountId ?? null,
      ).catch((cleanupError) => {
        console.warn("[CrmFileStorage] orphan Drive upload cleanup failed", cleanupError instanceof Error ? cleanupError.message : cleanupError);
      });
    }
    throw error;
  }

  return {
'''
if "FELFEL_MULTIDRIVE_RECORDING_V2_2" not in s:
    if old not in s:
        raise SystemExit("ANCHOR_NOT_FOUND:drive-only-insert")
    p.write_text(s.replace(old,new,1))
    changed.append("server/services/crmFileStorage.ts")

# Ensure returned fileUrl is the authenticated CRM URL rather than null.
replace_once(
    "server/services/crmFileStorage.ts",
    '''    fileUrl: driveResult.driveUrl ?? null,
    localUrl: null,
    protectedUrl: buildProtectedCrmFileUrl(crmFileId),''',
    '''    fileUrl: buildProtectedCrmFileUrl(crmFileId),
    localUrl: null,
    protectedUrl: buildProtectedCrmFileUrl(crmFileId),''',
    "return-protected-url",
)

# 2) Protected preview must route to the Drive account that owns the file.
replace_once(
    "server/routes/crmFilePreview.ts",
    '''  streamDriveFile: (
    driveFileId: string,
    rangeHeader: string | null,
    timeoutLabel: string
  ) => Promise<DrivePreviewStream>;''',
    '''  streamDriveFile: (
    driveFileId: string,
    rangeHeader: string | null,
    timeoutLabel: string,
    storageAccountId?: number | null,
  ) => Promise<DrivePreviewStream>;''',
    "preview-dependency-signature",
)

replace_once(
    "server/routes/crmFilePreview.ts",
    '''      const driveResponse = await dependencies.streamDriveFile(
        driveFileId,
        rangeHeader,
        "CRM file secure preview stream"
      );''',
    '''      const driveResponse = await dependencies.streamDriveFile(
        driveFileId,
        rangeHeader,
        "CRM file secure preview stream",
        Number((file as any).storageAccountId || 0) || null,
      );''',
    "preview-account-routing",
)

# 3) Central Drive stream/download helpers must pass account id.
replace_once(
    "server/_core/index.ts",
    '''async function streamCrmFileFromGoogleDrive(
  driveFileId: string,
  rangeHeader: string | null,
  _timeoutLabel: string,
) {
  const response = await streamStoredFileFromGoogleDriveRange(driveFileId, rangeHeader);''',
    '''async function streamCrmFileFromGoogleDrive(
  driveFileId: string,
  rangeHeader: string | null,
  _timeoutLabel: string,
  storageAccountId?: number | null,
) {
  const response = await streamStoredFileFromGoogleDriveRange(driveFileId, rangeHeader, storageAccountId);''',
    "central-stream-account",
)

replace_once(
    "server/_core/index.ts",
    '''      const fileBuffer = await downloadStoredFileFromGoogleDrive(driveFileId, "CRM public view-only preview");''',
    '''      const fileBuffer = await downloadStoredFileFromGoogleDrive(
        driveFileId,
        "CRM public view-only preview",
        undefined,
        Number((resolvedAny.file as any).storageAccountId || 0) || null,
      );''',
    "public-share-account",
)

replace_once(
    "server/_core/index.ts",
    '''      const buffer = await downloadStoredFileFromGoogleDrive(driveFileId, "CRM file protected download");''',
    '''      const buffer = await downloadStoredFileFromGoogleDrive(
        driveFileId,
        "CRM file protected download",
        undefined,
        Number((file as any).storageAccountId || 0) || null,
      );''',
    "protected-download-account",
)

print("PATCH_OK=" + ",".join(changed))
