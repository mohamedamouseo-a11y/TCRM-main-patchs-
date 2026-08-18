# Apply TCRM Developer Hub Safe Directory V2

Work directly on the CURRENT TCRM server checkout:

`/var/www/TCRM-MAIN`

Patch source repository:

`mohamedamouseo-a11y/TCRM-main-patchs-`

Patch:

`TCRM-DEVELOPER-HUB-SAFE-DIRECTORY-V2/APPLY_PATCH.py`

Expected Git HEAD baseline:

`3d6a67c61dd0abce01d803469f81bcbf45c730a6`

This is a completion patch over the already-applied Developer Hub repository-root hardening V1. The server working tree is intentionally dirty because V1 and Smart Search/parity changes are present. Preserve every unrelated change.

## Safety rules

- Do NOT reset, checkout, stash, clean, discard, or overwrite unrelated working-tree changes.
- Do NOT modify persistent Git configuration.
- Do NOT run `git config --global --add safe.directory ...`.
- Do NOT use persistent `safe.directory=*` as the fix.
- Do NOT change repository ownership or permissions.
- Do NOT push, pull, merge, sync, or run Safe Cleanup.
- Do NOT deploy.
- Do NOT restart PM2 until the patch, focused tests, build, and bundle verification are green.
- Do NOT push the TCRM production repository; normal system-managed push remains the owner's workflow.

## 1. Preflight

Run:

```bash
cd /var/www/TCRM-MAIN
pwd
git rev-parse --show-toplevel
git rev-parse HEAD
git branch --show-current
git status --short
```

Confirm:

- canonical root = `/var/www/TCRM-MAIN`
- branch = `main`
- HEAD = `3d6a67c61dd0abce01d803469f81bcbf45c730a6`
- existing V1 Developer Hub changes are present
- unrelated Smart Search/parity changes remain untouched

Also verify the current failure mechanism read-only:

```bash
env -i \
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
HOME=/tmp \
LC_ALL=C \
LANG=C \
GIT_CONFIG_NOSYSTEM=1 \
GIT_CONFIG_SYSTEM=/dev/null \
GIT_CONFIG_GLOBAL=/dev/null \
GIT_TERMINAL_PROMPT=0 \
git -C /var/www/TCRM-MAIN rev-parse --show-toplevel
```

The pre-patch isolated probe is expected to fail with dubious ownership on this server.

## 2. Apply V2

Obtain the patch script from the patch repository and run it against:

`/var/www/TCRM-MAIN`

Do not manually rewrite equivalent code unless the script refuses because its exact V1 anchors have changed. If it refuses, STOP and report the mismatch rather than forcing it.

## 3. Inspect the diff

Review only the V2 changes in:

- `server/services/developerHubRepositoryRoot.ts`
- `server/services/developerHubGitHubRuntime.ts`
- `server/routes/developerHub.ts`
- `server/services/developerHubRepositoryRoot.test.ts`
- `server/services/developerHubGitHubRuntime.test.ts`

Verify the implementation preserves all V1 fail-closed checks while adding command-scoped safe-directory trust only for the normalized/canonical repository root.

Important expected behavior:

1. Resolver probes use an equivalent of:

   `git -c safe.directory=<normalized-candidate> -C <normalized-candidate> rev-parse ...`

2. Runtime local/worktree configuration probes use an equivalent command-scoped `safe.directory=<canonicalRepoDir>`.

3. Sandboxed Git environments used by Developer Hub receive only the canonical `REPO_DIR` as `safe.directory` while global/system Git config remains disabled.

4. No persistent Git config entry is created.

5. No wildcard `safe.directory=*` is introduced by the patch.

6. Existing authorization, locks, preview fingerprints, controlled-push checks, safe-merge checks, secret filtering, cleanup quarantine/recovery, branch restrictions, and explicit Git cwd behavior remain unchanged.

Run:

```bash
git diff --check
```

## 4. Focused tests

Run:

```bash
pnpm exec vitest run \
  server/services/developerHubRepositoryRoot.test.ts \
  server/services/developerHubGitHubRuntime.test.ts
```

If tests fail because of the V2 patch, STOP and report the exact failure. Do not hide or bypass a failing test.

## 5. Verify the production ownership case read-only

After the source patch is applied, verify the isolated repository probe with a command-scoped exception:

```bash
env -i \
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
HOME=/tmp \
LC_ALL=C \
LANG=C \
GIT_CONFIG_NOSYSTEM=1 \
GIT_CONFIG_SYSTEM=/dev/null \
GIT_CONFIG_GLOBAL=/dev/null \
GIT_TERMINAL_PROMPT=0 \
git -c safe.directory=/var/www/TCRM-MAIN \
-C /var/www/TCRM-MAIN \
rev-parse --show-toplevel
```

Expected stdout:

`/var/www/TCRM-MAIN`

Also verify the local-config probe succeeds with the same command-scoped exception and does not persist configuration.

## 6. Build

If focused tests and `git diff --check` pass, run:

```bash
pnpm build
```

Verify:

```bash
test -s dist/index.js
grep -Fq 'safe.directory=' dist/index.js
grep -Fq 'Developer Hub repository root could not be resolved' dist/index.js
grep -Fq 'canonical Git work tree root' dist/index.js
```

Do not restart if the build fails or the required bundle markers are absent.

## 7. Restart only TCRM after successful verification

Record old PID:

```bash
oldpid=$(pm2 pid tamiyouz-crm)
echo "OLD PID=$oldpid"
```

Restart only:

```bash
pm2 restart tamiyouz-crm
```

Then verify:

```bash
newpid=$(pm2 pid tamiyouz-crm)
echo "NEW PID=$newpid"
pm2 describe tamiyouz-crm
readlink -f /proc/$newpid/cwd
tr '\0' ' ' < /proc/$newpid/cmdline
```

Required:

- PID changed
- status online
- cwd `/var/www/TCRM-MAIN`
- command `node /var/www/TCRM-MAIN/dist/index.js`

Perform a read-only HTTP health check against the existing service/port. Do NOT invoke Developer Hub Push/Pull/Sync/Safe Cleanup during this server-side verification.

## 8. Confirm no persistent trust mutation

Run read-only:

```bash
git config --global --get-all safe.directory || true
git config --system --get-all safe.directory || true
```

Confirm the patch did not add `/var/www/TCRM-MAIN` or any new wildcard to those persistent files.

## Final report

Return:

- HEAD before/after (should remain the same because no commit is requested)
- files changed by V2
- `git diff --check` result
- focused test result
- isolated command-scoped repository probe result
- local-config probe result
- confirmation no persistent Git config was changed
- build result
- old/new PM2 PID
- PM2 online/cwd/command verification
- HTTP health result
- final `git status --short`
- confirmation unrelated Smart Search/parity changes were preserved
- confirmation no push/pull/reset/merge/cleanup/deployment was performed

Leave the verified server checkout ready for the normal system-managed push.