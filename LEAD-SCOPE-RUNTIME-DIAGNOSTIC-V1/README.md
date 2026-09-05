# LEAD-SCOPE-RUNTIME-DIAGNOSTIC-V1

Target repo: `/var/www/TCRM-MAIN`
Required baseline HEAD: `f7f6cfed2c6ae853e7683a4c66837311469bc16f`

## Purpose
Temporarily instrument the exact `assertRowScope()` denial path for Mohamed Hamed (`userId=130`) on Lead `2139` / `2147`.

Browser proof already confirms `trpc.leads.byId` returns:
`FORBIDDEN: Access denied: Lead #2139 is outside your permission scope`

Static source and bundled dist both contain the owner fallback and should allow `ownerId=130`, so capture the real runtime values at the denial point.

## Apply
Apply `LEAD-SCOPE-RUNTIME-DIAGNOSTIC-V1/lead-scope-runtime-diagnostic.patch` only.

The patch must change only:
`server/security/phase3ScopeFilters.ts`

The diagnostic log is intentionally gated to:
- `kind === "lead"`
- user id `130`
- lead id `2139` or `2147`

It logs only when `isRowInScope()` returns false.

## Validate
1. Confirm only the one target source file changed.
2. Run the existing `server/security/phase3ScopeFilters.test.ts` regression test.
3. Run `npm run build`.
4. Reload only `tamiyouz-crm` with the existing safe PM2 method.
5. Reproduce `/leads/2139` once as Mohamed Hamed.
6. Capture the single `[RBAC_SCOPE_DENY_DIAG]` JSON line from PM2 logs.

Do not change DB/RBAC data.
Do not modify other source files.
Do not commit/push/reset/stash/clean/rebase.

## Report
Return only:

`BASELINE_HEAD=`
`FILES_CHANGED=`
`FOCUSED_TESTS=`
`BUILD=`
`PM2_RELOAD=`
`DIAG_LOG=`
`RUNTIME_KIND=`
`RUNTIME_SCOPE=`
`RUNTIME_DECISION_ALLOWED=`
`RUNTIME_DECISION_SOURCE=`
`RUNTIME_USER_ID=`
`RUNTIME_USER_ID_TYPE=`
`RUNTIME_ROLE=`
`RUNTIME_ROW_ID=`
`RUNTIME_OWNER_ID=`
`RUNTIME_OWNER_ID_TYPE=`
`ROOT_CAUSE_CONFIRMED=YES/NO`
`ROOT_CAUSE=`
`GIT_OPS=NONE`
