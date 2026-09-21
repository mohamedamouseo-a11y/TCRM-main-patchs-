#!/usr/bin/env python3
# FELFEL-AUTH-SELF-HEAL-V10
# Make status reconcile a successful V9 auth container exit if the background
# watcher did not finish. No new login is required when exit code is 0.

from pathlib import Path
import os

target = Path("/var/www/TCRM-MAIN/ai-staff/felfel/deploy/compose/bin/felfel-auth-identity")
if not target.exists():
    raise SystemExit("PATCH_FAIL=IDENTITY_PROVISIONER_MISSING")

s = target.read_text(encoding="utf-8")

old = '''  status)
    state="missing"
    docker inspect "$LOGIN_NAME" >/dev/null 2>&1 && state="$(docker inspect -f '{{.State.Status}}' "$LOGIN_NAME" 2>/dev/null || true)"
    echo "LOGIN_STATE=$state"
    echo "BOT_AUTHENTICATED=$(get_env BOT_AUTHENTICATED false)"
    echo "SESSION_PREFIX=$(get_env BOT_USERDATA_S3_PATH)"
    echo "MEETING_API_AUTH=$(docker exec vexa-v012-meeting-api-1 sh -lc 'printf "%s" "$BOT_AUTHENTICATED"' 2>/dev/null || true)"
    [ -f /tmp/felfel-auth-watch.log ] && echo "WATCH=$(tail -1 /tmp/felfel-auth-watch.log | tr '\n' ' ')"
    exit 0
    ;;'''

new = '''  status)
    state="missing"
    docker inspect "$LOGIN_NAME" >/dev/null 2>&1 && state="$(docker inspect -f '{{.State.Status}}' "$LOGIN_NAME" 2>/dev/null || true)"

    # V9 exit 0 means Google login was confirmed AND the critical Local State
    # + Cookies objects were flushed and uploaded. If the nohup watcher died or
    # got stuck, reconcile that successful result here instead of forcing
    # another manual login.
    if [ "$state" = "exited" ]; then
      code="$(docker inspect -f '{{.State.ExitCode}}' "$LOGIN_NAME" 2>/dev/null || echo 1)"
      if [ "$code" = "0" ] && [ "$(get_env BOT_AUTHENTICATED false)" != "true" ]; then
        set_env BOT_AUTHENTICATED true
        cd "$VEXA"
        docker compose -f "$COMPOSE" up -d --no-deps --force-recreate meeting-api >/dev/null
        sleep 3
        live="$(docker exec vexa-v012-meeting-api-1 sh -lc 'printf "%s" "$BOT_AUTHENTICATED"' 2>/dev/null || true)"
        if [ "$live" = "true" ]; then
          echo "AUTH_READY=YES PROVISION_VALIDATED=YES" >/tmp/felfel-auth-watch.log
        else
          set_env BOT_AUTHENTICATED false
          echo "AUTH_READY=NO" >/tmp/felfel-auth-watch.log
        fi
      fi
    fi

    echo "LOGIN_STATE=$state"
    echo "BOT_AUTHENTICATED=$(get_env BOT_AUTHENTICATED false)"
    echo "SESSION_PREFIX=$(get_env BOT_USERDATA_S3_PATH)"
    echo "MEETING_API_AUTH=$(docker exec vexa-v012-meeting-api-1 sh -lc 'printf "%s" "$BOT_AUTHENTICATED"' 2>/dev/null || true)"
    [ -f /tmp/felfel-auth-watch.log ] && echo "WATCH=$(tail -1 /tmp/felfel-auth-watch.log | tr '\n' ' ')"
    exit 0
    ;;'''

if new not in s:
    if old not in s:
        raise SystemExit("PATCH_FAIL=STATUS_ANCHOR_MISSING")
    s = s.replace(old, new, 1)

target.write_text(s, encoding="utf-8")
os.chmod(target, 0o755)

print("PATCH=PASS")
print("AUTH_STATUS_RECONCILE=ENABLED")
print("LOGIN_REQUIRED=NO")
print("BUILD_REQUIRED=NO")
