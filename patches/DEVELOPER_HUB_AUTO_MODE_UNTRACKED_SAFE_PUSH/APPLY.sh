#!/usr/bin/env bash
set -Eeuo pipefail
P=DEVELOPER_HUB_AUTO_MODE_UNTRACKED_SAFE_PUSH
T="${TCRM_PATH:-/var/www/TCRM-MAIN}"
W="/tmp/$P"
fail(){ echo "PRECHECK=FAIL:$1"; exit 1; }
[[ -d "$T/.git" ]] || fail TARGET
command -v pnpm >/dev/null || fail PNPM
rm -rf "$W"; mkdir -p "$W/backups"
cd "$T"
git rev-parse HEAD >"$W/head.before"
git branch --show-current >"$W/branch"
B="$(cat "$W/branch")"; [[ -n "$B" ]] || fail BRANCH
git remote get-url origin >"$W/origin"
git ls-remote origin "refs/heads/$B" | awk 'NR==1{print $1}' >"$W/remote.before"
[[ -s "$W/remote.before" ]] || fail REMOTE_SHA
{ git diff --name-only; git diff --cached --name-only; git ls-files --others --exclude-standard; } | LC_ALL=C sort -u >"$W/changes.before"
git diff --cached --name-only | LC_ALL=C sort -u >"$W/staged.before"
{
  grep -RIlE --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=dist --exclude-dir=build 'unexpected untracked file.*Auto mode|untracked file.*not allowed.*Auto mode' client server shared scripts 2>/dev/null || true
} | LC_ALL=C sort -u >"$W/blocker-files.txt"
[[ -s "$W/blocker-files.txt" ]] || fail BLOCKER_NOT_FOUND
export NODE_OPTIONS="${NODE_OPTIONS:-} --max-old-space-size=8192"
set +e
pnpm exec tsc --noEmit --incremental false >"$W/tsc.before.log" 2>&1
set -e
grep -F 'error TS' "$W/tsc.before.log" | sed "s#${T}/##g" | LC_ALL=C sort -u >"$W/tsc.before.errors" || true
C="$(wc -l <"$W/tsc.before.errors" | tr -d ' ')"
{ git diff --name-only; git diff --cached --name-only; git ls-files --others --exclude-standard; } | LC_ALL=C sort -u >"$W/changes.after-preflight"
cmp -s "$W/changes.before" "$W/changes.after-preflight" || fail PREFLIGHT_MUTATION
echo "PRECHECK=PASS"
echo "BLOCKER_FILES=$(wc -l <"$W/blocker-files.txt" | tr -d ' ')"
echo "TSC_BASELINE_ERROR_COUNT=$C"
echo "TARGET_HEAD=$(cat "$W/head.before")"
