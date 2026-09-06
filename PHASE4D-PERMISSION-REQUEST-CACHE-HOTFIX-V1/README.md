# Phase 4D — Permission Request Cache Hotfix V1

## Purpose
Reduce long page-loading latency caused by repeated permission-engine SQL inside the same tRPC HTTP batch, without changing permission semantics.

## Target state
- Project: `/var/www/TCRM-MAIN`
- Git HEAD must remain: `3e0aa9de85e55253dba928b5dedf96098286bec8`
- Phase 4D Field Permissions V1 must already be present in the working tree and remain uncommitted.
- Existing intentional DB RBAC fix for AccountManager role 12 is out of scope and must not be changed.

## Project files changed by this hotfix
1. `server/security/permissionEngine.ts`
2. `server/_core/trpc.ts`
3. `server/permissionsAdminRouter.ts`

Phase 4D already modifies these additional project files and they must remain untouched by this hotfix:
- `server/routers.ts`
- `client/src/pages/RolesPermissions.tsx`

Therefore after applying this hotfix the complete working-tree modified-file set relative to HEAD must be exactly these five files:
- `client/src/pages/RolesPermissions.tsx`
- `server/_core/trpc.ts`
- `server/permissionsAdminRouter.ts`
- `server/routers.ts`
- `server/security/permissionEngine.ts`

## Design

### Query-only request cache
Caching is enabled only when authorization runs for a tRPC **query**. Mutations deliberately bypass this request cache so a permission-changing mutation cannot authorize later work using stale data from the same HTTP batch.

The cache is stored in a `WeakMap` keyed by the Express request object. This means:
- no cross-request cache,
- no TTL,
- no global permission staleness,
- no user-to-user sharing,
- cache lifetime is bounded by the request object's lifetime.

### What is cached per request
- active assigned dynamic role IDs for the authenticated user,
- active user override rows keyed by `userId + permissionKey`,
- active role/permission graph rows keyed by `permissionKey`.

The role graph query no longer performs the correlated `EXISTS(user_roles...)` once per role. Active assigned role IDs are read once per request instead.

### Preserved semantics
- Super Admin bypass unchanged.
- User deny > user allow > dynamic role > legacy role > none unchanged.
- Temporary Access `starts_at` / `expires_at` unchanged.
- Role Inheritance traversal unchanged.
- Phase 4D `scope_config` / field policy unchanged.
- Data scopes unchanged.
- No DB/schema/migration changes.
- No cache for mutations.

## Apply
From an isolated copy first. Do **not** restart production during the first validation pass.

```bash
python3 PHASE4D-PERMISSION-REQUEST-CACHE-HOTFIX-V1/APPLY_PATCH.py /path/to/isolated/TCRM-MAIN
python3 PHASE4D-PERMISSION-REQUEST-CACHE-HOTFIX-V1/VERIFY.py /path/to/isolated/TCRM-MAIN
```

Only after isolated validation passes should the same patch be considered for the live working tree.

## Required verification before any production reload
- `VERIFY=PASS`
- exactly the expected five modified files relative to baseline
- no untracked files
- no schema/migration files
- query authorization uses request object cache
- mutation authorization explicitly bypasses cache
- correlated `EXISTS` removed from `evaluatePermission`
- user-role active/expiry predicates preserved
- Temporary Access predicates preserved
- Phase 4D `scope_config` reads preserved
- focused TypeScript validation shows no new errors from hotfix files
- build passes in the validation copy if resources permit

## Runtime acceptance after approved production apply
Measure the same authenticated page before/after and report actual timings. Do not claim a speedup from static inspection alone.

Required checks:
- auth/session still works
- Toka Mohamed still sees exactly clients `15,20,21,110,115`
- no unexpected client visibility
- permission decisions for representative users/permissions remain identical
- page loading improves measurably
- PM2 remains online

## Prohibited
- no DB writes
- no schema/migration changes
- no permission grants/revokes
- no unrelated code edits
- no file deletion
- no Git mutation in TCRM Main
- no production PM2 reload during isolated validation
