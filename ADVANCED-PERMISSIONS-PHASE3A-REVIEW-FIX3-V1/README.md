# Advanced Permissions Phase 3A — Review Fix 3 V1

Verifier-only correction after Fix 2.

## Why
Fix 2 correctly imports `getDealsScoped` and removes the Phase 3A TS2304 error, but its verifier required only the inline form:

`getDealsScoped(dealPermissionScopeSql(ctx))`

The actual correct code uses:

```ts
const scopeSql = dealPermissionScopeSql(ctx);
return getDealsScoped(scopeSql);
```

Fix 3 updates only the verifier so it accepts either equivalent safe form.

## Production changes
None. No router, DB, permission engine, schema, role, or scope mapping is modified.

## Apply

```bash
python3 ADVANCED-PERMISSIONS-PHASE3A-REVIEW-FIX3-V1/APPLY_PATCH.py /var/www/TCRM-MAIN
cd /var/www/TCRM-MAIN
pnpm exec tsx scripts/verify-advanced-permissions-phase3a-fix2.ts
```

Then run the normal check/build/test commands. Do not start Phase 3B.
