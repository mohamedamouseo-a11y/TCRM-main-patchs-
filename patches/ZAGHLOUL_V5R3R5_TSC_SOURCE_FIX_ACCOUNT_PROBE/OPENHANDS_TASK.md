# OpenHands task — ZAGHLOUL_V5R3R5_TSC_SOURCE_FIX_ACCOUNT_PROBE

Target: `/var/www/TCRM-MAIN`

Execute exactly:

```bash
bash patches/ZAGHLOUL_V5R3R5_TSC_SOURCE_FIX_ACCOUNT_PROBE/APPLY.sh
bash patches/ZAGHLOUL_V5R3R5_TSC_SOURCE_FIX_ACCOUNT_PROBE/VERIFY.sh
```

If the patch repo is cloned separately, run the two scripts from that clone and keep `TCRM_PATH=/var/www/TCRM-MAIN`.

Do not edit source manually beyond what `APPLY.sh` does. Do not install dependencies. Do not alter DB data. Do not create commits or push TCRM.

Return only these lines (and every `NEW_TS_ERROR=` line if any):

`PRECHECK`
`DEPENDENCY_MANIFEST_MISMATCH`
`MISPLACED_NEXT_PAGE`
`TSC_BASELINE_EXIT`
`TSC_CANDIDATE_EXIT`
`TSC_BASELINE_ERRORS`
`TSC_CANDIDATE_ERRORS`
`TSC_NEW_ERROR_COUNT`
`ACCOUNT_MANAGEMENT`
`AUTH_MODE`
`BUILD`
`PM2`
`HTTP_ZAGHLOUL`
`HTTP_ZAGHLOUL_V5`
`HTTP_ZAGHLOUL_LEGACY`
`BASELINE_HEAD`
`CANDIDATE_HEAD`
`FINAL_MARKER`
