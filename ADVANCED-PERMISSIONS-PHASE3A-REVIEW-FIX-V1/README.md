# Advanced Permissions Phase 3A — Reviewed Fix V1

Target reviewed TCRM main commit: `be2017a36a2ebc1b4c824606183d3da98682385a`.

This is a narrow corrective patch for the already-applied Phase 3A implementation.

## Review findings

1. `own` and `assigned` were treated identically for Leads, Deals and Clients. This can broaden access beyond the requested scope semantics.
2. Lead export builds the scope against alias `l.ownerId`, while the `assigned` subquery in `phase3ScopeFilters.ts` hardcoded `leads.id`. That can produce invalid SQL on export when the `leads` table is aliased as `l`.
3. `department`, `created_by`, `custom`, and `none` correctly deny by default because the current schema does not provide a safe mapping.
4. Existing legacy row-level security remains in place and should continue to narrow access.

## Correct semantics in this patch

- Lead `own`: `lead.ownerId = current user` only.
- Lead `assigned`: active `lead_assignments` row for current user only.
- Deal `own`: linked lead owner is current user.
- Deal `assigned`: active assignment on linked lead for current user.
- Client `own`: `accountManagerId = current user` only.
- Client `assigned`: `accountManagerId = current user` only (the current schema has no separate direct client assignment table).
- Team: existing owner/account-manager team mapping remains.
- Unsupported scopes: deny-by-default.

## Files replaced

- `server/security/phase3ScopeFilters.ts`
- `scripts/verify-advanced-permissions-phase3a.ts`

No database migration. No Phase 3B. No git commands are executed by the patch.

## Apply

```bash
python3 ADVANCED-PERMISSIONS-PHASE3A-REVIEW-FIX-V1/APPLY_PATCH.py /var/www/TCRM-MAIN
```

## Verify

```bash
pnpm exec tsx scripts/verify-advanced-permissions-phase3a.ts
pnpm check
pnpm build
pnpm test
```
