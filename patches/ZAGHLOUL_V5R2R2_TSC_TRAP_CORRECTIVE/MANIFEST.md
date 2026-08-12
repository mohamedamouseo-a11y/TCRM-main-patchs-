# ZAGHLOUL_V5R2R2_TSC_TRAP_CORRECTIVE

Target: `/var/www/TCRM-MAIN`

## Corrective scope
Cumulative correction over `ZAGHLOUL_V5R2R1_TSC_GUARD_CORRECTIVE`.

OpenHands confirmed V5R2R1 reached the TSC baseline with:
- `BASELINE_GUARD=PASS`
- `DUPLICATE_ROUTER_GUARD=PASS_UNUSED`
- `TSC_BASELINE_ERROR_COUNT=191`
- `V5_BASELINE_ERROR_COUNT=17`
- `MUTATED=0`

The remaining failure is shell control-flow only: the global `ERR` trap can fire around the intentionally failing `pnpm check` baseline before the return code is captured.

## Fix
- Do not use `set +e` around expected TSC failures.
- Run each `pnpm check` as the condition of an explicit `if ...; then ... else ... fi` block. Commands used as an `if` condition are expected-status probes and will not invoke the global `ERR` trap for a non-zero TSC result.
- Capture baseline/candidate RC explicitly.
- Preserve all V5R2R1 guards and runtime-neutral changes.
- Keep mutation tracking before the first filesystem mutation.

## Reviewed production blobs
Production was reported unchanged (`MUTATED=0`), therefore guards remain:
- `server/routes/zaghloul-v5/router.ts`: `a552ee2baa2ce1021e7ec5ace8397628509497e6`
- `server/services/zaghloul-v5/v5Service.ts`: `ad265d6774c3fac47c66adb20ef0d077ee60bac4`

## Required gates
- duplicate router confirmed unused
- V5 candidate diagnostics = 0
- TSC new diagnostics = 0
- candidate total < baseline total
- production build PASS

## Non-scope
No DB migration, dependency install/update, WhatsApp config changes, UI route switchover, or production Git push.

## Next patch
After success run:
`patches/ZAGHLOUL_V5R1_NATIVE_SWITCHOVER_CORRECTIVE/APPLY.sh`

## Success marker
`ZAGHLOUL_V5R2R2_TSC_TRAP_CORRECTIVE_OK`
