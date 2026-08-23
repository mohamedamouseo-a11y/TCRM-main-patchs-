# TCRM TEM Phase 5 — Track AI Migration

Patch ID: `TCRM_TEM_PHASE5_TRACK_AI_MIGRATION`

Purpose: make the already-applied Phase 5 migration file visible to Git/Developer Hub without weakening the repository-wide `*.sql` protection.

Target checkout: `/var/www/TCRM-MAIN`

Exact migration:

`drizzle/migrations/20260823_tem_ai_marketing_agent.sql`

The patch adds only this exact negation rule to the root `.gitignore`:

`!/drizzle/migrations/20260823_tem_ai_marketing_agent.sql`

Safety boundaries:

- Does not switch, pull, reset, merge, rebase, commit, or push TCRM.
- Does not modify the migration content.
- Does not execute any database migration.
- Does not send email or change TEM workers/scheduler/runtime settings.
- Keeps the broad `*.sql` ignore rule in force for every other SQL file.
- Requires the current `.gitignore` Git blob baseline `834799ad53a9269933798db3c4b48442fd8debec` unless the exact rule is already present.
- Verifies the migration still contains additive `CREATE TABLE IF NOT EXISTS` statements for `tem_ai_proposals` and `tem_ai_audit_events` and rejects destructive SQL patterns.
- Backs up `.gitignore` under the ignored local patch-state directory and supports rollback.
- Runs `pnpm check`; known unrelated repository baseline errors are reported but TEM Phase 5-specific typecheck errors fail closed.
- Runs the TEM AI policy tests and the production build.

Apply:

```bash
bash patches/TCRM_TEM_PHASE5_TRACK_AI_MIGRATION/APPLY.sh
```

Verify:

```bash
bash patches/TCRM_TEM_PHASE5_TRACK_AI_MIGRATION/VERIFY.sh
```

Rollback:

```bash
bash patches/TCRM_TEM_PHASE5_TRACK_AI_MIGRATION/ROLLBACK.sh
```

Expected apply marker:

`FINAL_MARKER=TCRM_TEM_PHASE5_MIGRATION_TRACKING_READY_OK`

Expected verify marker:

`FINAL_MARKER=TCRM_TEM_PHASE5_MIGRATION_TRACKING_VERIFY_OK`

After a successful apply, the migration should appear in `git status` and Developer Hub Review Push. The user performs the final commit/push manually from Developer Hub.
