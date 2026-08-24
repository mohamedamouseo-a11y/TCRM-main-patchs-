#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import runpy
import subprocess
import sys

PATCH_ID = "FELFEL-VIDEO-AUDIO-RECORDING-DRIVE-V1-V3"
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


def find_vexa_root() -> pathlib.Path:
    candidates = [
        root / "ai-staff/felfel/vexa",
        root / "ai-staff/felfel/vexa-main",
        root / "ai-staff/felfel",
    ]
    for candidate in candidates:
        if (candidate / "core/meetings/services/bot/src/index.ts").is_file() and (
            candidate / "core/meetings/modules/recording/src/video-recording.ts"
        ).is_file():
            return candidate
    raise SystemExit("Vexa source root disappeared after V1 application")


if not original.is_file():
    raise SystemExit("Approved V1 apply script is missing")
if run("git", "rev-parse", "--show-toplevel") != str(root):
    raise SystemExit("Run from canonical TCRM root")
if run("git", "rev-parse", "HEAD") != BASELINE_SHA:
    raise SystemExit(f"{PATCH_ID} requires baseline {BASELINE_SHA}")
if run("git", "status", "--short"):
    raise SystemExit("Refusing to apply on a dirty TCRM worktree")

# Apply the guarded V1 body first: TCRM recording integration + Vexa bot lifecycle wiring.
old_argv = sys.argv[:]
try:
    sys.argv = [str(original), str(root)]
    runpy.run_path(str(original), run_name="__main__")
finally:
    sys.argv = old_argv

# ---------------------------------------------------------------------------
# 1) Compile correctness: recording UI uses server-returned meetingId.
# ---------------------------------------------------------------------------
page_path = root / "client/src/pages/FelfelPage.tsx"
page = page_path.read_text(encoding="utf-8")
page = replace_once(
    page,
    '''type MeetingRef = {\n  platform: string;\n  nativeId: string;\n''',
    '''type MeetingRef = {\n  meetingId?: string | null;\n  platform: string;\n  nativeId: string;\n''',
    "MeetingRef meetingId",
)

# Explicit recording acknowledgement before joining. Server also requires literal true.
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
# 2) Adapter regression: privacy guard now performs GET /meetings before POST
# /bots. Make the existing focused test locate the bot request and pin recording
# flags instead of assuming /bots is the first fetch call.
# ---------------------------------------------------------------------------
adapter_test_path = root / "server/services/felfel/felfelAdapter.test.ts"
adapter_test = adapter_test_path.read_text(encoding="utf-8")
adapter_test = replace_once(
    adapter_test,
    '''    const botRequest = fetchMock.mock.calls[0]?.[1] as RequestInit;\n    expect(fetchMock.mock.calls[0]?.[0]).toContain("/bots");\n    expect(new Headers(botRequest?.headers).get("X-API-Key")).toBe("scoped-user-token");\n''',
    '''    const botCall = fetchMock.mock.calls.find((call) => String(call?.[0] || "").endsWith("/bots"));\n    expect(botCall).toBeTruthy();\n    const botRequest = botCall?.[1] as RequestInit;\n    expect(new Headers(botRequest?.headers).get("X-API-Key")).toBe("scoped-user-token");\n    expect(JSON.parse(String(botRequest?.body || "{}"))).toMatchObject({\n      recording_enabled: true,\n      transcribe_enabled: true,\n    });\n''',
    "adapter recording request regression",
)
adapter_test_path.write_text(adapter_test, encoding="utf-8")

# ---------------------------------------------------------------------------
# 3) Large recording path: Vexa video upload must stream the ffmpeg output from
# disk. Never read/Buffer.concat a whole multi-hour video in bot memory.
# ---------------------------------------------------------------------------
vexa_root = find_vexa_root()
vexa_video_path = vexa_root / "core/meetings/modules/recording/src/video-recording.ts"
vexa_video = vexa_video_path.read_text(encoding="utf-8")
method_start = vexa_video.find("  async upload(callbackUrl: string, token: string): Promise<void> {")
method_end_marker = "\n  /**\n   * Mux an audio file into the video"
method_end = vexa_video.find(method_end_marker, method_start)
if method_start < 0 or method_end < 0:
    raise SystemExit("Could not isolate upstream VideoRecordingService.upload method")
new_upload_method = r'''  async upload(callbackUrl: string, token: string): Promise<void> {
    if (!fs.existsSync(this.filePath)) {
      log(`[VideoRecording] File not found for upload: ${this.filePath}`);
      return;
    }

    const fileStats = await fs.promises.stat(this.filePath);
    const durationSeconds = (Date.now() - this.startTime) / 1000;
    log(`[VideoRecording] Streaming ${fileStats.size} bytes (${durationSeconds.toFixed(1)}s) to ${callbackUrl}`);

    const boundary = `----VexaVideoRecording${Date.now()}`;
    const contentTypeMap: Record<string, string> = {
      webm: 'video/webm',
      mkv: 'video/x-matroska',
      mp4: 'video/mp4',
    };
    const fileContentType = contentTypeMap[this.format] || 'video/webm';
    const metadata = JSON.stringify({
      meeting_id: this.meetingId,
      session_uid: this.sessionUid,
      media_type: 'video',
      format: this.format,
      duration_seconds: durationSeconds,
      file_size_bytes: fileStats.size,
      start_time_utc: this.startTime ? new Date(this.startTime).toISOString() : undefined,
    });
    const prefix = Buffer.from(
      `--${boundary}\r\nContent-Disposition: form-data; name="metadata"\r\nContent-Type: application/json\r\n\r\n${metadata}\r\n` +
      `--${boundary}\r\nContent-Disposition: form-data; name="file"; filename="video.${this.format}"\r\nContent-Type: ${fileContentType}\r\n\r\n`
    );
    const suffix = Buffer.from(`\r\n--${boundary}--\r\n`);
    const contentLength = prefix.length + fileStats.size + suffix.length;

    return new Promise((resolve, reject) => {
      const url = new URL(callbackUrl);
      const transport = url.protocol === 'https:' ? https : http;
      let settled = false;
      const finish = (err?: Error) => {
        if (settled) return;
        settled = true;
        if (err) reject(err); else resolve();
      };
      const req = transport.request(
        {
          hostname: url.hostname,
          port: url.port,
          path: `${url.pathname}${url.search}`,
          method: 'POST',
          headers: {
            'Content-Type': `multipart/form-data; boundary=${boundary}`,
            'Content-Length': contentLength,
            'Authorization': `Bearer ${token}`,
          },
        },
        (res) => {
          let responseData = '';
          res.on('data', (chunk) => { responseData += chunk; });
          res.on('end', () => {
            if (res.statusCode && res.statusCode >= 200 && res.statusCode < 300) {
              log(`[VideoRecording] Upload successful: ${res.statusCode}`);
              finish();
            } else {
              log(`[VideoRecording] Upload failed: ${res.statusCode} - ${responseData}`);
              finish(new Error(`Video upload failed with status ${res.statusCode}: ${responseData}`));
            }
          });
        }
      );
      req.on('error', (err) => finish(err));
      req.write(prefix);
      const fileStream = fs.createReadStream(this.filePath);
      fileStream.on('error', (err) => {
        req.destroy(err);
        finish(err);
      });
      fileStream.on('end', () => req.end(suffix));
      fileStream.pipe(req, { end: false });
    });
  }
'''
vexa_video = vexa_video[:method_start] + new_upload_method + vexa_video[method_end:]
vexa_video_path.write_text(vexa_video, encoding="utf-8")
if "await fs.promises.readFile(this.filePath)" in new_upload_method or "Buffer.concat(parts)" in new_upload_method:
    raise SystemExit("Video upload memory-safety guard failed")

# ---------------------------------------------------------------------------
# 4) Reuse existing TCRM streamed Drive uploader with a recording-sized timeout.
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
stream_start = storage.find("export async function storeCrmFileStreamDriveOnly")
stream_end = storage.find("\n\nexport async function storeCrmFileDriveOnly", stream_start)
if stream_start < 0 or stream_end < 0:
    raise SystemExit("Could not isolate storeCrmFileStreamDriveOnly")
stream_section = storage[stream_start:stream_end]
stream_section = replace_once(
    stream_section,
    '''    appProperties: input.appProperties,\n  });\n''',
    '''    appProperties: input.appProperties,\n    timeoutMs: 30 * 60 * 1000,\n  });\n''',
    "recording Drive timeout",
)
stream_section = replace_once(
    stream_section,
    '''  const db = await getDb();\n  if (!db) throw new Error("Database connection failed");\n  const [inserted] = await db.insert(crmFiles).values({\n''',
    '''  const db = await getDb();\n  if (!db) {\n    await deleteStoredFileFromGoogleDrive(driveResult.driveFileId).catch(() => undefined);\n    throw new Error("Database connection failed");\n  }\n  let inserted: any;\n  try {\n    [inserted] = await db.insert(crmFiles).values({\n''',
    "stream CRM registration try",
)
stream_section = replace_once(
    stream_section,
    '''    uploadedBy: input.uploadedBy,\n  } as any).$returningId();\n  const crmFileId = Number((inserted as any)?.id ?? (inserted as any)?.insertId ?? 0) || null;\n''',
    '''    uploadedBy: input.uploadedBy,\n    } as any).$returningId();\n  } catch (error) {\n    await deleteStoredFileFromGoogleDrive(driveResult.driveFileId).catch((rollbackError) => {\n      console.warn("[CrmFileStorage] recording Drive rollback failed", rollbackError);\n    });\n    throw error;\n  }\n  const crmFileId = Number((inserted as any)?.id ?? (inserted as any)?.insertId ?? 0) || null;\n''',
    "stream CRM registration rollback",
)
storage = storage[:stream_start] + stream_section + storage[stream_end:]
storage_path.write_text(storage, encoding="utf-8")

# Final source scope validation. Vexa deployment files are intentionally ignored
# by the parent repository; their exact paths are reported separately.
tracked = [
    "client/src/pages/FelfelPage.tsx",
    "server/routers.ts",
    "server/services/crmFileStorage.ts",
    "server/services/googleDriveFileStorage.ts",
    "server/services/felfel/felfelAdapter.ts",
    "server/services/felfel/felfelAdapter.test.ts",
    "server/services/felfel/felfelRecordingDriveService.ts",
    "server/services/felfel/felfelRecordingDriveService.test.ts",
    "server/services/felfel/vexa-video-overlay/README.md",
]
run("git", "diff", "--check", "--", *tracked)
status = run("git", "status", "--short")
for rel in tracked:
    if rel not in status:
        raise SystemExit(f"Expected V3 TCRM path missing from worktree: {rel}")

print(f"{PATCH_ID} applied")
print(f"BASELINE={BASELINE_SHA}")
print(f"VEXA_SOURCE_ROOT={vexa_root}")
print(f"VEXA_BOT_INDEX_MODIFIED={vexa_root / 'core/meetings/services/bot/src/index.ts'}")
print(f"VEXA_VIDEO_RECORDER_MODIFIED={vexa_video_path}")
print("AUDIO_RECORDING=VEXA_RECORDING_V1")
print("VIDEO_RECORDING=VEXA_X11GRAB_FFMPEG")
print("VIDEO_UPLOAD_STREAMING_FROM_DISK=YES")
print("TCRM_TO_GOOGLE_DRIVE_STREAMING=YES")
print("GOOGLE_DRIVE_RECORDING_TIMEOUT_MS=1800000")
print("RECORDING_ACKNOWLEDGEMENT_REQUIRED=YES")
print("ONE_ACTIVE_MEETING_PRIVACY_GUARD=YES")
print("RECORDINGS_SAVED_AS_SEPARATE_VIDEO_AND_AUDIO_FILES=YES")
print("CRM_FILES_REGISTRATION=YES")
print("DB_SCHEMA_CHANGED=NO")
print("DB_MIGRATION_RUN=NO")
print("NEW_GOOGLE_DRIVE_INTEGRATION=NO")
print("CUSTOM_VEXA_IMAGE=tcrm-vexa-lite:video-audio-drive-v1")
print("EXPECTED_TRACKED_TCRM_FILES=9")
print("NO_BUILD_RESTART_REAL_MEETING_RECORDING_DRIVE_UPLOAD_COMMIT_PUSH_FETCH_PULL_RESET_MERGE_REBASE_MIGRATION_PERFORMED=YES")
