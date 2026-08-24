# TCRM — Developer Hub Trusted SQL Sync Bootstrap V1

Purpose: unblock the **old live Developer Hub runtime** at live HEAD `90b1d4573626e0fad4c7629df1b062e939099e7e` so it can fast-forward safely to canonical GitHub `main` without weakening the permanent security policy.

## Root cause

The old live Developer Hub security code blocks every `.sql` path as a database/archive risk, including legitimate versioned migrations under trusted source roots such as `drizzle/migrations/`.

Canonical GitHub `main` already contains the corrected policy: `.sql` remains blocked everywhere except trusted source paths, while `.env`, keys, dumps, DB files, archives, runtime directories and secret-bearing content remain blocked/scanned.

This creates a bootstrap problem: the old runtime cannot sync to the newer `main` because it blocks the migrations that contain the newer source history.

## Scope

Temporary bootstrap changes exactly one tracked source file:

- `server/services/developerHubGitHubSecurity.ts`

It adds only the trusted-source `.sql` exception already represented by the canonical-main policy.

It does **not**:

- allow `.sql` outside trusted source roots;
- allow `.dump`, `.db`, `.sqlite`, archives, private keys, env files or credentials;
- touch migrations, database state, Mautic runtime files, customer data, branches or GitHub history.

## Critical bootstrap workflow

1. Run helper `--check`, `--apply`, `--verify` on old live HEAD.
2. Run a targeted runtime assertion proving trusted migrations are allowed and unsafe SQL/dumps/env files remain blocked.
3. Build the old checkout so `dist/index.js` contains the bootstrap logic.
4. Confirm PM2 production entrypoint is `dist/index.js` (or an equivalent ignored build artifact). If not, STOP.
5. Restore **only** `server/services/developerHubGitHubSecurity.ts` to old HEAD so tracked worktree is clean.
6. Reload PM2 from the already-built bootstrap `dist/index.js`.
7. Use Developer Hub authenticated Review Sync and fast-forward to canonical `main`.
8. Rebuild canonical `main`, which contains the permanent source-side trusted SQL policy.
9. Continue the already-approved Felfel Reference V7 preservation patch and final visual acceptance.

The source restoration in step 5 is an intentional rollback of this temporary bootstrap only; it must not touch any unrelated path.

## Safety markers

- Expected old live HEAD: `90b1d4573626e0fad4c7629df1b062e939099e7e`
- Canonical main target: `8d64505bb264d3c8aeb5e956a54cd08bc336945d`
- Marker: `TCRM_DEVELOPER_HUB_TRUSTED_SQL_SYNC_BOOTSTRAP_V1`
- Mautic files touched: `0`
- DB migrations executed: `0`
- Force push: `NO`
- New branch: `NO`

## Helper

`apply_developer_hub_trusted_sql_sync_bootstrap_v1.py`
