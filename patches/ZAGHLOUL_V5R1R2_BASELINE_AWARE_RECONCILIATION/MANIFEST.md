# ZAGHLOUL_V5R1R2_BASELINE_AWARE_RECONCILIATION

Target: `/var/www/TCRM-MAIN`

## Purpose
Cumulative verification-only corrective over `ZAGHLOUL_V5R1R1_POST_APPLY_RECONCILIATION`.

V5R1R1 correctly verified the deployed source blobs, routes, build, PM2 and HTTP, but incorrectly required the whole repository to have zero TypeScript errors. OpenHands verified the current repository has an accepted pre-existing TSC baseline of 191 errors while the V5R1 touched files themselves introduce no errors.

## Verified deployed source guards
- `client/src/App.tsx`: `242bd67ff1766f00decf66d7a91fcb2c83552856`
- `client/src/pages/ZaghloulV5Page.tsx`: `a7b7d15671c9f8a6fed17608d8b07adad62920b8`

## Accepted legacy TSC ceiling
- `191` errors, verified before this corrective.
- This corrective does **not** approve future TypeScript growth.

## Verification model
1. Exact deployed source blob guards must pass.
2. Static V5 route/tRPC checks must pass.
3. Run a clean non-incremental TSC baseline with increased Node heap to avoid the prior OOM false failure.
4. TSC baseline may contain legacy errors, but:
   - total errors must not exceed the accepted ceiling of 191;
   - `client/src/App.tsx` must have zero TypeScript errors;
   - `client/src/pages/ZaghloulV5Page.tsx` must have zero TypeScript errors.
5. Run production build.
6. Re-verify the exact source blobs after build.
7. Run clean non-incremental TSC again and compare normalized error fingerprints against the first run.
8. Require `TSC_NEW_ERROR_COUNT=0` and the same patch-scope zero-error rule.
9. Verify PM2 is online and `/zaghloul`, `/zaghloul-v5`, `/zaghloul-legacy` all return HTTP 200.
10. No production source mutation and no PM2 reload are performed.

## Non-scope
- No source edits.
- No DB migration.
- No dependency install/update.
- No WhatsApp configuration changes.
- No WACRM feature expansion.
- No production Git push.

## Success marker
`ZAGHLOUL_V5R1R2_BASELINE_AWARE_RECONCILIATION_OK`
