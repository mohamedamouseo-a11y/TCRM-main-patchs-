# Advanced Permissions Phase 3B — Files / Drive V1

Baseline: TCRM main at/after `0a544cc963764c85ba26d90b112488a36eb6d43d`.

## Goal
Apply the existing Advanced Permissions engine to CRM file operations while preserving every existing file/context/share/security check.

This phase covers the business-facing CRM files surface only. Google Drive technical configuration/OAuth/settings remains for the later Integrations/Settings phase.

## Permission mapping
Use only existing catalog keys:
- read/list/detail/download -> `files.view`
- upload/create/store -> `files.upload`
- rename/metadata/update -> `files.edit`
- soft-delete/permanent-delete/restore where the route is a file mutation -> `files.delete`
- create/revoke/list public share links -> `files.share`

Do not invent new permission keys.

## Existing security MUST remain authoritative
New RBAC is additive only. Keep and still execute all existing guards/checks including, where present:
- `assertCrmFileContextAccess`
- `assertCrmFileRowAccess`
- `canDownloadCrmFileCanonical`
- account-management/client/workflow access checks
- share-link security policy checks
- developer/moderator protections
- audit logging

RBAC answers whether the user may perform the action at all. Existing context/row checks still answer whether that user may touch that concrete file/entity.

## Scope policy
Do NOT create new generic row filtering in this patch. For Files, the existing entity/context security is the row-level source of truth in V1.
Unsupported permission data scopes must not broaden access. Do not bypass existing file-context checks based on scope.

## Exclusions
Do not modify:
- Google Drive OAuth/configuration/settings routes
- Backup Center
- Integrations
- WhatsApp/Messenger/Tara
- Meetings/Felfel/TAM meeting flows
- Phase 4/5 field permissions

## Apply
Run:
```bash
python3 ADVANCED-PERMISSIONS-PHASE3B-FILES-DRIVE-V1/APPLY_PATCH.py /var/www/TCRM-MAIN
```

Then inspect `server/routers.ts` and wire the actual CRM-file routes with the smallest additive diff. Reuse the existing procedures and compose with `.use(files...Scope)`; never replace a current procedure/guard with a weaker one.

## Validation
```bash
pnpm exec tsx scripts/verify-advanced-permissions-phase3b-files-drive.ts
NODE_OPTIONS=--max-old-space-size=8192 pnpm check
NODE_OPTIONS=--max-old-space-size=8192 pnpm build
NODE_OPTIONS=--max-old-space-size=8192 pnpm test
```

Do not commit/push/merge/reset/rebase. Stop and report.