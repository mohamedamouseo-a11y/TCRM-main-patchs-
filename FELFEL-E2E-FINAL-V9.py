#!/usr/bin/env python3
# FELFEL-E2E-FINAL-V9
# Final fix: durable Google auth profile + truthful meeting lifecycle.

from pathlib import Path
import os

ROOT = Path("/var/www/TCRM-MAIN")

def read(rel):
    p = ROOT / rel
    if not p.exists():
        raise SystemExit("PATCH_FAIL=missing:" + rel)
    return p.read_text(encoding="utf-8")

def write(rel, text, mode=None):
    p = ROOT / rel
    p.write_text(text, encoding="utf-8")
    if mode is not None:
        os.chmod(p, mode)

rel = "server/services/felfel/felfelCrmMeetingService.ts"
s = read(rel)

old = '''export function mapLifecycle(status: string, active: boolean, previousStatus?: string | null) {
  const normalized = String(status || "").toLowerCase();
  const previous = String(previousStatus || "").toLowerCase();
  if (active || ["live", "in_call", "joined", "started"].some((v) => normalized.includes(v))) return "live";
  if (["waiting", "admission", "admitted", "pending"].some((v) => normalized.includes(v))) return "waiting";
  if (["ended", "stopped", "completed", "finished"].some((v) => normalized.includes(v))) return "ended";
  if (["joining", "starting", "queued"].some((v) => normalized.includes(v))) return "joining";
  if (["joining", "waiting", "live", "ended", "processing"].includes(previous)) return "ended";
  if (["completed", "failed"].includes(previous)) return previous;
  return "scheduled";
}'''

new = '''export function mapLifecycle(status: string, active: boolean, previousStatus?: string | null) {
  const normalized = String(status || "").toLowerCase();
  const previous = String(previousStatus || "").toLowerCase();
  // active only proves a bot workload exists; it does not prove Meet admission.
  if (["live", "in_call", "joined", "started", "recording"].some((v) => normalized.includes(v))) return "live";
  if (["waiting", "admission", "admitted", "pending"].some((v) => normalized.includes(v))) return "waiting";
  if (["joining", "starting", "queued", "requested"].some((v) => normalized.includes(v))) return "joining";
  if (["ended", "stopped", "completed", "finished", "failed", "rejected", "auth_session_missing"].some((v) => normalized.includes(v))) return "ended";
  if (["joining", "waiting", "live", "ended", "processing"].includes(previous) && !active) return "ended";
  if (["completed", "failed"].includes(previous)) return previous;
  return "scheduled";
}'''

if new not in s:
    if old not in s:
        raise SystemExit("PATCH_FAIL=mapLifecycle_anchor_missing")
    s = s.replace(old, new, 1)

old_end = '''        await db.update(crmMeetings).set({
          status: "ended",
          felfelStatus: historical?.status || remote.status || "ended",
          recordingStatus: isRecordingComplete(String(meeting.recordingStatus || ""))
            ? meeting.recordingStatus
            : "processing",
          startedAt: meeting.startedAt || (remote.startedAt ? asDate(remote.startedAt) : null),
          endedAt: meeting.endedAt || new Date(),
        }).where(eq(crmMeetings.id, id));'''

new_end = '''        const admitted = wasKnownLive || Boolean(meeting.startedAt);
        await db.update(crmMeetings).set({
          status: admitted ? "ended" : "failed",
          felfelStatus: historical?.status || remote.status || "ended",
          recordingStatus: isRecordingComplete(String(meeting.recordingStatus || ""))
            ? meeting.recordingStatus
            : admitted ? "processing" : "failed",
          transcriptStatus: admitted ? meeting.transcriptStatus : "failed",
          analysisStatus: admitted ? meeting.analysisStatus : "failed",
          startedAt: meeting.startedAt || (remote.startedAt ? asDate(remote.startedAt) : null),
          endedAt: meeting.endedAt || new Date(),
          processingLockUntil: admitted ? meeting.processingLockUntil : null,
          lastError: admitted ? meeting.lastError : (meeting.lastError || "Felfel bot did not reach an admitted/live state"),
        }).where(eq(crmMeetings.id, id));'''

if new_end not in s:
    if old_end not in s:
        raise SystemExit("PATCH_FAIL=lifecycle_end_anchor_missing")
    s = s.replace(old_end, new_end, 1)

old_schedule = '''        // Process only after the upstream bot is no longer active, allowing
        // Vexa to finalize transcript and recording artifacts first.
        setTimeout(() => {
          void processLinkedFelfelMeeting(id).catch(() => undefined);
        }, 3_000);
        stopLifecycleMonitor(id);
        return;'''

new_schedule = '''        // Process only if the bot was actually admitted/live.
        if (wasKnownLive || Boolean(meeting.startedAt)) {
          setTimeout(() => {
            void processLinkedFelfelMeeting(id).catch(() => undefined);
          }, 3_000);
        }
        stopLifecycleMonitor(id);
        return;'''

if new_schedule not in s:
    if old_schedule not in s:
        raise SystemExit("PATCH_FAIL=process_schedule_anchor_missing")
    s = s.replace(old_schedule, new_schedule, 1)

guard_anchor = '''  if (!meeting.platform || !meeting.nativeMeetingId) throw new Error("Felfel meeting identity is not available");
  const intelligenceAlreadyComplete = isMeetingIntelligenceComplete(meeting);'''

guard_new = '''  if (!meeting.platform || !meeting.nativeMeetingId) throw new Error("Felfel meeting identity is not available");
  if (
    !meeting.startedAt
    && !isRecordingComplete(String(meeting.recordingStatus || ""))
    && ["ended", "failed", "joining", "waiting"].includes(String(meeting.status || "").toLowerCase())
  ) {
    await db.update(crmMeetings).set({
      status: "failed",
      recordingStatus: "failed",
      transcriptStatus: "failed",
      analysisStatus: "failed",
      processingLockUntil: null,
      failedAt: meeting.failedAt || new Date(),
      lastError: meeting.lastError || "Felfel bot never joined the meeting",
    }).where(eq(crmMeetings.id, id));
    return (await loadMeeting(id)).meeting;
  }
  const intelligenceAlreadyComplete = isMeetingIntelligenceComplete(meeting);'''

if guard_new not in s:
    if guard_anchor not in s:
        raise SystemExit("PATCH_FAIL=processing_guard_anchor_missing")
    s = s.replace(guard_anchor, guard_new, 1)

write(rel, s)

script_rel = "ai-staff/felfel/deploy/compose/bin/felfel-auth-identity"
x = read(script_rel)

old_block = '''    Xvfb :99 -screen 0 1920x1080x24 >/tmp/xvfb-login.log 2>&1 &
    for i in $(seq 1 30); do [ -e /tmp/.X11-unix/X99 ] && break; sleep .2; done
    fluxbox >/tmp/fluxbox-login.log 2>&1 &
    x11vnc -display :99 -forever -shared -passwd "$VNC_PASS" -rfbport 5900 >/tmp/x11vnc-login.log 2>&1 &
    websockify --web /usr/share/novnc 6080 localhost:5900 >/tmp/websockify-login.log 2>&1 &
    exec node /app/core/meetings/modules/remote-browser/dist/provision-cli.js
  ' >/dev/null'''

new_block = '''    Xvfb :99 -screen 0 1920x1080x24 >/tmp/xvfb-login.log 2>&1 & XVFB_PID=$!
    for i in $(seq 1 30); do [ -e /tmp/.X11-unix/X99 ] && break; sleep .2; done
    fluxbox >/tmp/fluxbox-login.log 2>&1 & FLUX_PID=$!
    x11vnc -display :99 -forever -shared -passwd "$VNC_PASS" -rfbport 5900 >/tmp/x11vnc-login.log 2>&1 & VNC_PID=$!
    websockify --web /usr/share/novnc 6080 localhost:5900 >/tmp/websockify-login.log 2>&1 & WS_PID=$!
    set +e
    node /app/core/meetings/modules/remote-browser/dist/provision-cli.js
    rc=$?
    set -e
    if [ "$rc" = "0" ]; then
      export AWS_ACCESS_KEY_ID="$BOT_S3_ACCESS_KEY"
      export AWS_SECRET_ACCESS_KEY="$BOT_S3_SECRET_KEY"
      LOCAL_STATE="$LOGIN_PROFILE_DIR/Local State"
      COOKIES="$LOGIN_PROFILE_DIR/Default/Cookies"
      if [ ! -s "$LOCAL_STATE" ] || [ ! -s "$COOKIES" ]; then
        echo "AUTH_PROFILE_CRITICAL_FILES_MISSING"
        rc=44
      else
        aws s3 cp "$LOCAL_STATE" "s3://$BOT_S3_BUCKET/$BOT_USERDATA_S3_PATH/browser-data/Local State" --endpoint-url "$BOT_S3_ENDPOINT" >/dev/null || rc=45
        if [ "$rc" = "0" ]; then
          aws s3 cp "$COOKIES" "s3://$BOT_S3_BUCKET/$BOT_USERDATA_S3_PATH/browser-data/Default/Cookies" --endpoint-url "$BOT_S3_ENDPOINT" >/dev/null || rc=46
        fi
      fi
    fi
    kill "$WS_PID" "$VNC_PID" "$FLUX_PID" "$XVFB_PID" >/dev/null 2>&1 || true
    wait "$WS_PID" "$VNC_PID" "$FLUX_PID" "$XVFB_PID" >/dev/null 2>&1 || true
    exit "$rc"
  ' >/dev/null'''

if new_block not in x:
    if old_block not in x:
        raise SystemExit("PATCH_FAIL=auth_runtime_anchor_missing")
    x = x.replace(old_block, new_block, 1)

write(script_rel, x, 0o755)

print("PATCH=PASS")
print("FILES=2")
print("AUTH_PROFILE=CRITICAL_FILES_EXPLICITLY_PERSISTED")
print("FALSE_RECORDING=FIXED")
print("FAILED_JOIN_PROCESSING_LOOP=FIXED")
