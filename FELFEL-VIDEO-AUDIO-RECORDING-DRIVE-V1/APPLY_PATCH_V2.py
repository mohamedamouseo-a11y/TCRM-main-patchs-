#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import runpy
import subprocess
import sys

PATCH_ID = "FELFEL-VIDEO-AUDIO-RECORDING-DRIVE-V1-V2"
BASELINE_SHA = "90b1d4573626e0fad4c7629df1b062e939099e7e"
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
assets = pathlib.Path(__file__).resolve().parent
original = assets / "APPLY_PATCH.py"


def run(*args: str) -> str:
    p = subprocess.run(list(args), cwd=root, text=True, capture_output=True)
    if p.returncode != 0:
        sys.stdout.write(p.stdout)
        sys.stderr.write(p.stderr)
        raise SystemExit(f"Command failed ({p.returncode}): {' '.join(args)}")
    return p.stdout.strip()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected anchor exactly once, found {count}")
    return text.replace(old, new, 1)


if not original.is_file():
    raise SystemExit("Approved V1 apply script is missing")
if run("git", "rev-parse", "--show-toplevel") != str(root):
    raise SystemExit("Run from canonical TCRM root")
if run("git", "rev-parse", "HEAD") != BASELINE_SHA:
    raise SystemExit(f"{PATCH_ID} requires baseline {BASELINE_SHA}")
if run("git", "status", "--short"):
    raise SystemExit("Refusing to apply on a dirty TCRM worktree")

# Apply the reviewed V1 body first. It performs its own source/version/asset guards.
old_argv = sys.argv[:]
try:
    sys.argv = [str(original), str(root)]
    runpy.run_path(str(original), run_name="__main__")
finally:
    sys.argv = old_argv

# ---------------------------------------------------------------------------
# V2 hardening 1: MeetingRef must expose the server-returned meetingId used by
# recordingStatus/saveRecordingToDrive. This is a compile-time correctness fix.
# ---------------------------------------------------------------------------
page_path = root / "client/src/pages/FelfelPage.tsx"
page = page_path.read_text(encoding="utf-8")
page = replace_once(
    page,
    '''type MeetingRef = {\n  platform: string;\n  nativeId: string;\n''',
    '''type MeetingRef = {\n  meetingId?: string | null;\n  platform: string;\n  nativeId: string;\n''',
    "MeetingRef meetingId",
)

# Explicit acknowledgement before any recording-enabled join. This is not a
# legal-consent engine; it forces the operator to confirm they have handled the
# applicable notice/permission requirements before starting capture.
page = replace_once(
    page,
    '''  const [botName, setBotName] = useState("Felfel");\n''',
    '''  const [botName, setBotName] = useState("Felfel");\n  const [recordingConsent, setRecordingConsent] = useState(false);\n''',
    "recording acknowledgement state",
)
page = replace_once(
    page,
    '''      setFollowUpTopic("");\n      setMeetingUrl(data.meetingUrl || meetingUrl);\n''',
    '''      setFollowUpTopic("");\n      setRecordingConsent(false);\n      setMeetingUrl(data.meetingUrl || meetingUrl);\n''',
    "recording acknowledgement reset",
)
old_form = '''          <CardContent className="grid gap-4 md:grid-cols-[minmax(0,1fr)_220px_auto] md:items-end">\n            <div className="space-y-2">\n              <Label htmlFor="felfel-meeting-url">{ar ? "رابط الاجتماع" : "Meeting URL"}</Label>\n              <Input id="felfel-meeting-url" dir="ltr" value={meetingUrl} onChange={(event) => setMeetingUrl(event.target.value)} placeholder="https://meet.google.com/abc-defg-hij" aria-invalid={Boolean(meetingUrl) && !urlValid} />\n              {meetingUrl && <p className={`text-xs ${urlValid ? "text-emerald-600" : "text-destructive"}`}>{urlValid ? `${ar ? "المنصة" : "Platform"}: ${platformLabel(platform, ar)}` : (ar ? "رابط غير مدعوم. استخدم Google Meet أو Teams أو Zoom أو Jitsi." : "Unsupported link. Use Google Meet, Teams, Zoom, or Jitsi.")}</p>}\n            </div>\n            <div className="space-y-2">\n              <Label htmlFor="felfel-bot-name">{ar ? "اسم الوكيل" : "Bot name"}</Label>\n              <Input id="felfel-bot-name" value={botName} onChange={(event) => setBotName(event.target.value)} maxLength={100} />\n            </div>\n            <Button onClick={() => createMeetingM.mutate({ meetingUrl: meetingUrl.trim(), botName: botName.trim() || "Felfel" })} disabled={!urlValid || createMeetingM.isPending} className="gap-2">\n              {createMeetingM.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Mic2 className="h-4 w-4" />}\n              {ar ? "دخول الاجتماع" : "Join meeting"}\n            </Button>\n          </CardContent>\n'''
new_form = '''          <CardContent className="space-y-4">\n            <div className="grid gap-4 md:grid-cols-[minmax(0,1fr)_220px_auto] md:items-end">\n              <div className="space-y-2">\n                <Label htmlFor="felfel-meeting-url">{ar ? "رابط الاجتماع" : "Meeting URL"}</Label>\n                <Input id="felfel-meeting-url" dir="ltr" value={meetingUrl} onChange={(event) => setMeetingUrl(event.target.value)} placeholder="https://meet.google.com/abc-defg-hij" aria-invalid={Boolean(meetingUrl) && !urlValid} />\n                {meetingUrl && <p className={`text-xs ${urlValid ? "text-emerald-600" : "text-destructive"}`}>{urlValid ? `${ar ? "المنصة" : "Platform"}: ${platformLabel(platform, ar)}` : (ar ? "رابط غير مدعوم. استخدم Google Meet أو Teams أو Zoom أو Jitsi." : "Unsupported link. Use Google Meet, Teams, Zoom, or Jitsi.")}</p>}\n              </div>\n              <div className="space-y-2">\n                <Label htmlFor="felfel-bot-name">{ar ? "اسم الوكيل" : "Bot name"}</Label>\n                <Input id="felfel-bot-name" value={botName} onChange={(event) => setBotName(event.target.value)} maxLength={100} />\n              </div>\n              <Button onClick={() => createMeetingM.mutate({ meetingUrl: meetingUrl.trim(), botName: botName.trim() || "Felfel", recordingConsent: true })} disabled={!urlValid || !recordingConsent || createMeetingM.isPending} className="gap-2">\n                {createMeetingM.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Video className="h-4 w-4" />}\n                {ar ? "دخول + بدء التسجيل" : "Join + start recording"}\n              </Button>\n            </div>\n            <label className="flex cursor-pointer items-start gap-3 rounded-xl border bg-muted/20 p-3 text-sm">\n              <input type="checkbox" className="mt-1 h-4 w-4" checked={recordingConsent} onChange={(event) => setRecordingConsent(event.target.checked)} />\n              <span>{ar ? "أؤكد أنني مسؤول عن إخطار المشاركين والحصول على أي موافقات لازمة قبل تسجيل الفيديو والصوت وفق القواعد المطبقة على الاجتماع." : "I confirm I am responsible for notifying participants and obtaining any required permission before video/audio recording under the rules applicable to this meeting."}</span>\n            </label>\n          </CardContent>\n'''
page = replace_once(page, old_form, new_form, "recording acknowledgement UI")
page_path.write_text(page, encoding="utf-8")

# ---------------------------------------------------------------------------
# V2 hardening 2: strict server-side acknowledgement. A browser cannot start a
# recording-enabled meeting without sending literal true.
# ---------------------------------------------------------------------------
router_path = root / "server/routers.ts"
routers = router_path.read_text(encoding="utf-8")
routers = replace_once(
    routers,
    '''        meetingUrl: z.string().url().max(2000),\n        botName: z.string().trim().max(100).optional(),\n      }))\n      .mutation(({ input }) => createFelfelMeeting(input.meetingUrl, input.botName)),\n''',
    '''        meetingUrl: z.string().url().max(2000),\n        botName: z.string().trim().max(100).optional(),\n        recordingConsent: z.literal(true),\n      }).strict())\n      .mutation(({ input }) => createFelfelMeeting(input.meetingUrl, input.botName)),\n''',
    "recording acknowledgement router",
)
router_path.write_text(routers, encoding="utf-8")

# ---------------------------------------------------------------------------
# V2 hardening 3: large recordings use the existing streaming Drive uploader
# but allow a longer bounded upload window than ordinary CRM attachments.
# ---------------------------------------------------------------------------
drive_path = root / "server/services/googleDriveFileStorage.ts"
drive = drive_path.read_text(encoding="utf-8")
drive = replace_once(
    drive,
    '''  appProperties?: Record<string, string>;\n  signal?: AbortSignal;\n}): Promise<StoredDriveUploadResult> {\n''',
    '''  appProperties?: Record<string, string>;\n  signal?: AbortSignal;\n  timeoutMs?: number;\n}): Promise<StoredDriveUploadResult> {\n''',
    "Drive stream timeout option",
)
drive = replace_once(
    drive,
    '''  const timeoutMs = getDriveStreamUploadTimeoutMs();\n''',
    '''  const requestedTimeoutMs = Number(args.timeoutMs || 0);\n  const timeoutMs = Number.isFinite(requestedTimeoutMs) && requestedTimeoutMs > 0\n    ? Math.max(getDriveStreamUploadTimeoutMs(), requestedTimeoutMs)\n    : getDriveStreamUploadTimeoutMs();\n''',
    "Drive stream timeout resolution",
)
drive_path.write_text(drive, encoding="utf-8")

storage_path = root / "server/services/crmFileStorage.ts"
storage = storage_path.read_text(encoding="utf-8")
storage = replace_once(
    storage,
    '''    appProperties: input.appProperties,\n  });\n''',
    '''    appProperties: input.appProperties,\n    timeoutMs: 30 * 60 * 1000,\n  });\n''',
    "recording Drive timeout",
)
# Roll back the Drive object if CRM Files registration fails after the stream upload.
storage = replace_once(
    storage,
    '''  const db = await getDb();\n  if (!db) throw new Error("Database connection failed");\n  const [inserted] = await db.insert(crmFiles).values({\n    entityType: input.entityType,\n''',
    '''  const db = await getDb();\n  if (!db) {\n    await deleteStoredFileFromGoogleDrive(driveResult.driveFileId).catch(() => undefined);\n    throw new Error("Database connection failed");\n  }\n  let inserted: any;\n  try {\n    [inserted] = await db.insert(crmFiles).values({\n    entityType: input.entityType,\n''',
    "stream CRM registration try",
)
storage = replace_once(
    storage,
    '''    uploadedBy: input.uploadedBy,\n  } as any).$returningId();\n  const crmFileId = Number((inserted as any)?.id ?? (inserted as any)?.insertId ?? 0) || null;\n  return {\n''',
    '''    uploadedBy: input.uploadedBy,\n    } as any).$returningId();\n  } catch (error) {\n    await deleteStoredFileFromGoogleDrive(driveResult.driveFileId).catch((rollbackError) => {\n      console.warn("[CrmFileStorage] recording Drive rollback failed", rollbackError);\n    });\n    throw error;\n  }\n  const crmFileId = Number((inserted as any)?.id ?? (inserted as any)?.insertId ?? 0) || null;\n  return {\n''',
    "stream CRM registration rollback",
)
storage_path.write_text(storage, encoding="utf-8")

tracked = [
    "server/services/felfel/felfelAdapter.ts",
    "server/services/crmFileStorage.ts",
    "server/services/googleDriveFileStorage.ts",
    "server/services/felfel/felfelRecordingDriveService.ts",
    "server/services/felfel/felfelRecordingDriveService.test.ts",
    "server/services/felfel/vexa-video-overlay/README.md",
    "server/routers.ts",
    "client/src/pages/FelfelPage.tsx",
]
run("git", "diff", "--check", "--", *tracked)
status = run("git", "status", "--short")
for rel in tracked:
    if rel not in status:
        raise SystemExit(f"Expected V2 TCRM path missing from worktree: {rel}")

print(f"{PATCH_ID} applied")
print("RECORDING_ACKNOWLEDGEMENT_REQUIRED=YES")
print("MEETING_REF_MEETING_ID_TYPE_FIXED=YES")
print("GOOGLE_DRIVE_RECORDING_STREAM_TIMEOUT_MS=1800000")
print("DRIVE_ROLLBACK_ON_CRM_REGISTRATION_FAILURE=YES")
print("EXPECTED_TRACKED_TCRM_FILES=8")
print("VEXA_VIDEO_OVERLAY_APPLIED_BY_V1=YES")
print("NO_BUILD_RESTART_REAL_MEETING_RECORDING_DRIVE_UPLOAD_COMMIT_PUSH_FETCH_PULL_RESET_MERGE_REBASE_MIGRATION_PERFORMED=YES")
