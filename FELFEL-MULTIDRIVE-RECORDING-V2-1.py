#!/usr/bin/env python3
from pathlib import Path

p = Path("/var/www/TCRM-MAIN/server/services/felfel/felfelCrmMeetingService.ts")
s = p.read_text()

old = '''      recordingStatus: recording.status,
      recordingDriveFileId: recording.driveFileId || null,
      recordingDriveUrl: recording.driveUrl || null,
'''
new = '''      recordingStatus: recording.status,
      recordingDriveFileId: recording.driveFileId || null,
      recordingStorageAccountId: recording.storageAccountId || null,
      recordingDriveUrl: recording.driveUrl || null,
'''

# Only patch the remaining initial-processing occurrence.
if s.count("recordingStorageAccountId: recording.storageAccountId || null") >= 2:
    print("PATCH_OK=already_applied")
    raise SystemExit(0)

idx = s.rfind(old)
if idx < 0:
    raise SystemExit("ANCHOR_NOT_FOUND")

s = s[:idx] + s[idx:].replace(old, new, 1)
p.write_text(s)
print("PATCH_OK=initial_processing_storage_account")
