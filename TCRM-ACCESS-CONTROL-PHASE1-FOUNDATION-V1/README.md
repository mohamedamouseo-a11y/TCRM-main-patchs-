# TCRM Access Control — Phase 1 Foundation V1

Target source repository: `mohamedamouseo-a11y/TCRM-MAIN-Tamiyouz-CRM-`

Baseline inspected: `main` at commit `09ebaf500f3a06ad8650b204752e59a1f7c3fd5e`.

## What this patch adds

This is the first safe foundation for the new enterprise permissions system. It is intentionally **shadow-mode first** and does not replace the existing hard-coded TCRM role checks yet.

It adds:

- Central permission registry using `module.resource.action` keys.
- RBAC candidates from multiple roles.
- Explicit `DENY` precedence over any `ALLOW`.
- Data scopes: `own`, `assigned`, `team`, `department`, `branch`, `custom`, `all`.
- Safe structured ABAC conditions (`eq`, `neq`, `in`, `not_in`, `lt`, `lte`, `gt`, `gte`, `exists`).
- Direct user overrides.
- Temporary access grants with start/end times.
- Legacy-role bridge for gradual migration.
- Access decision logging.
- Organization-unit foundation for organization / branch / department / team.
- Admin API for roles, role permissions, user assignment, overrides, temporary grants and access simulation.
- Default-deny behavior when no matching policy exists.
- Admin bootstrap only; non-admin operational roles intentionally start without new-engine permissions until reviewed.

## Patch layout

`payload/` contains new source files that must be copied into the TCRM root preserving paths.

`INTEGRATION.patch` only mounts the new `accessControlRouter` inside `server/routers.ts`.

No file in this patch repository is a replacement for the TCRM repository itself.

## Safe apply sequence

From a clean checkout of TCRM main:

```bash
# 1. Copy payload while preserving paths
cp -R /path/to/TCRM-ACCESS-CONTROL-PHASE1-FOUNDATION-V1/payload/. ./

# 2. Verify integration patch first
git apply --check /path/to/TCRM-ACCESS-CONTROL-PHASE1-FOUNDATION-V1/INTEGRATION.patch

# 3. Apply router integration
git apply /path/to/TCRM-ACCESS-CONTROL-PHASE1-FOUNDATION-V1/INTEGRATION.patch

# 4. DB migration dry-run
npx tsx scripts/apply-access-control-phase1-migration.ts

# 5. Apply migration
npx tsx scripts/apply-access-control-phase1-migration.ts --apply

# 6. Tests / TypeScript gate
npx vitest run server/services/accessControl/accessDecision.test.ts
npm run check
```

## Runtime mode

Phase 1 reports:

```text
mode = shadow
```

The existing TCRM authorization remains authoritative for existing modules. The new engine is available through `accessControl.*` APIs for configuration, simulation, validation and later module-by-module migration.

## New API surface

- `accessControl.status`
- `accessControl.check`
- `accessControl.registry`
- `accessControl.overview`
- `accessControl.roles`
- `accessControl.rolePermissions`
- `accessControl.createRole`
- `accessControl.setRolePermission`
- `accessControl.assignRole`
- `accessControl.setUserOverride`
- `accessControl.grantTemporary`
- `accessControl.simulate`

## Security guarantees in this phase

1. New engine is default-deny.
2. Explicit deny wins over every allow source.
3. Only existing `adminProcedure` can mutate the access-control model.
4. Migration is additive and does not alter `users.role`.
5. Existing sidebar/API authorization is not removed.
6. Only the `Admin` compatibility role is seeded with full new-engine permissions; all other roles require review before being populated.
7. Temporary grants expire automatically through query-time validity checks.
8. Simulation decisions can be logged for audit/debugging.

## Next phase

Phase 2 should add the actual Access Control Center UI: Overview, Roles, Permission Matrix, Users, Data Scopes, Field Security, Policies, Temporary Access, Access Simulator and Decision Logs. After that, enforcement should move module-by-module behind a shadow comparison gate rather than globally in one release.
