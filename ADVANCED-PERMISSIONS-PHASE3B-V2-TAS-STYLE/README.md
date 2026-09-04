# Advanced Permissions Phase 3B V2 — TAS-style simple UX + per-user overrides

This package continues safely from the current working tree. If `ADVANCED-PERMISSIONS-PHASE3B-V1` is already applied, the V2 applier detects it and **does not replay V1**. If V1 is missing, V2 applies it once before the V2 additions.

Baseline: TCRM main at/after `a56f832ce06654d3c0e39ee673b306ae2daa74eb` (Phase 3A reviewed fixes landed).

## Product rules

1. Keep the engine advanced internally, but make the admin experience simple.
2. Basic role editor should look/behave like TAS:
   - one row/card per module;
   - action toggles/checkboxes for the actions that exist in that module;
   - one simple module Data Scope selector used as the default for allowed actions;
   - bulk actions: View Only / Full Access / Clear;
   - Advanced toggle expands per-action effect/scope so no engine capability is lost.
3. Add a **User Overrides** tab/section:
   - select a concrete user;
   - show their base role(s);
   - for every module/action choose `Inherit`, `Allow`, or `Deny`;
   - Allow can choose a scope; Deny is always `none`;
   - optional reason + start/end dates are supported by API; UI may keep dates under Advanced override options;
   - effective rule stays: explicit user deny > explicit user allow > role permissions > legacy fallback.
4. `ServiceAdvisor`, `PartsAgent`, `CrmFollowUp` are Automotive-only legacy roles and are NOT active/selectable TCRM roles anymore.
   - they are removed from client/server `APP_USER_ROLES`;
   - they are not seeded for new Phase1 installs;
   - previously seeded RBAC rows are hidden from Roles & Permissions;
   - legacy normalization strings remain temporarily for safe compatibility with old DB records. Do not add them back to selectable lists.
5. Do not delete or rewrite old DB users automatically in this patch. If old users still carry those role strings, report them; migration/reassignment must be deliberate.
6. Keep Admin/Developer/SalesManager/SalesAgent/ColdSalesAgent/TechnicalAccountManager/AccountManager/AccountManagerLead/Viewer/MediaBuyer/BusinessDeveloper/Moderator plus dynamic custom roles.
7. Keep existing account-management, TAM, TOS, moderator, developer, and legacy guards. New RBAC is additive.

## Phase 3B enforcement in this package

From V1:
- Activities: permission action + Lead data scope.
- Client Tasks: permission action + Client/assignment scope; `tasks.assign` required only when changing assignment.
- Contracts: permission action + Client/renewal assignment scope.
- Unsupported `department`, `created_by`, `custom`, `none` remain fail-closed for these Phase3B entities until explicit semantics exist.
- Meetings/Felfel/TAM meeting flows are not touched.

## Apply deterministic part

```bash
python3 ADVANCED-PERMISSIONS-PHASE3B-V2-TAS-STYLE/APPLY_PATCH.py /var/www/TCRM-MAIN
```

The applier:
- detects whether Phase3B V1 is already present and skips replay when it is;
- otherwise applies V1 once;
- installs `permissionUserOverrideAdmin.ts`;
- adds permission-admin API routes for users and overrides;
- removes Automotive-only roles from active role catalogs/new migration seed;
- hides old seeded Automotive RBAC roles from the Roles list;
- keeps legacy normalization compatibility only.

## Required UI adaptation after APPLY_PATCH

Modify `client/src/pages/RolesPermissions.tsx` with the smallest safe diff:

### A. Basic / Advanced role matrix
- default mode = Basic;
- group catalog by `moduleKey`;
- module row shows action toggles for its real actions only;
- each module has one scope selector; when changed in Basic mode it applies to every currently allowed permission in that module;
- Basic `Full Access` = allow every action in module with selected module scope;
- Basic `View Only` = only view allowed, other actions inherit/clear;
- Basic `Clear` = all actions inherit;
- `Advanced` reveals current per-permission `Allow / Deny / Inherit` + per-action scope controls exactly as Phase2 supported.

### B. User Overrides
Use:
- `permissionsAdmin.listUsersForPermissions`
- `permissionsAdmin.getUserPermissionProfile`
- `permissionsAdmin.replaceUserOverrides`

UI requirements:
- a tab/button named `User Overrides` / `استثناءات المستخدمين`;
- searchable user selector;
- display base role names and current override count;
- same module/action matrix, but tri-state `Inherit / Allow / Deny`;
- Inherit means no row in `user_permission_overrides`;
- Allow supports scope;
- Deny saves `effect=deny`, `dataScope=none`;
- save replaces overrides for the selected user only;
- show a clear warning that user override wins over role permission;
- no role is changed when saving user overrides.

## Validation

Run:

```bash
pnpm exec tsx scripts/verify-advanced-permissions-phase3b-v2.ts
NODE_OPTIONS=--max-old-space-size=8192 pnpm check
NODE_OPTIONS=--max-old-space-size=8192 pnpm build
NODE_OPTIONS=--max-old-space-size=8192 pnpm test
```

Do not commit/push/merge/reset/rebase. Stop and report results.
