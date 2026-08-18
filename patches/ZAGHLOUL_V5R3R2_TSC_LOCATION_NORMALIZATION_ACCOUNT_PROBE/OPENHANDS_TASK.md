# OPENHANDS TASK — ZAGHLOUL_V5R3R2_TSC_LOCATION_NORMALIZATION_ACCOUNT_PROBE

Target: `/var/www/TCRM-MAIN`

1. Run this patch's `APPLY.sh`.
2. Run this patch's `VERIFY.sh`.
3. Do **not** modify TCRM source, database, dependencies, package/lock files, PM2, or git history.
4. Do not rewrite the reported pre-existing TypeScript errors. This phase verifies that they are baseline-equivalent after location normalization.
5. If verification fails, return the exact failing field/output only. Do not fake or manually edit verifier output.
6. Success requires:
   - ACCOUNT_MANAGEMENT=PASS
   - AUTH_MODE=TCRM_SESSION
   - TSC baseline/candidate exits are normal TypeScript exits (0/1/2), never 137/134/9
   - TSC_NEW_ERROR_COUNT=0 after location-independent multiset comparison
   - FINAL_MARKER=ZAGHLOUL_V5R3R2_TSC_LOCATION_NORMALIZATION_ACCOUNT_PROBE_OK

Return only:
ACCOUNT_MANAGEMENT
AUTH_MODE
TSC_BASELINE_EXIT
TSC_CANDIDATE_EXIT
TSC_BASELINE_ERRORS
TSC_CANDIDATE_ERRORS
TSC_NEW_ERROR_COUNT
FINAL_MARKER
