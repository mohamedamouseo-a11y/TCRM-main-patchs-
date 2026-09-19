#!/usr/bin/env python3
from pathlib import Path

ROOT = Path("/var/www/TCRM-MAIN")
changed = []

def patch(path, old, new, required=True):
    p = ROOT / path
    s = p.read_text()
    if new in s:
        return
    if old not in s:
        if required:
            raise SystemExit(f"ANCHOR_NOT_FOUND:{path}")
        return
    p.write_text(s.replace(old, new, 1))
    changed.append(path)

# 1) Drive-only CRM uploads must use the multi-Drive pool.
patch(
    "server/services/crmFileStorage.ts",
    '''export async function storeCrmFileDriveOnly(input: StoreCrmFileInput) {
  const { uploadStoredFileToGoogleDrive } = await import("./googleDriveFileStorage");
  const driveResult = await uploadStoredFileToGoogleDrive({''',
    '''export async function storeCrmFileDriveOnly(input: StoreCrmFileInput) {
  const { uploadStoredFileViaGoogleDrivePool } = await import("./googleDriveStoragePool");
  const driveResult = await uploadStoredFileViaGoogleDrivePool({'''
)

patch(
    "server/services/crmFileStorage.ts",
    '''    driveFileId: driveResult.driveFileId ?? null,
    driveUrl: driveResult.driveUrl ?? null,
    driveUploadStatus: "uploaded" as const,''',
    '''    driveFileId: driveResult.driveFileId ?? null,
    storageAccountId: driveResult.storageAccountId ?? null,
    driveUrl: driveResult.driveUrl ?? null,
    driveUploadStatus: "uploaded" as const,'''
)

# 2) Fix account-aware Drive reads without a static circular import.
p = ROOT / "server/services/googleDriveFileStorage.ts"
s = p.read_text()
if "async function resolvePoolAccountSettings(" not in s:
    anchor = '''const MAX_OAUTH_STATES = 5;
'''
    repl = '''const MAX_OAUTH_STATES = 5;

async function resolvePoolAccountSettings(storageAccountId?: number | null) {
  const { getPoolAccountSettings } = await import("./googleDriveStoragePool");
  return getPoolAccountSettings(storageAccountId);
}
'''
    if anchor not in s:
        raise SystemExit("ANCHOR_NOT_FOUND:googleDriveFileStorage helper")
    s = s.replace(anchor, repl, 1)
    s = s.replace("await getPoolAccountSettings(", "await resolvePoolAccountSettings(")
    p.write_text(s)
    changed.append("server/services/googleDriveFileStorage.ts")

patch(
    "server/services/googleDriveFileStorage.ts",
    '''  const metadata = await getStoredGoogleDriveFileMetadata(fileId);
  const range = parseGoogleDriveByteRangeHeader(rangeHeader, metadata.size);
  const drive = await getDriveClient();''',
    '''  const settings = await resolvePoolAccountSettings(storageAccountId);
  const metadata = await getStoredGoogleDriveFileMetadata(fileId, storageAccountId);
  const range = parseGoogleDriveByteRangeHeader(rangeHeader, metadata.size);
  const drive = await getDriveClient(settings);'''
)

# 3) Felfel must persist the account that actually stores the recording.
patch(
    "server/services/felfel/felfelCrmMeetingService.ts",
    '''        driveFileId: String(existing.driveFileId),
        driveUrl: existing.driveUrl || null,''',
    '''        driveFileId: String(existing.driveFileId),
        storageAccountId: Number(existing.storageAccountId || 0) || null,
        driveUrl: existing.driveUrl || null,'''
)

patch(
    "server/services/felfel/felfelCrmMeetingService.ts",
    '''        driveFileId: stored.driveFileId,
        driveUrl: stored.driveUrl || null,''',
    '''        driveFileId: stored.driveFileId,
        storageAccountId: Number(stored.storageAccountId || 0) || null,
        driveUrl: stored.driveUrl || null,'''
)

patch(
    "server/services/felfel/felfelCrmMeetingService.ts",
    '''  const video = media.find((item) => item.mediaType === "video") || null;
  const audio = media.find((item) => item.mediaType === "audio") || null;
  const audioReady = Boolean(audio?.driveFileId);''',
    '''  const video = media.find((item) => item.mediaType === "video") || null;
  const audio = media.find((item) => item.mediaType === "audio") || null;
  const storageAccountId = Number(video?.storageAccountId || audio?.storageAccountId || 0) || null;
  const audioReady = Boolean(audio?.driveFileId);'''
)

patch(
    "server/services/felfel/felfelCrmMeetingService.ts",
    '''    driveFileId: video?.driveFileId || audio?.driveFileId || null,
    driveUrl: video?.driveUrl || video?.protectedUrl || audio?.driveUrl || audio?.protectedUrl || null,''',
    '''    driveFileId: video?.driveFileId || audio?.driveFileId || null,
    storageAccountId,
    driveUrl: video?.driveUrl || video?.protectedUrl || audio?.driveUrl || audio?.protectedUrl || null,'''
)

patch(
    "server/services/felfel/felfelCrmMeetingService.ts",
    '''      mediaType: item.mediaType,
      protectedUrl: item.protectedUrl || null,''',
    '''      mediaType: item.mediaType,
      storageAccountId: item.storageAccountId || null,
      protectedUrl: item.protectedUrl || null,'''
)

# Both DB update paths: recording-only retry + first processing.
p = ROOT / "server/services/felfel/felfelCrmMeetingService.ts"
s = p.read_text()
needle = '''recordingDriveFileId: recording.driveFileId || null,
        recordingDriveUrl: recording.driveUrl || null,'''
replacement = '''recordingDriveFileId: recording.driveFileId || null,
        recordingStorageAccountId: recording.storageAccountId || null,
        recordingDriveUrl: recording.driveUrl || null,'''
count = s.count(needle)
if count:
    s = s.replace(needle, replacement)
    p.write_text(s)
    if "server/services/felfel/felfelCrmMeetingService.ts" not in changed:
        changed.append("server/services/felfel/felfelCrmMeetingService.ts")

marker = ROOT / ".felfel_multidrive_recording_v2"
marker.write_text("\n".join(changed) + "\n")
print("PATCH_OK=" + ",".join(changed))
