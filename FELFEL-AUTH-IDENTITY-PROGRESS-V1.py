#!/usr/bin/env python3
# FELFEL-AUTH-IDENTITY-PROGRESS-V1
# 1) Upload progress never shows 100% until every required Drive file has returned
#    from upload AND passed metadata verification.
# 2) Adds a one-time authenticated-Google identity provisioner for Felfel.

from pathlib import Path
import os

ROOT = Path("/var/www/TCRM-MAIN")

def read(rel):
    p = ROOT / rel
    if not p.exists():
        raise SystemExit("PATCH_FAIL=missing:" + rel)
    return p.read_text(encoding="utf-8")

def write(rel, text):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")

rel = "server/services/felfel/felfelCrmMeetingService.ts"
s = read(rel)

old = '''  const reportUpload = async (bytes: number) => {
    const percent = Math.max(0, Math.min(100, Math.floor((bytes / totalBytes) * 100)));
    const now = Date.now();
    if (percent <= lastProgress || (percent < 100 && now - lastProgressAt < 750)) return;
    lastProgress = percent;
    lastProgressAt = now;
    await setRecordingProgress(Number(meeting.id), "uploading", percent);
  };'''

new = '''  const reportUpload = async (bytes: number) => {
    const rawPercent = Math.max(0, Math.min(100, Math.floor((bytes / totalBytes) * 100)));
    // Reading the final request-body byte is not the same as Google Drive
    // acknowledging + persisting the object. Keep 100 reserved for the
    // post-upload metadata verification below.
    const percent = Math.min(98, rawPercent);
    const now = Date.now();
    if (percent <= lastProgress || (percent < 98 && now - lastProgressAt < 750)) return;
    lastProgress = percent;
    lastProgressAt = now;
    await setRecordingProgress(Number(meeting.id), "uploading", percent);
  };'''

if new not in s:
    if old not in s:
        raise SystemExit("PATCH_FAIL=progress_report_anchor_missing")
    s = s.replace(old, new, 1)

anchor = '''  const recordingStatus = videoReady ? "uploaded" : "uploaded_audio_only";

  return {'''
replacement = '''  const recordingStatus = videoReady ? "uploaded" : "uploaded_audio_only";

  // 100 means every required artifact has completed upload AND the Drive
  // metadata verification inside storeCrmFileDriveOnly has succeeded.
  if (complete) {
    await setRecordingProgress(Number(meeting.id), "uploading", 100);
  }

  return {'''

if replacement not in s:
    if anchor not in s:
        raise SystemExit("PATCH_FAIL=progress_verified_anchor_missing")
    s = s.replace(anchor, replacement, 1)

write(rel, s)

script_rel = "ai-staff/felfel/deploy/compose/bin/felfel-auth-identity"
script = r'''#!/usr/bin/env bash
set -euo pipefail

VEXA=/var/www/TCRM-MAIN/ai-staff/felfel
ENVFILE="$VEXA/deploy/compose/.env"
COMPOSE="$VEXA/deploy/compose/docker-compose.yml"
BOT_IMAGE="${BROWSER_IMAGE:-vexaai/vexa-bot:v012}"
LOGIN_NAME=felfel-auth-login
LOGIN_PORT="${FELFEL_AUTH_LOGIN_PORT:-16080}"
PREFIX="${FELFEL_AUTH_PREFIX:-userdata/felfel-google}"
POLICY_NAME=felfel-userdata
AVATAR="$(find /var/www/TCRM-MAIN -type f -path '*/ai-staff/felfel-avatar.webp' 2>/dev/null | head -1 || true)"

cd "$VEXA"
touch "$ENVFILE"

get_env() {
  local key="$1" default="${2:-}"
  local value
  value="$(grep -E "^${key}=" "$ENVFILE" | tail -1 | cut -d= -f2- || true)"
  value="${value%\"}"; value="${value#\"}"
  value="${value%\'}"; value="${value#\'}"
  printf '%s' "${value:-$default}"
}

set_env() {
  local key="$1" value="$2"
  if grep -q -E "^${key}=" "$ENVFILE"; then
    sed -i "s|^${key}=.*|${key}=${value}|" "$ENVFILE"
  else
    printf '%s=%s\n' "$key" "$value" >>"$ENVFILE"
  fi
}

case "${1:-prepare}" in
  status)
    state="missing"
    docker inspect "$LOGIN_NAME" >/dev/null 2>&1 && state="$(docker inspect -f '{{.State.Status}}' "$LOGIN_NAME" 2>/dev/null || true)"
    echo "LOGIN_STATE=$state"
    echo "BOT_AUTHENTICATED=$(get_env BOT_AUTHENTICATED false)"
    echo "SESSION_PREFIX=$(get_env BOT_USERDATA_S3_PATH)"
    echo "MEETING_API_AUTH=$(docker exec vexa-v012-meeting-api-1 sh -lc 'printf "%s" "$BOT_AUTHENTICATED"' 2>/dev/null || true)"
    [ -f /tmp/felfel-auth-watch.log ] && echo "WATCH=$(tail -1 /tmp/felfel-auth-watch.log | tr '\n' ' ')"
    exit 0
    ;;
  prepare) ;;
  *) echo "USAGE=$0 prepare|status"; exit 2 ;;
esac

[ -n "$AVATAR" ] || { echo "RESULT=AVATAR_NOT_FOUND"; exit 1; }

docker image inspect "$BOT_IMAGE" >/dev/null 2>&1 || { echo "RESULT=BOT_IMAGE_MISSING"; exit 1; }

docker run --rm --entrypoint sh "$BOT_IMAGE" -lc '
  test -f /app/core/meetings/modules/remote-browser/dist/provision-cli.js &&
  command -v aws >/dev/null &&
  command -v Xvfb >/dev/null &&
  command -v x11vnc >/dev/null &&
  command -v websockify >/dev/null
' || { echo "RESULT=LOGIN_RUNTIME_INCOMPLETE"; exit 1; }

NETWORK="$(docker inspect vexa-v012-meeting-api-1 \
  --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}}{{"\n"}}{{end}}' \
  | head -1)"
[ -n "$NETWORK" ] || { echo "RESULT=VEXA_NETWORK_NOT_FOUND"; exit 1; }

BUCKET="$(get_env MINIO_BUCKET vexa)"
ROOT_USER="$(get_env MINIO_ACCESS_KEY vexa-access-key)"
ROOT_PASS="$(get_env MINIO_SECRET_KEY vexa-secret-key)"

BOT_ACCESS="$(get_env BOT_S3_ACCESS_KEY)"
BOT_SECRET="$(get_env BOT_S3_SECRET_KEY)"
if [ -z "$BOT_ACCESS" ] || [ -z "$BOT_SECRET" ]; then
  BOT_ACCESS="felfel$(openssl rand -hex 6)"
  BOT_SECRET="$(openssl rand -hex 24)"
  POLICY_FILE=/tmp/felfel-userdata-policy.json
  cat >"$POLICY_FILE" <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetBucketLocation", "s3:ListBucket"],
      "Resource": ["arn:aws:s3:::${BUCKET}"],
      "Condition": {"StringLike": {"s3:prefix": ["${PREFIX}", "${PREFIX}/*"]}}
    },
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
      "Resource": ["arn:aws:s3:::${BUCKET}/${PREFIX}/*"]
    }
  ]
}
EOF

  docker run --rm \
    --network "$NETWORK" \
    -v "$POLICY_FILE:/tmp/policy.json:ro" \
    -e ROOT_USER="$ROOT_USER" \
    -e ROOT_PASS="$ROOT_PASS" \
    -e BOT_ACCESS="$BOT_ACCESS" \
    -e BOT_SECRET="$BOT_SECRET" \
    -e POLICY_NAME="$POLICY_NAME" \
    minio/mc:latest sh -lc '
      set -e
      mc alias set local http://minio:9000 "$ROOT_USER" "$ROOT_PASS" >/dev/null
      mc admin user add local "$BOT_ACCESS" "$BOT_SECRET" >/dev/null
      mc admin policy create local "$POLICY_NAME" /tmp/policy.json >/dev/null 2>&1 || true
      mc admin policy attach local "$POLICY_NAME" --user "$BOT_ACCESS" >/dev/null
    '
  rm -f "$POLICY_FILE"
fi

set_env BOT_USERDATA_S3_PATH "$PREFIX"
set_env BOT_S3_ENDPOINT "http://minio:9000"
set_env BOT_S3_BUCKET "$BUCKET"
set_env BOT_S3_ACCESS_KEY "$BOT_ACCESS"
set_env BOT_S3_SECRET_KEY "$BOT_SECRET"
set_env BOT_AUTHENTICATED false

docker rm -f "$LOGIN_NAME" >/dev/null 2>&1 || true

VNC_PASS="$(openssl rand -hex 6)"
printf '%s' "$VNC_PASS" >/tmp/felfel-vnc-pass
chmod 600 /tmp/felfel-vnc-pass

docker run -d \
  --name "$LOGIN_NAME" \
  --network "$NETWORK" \
  -p "0.0.0.0:${LOGIN_PORT}:6080" \
  -v "$AVATAR:/tmp/felfel-avatar.webp:ro" \
  -e AUTH_PLATFORM=google \
  -e LOGIN_TIMEOUT_MS=1200000 \
  -e LOGIN_PROFILE_DIR=/tmp/felfel-login-profile \
  -e BOT_USERDATA_S3_PATH="$PREFIX" \
  -e BOT_S3_ENDPOINT=http://minio:9000 \
  -e BOT_S3_BUCKET="$BUCKET" \
  -e BOT_S3_ACCESS_KEY="$BOT_ACCESS" \
  -e BOT_S3_SECRET_KEY="$BOT_SECRET" \
  -e VNC_PASS="$VNC_PASS" \
  --entrypoint bash \
  "$BOT_IMAGE" -lc '
    set -e
    export DISPLAY=:99
    Xvfb :99 -screen 0 1920x1080x24 >/tmp/xvfb-login.log 2>&1 &
    for i in $(seq 1 30); do [ -e /tmp/.X11-unix/X99 ] && break; sleep .2; done
    fluxbox >/tmp/fluxbox-login.log 2>&1 &
    x11vnc -display :99 -forever -shared -passwd "$VNC_PASS" -rfbport 5900 >/tmp/x11vnc-login.log 2>&1 &
    websockify --web /usr/share/novnc 6080 localhost:5900 >/tmp/websockify-login.log 2>&1 &
    node /app/core/meetings/modules/remote-browser/dist/provision-cli.js
  ' >/dev/null

cat >/tmp/felfel-auth-watch.sh <<'WATCH'
#!/usr/bin/env bash
set -u
VEXA=/var/www/TCRM-MAIN/ai-staff/felfel
ENVFILE="$VEXA/deploy/compose/.env"
COMPOSE="$VEXA/deploy/compose/docker-compose.yml"
NAME=felfel-auth-login
docker wait "$NAME" >/dev/null 2>&1 || exit 1
CODE="$(docker inspect -f '{{.State.ExitCode}}' "$NAME" 2>/dev/null || echo 1)"
if [ "$CODE" != "0" ]; then
  echo "AUTH_LOGIN_FAILED exit=$CODE"
  exit 1
fi
while docker ps --format '{{.Names}} {{.Image}}' | grep -v "^${NAME} " | grep -q 'vexaai/vexa-bot'; do
  sleep 5
done
if grep -q '^BOT_AUTHENTICATED=' "$ENVFILE"; then
  sed -i 's/^BOT_AUTHENTICATED=.*/BOT_AUTHENTICATED=true/' "$ENVFILE"
else
  echo 'BOT_AUTHENTICATED=true' >>"$ENVFILE"
fi
cd "$VEXA" || exit 1
docker compose -f "$COMPOSE" up -d --no-deps --force-recreate meeting-api >/dev/null
sleep 5
LIVE="$(docker exec vexa-v012-meeting-api-1 sh -lc 'printf "%s" "$BOT_AUTHENTICATED"' 2>/dev/null || true)"
if [ "$LIVE" = "true" ]; then
  echo "AUTH_READY=YES"
else
  echo "AUTH_READY=NO"
fi
WATCH
chmod +x /tmp/felfel-auth-watch.sh
nohup /tmp/felfel-auth-watch.sh >/tmp/felfel-auth-watch.log 2>&1 </dev/null &

echo "RESULT=LOGIN_REQUIRED"
echo "LOGIN_PORT=$LOGIN_PORT"
echo "VNC_PASSWORD=$VNC_PASS"
echo "AVATAR_FILE=/tmp/felfel-avatar.webp"
echo "INSTRUCTIONS=Open noVNC on this server port, sign into the dedicated Felfel Google account, then set its Google profile photo using AVATAR_FILE. Leave the browser open until login confirmation closes the container."
'''
write(script_rel, script)
os.chmod(ROOT / script_rel, 0o755)

print("PATCH=PASS")
print("FILES=2")
print("PROGRESS=STREAM_BYTES_MAX_98_THEN_100_AFTER_DRIVE_VERIFY")
print("IDENTITY=AUTHENTICATED_GOOGLE_PROVISIONER_READY")
