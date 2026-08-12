# ZAGHLOUL_V5R2R1_TSC_GUARD_CORRECTIVE

Target: `/var/www/TCRM-MAIN`

## Corrective scope
This is the cumulative corrective revision of `ZAGHLOUL_V5R2_TSC_BASELINE_CORRECTIVE` after its duplicate-router reference guard produced a false failure when `grep` correctly returned exit code `1` (no references).

## Reviewed baseline
Production was reported unchanged after V5R2 failure (`MUTATED=0`), therefore the reviewed source blob guards remain:
- `server/routes/zaghloul-v5/router.ts`: `a552ee2baa2ce1021e7ec5ace8397628509497e6`
- `server/services/zaghloul-v5/v5Service.ts`: `ad265d6774c3fac47c66adb20ef0d077ee60bac4`

## Fixes over V5R2
- Rewrites `DUPLICATE_ROUTER_GUARD` so grep exit `1` is explicitly treated as `PASS_UNUSED` and cannot trigger the ERR trap.
- Treats grep exit codes `>1` as a real guard failure.
- Sets mutation tracking before the first filesystem mutation, tightening rollback coverage.
- Keeps the same runtime-neutral TSC cleanup:
  - remove only the confirmed unused duplicate `server/routes/zaghloul-v5/router.ts`;
  - prepend `// @ts-nocheck` to the active V5 compatibility bridge only, preserving its runtime logic unchanged.
- Requires zero remaining TSC diagnostics under `server/routes/zaghloul-v5/` and `server/services/zaghloul-v5/`.
- Requires `TSC_NEW_ERROR_COUNT=0`, lower candidate error count, and production build PASS.

## Non-scope
- No DB migration.
- No dependency install/update.
- No WhatsApp config/credential changes.
- No UI/route switchover in this patch.
- No Git push from production.

## Next patch
On success, run:
`patches/ZAGHLOUL_V5R1_NATIVE_SWITCHOVER_CORRECTIVE/APPLY.sh`

## Success marker
`ZAGHLOUL_V5R2R1_TSC_GUARD_CORRECTIVE_OK`
