# Manus Apply Prompt — Developer Hub Repository Root Hardening V1

Work directly on the CURRENT TCRM server checkout.

## Source
Patch repository:
`mohamedamouseo-a11y/TCRM-main-patchs-`

Patch file:
`TCRM-DEVELOPER-HUB-REPOSITORY-ROOT-HARDENING-V1/APPLY_PATCH.py`

Expected TCRM baseline HEAD:
`3d6a67c61dd0abce01d803469f81bcbf45c730a6`

Expected server repository root from prior diagnostic:
`/var/www/TCRM-MAIN`

## Critical rules
- Apply to the CURRENT server checkout, not a separate clone.
- Do NOT push to GitHub.
- Do NOT deploy.
- Do NOT restart PM2 or any service.
- Do NOT pull or reset the repository.
- Preserve all unrelated Smart Search/parity working-tree changes.
- The patch script is intentionally baseline-locked and will refuse to overwrite dirty target files.

## Step 1 — Preflight
Run read-only checks first:

```bash
cd /var/www/TCRM-MAIN
git rev-parse --show-toplevel
git rev-parse HEAD
git branch --show-current
git status --short
```

Confirm:
- canonical root is `/var/www/TCRM-MAIN`
- branch is `main`
- HEAD is exactly `3d6a67c61dd0abce01d803469f81bcbf45c730a6`

Then confirm these patch target files have NO existing local modifications:

```bash
git status --short -- \
  server/services/developerHubRepositoryRoot.ts \
  server/services/developerHubGitHubRuntime.ts \
  server/services/GitHubSyncService.ts \
  server/routes/developerHub.ts \
  server/services/developerHubRepositoryRoot.test.ts \
  server/services/developerHubGitHubRuntime.test.ts
```

If any target file is dirty, STOP and report it. Do not overwrite it.

## Step 2 — Obtain and apply patch
Use the patch file from the patch repository and run it against `/var/www/TCRM-MAIN`.

Example if the patch repo is already available locally:

```bash
python3 /PATH/TO/TCRM-main-patchs-/TCRM-DEVELOPER-HUB-REPOSITORY-ROOT-HARDENING-V1/APPLY_PATCH.py /var/www/TCRM-MAIN
```

The patch must harden Developer Hub repository resolution so that:

1. `resolveDeveloperHubRepositoryRoot()` returns only a validated TCRM Git root and no longer silently falls back to a non-Git path.
2. `assertSafeRepositoryGitConfiguration()` validates the canonical Git root BEFORE running `git config --local`.
3. The legacy `GitHubSyncService.ts` no longer falls back directly to `process.cwd()` and reuses the shared resolver.
4. Developer Hub preview/execute actions fail clearly and non-mutatingly when repository resolution failed.
5. All existing explicit `cwd: REPO_DIR` Git execution behavior remains intact.
6. No `process.chdir()` is introduced.
7. Existing Developer Hub authorization, locks, preview fingerprints, controlled push, safe sync, cleanup quarantine/recovery, branch checks, secret redaction, and Git sandboxing remain unchanged.

## Step 3 — Inspect diff
Run:

```bash
git diff --check
git diff -- \
  server/services/developerHubRepositoryRoot.ts \
  server/services/developerHubGitHubRuntime.ts \
  server/services/GitHubSyncService.ts \
  server/routes/developerHub.ts \
  server/services/developerHubRepositoryRoot.test.ts \
  server/services/developerHubGitHubRuntime.test.ts
```

Verify the diff contains only the intended repository-root hardening and tests.

## Step 4 — Focused tests
Run:

```bash
pnpm exec vitest run \
  server/services/developerHubRepositoryRoot.test.ts \
  server/services/developerHubGitHubRuntime.test.ts
```

If focused tests fail, diagnose and report. Do not push or deploy.

## Step 5 — Optional broader validation
If resources allow, run the normal project validation commands used by this checkout, but do not let unrelated pre-existing Smart Search/parity failures cause you to overwrite or revert unrelated work.

At minimum report:
- `git diff --check`
- focused test result
- whether TypeScript/build validation was attempted
- any failures and whether they are related to this patch

## Step 6 — Safe reproduction after patch
Without performing any mutation-capable Git action, verify the intended behavior:

- valid repo root `/var/www/TCRM-MAIN` passes repository-root validation
- a non-repository directory such as `/var/www` is rejected before `git config --local`
- a nested directory under the repo is rejected as non-canonical by the safety boundary

Do NOT run actual push, pull, sync, cleanup, reset, merge, branch switch, or deployment as part of this verification.

## Final report
Return:
1. Server HEAD before application
2. Files changed
3. Exact diff summary
4. `git diff --check` result
5. Focused test result
6. Safe reproduction result
7. Any unrelated existing failures
8. Final `git status --short`
9. Confirmation that no push, deploy, service restart, pull, reset, merge, or cleanup was performed

Leave the verified server checkout ready for the normal system-managed push workflow.
