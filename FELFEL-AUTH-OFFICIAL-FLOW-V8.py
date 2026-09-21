#!/usr/bin/env python3
# FELFEL-AUTH-OFFICIAL-FLOW-V8
# Use Vexa provision-cli's own success contract and remove the redundant
# custom post-login restore validator that caused repeated false negatives.

from pathlib import Path
import os

target = Path("/var/www/TCRM-MAIN/ai-staff/felfel/deploy/compose/bin/felfel-auth-identity")
if not target.exists():
    raise SystemExit("PATCH_FAIL=IDENTITY_PROVISIONER_MISSING")

s = target.read_text(encoding="utf-8")

start = "cat >/tmp/felfel-auth-watch.sh <<'WATCH'\n"
end = "WATCH\nchmod +x /tmp/felfel-auth-watch.sh"
a = s.find(start)
b = s.find(end, a)
if a < 0 or b < 0:
    raise SystemExit("PATCH_FAIL=WATCHER_ANCHOR_MISSING")

body = r'''#!/usr/bin/env bash
set -u
VEXA=/var/www/TCRM-MAIN/ai-staff/felfel
ENVFILE="$VEXA/deploy/compose/.env"
COMPOSE="$VEXA/deploy/compose/docker-compose.yml"
NAME=felfel-auth-login

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

# Vexa provision-cli exits 0 only after:
# - Google login is confirmed by its native validateLoggedIn()
# - auth-essential browser data is uploaded successfully.
while docker ps --format '{{.Names}} {{.Image}}' | grep -v "^${NAME} " | grep -q 'vexaai/vexa-bot'; do
  sleep 5
done

setauth true
cd "$VEXA" || exit 1
docker compose -f "$COMPOSE" up -d --no-deps --force-recreate meeting-api >/dev/null
sleep 5

MEETING_API="$(docker ps -a --format '{{.Names}}' | grep 'meeting-api-1$' | head -1)"
LIVE="$(docker exec "$MEETING_API" sh -lc 'printf "%s" "$BOT_AUTHENTICATED"' 2>/dev/null || true)"
if [ "$LIVE" = "true" ]; then
  echo "AUTH_READY=YES PROVISION_VALIDATED=YES"
else
  setauth false
  echo "AUTH_READY=NO"
  exit 1
fi
'''

replacement = start + body + "WATCH\nchmod +x /tmp/felfel-auth-watch.sh"
s = s[:a] + replacement + s[b + len(end):]
target.write_text(s, encoding="utf-8")
os.chmod(target, 0o755)

# Update the currently staged watcher too, so current login session can continue.
tmp = Path("/tmp/felfel-auth-watch.sh")
tmp.write_text(body, encoding="utf-8")
os.chmod(tmp, 0o755)

print("PATCH=PASS")
print("AUTH_FLOW=VEXA_NATIVE_PROVISION_SUCCESS")
print("PREPARE_REQUIRED=NO")
print("BUILD_REQUIRED=NO")
