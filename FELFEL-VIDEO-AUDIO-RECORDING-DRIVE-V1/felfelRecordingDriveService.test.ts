import { describe, expect, it } from "vitest";
import {
  buildFelfelRecordingEntityKey,
  selectFelfelRecordingForMeeting,
  summarizeFelfelRecording,
} from "./felfelRecordingDriveService";
import type { FelfelRecording } from "./felfelAdapter";

function recording(id: string, meetingId: string, media: Array<"audio" | "video">): FelfelRecording {
  return {
    id,
    meetingId,
    sessionUid: `session-${id}`,
    status: "completed",
    mediaFiles: media.map((type, index) => ({
      id: String(index + 1),
      type,
      format: "webm",
      durationSeconds: 60,
      fileSize: 1000,
      isFinal: true,
    })),
  };
}

describe("felfelRecordingDriveService helpers", () => {
  it("selects the newest recording belonging to the requested meeting id", () => {
    const selected = selectFelfelRecordingForMeeting([
      recording("10", "101", ["audio", "video"]),
      recording("12", "101", ["audio", "video"]),
      recording("99", "202", ["audio", "video"]),
    ], "101");
    expect(selected?.id).toBe("12");
  });

  it("requires both video and audio readiness for final Drive export", () => {
    expect(summarizeFelfelRecording(recording("1", "101", ["audio"]))).toMatchObject({
      audioReady: true,
      videoReady: false,
    });
    expect(summarizeFelfelRecording(recording("2", "101", ["audio", "video"]))).toMatchObject({
      audioReady: true,
      videoReady: true,
    });
  });

  it("builds stable separate Drive entity keys for video and audio", () => {
    expect(buildFelfelRecordingEntityKey({
      platform: "google_meet",
      nativeId: "abc-defg-hij",
      mediaType: "video",
    })).toBe("felfel-recording:google_meet:abc-defg-hij:video");
    expect(buildFelfelRecordingEntityKey({
      platform: "google_meet",
      nativeId: "abc-defg-hij",
      mediaType: "audio",
    })).toBe("felfel-recording:google_meet:abc-defg-hij:audio");
  });
});
