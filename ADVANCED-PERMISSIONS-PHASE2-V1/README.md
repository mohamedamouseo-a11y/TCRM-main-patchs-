# TCRM Advanced Permissions — Phase 2 V1

Baseline inspected: `TCRM-MAIN-Tamiyouz-CRM-` main at `5fe3f9b81fdcc9f032cdd80d65e45a941d8f85d8`.

This patch builds on Advanced Permissions Phase 1 and adds the administration surface only. It does **not** implement Phase 3 data-scope query filtering or field-level permissions.

## What Phase 2 adds

- Admin route: `/settings/roles-permissions`
- Roles list with active/system state, user count and permission count
- Create custom role
- Edit role display metadata
- Duplicate role with its role permissions
- Activate/deactivate custom roles
- Delete custom roles only when they are not assigned to active users
- Permission Matrix based strictly on the Phase 1 permission catalog
- Tri-state permission assignment: Not assigned / Allow / Explicit deny
- Data scope selector: all, team, department, own, assigned, created_by, custom, none
- Bulk presets: Clear all, View only, Full access
- Search + module filter
- Server-side tRPC permission guards using `roles.view`, `roles.create`, `roles.edit`, `roles.delete`, `roles.assign_permissions`
- Permission audit records in `permission_audit_logs`
- Admin-only sidebar entry; backend remains the security authority

## Intentionally NOT included

- No `users.role` removal or enum changes
- No global router migration
- No sidebar hiding for all modules based on dynamic permissions
- No Leads/Deals/Clients query scope filtering
- No field-level masking
- No user override UI
- No temporary access UI
- No role inheritance UI
- No automatic database migration (Phase 1 tables must already exist)
- No git commit/push/reset/rebase

## Apply

From the patch folder:

```bash
python3 APPLY_PATCH.py /var/www/TCRM-MAIN
```

The applier checks for Phase 1, copies four implementation files, and applies marker-based changes only to:

- `server/routers.ts`
- `client/src/App.tsx`
- `client/src/components/CRMLayout.tsx`
- `client/src/lib/i18n.ts`

Backups are placed under `.patch-backups/advanced-permissions-phase2-<timestamp>/`.

## Verify

```bash
cd /var/www/TCRM-MAIN
pnpm exec tsx scripts/verify-advanced-permissions-phase2.ts
pnpm check
pnpm build
pnpm test
```

Known pre-existing test failure from Phase 1 baseline may remain:

`twsCollaborationRouter.v2c.test.ts` → `User access is inactive`

Do not classify that as a Phase 2 regression unless its behavior changes or additional permission-related tests fail.

## Security notes

System roles cannot be deactivated or deleted by the new service. A custom role assigned to active users cannot be deleted. All role mutations are protected server-side and audited. Data scopes are stored in `role_permissions` but are not yet used to filter module queries; that enforcement is reserved for Phase 3.
