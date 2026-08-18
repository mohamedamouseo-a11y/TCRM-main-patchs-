# ZAGHLOUL_V5R3R3_BASELINE_DEPENDENCY_PARITY_TSC

Target: `/var/www/TCRM-MAIN`
Parent: `ZAGHLOUL_V5R3R2_TSC_LOCATION_NORMALIZATION_ACCOUNT_PROBE`
Baseline: `c7ca52c5bb0495400ed327601d50cf6c7a363c73`

## Root cause fixed
V5R3R2 created a detached baseline worktree under `/tmp`, but that worktree had no installed `node_modules`. Running `npx tsc` there did not reproduce the real baseline compiler/dependency environment, so it reported `TSC_BASELINE_ERRORS=0` while the candidate reported 230 diagnostics.

## Correct baseline strategy
This verifier must compare source revisions while keeping the compiler/dependency environment identical:

1. Create a detached baseline worktree at the pinned baseline commit.
2. Require the live target to have `node_modules/.bin/tsc`.
3. Require dependency manifests to be identical between baseline and candidate:
   - `package.json`
   - any lockfile present in either tree: `pnpm-lock.yaml`, `package-lock.json`, `yarn.lock`
4. Symlink the live target's `node_modules` into the baseline worktree.
5. Run the exact same local TypeScript binary for both baseline and candidate with `NODE_OPTIONS=--max-old-space-size=16384`.
6. Reject OOM/signal exits (137/134/9) and any non-TypeScript exit outside 0/1/2.
7. Compare diagnostics location-independently as a multiset: `relative-path :: TS-code :: message`.
8. Require `TSC_NEW_ERROR_COUNT=0`.

This patch is verification-only and must not modify TCRM source, DB, dependencies, PM2, or git history.

## Account-management proof
Also rerun the real `getZaghloulV5Settings()` probe and require `authMode === "TCRM_SESSION"`.

## Success
`ZAGHLOUL_V5R3R3_BASELINE_DEPENDENCY_PARITY_TSC_OK`
