# OpenHands / Replit task

Target: `/var/www/TCRM-MAIN`

Run exactly:

```bash
bash APPLY.sh
bash VERIFY.sh
```

Do not modify TCRM source, DB, dependencies, PM2, package/lock files, or git history.

Return every line beginning with one of:

- `PRECHECK=`
- `DEPENDENCY_MANIFEST_MISMATCH=`
- `TSC_BASELINE_EXIT=`
- `TSC_CANDIDATE_EXIT=`
- `TSC_BASELINE_ERRORS=`
- `TSC_CANDIDATE_ERRORS=`
- `TSC_NEW_ERROR_COUNT=`
- `NEW_TS_ERROR=`
- `ACCOUNT_MANAGEMENT=`
- `AUTH_MODE=`
- `ACCOUNT_PROBE_ERROR=`
- `BASELINE_HEAD=`
- `CANDIDATE_HEAD=`
- `FINAL_MARKER=`
