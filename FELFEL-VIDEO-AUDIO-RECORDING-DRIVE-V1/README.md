# Felfel Video + Audio Recording + TCRM Google Drive V1

Baseline TCRM commit: `90b1d4573626e0fad4c7629df1b062e939099e7e`.

This patch reuses Vexa v0.12 recording primitives instead of creating a second meeting bot. Vexa already ships `VideoRecordingService`, which records the Xvfb display with ffmpeg and uploads `media_type=video`; its standard bot composition root currently wires the audio recording path only. The patch wires the existing video service into the same bot lifecycle while preserving the existing audio recorder.

TCRM then reads the finalized Vexa `video` and `audio` recording masters and streams them directly into the existing TCRM Google Drive storage. Both files are registered in CRM Files under the selected client. No new Google OAuth/settings implementation and no database migration are introduced.

Privacy guard: Vexa Lite runs bot child processes against one shared Xvfb display. To avoid cross-meeting screen capture, TCRM refuses a second active Felfel meeting while video-recording mode is enabled. This remains until the deployment has one isolated display per bot.

Production Vexa source remains outside the parent TCRM Git repository under `ai-staff/felfel`; the patch repository is the approved source of this overlay. The custom image tag is `tcrm-vexa-lite:video-audio-drive-v1`.

The patch itself does not build the image, restart services, join a real meeting, create a recording, upload to Drive, commit, push, fetch, pull, reset, merge, rebase, or run migrations.
