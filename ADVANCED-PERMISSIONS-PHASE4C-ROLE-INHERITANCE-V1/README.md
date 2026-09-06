# Advanced Permissions Phase 4C — Role Inheritance V1

Target baseline:
`7da712b977843ee28c2de2b49b7cc6ad94338a41`

Target project path on server:
`/var/www/TCRM-MAIN`

## Scope
This phase activates role inheritance using the existing `roles.parent_role_id` column. No DB schema or migration is added.

It changes only:
- `server/security/permissionAdminService.ts`
- `server/permissionsAdminRouter.ts`
- `server/security/permissionEngine.ts`
- `client/src/pages/RolesPermissions.tsx`

## Behavior
- Create/Edit Role can optionally select a parent role.
- Parent role must exist and be active.
- Self-parenting and inheritance cycles are rejected server-side.
- A child role inherits a permission only when that child has no direct assignment for that permission.
- A direct child Allow/Deny overrides the inherited value for that role chain.
- With multiple assigned roles, the existing deny-wins behavior remains unchanged across the effective role results.
- User override precedence remains unchanged:
  Super Admin → user deny → user allow → dynamic role (with inheritance) → legacy role (with inheritance) → deny.
- Legacy roles may also inherit through the same existing parent relation.
- Permission Tester automatically reflects the effective inherited result through the existing engine.

## Must NOT change
- DB schema or migrations.
- User Override / Temporary Access behavior.
- Permission scope semantics.
- `users.role` legacy semantics.
- Sales/TAM/TOS/Account Management guards.
- Tara / WhatsApp / Messenger / Meetings / Felfel flows.

## Apply
From a checkout of this patch branch:

```bash
python3 ADVANCED-PERMISSIONS-PHASE4C-ROLE-INHERITANCE-V1/APPLY_PATCH.py /var/www/TCRM-MAIN
python3 ADVANCED-PERMISSIONS-PHASE4C-ROLE-INHERITANCE-V1/VERIFY.py /var/www/TCRM-MAIN
```

Then from `/var/www/TCRM-MAIN`:

```bash
NODE_OPTIONS=--max-old-space-size=8192 pnpm check
NODE_OPTIONS=--max-old-space-size=8192 pnpm build
pm2 reload tamiyouz-crm --update-env
```

`pnpm check` may still show pre-existing unrelated errors; report them without fixing them.

## Safety
- No DB writes are required just to apply/verify the patch.
- Do not create test roles/users just for verification.
- Do not modify unrelated dirty files.
- No commit/push/pull/merge/rebase in the target project.
- Do not run git clean/reset/restore/checkout/stash.
- Do not delete any project file.

## Expected report

```text
HEAD_BEFORE=
FILES_CHANGED=
UNTRACKED_FILES=
PATCH_APPLIED=
VERIFY=
CHECK=
BUILD=
PM2_RELOAD=
PARENT_ROLE_UI=YES/NO
CYCLE_GUARD=YES/NO
DIRECT_CHILD_OVERRIDE=YES/NO
INHERITED_PERMISSION_ENGINE=YES/NO
PRECEDENCE_UNCHANGED=YES/NO
DB_CHANGES=YES/NO
NEEDS_ADAPTATION=YES/NO
GIT_OPS=NONE
STATUS=
```
