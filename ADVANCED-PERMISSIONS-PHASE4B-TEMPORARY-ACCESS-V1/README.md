# Advanced Permissions Phase 4B — Temporary Access V1

Target baseline:
`eb497212634c73a111b5ae7236797210be1a3a83`

Target project path on server:
`/var/www/TCRM-MAIN`

## Scope
This phase completes temporary access for **User Permission Overrides** without adding DB tables or changing the existing precedence model.

It changes only:
- `client/src/pages/RolesPermissions.tsx`
- `server/security/permissionEngine.ts`

## Behavior
- Preserve existing `startsAt`, `expiresAt`, and `reason` when an override profile is loaded and re-saved.
- Add optional **Starts at**, **Expires at**, and **Reason** controls to User Overrides UI.
- Blank start/end means permanent override.
- Reject expiry earlier than/equal to start in the UI before save.
- Show simple state: Permanent / Scheduled / Temporarily active / Expired.
- Permission Engine must enforce both boundaries:
  - future `starts_at` override is NOT effective yet.
  - expired `expires_at` override is NOT effective.
- Existing precedence remains unchanged:
  Super Admin → user deny → user allow → dynamic role → legacy role → deny.
- Existing Phase 4A Permission Tester remains unchanged.

## Must NOT change
- DB schema or migrations.
- Role permissions.
- Role assignment semantics.
- Sales/TAM/TOS/Account Management guards.
- Tara / WhatsApp / Messenger / Meetings / Felfel flows.
- `users.role` legacy behavior.

## Apply
From a checkout of this patch branch:

```bash
python3 ADVANCED-PERMISSIONS-PHASE4B-TEMPORARY-ACCESS-V1/APPLY_PATCH.py /var/www/TCRM-MAIN
python3 ADVANCED-PERMISSIONS-PHASE4B-TEMPORARY-ACCESS-V1/VERIFY.py /var/www/TCRM-MAIN
```

Then from `/var/www/TCRM-MAIN`:

```bash
NODE_OPTIONS=--max-old-space-size=8192 pnpm check
NODE_OPTIONS=--max-old-space-size=8192 pnpm build
pm2 reload tamiyouz-crm --update-env
```

`pnpm check` may still show pre-existing unrelated errors; report them without fixing them.

## Safety
- No DB writes are required for apply/verify.
- No test user or permission records should be created just to verify this patch.
- No delete/reset/stash/checkout operations.
- Do not run `git clean`.
- No commit/push/pull/merge/rebase in the target project.
- Preserve unrelated dirty files; if any exist, stop and report before applying.

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
TEMP_FIELDS_PRESERVED=YES/NO
FUTURE_START_ENFORCED=YES/NO
EXPIRY_ENFORCED=YES/NO
DB_CHANGES=YES/NO
NEEDS_ADAPTATION=YES/NO
GIT_OPS=NONE
STATUS=
```
