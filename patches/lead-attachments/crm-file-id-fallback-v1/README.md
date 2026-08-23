# TCRM Lead Attachment crmFileId Fallback V1

## Confirmed production root cause

The Lead attachment upload reaches Google Drive successfully and inserts a valid row in `crm_files`, but the live MySQL/Drizzle runtime can return no usable ID from `$returningId()`. `storeCrmFile()` then returns `crmFileId=null`, so `LeadProfile.tsx` stops at `File record was not created` and never calls `attachments.create`.

## Patch scope

Only:

- `server/services/crmFileStorage.ts`

No changes to:

- Google Drive configuration/OAuth
- database schema or migrations
- frontend Lead UX
- attachment business rules
- permissions
- routes

## Fix

Keep the existing `$returningId()` fast path. If it produces no positive ID, query the just-created `crm_files` row using the exact generated `storageKey`, take its `id`, and fail explicitly if the ID still cannot be resolved.

This preserves the current upload architecture while ensuring a successful database insert always propagates a usable `crmFileId` back to the Lead attachment flow.

## Apply

From the TCRM project root:

```bash
node <PATCH_REPO_PATH>/patches/lead-attachments/crm-file-id-fallback-v1/apply.mjs --check
node <PATCH_REPO_PATH>/patches/lead-attachments/crm-file-id-fallback-v1/apply.mjs --apply
node <PATCH_REPO_PATH>/patches/lead-attachments/crm-file-id-fallback-v1/apply.mjs --verify
```

Then run the normal type/build checks and production validation.

## Expected production validation

A controlled Lead TXT/JPG upload should produce:

1. Google Drive upload succeeds.
2. `crm_files` row is created with a positive ID.
3. `fileStorage.upload` returns the same positive `crmFileId`.
4. `LeadProfile.tsx` passes its guard.
5. `attachments.create` is sent.
6. `lead_attachments` row is created.
7. Attachment appears on the Lead without the `File record was not created` toast.
