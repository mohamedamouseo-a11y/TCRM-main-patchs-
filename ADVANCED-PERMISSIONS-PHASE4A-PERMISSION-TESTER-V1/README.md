# Advanced Permissions — Phase 4A Permission Tester V1

## Baseline

Target TCRM Main HEAD must be exactly:

`46c97d6df963bcedb12150b226385026f5d549d7`

Target server path:

`/var/www/TCRM-MAIN`

## Scope

This subphase adds the read-only **Permission Tester** promised in Phase 4.

It deliberately does **not** implement the rest of Phase 4 yet. User Overrides were already delivered earlier in Phase 3B V2, so this package does not duplicate or rewrite them.

The tester lets an authorized permissions administrator:

- choose a user;
- test all permissions or one permission key;
- see the real result returned by the existing `evaluatePermission()` engine;
- see Allowed / Denied, effective Data Scope, decision source, role IDs when available, and a human-readable reason;
- diagnose Super Admin bypass, explicit user allow/deny, dynamic role grants/denies, legacy fallback, and no-grant results.

## Production files expected to change

Only:

- `server/permissionsAdminRouter.ts`
- `client/src/pages/RolesPermissions.tsx`

No DB migration. No schema change. No role rewrite. No permission-engine precedence change. No module/router enforcement changes.

## Apply

From a temporary checkout/download of this patch branch, run:

```bash
python3 ADVANCED-PERMISSIONS-PHASE4A-PERMISSION-TESTER-V1/APPLY_PATCH.py /var/www/TCRM-MAIN
```

The applier is baseline-pinned and marker-based. If the exact expected anchors do not match, stop and report the mismatch. Do not improvise a broad rewrite.

## Verify

Run the verifier from the patch package without copying it into TCRM:

```bash
python3 ADVANCED-PERMISSIONS-PHASE4A-PERMISSION-TESTER-V1/VERIFY.py /var/www/TCRM-MAIN
```

Then from `/var/www/TCRM-MAIN` run:

```bash
NODE_OPTIONS=--max-old-space-size=8192 pnpm check
NODE_OPTIONS=--max-old-space-size=8192 pnpm build
```

If `pnpm check` hits a known project-wide memory/pre-existing issue, report it exactly; do not modify unrelated code to make it pass.

After build, use the normal safe PM2 reload for `tamiyouz-crm` only, then open Roles & Permissions → Permission Tester and verify one user plus one individual permission.

## Safety rules

- No DB changes.
- No `git commit`, `git push`, `git pull`, `git merge`, `git reset`, `git rebase`, `git stash`, or `git clean`.
- Do not delete files or directories.
- Do not touch unrelated modified files if any are present; stop and report before applying if the target working tree is not at the expected baseline state.
- Preserve existing User Overrides, legacy role compatibility, Super Admin behavior, and all existing security guards.
- Do not start Field Permissions, Role Inheritance, Temporary Access UI, or Phase 5 in this task.

## Report

Return only:

```text
HEAD_BEFORE=
FILES_CHANGED=
UNTRACKED_FILES=
PATCH_APPLIED=YES/NO
VERIFY=PASS/FAIL
CHECK=
BUILD=
PM2_RELOAD=
TESTER_UI=PASS/FAIL
SAMPLE_USER=
SAMPLE_PERMISSION=
SAMPLE_RESULT=
SAMPLE_SCOPE=
SAMPLE_SOURCE=
SAMPLE_REASON=
NEEDS_ADAPTATION=YES/NO
GIT_OPS=NONE
STATUS=
```
