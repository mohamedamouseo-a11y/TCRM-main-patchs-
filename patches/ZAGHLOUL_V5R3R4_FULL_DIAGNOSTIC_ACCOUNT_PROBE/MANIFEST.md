# ZAGHLOUL_V5R3R4_FULL_DIAGNOSTIC_ACCOUNT_PROBE

Target: `/var/www/TCRM-MAIN`
Parent: `ZAGHLOUL_V5R3R3_BASELINE_DEPENDENCY_PARITY_TSC`
Baseline: `c7ca52c5bb0495400ed327601d50cf6c7a363c73`

## Purpose
R3 correctly reached TypeScript comparison but exited before the account probe when candidate-only diagnostics existed. Its account probe also used top-level await in `tsx -e`, which can fail depending on tsx/esbuild mode.

R4 is verification-only and fixes evidence collection:
- same baseline/candidate dependency environment as R3;
- location-independent multiset comparison;
- NEVER hide candidate-only diagnostics;
- write and print each candidate-only diagnostic as `NEW_TS_ERROR=...`;
- run account probe even when TSC has new errors;
- account probe uses an async IIFE, not top-level await;
- emit final verdict only after both TSC and account probes complete.

No TCRM source, database, dependency, PM2, or git history mutation is allowed.

Success marker:
`ZAGHLOUL_V5R3R4_FULL_DIAGNOSTIC_ACCOUNT_PROBE_OK`
