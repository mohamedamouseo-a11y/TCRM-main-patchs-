# TCRM Advanced Permissions — Phase 3B V1

Target TCRM main baseline: `a56f832ce06654d3c0e39ee673b306ae2daa74eb`.

Scope: backend enforcement for **Activities, Client Tasks, Contracts** only.

## Security rules

This phase must only NARROW access. Existing Sales/TAM/Account-Management/TOS security remains authoritative and must execute as well.

### Activities
Permissions: `activities.view/create/edit/delete`.
Data scope follows the activity's parent Lead, using the already-reviewed Phase 3A lead scope semantics:
- all: allowed (subject to existing guards)
- own: lead owner only
- assigned: active lead assignment only (separate from owner)
- team: lead owner's team
- department / created_by / custom / none: deny-by-default

`byUser` must not bypass lead scope. Use the scoped DB helper installed by this patch, not an unscoped fetch followed by frontend filtering.

### Client Tasks
Permissions: `tasks.view/create/edit/delete/assign`.
Scope mapping is schema-grounded:
- all: allowed, subject to existing task/account-management security
- own: parent client `accountManagerId == user.id`
- assigned: task `assignedTo == user.id`
- team: parent client's account manager belongs to `user.teamId`
- department / created_by / custom / none: deny-by-default

For create under `assigned` scope, `assignedTo` must equal the caller. For `own/team`, the parent client must be in scope. Existing TOS assignee/project membership checks remain unchanged.

### Contracts
Permissions: `contracts.view/create/edit/delete/export`.
Scope mapping:
- all: allowed
- own: parent client's `accountManagerId == user.id`
- assigned: contract `renewalAssignedTo == user.id`
- team: parent client's account manager belongs to `user.teamId`
- department / created_by / custom / none: deny-by-default

Existing `assertAccountManagementClientAccess`, `assertAccountManagementContractAccess`, renewal assignment rules, and AccountManager restrictions must remain.

## Expected changes
- Add `server/security/phase3bScope.ts`.
- Add Phase 3B permission middleware exports in `server/_core/trpc.ts`.
- Integrate Activities / Client Tasks / Contracts routes in `server/routers.ts`.
- Add `getActivitiesByUserScoped()` in `server/db.ts` so activity feed scope is enforced at SQL source.
- Add verifier `scripts/verify-advanced-permissions-phase3b.ts`.

## Explicitly excluded
- Meetings/Felfel/TAM meeting flows (deferred until separately mapped; do not alter them here).
- Phase 4 field permissions/user override UI/inheritance/temporary access.
- Phase 5 caching/hardening beyond tests needed for this phase.
- `users.role` changes.

## Validation
Run:

```bash
pnpm exec tsx scripts/verify-advanced-permissions-phase3b.ts
NODE_OPTIONS=--max-old-space-size=8192 pnpm check
NODE_OPTIONS=--max-old-space-size=8192 pnpm build
NODE_OPTIONS=--max-old-space-size=8192 pnpm test
```

If unrelated pre-existing TypeScript/test failures remain, report them; do not fix them. No git commit/push/merge/reset/rebase.