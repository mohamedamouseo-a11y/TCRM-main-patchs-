# ZAGHLOUL_V5R3R2_TSC_LOCATION_NORMALIZATION_ACCOUNT_PROBE

Target: `/var/www/TCRM-MAIN`
Parent: `ZAGHLOUL_V5R3R1_ACCOUNT_AUTH_TSC_HARDENING`
Baseline: `c7ca52c5bb0495400ed327601d50cf6c7a363c73`

## Diagnosis
V5R3R1 reported baseline=230, candidate=230, but 9 candidate-only diagnostics. Those 9 diagnostics are from code already present in the baseline `v5Service.ts`; V5R3 inserted/changed lines elsewhere, so `(line,column)` moved and the verifier treated the same pre-existing diagnostic as new.

Examples already present at baseline:
- `chats?.total`
- `result?.messages`
- `settings?.mediaStorageEnabled`
- `settings?.webhookUrl`
- `settings?.allowedOrigins`
- `settings?.rateLimits`

Therefore the correct gate is **diagnostic identity independent of source location**, while still preserving multiplicity.

## Correct TypeScript comparison
Normalize each `tsc --pretty false` diagnostic to:

`relative-file-path :: TS-code :: message`

Strip only the `(line,column)` location. Compare using a multiset/Counter, not a Set, so an additional duplicate diagnostic is still detected.

Required:
- baseline and candidate run with `NODE_OPTIONS=--max-old-space-size=16384`;
- capture exit codes;
- reject OOM/signal exits including 137/134/9;
- allow normal TypeScript exits 0/1/2;
- report raw diagnostic counts;
- report normalized candidate-only multiplicity as `TSC_NEW_ERROR_COUNT`;
- require `TSC_NEW_ERROR_COUNT=0`.

## Account-management proof
Do not trust a manually written result file. Execute `getZaghloulV5Settings()` against the live target runtime and require:

`authMode === "TCRM_SESSION"`

Also prove the Zaghloul V5 settings route remains behind `protectedProcedure` / TCRM auth. No second auth system is permitted.

## Scope
Verification-only. Do not modify TCRM source, database, dependencies, package/lock files, PM2, or git history.

Success marker:
`ZAGHLOUL_V5R3R2_TSC_LOCATION_NORMALIZATION_ACCOUNT_PROBE_OK`
