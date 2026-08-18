# TCRM Developer Hub Safe Directory V2.1 — Test Repair

Work directly on the CURRENT server checkout:

`/var/www/TCRM-MAIN`

Patch source repository:

`mohamedamouseo-a11y/TCRM-main-patchs-`

Repair patch:

`TCRM-DEVELOPER-HUB-SAFE-DIRECTORY-V2.1-TEST-REPAIR/APPLY_PATCH.py`

Expected Git HEAD baseline remains:

`3d6a67c61dd0abce01d803469f81bcbf45c730a6`

## Safety rules

- Preserve all Smart Search/parity working-tree changes.
- Preserve all Developer Hub V1 and V2 implementation changes already applied.
- Do not reset, checkout, clean, discard, stage, commit, pull, merge, or push.
- Do not modify persistent Git configuration.
- Do not add `safe.directory=*`.
- The V2.1 patch is test-source repair only.

## 1. Preflight

```bash
cd /var/www/TCRM-MAIN
git rev-parse --show-toplevel
git rev-parse HEAD
git status --short
```

Confirm the V2 markers are already present:

```bash
grep -Fq 'safe.directory=${normalizedCandidate}' server/services/developerHubRepositoryRoot.ts
grep -Fq 'safe.directory=${repoDir}' server/services/developerHubGitHubRuntime.ts
grep -Fq 'createSafeGitEnvironment(REPO_DIR)' server/routes/developerHub.ts
```

If any marker is missing, STOP and report. Do not apply V2.1 to a non-V2 checkout.

## 2. Apply V2.1 repair

Run the repair script against `/var/www/TCRM-MAIN`.

The repair should only modify:

- `server/services/developerHubRepositoryRoot.test.ts`
- `server/services/developerHubGitHubRuntime.test.ts`

It must repair:

1. the malformed multiline `safe.directory` assertion that caused the Vitest transform error;
2. the V2 repository-root test helper so `spawnSync` is imported using ESM-compatible `node:child_process` syntax instead of runtime `require()`.

## 3. Diff validation

```bash
git diff --check

git diff -- \
  server/services/developerHubRepositoryRoot.test.ts \
  server/services/developerHubGitHubRuntime.test.ts
```

Confirm no production implementation source was changed by V2.1 itself.

## 4. Focused tests

Run:

```bash
pnpm exec vitest run \
  server/services/developerHubRepositoryRoot.test.ts \
  server/services/developerHubGitHubRuntime.test.ts
```

If the focused tests fail for a V1/V2/V2.1-related reason, STOP and return the exact error. Do not build or restart.

## 5. Read-only safe-directory verification

Only after focused tests pass, run read-only checks proving the actual mixed-ownership checkout is accepted without persistent Git config:

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

And:

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
    config --local --includes --null --name-only --list >/dev/null
```

Both must exit 0.

Verify no persistent `/var/www/TCRM-MAIN` entry was introduced by this work and do not change any config:

```bash
git config --global --get-all safe.directory || true
git config --system --get-all safe.directory || true
```

## 6. Build

Only after focused tests and read-only probes pass:

```bash
pnpm build
```

If build fails because of V1/V2/V2.1, STOP. If it fails only because of clearly pre-existing unrelated Smart Search/parity work, document that precisely and STOP before restart unless the current `dist/index.js` is independently proven to contain the V2 implementation.

After a successful build verify markers in `dist/index.js`:

```bash
test -s dist/index.js
grep -Fq 'safe.directory=' dist/index.js
grep -Fq 'canonical Git work tree root' dist/index.js
grep -Fq 'Developer Hub repository root could not be resolved' dist/index.js
```

## 7. Restart only TCRM

Only after successful build verification:

```bash
oldpid=$(pm2 pid tamiyouz-crm)
pm2 restart tamiyouz-crm
newpid=$(pm2 pid tamiyouz-crm)

echo "OLD PID=$oldpid"
echo "NEW PID=$newpid"
pm2 describe tamiyouz-crm
readlink -f /proc/$newpid/cwd
tr '\0' ' ' < /proc/$newpid/cmdline
```

Required:

- new PID differs from old PID;
- status is `online`;
- cwd is `/var/www/TCRM-MAIN`;
- command is `node /var/www/TCRM-MAIN/dist/index.js`.

## 8. Health check

Run a read-only request against the existing app port, for example:

```bash
curl -fsS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3002/
```

Expected HTTP 200.

Do NOT invoke Developer Hub Push/Pull/Sync/Safe Cleanup during this server task.

## Final report

Return:

- HEAD before/after;
- files changed by V2.1;
- `git diff --check` result;
- focused test summary;
- isolated safe-directory probe results;
- confirmation no persistent Git config was added;
- build result;
- old/new PM2 PID if restarted;
- PM2 status/cwd/command;
- HTTP health result;
- final `git status --short`;
- confirmation no push/pull/reset/merge/cleanup/commit/deployment occurred.
