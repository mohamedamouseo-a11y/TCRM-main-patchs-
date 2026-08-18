# Execute ZAGHLOUL_V5R3R1_ACCOUNT_AUTH_TSC_HARDENING

Target: `/var/www/TCRM-MAIN`

Run exactly:

1. `APPLY.sh`
2. `VERIFY.sh`

Do not edit unrelated source. Do not install dependencies. Do not git commit/push. Do not fake probe/results data.

Success requires the verifier to print:
- `ACCOUNT_MANAGEMENT=PASS`
- `AUTH_MODE=TCRM_SESSION`
- normal `TSC_BASELINE_EXIT` and `TSC_CANDIDATE_EXIT` (0/1/2 only; never 137)
- `TSC_NEW_ERROR_COUNT=0`
- `TESTS=PASS`
- `BUILD=PASS`
- `FINAL_MARKER=ZAGHLOUL_V5R3R1_ACCOUNT_AUTH_TSC_HARDENING_OK`

Return only those final fields plus any failing diagnostic if verification stops.
