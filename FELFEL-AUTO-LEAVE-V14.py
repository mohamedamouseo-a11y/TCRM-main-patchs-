#!/usr/bin/env python3
# FELFEL-AUTO-LEAVE-V14
# Vexa defaults to 10 minutes of remote-audio silence before left_alone.
# TCRM sales meetings should finalize sooner after everybody leaves.
# This sets a per-meeting silence window (default 3 minutes), configurable by env.

from pathlib import Path

target = Path("/var/www/TCRM-MAIN/server/services/felfel/felfelAdapter.ts")
if not target.exists():
    raise SystemExit("PATCH_FAIL=ADAPTER_MISSING")

s = target.read_text(encoding="utf-8")

anchor = '''export async function createFelfelMeeting(meetingUrl: string, botName?: string): Promise<FelfelMeeting> {
  const parsed = detectFelfelMeetingUrl(meetingUrl);
  if (!parsed) throw new FelfelAdapterError("Unsupported or invalid meeting URL");
  const platform = ensureSupportedPlatform(parsed.platform);
  const payload = await requestJson<unknown>(FELFEL_GATEWAY_URL, "/bots", {'''

replacement = '''export async function createFelfelMeeting(meetingUrl: string, botName?: string): Promise<FelfelMeeting> {
  const parsed = detectFelfelMeetingUrl(meetingUrl);
  if (!parsed) throw new FelfelAdapterError("Unsupported or invalid meeting URL");
  const platform = ensureSupportedPlatform(parsed.platform);
  const configuredAutoLeaveMs = Number(process.env.FELFEL_AUTO_LEAVE_SILENCE_MS || 180_000);
  const autoLeaveSilenceMs = Number.isFinite(configuredAutoLeaveMs) && configuredAutoLeaveMs > 0
    ? Math.floor(configuredAutoLeaveMs)
    : 180_000;
  const payload = await requestJson<unknown>(FELFEL_GATEWAY_URL, "/bots", {'''

if replacement not in s:
    if anchor not in s:
        raise SystemExit("PATCH_FAIL=CREATE_MEETING_ANCHOR_MISSING")
    s = s.replace(anchor, replacement, 1)

old_body = '''      bot_name: (botName || "Felfel").trim().slice(0, 100) || "Felfel",
      recording_enabled: true,
    }),'''

new_body = '''      bot_name: (botName || "Felfel").trim().slice(0, 100) || "Felfel",
      recording_enabled: true,
      automatic_leave: {
        max_time_left_alone: autoLeaveSilenceMs,
      },
    }),'''

if new_body not in s:
    if old_body not in s:
        raise SystemExit("PATCH_FAIL=BOT_PAYLOAD_ANCHOR_MISSING")
    s = s.replace(old_body, new_body, 1)

target.write_text(s, encoding="utf-8")

print("PATCH=PASS")
print("FILES=server/services/felfel/felfelAdapter.ts")
print("AUTO_LEAVE_DEFAULT_MS=180000")
print("CONFIG=FELFEL_AUTO_LEAVE_SILENCE_MS")
