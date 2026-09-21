#!/usr/bin/env python3
# FELFEL-SALES-AUTH-GOOGLE-RESTORE-V3
# Minimal fix:
# 1) launchLinkedMeeting uses the same canonical meeting scope gate as createLinkedMeeting.
# 2) Google auth is enabled only after the uploaded S3 profile is restored and validated.

from pathlib import Path
import os, re

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

routers_rel = "server/routers.ts"
s = read(routers_rel)

old = '''    launchLinkedMeeting: felfelLinkedProcedure
      .input(z.object({ id: z.number().int().positive(), botName: z.string().trim().max(100).optional().default("Felfel") }).strict())
      .mutation(async ({ input, ctx }) => {
        await assertFelfelMeetingAccess(ctx.user as any, { meetingId: input.id }, "write");
        return launchLinkedFelfelMeeting(input.id, "Felfel");
      }),'''

new = '''    launchLinkedMeeting: felfelLinkedProcedure
      .input(z.object({ id: z.number().int().positive(), botName: z.string().trim().max(100).optional().default("Felfel") }).strict())
      .mutation(async ({ input, ctx }) => {
        const meeting = await getLinkedFelfelMeeting(input.id);
        await assertMeetingCreateScopeForContext(ctx, {
          leadId: Number(meeting?.leadId || 0) || null,
          clientId: Number(meeting?.clientId || 0) || null,
        });
        return launchLinkedFelfelMeeting(input.id, "Felfel");
      }),'''

if new not in s:
    if old not in s:
        raise SystemExit("PATCH_FAIL=launchLinkedMeeting_anchor_missing")
    s = s.replace(old, new, 1)

write(routers_rel, s)

script_rel = "ai-staff/felfel/deploy/compose/bin/felfel-auth-identity"
x = read(script_rel)

x = re.sub(r'-e LOGIN_TIMEOUT_MS=\d+ \\\n', '-e LOGIN_TIMEOUT_MS=3600000 \\\n', x, count=1)

marker = 'set_env BOT_AUTHENTICATED false\n'
disable_live = '''set_env BOT_AUTHENTICATED false
# FELFEL_AUTH_RESTORE_VERIFY_V3
cd "$VEXA"
docker compose -f "$COMPOSE" up -d --no-deps --force-recreate meeting-api >/dev/null
'''
if 'FELFEL_AUTH_RESTORE_VERIFY_V3' not in x:
    if marker not in x:
        raise SystemExit("PATCH_FAIL=auth_disable_anchor_missing")
    x = x.replace(marker, disable_live, 1)

start = "cat >/tmp/felfel-auth-watch.sh <<'WATCH'\n"
end = "WATCH\nchmod +x /tmp/felfel-auth-watch.sh"
a = x.find(start)
b = x.find(end, a)
if a < 0 or b < 0:
    raise SystemExit("PATCH_FAIL=watcher_anchor_missing")

watcher = r'''cat >/tmp/felfel-auth-watch.sh <<'WATCH'
#!/usr/bin/env bash
set -u
VEXA=/var/www/TCRM-MAIN/ai-staff/felfel
ENVFILE="$VEXA/deploy/compose/.env"
COMPOSE="$VEXA/deploy/compose/docker-compose.yml"
NAME=felfel-auth-login

envv() {
  local key="$1" default="${2:-}" value
  value="$(grep -E "^${key}=" "$ENVFILE" | tail -1 | cut -d= -f2- || true)"
  value="${value%\"}"; value="${value#\"}"
  value="${value%\'}"; value="${value#\'}"
  printf '%s' "${value:-$default}"
}
setauth() {
  local value="$1"
  if grep -q '^BOT_AUTHENTICATED=' "$ENVFILE"; then
    sed -i "s/^BOT_AUTHENTICATED=.*/BOT_AUTHENTICATED=${value}/" "$ENVFILE"
  else
    echo "BOT_AUTHENTICATED=${value}" >>"$ENVFILE"
  fi
}

docker wait "$NAME" >/dev/null 2>&1 || exit 1
CODE="$(docker inspect -f '{{.State.ExitCode}}' "$NAME" 2>/dev/null || echo 1)"
if [ "$CODE" != "0" ]; then
  setauth false
  echo "AUTH_LOGIN_FAILED exit=$CODE"
  exit 1
fi

while docker ps --format '{{.Names}} {{.Image}}' | grep -v "^${NAME} " | grep -q 'vexaai/vexa-bot'; do
  sleep 5
done

MEETING_API="$(docker ps -a --format '{{.Names}}' | grep 'meeting-api-1$' | head -1)"
[ -n "$MEETING_API" ] || { setauth false; echo "AUTH_RESTORE_VALIDATE_FAILED meeting_api_missing"; exit 1; }

NETWORK="$(docker inspect "$MEETING_API" --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}}{{"\n"}}{{end}}' | head -1)"
BOT_IMAGE="$(envv BROWSER_IMAGE vexaai/vexa-bot:v012)"
PREFIX="$(envv BOT_USERDATA_S3_PATH userdata/felfel-google)"
ENDPOINT="$(envv BOT_S3_ENDPOINT http://minio:9000)"
BUCKET="$(envv BOT_S3_BUCKET vexa)"
ACCESS="$(envv BOT_S3_ACCESS_KEY)"
SECRET="$(envv BOT_S3_SECRET_KEY)"

if [ -z "$NETWORK" ] || [ -z "$ACCESS" ] || [ -z "$SECRET" ]; then
  setauth false
  echo "AUTH_RESTORE_VALIDATE_FAILED storage_config"
  exit 1
fi

if ! docker run --rm   --network "$NETWORK"   -e BOT_USERDATA_S3_PATH="$PREFIX"   -e BOT_S3_ENDPOINT="$ENDPOINT"   -e BOT_S3_BUCKET="$BUCKET"   -e BOT_S3_ACCESS_KEY="$ACCESS"   -e BOT_S3_SECRET_KEY="$SECRET"   --entrypoint bash   "$BOT_IMAGE" -lc '
    set -e
    export DISPLAY=:98
    Xvfb :98 -screen 0 1280x900x24 >/tmp/felfel-auth-verify-xvfb.log 2>&1 &
    for i in $(seq 1 30); do [ -e /tmp/.X11-unix/X98 ] && break; sleep .2; done
    node - <<"NODE"
const rb = require("/app/core/meetings/modules/remote-browser/dist");
(async () => {
  const dir = "/tmp/felfel-restored-profile";
  const cfg = {
    userdataS3Path: process.env.BOT_USERDATA_S3_PATH,
    s3Endpoint: process.env.BOT_S3_ENDPOINT,
    s3Bucket: process.env.BOT_S3_BUCKET,
    s3AccessKey: process.env.BOT_S3_ACCESS_KEY,
    s3SecretKey: process.env.BOT_S3_SECRET_KEY,
  };
  rb.syncBrowserDataFromS3(cfg, dir);
  const { context, page } = await rb.launchPersistentBrowser({
    dataDir: dir,
    args: rb.getAuthenticatedBrowserArgs(),
  });
  let ok = false;
  try {
    const state = await rb.validateLoggedIn(page, "google");
    if (state.loggedIn) {
      const response = await context.request.get(
        "https://accounts.google.com/ListAccounts?gpsia=1&source=ChromiumBrowser&json=standard",
        { timeout: 30000 }
      );
      let body = await response.text();
      const firstArray = body.indexOf("[");
      if (firstArray > 0) body = body.slice(firstArray);
      const parsed = JSON.parse(body);
      const accounts = Array.isArray(parsed) && Array.isArray(parsed[1]) ? parsed[1] : [];
      ok = accounts.some((account) =>
        Array.isArray(account) &&
        String(account[0] || "").trim().length > 0 &&
        String(account[1] || "").includes("@")
      );
    }
  } catch (_) {
    ok = false;
  }
  await context.close().catch(() => {});
  console.log("RESTORED_GOOGLE_AUTH=" + (ok ? "YES" : "NO"));
  process.exit(ok ? 0 : 42);
})().catch(() => process.exit(42));
NODE
  ' >/tmp/felfel-auth-validate.log 2>&1
then
  setauth false
  docker run --rm     --network "$NETWORK"     -e AWS_ACCESS_KEY_ID="$ACCESS"     -e AWS_SECRET_ACCESS_KEY="$SECRET"     -e ENDPOINT="$ENDPOINT" -e BUCKET="$BUCKET" -e PREFIX="$PREFIX"     --entrypoint sh "$BOT_IMAGE" -lc     'aws s3 rm "s3://${BUCKET}/${PREFIX}/browser-data" --recursive --endpoint-url "$ENDPOINT" >/dev/null 2>&1 || true'     >/dev/null 2>&1 || true
  cd "$VEXA" || exit 1
  docker compose -f "$COMPOSE" up -d --no-deps --force-recreate meeting-api >/dev/null
  echo "AUTH_RESTORE_INVALID LOGIN_REQUIRED"
  exit 1
fi

setauth true
cd "$VEXA" || exit 1
docker compose -f "$COMPOSE" up -d --no-deps --force-recreate meeting-api >/dev/null
sleep 5
MEETING_API="$(docker ps -a --format '{{.Names}}' | grep 'meeting-api-1$' | head -1)"
LIVE="$(docker exec "$MEETING_API" sh -lc 'printf "%s" "$BOT_AUTHENTICATED"' 2>/dev/null || true)"
if [ "$LIVE" = "true" ]; then
  echo "AUTH_READY=YES RESTORE_VALIDATED=YES"
else
  setauth false
  echo "AUTH_READY=NO"
  exit 1
fi
WATCH
chmod +x /tmp/felfel-auth-watch.sh'''

x = x[:a] + watcher + x[b + len(end):]
write(script_rel, x, 0o755)

print("PATCH=PASS")
print("FILES=2")
print("SALES_AUTH=CREATE_SCOPE_PARITY")
print("GOOGLE_AUTH=RESTORED_PROFILE_VALIDATION")
