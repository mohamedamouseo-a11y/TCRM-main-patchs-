#!/usr/bin/env bash
set -Eeuo pipefail
P=DEVELOPER_HUB_AUTO_MODE_UNTRACKED_SAFE_PUSH
T="${TCRM_PATH:-/var/www/TCRM-MAIN}"
W="/tmp/$P"
fail(){ echo "FINAL_MARKER=FAIL:$1"; exit 1; }
[[ -d "$T/.git" && -d "$W" ]] || fail PREFLIGHT
cd "$T"
[[ "$(git rev-parse HEAD)" == "$(cat "$W/head.before")" ]] || fail COMMIT_DURING_PATCH
B="$(cat "$W/branch")"
R="$(git ls-remote origin "refs/heads/$B" | awk 'NR==1{print $1}')"
[[ "$R" == "$(cat "$W/remote.before")" ]] || fail GIT_PUSH_DURING_PATCH
[[ -s "$W/patched-files.txt" && -s "$W/test-files.txt" ]] || fail PATCH_METADATA_MISSING
LC_ALL=C sort -u "$W/patched-files.txt" -o "$W/patched-files.txt"
LC_ALL=C sort -u "$W/test-files.txt" -o "$W/test-files.txt"
MATCH=0
while IFS= read -r f; do
 [[ -n "$f" && "$f" != /* && "$f" != *".."* && -e "$T/$f" ]] || fail BAD_PATCH_PATH
 case "$f" in apps/zaghloul-wacrm/*|server/services/zaghloul*|*/migrations/*|package.json|pnpm-lock.yaml|package-lock.json|yarn.lock) fail OUT_OF_SCOPE;; esac
 grep -Fxq "$f" "$W/blocker-files.txt" && MATCH=1
 if ! grep -Fxq "$f" "$W/new-files.txt" 2>/dev/null; then [[ -f "$W/backups/$f" ]] || fail BACKUP_MISSING; fi
done <"$W/patched-files.txt"
[[ "$MATCH" == 1 ]] || fail BLOCKER_FILE_NOT_PATCHED
{ git diff --name-only; git diff --cached --name-only; git ls-files --others --exclude-standard; } | LC_ALL=C sort -u >"$W/changes.now"
comm -13 "$W/changes.before" "$W/changes.now" >"$W/introduced"
while IFS= read -r f; do [[ -z "$f" ]] || grep -Fxq "$f" "$W/patched-files.txt" || fail UNDECLARED_MUTATION; done <"$W/introduced"
git diff --cached --name-only | LC_ALL=C sort -u >"$W/staged.now"
cmp -s "$W/staged.before" "$W/staged.now" || fail STAGING_DURING_PATCH
# Production code may never contain broad staging commands.
while IFS= read -r f; do
 grep -Fxq "$f" "$W/test-files.txt" && continue
 if grep -nE 'git[[:space:]]+add[[:space:]]+(-A|--all|\.)' "$T/$f" >/dev/null 2>&1; then fail BROAD_GIT_ADD; fi
done <"$W/patched-files.txt"
echo "BROAD_GIT_ADD=NONE"
mapfile -t TF <"$W/test-files.txt"
for f in "${TF[@]}"; do [[ -f "$T/$f" ]] || fail TEST_FILE_MISSING; grep -Fxq "$f" "$W/patched-files.txt" || fail TEST_NOT_DECLARED; done
rm -f "$W/fixture-results.env"
DEVHUB_FIXTURE_RESULTS="$W/fixture-results.env" pnpm exec vitest run "${TF[@]}" >"$W/fixtures.log" 2>&1 || { cat "$W/fixtures.log"; fail FIXTURES; }
[[ -f "$W/fixture-results.env" ]] || fail FIXTURE_RESULTS_MISSING
for k in FIXTURE_TESTS UNTRACKED_SAFE_ALLOW SECRET_BLOCK SYMLINK_BLOCK RUNTIME_BLOCK MIXED_SET_ATOMIC_BLOCK LARGE_SET_441 EXACT_STAGE_SET GIT_PUSH_DURING_FIXTURES; do
 v="$(grep -E "^${k}=" "$W/fixture-results.env" | tail -1 | cut -d= -f2-)"; [[ "$v" == PASS || ( "$k" == GIT_PUSH_DURING_FIXTURES && "$v" == NONE ) ]] || fail "$k"; echo "$k=$v";
done
export NODE_OPTIONS="${NODE_OPTIONS:-} --max-old-space-size=8192"
set +e
pnpm exec tsc --noEmit --incremental false >"$W/tsc.after.log" 2>&1
set -e
grep -F 'error TS' "$W/tsc.after.log" | sed "s#${T}/##g" | LC_ALL=C sort -u >"$W/tsc.after.errors" || true
comm -13 "$W/tsc.before.errors" "$W/tsc.after.errors" >"$W/tsc.new"
N="$(wc -l <"$W/tsc.new" | tr -d ' ')"; echo "TSC_NEW_ERROR_COUNT=$N"; [[ "$N" == 0 ]] || { cat "$W/tsc.new"; fail TSC; }
pnpm build >"$W/build.log" 2>&1 || { cat "$W/build.log"; fail BUILD; }; echo "BUILD=PASS"
[[ "$(git rev-parse HEAD)" == "$(cat "$W/head.before")" ]] || fail COMMIT_DURING_PATCH
R2="$(git ls-remote origin "refs/heads/$B" | awk 'NR==1{print $1}')"; [[ "$R2" == "$(cat "$W/remote.before")" ]] || fail GIT_PUSH_DURING_PATCH
echo "GIT_PUSH_DURING_PATCH=NONE"
pm2 jlist >"$W/pm2.json"
NAME="$(node - "$T" "$W/pm2.json" <<'NODE'
const fs=require('fs'),path=require('path');const t=path.resolve(process.argv[2]);const a=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));const p=a.find(x=>x?.pm2_env?.pm_cwd&&path.resolve(x.pm2_env.pm_cwd)===t);if(p?.name)process.stdout.write(p.name)
NODE
)"; [[ -n "$NAME" ]] || fail PM2
pm2 reload "$NAME" >/dev/null; sleep 2
pm2 jlist >"$W/pm2.after.json"
PORT="$(node - "$T" "$W/pm2.after.json" <<'NODE'
const fs=require('fs'),path=require('path');const t=path.resolve(process.argv[2]);const a=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));const p=a.find(x=>x?.pm2_env?.pm_cwd&&path.resolve(x.pm2_env.pm_cwd)===t);if(!p||p?.pm2_env?.status!=='online')process.exit(2);const port=p?.pm2_env?.env?.PORT??p?.pm2_env?.PORT;if(port)process.stdout.write(String(port));
NODE
)" || fail PM2
[[ "$PORT" =~ ^[0-9]+$ ]] || fail PORT
CODE="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 10 "http://127.0.0.1:$PORT/settings" || true)"; [[ "$CODE" == 200 ]] || fail HTTP
echo "PM2=PASS:$NAME"
echo "HTTP=PASS:200"
echo "FINAL_MARKER=${P}_OK"
