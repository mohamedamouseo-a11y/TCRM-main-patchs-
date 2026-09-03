# TCRM Advanced Permissions — Phase 1 Foundation V1

Target source repository: `mohamedamouseo-a11y/TCRM-MAIN-Tamiyouz-CRM-` branch `main`.

This package lives only in the patches repository. It does **not** modify or push to TCRM `main`.

## Scope

Phase 1 establishes the permission foundation only:

- Dynamic `roles` table.
- Dynamic `permissions` catalog.
- `role_permissions` grants with data scope.
- `user_roles` many-to-many assignments.
- `user_permission_overrides` explicit allow/deny.
- `permission_audit_logs` for permission changes.
- Legacy user-role migration/compatibility.
- Central permission engine.
- Super-admin/legacy-admin compatibility bypass to avoid lockout during rollout.
- Reusable tRPC permission guards for later module integration.
- Verification script.

Phase 1 intentionally does **not** convert every existing router/module to the new engine. That belongs to Phase 3.

## Files installed into TCRM

- `scripts/apply-advanced-permissions-phase1-migration.ts`
- `scripts/verify-advanced-permissions-phase1.ts`
- `server/security/permissionEngine.ts`
- `server/security/permissionCatalog.ts`
- `server/security/permissionProcedure.ts`

It also patches:

- `package.json` with migration/verification scripts.
- `server/_core/trpc.ts` to export reusable `permissionProcedure(...)` and `anyPermissionProcedure(...)` wrappers while preserving existing `protectedProcedure` / `adminProcedure` behavior.

## Apply

From a checkout of the target TCRM repository:

```bash
python3 APPLY_PATCH.py /path/to/TCRM
```

Then run:

```bash
pnpm db:migrate:advanced-permissions-phase1
pnpm verify:advanced-permissions-phase1
pnpm check
```

## Compatibility / lockout policy

The engine is deny-by-default for permission keys once a user is evaluated through the new guard, but Phase 1 does not replace existing router guards automatically.

Super-admin bypass is granted when any of these match:

- role normalized to `superadmin` or `super_admin`;
- email is listed in `PERMISSIONS_SUPER_ADMIN_EMAILS` (comma separated);
- legacy `Admin` role while `PERMISSIONS_LEGACY_ADMIN_BYPASS` is not explicitly `false`.

The legacy Admin bypass exists only to prevent deployment lockouts while roles are migrated. It can be disabled after the permission center is populated.

## Data scopes

Supported scopes in Phase 1:

- `all`
- `team`
- `department`
- `own`
- `assigned`
- `created_by`
- `custom`
- `none`

The engine returns the effective scope. Query-level enforcement is performed by each module during Phase 3.

## Resolution priority

1. Super-admin bypass.
2. Explicit user deny override.
3. Explicit user allow override.
4. Grants inherited from active dynamic roles.
5. Legacy role mapping fallback seeded by migration.
6. Deny.

Explicit deny always wins over grants.

## Rollback

The migration creates new tables and does not remove the existing `users.role` column. If rollout must be abandoned, stop using the new permission guards and drop the six Phase-1 tables manually after confirming no later phase depends on them.
