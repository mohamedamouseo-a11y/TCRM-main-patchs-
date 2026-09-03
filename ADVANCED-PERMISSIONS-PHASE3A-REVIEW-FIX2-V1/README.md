# Advanced Permissions Phase 3A — Review Fix 2 V1

Target baseline: Phase 3A + Review Fix 1 applied on TCRM commit `be2017a36a2ebc1b4c824606183d3da98682385a`.

## Finding
`server/routers.ts` calls `getDealsScoped(...)` in the Phase 3A deals list path, while `getDealsScoped` is exported by `server/db.ts` but missing from the large `from "./db"` import list. This produces TypeScript error `TS2304: Cannot find name 'getDealsScoped'` and can become a runtime ReferenceError when that route executes.

## Scope
This patch does exactly one code change:
- add `getDealsScoped` to the existing `server/routers.ts` import list from `./db`.

It also installs a tiny verifier script.

No other permissions, mappings, roles, routers, DB schema, migrations, Phase 3B work, or git operations are performed.

## Apply
```bash
python3 ADVANCED-PERMISSIONS-PHASE3A-REVIEW-FIX2-V1/APPLY_PATCH.py /var/www/TCRM-MAIN
cd /var/www/TCRM-MAIN
pnpm exec tsx scripts/verify-advanced-permissions-phase3a-fix2.ts
pnpm check
pnpm build
pnpm test
```
