نفّذ فقط Advanced Permissions Phase 3B Files / Drive V1 على `/var/www/TCRM-MAIN`.

Patch repo:
mohamedamouseo-a11y/TCRM-main-patchs-

Branch:
phase3b-files-drive-v1

Folder:
ADVANCED-PERMISSIONS-PHASE3B-FILES-DRIVE-V1

1) اقرأ README.md بالكامل.
2) شغّل:
```bash
python3 ADVANCED-PERMISSIONS-PHASE3B-FILES-DRIVE-V1/APPLY_PATCH.py /var/www/TCRM-MAIN
```
3) عدّل فقط `server/routers.ts` بأقل diff ممكن لربط CRM file routes الفعلية:
- read/list/detail/download -> files.view
- upload/create/store -> files.upload
- metadata/rename/update -> files.edit
- file delete/restore -> files.delete
- share-link list/create/revoke -> files.share

استخدم `.use(files...Scope)` فوق الـprocedure/guard الحالي؛ لا تستبدل أي guard موجود.

لازم تفضل كل الحمايات الحالية شغالة، خصوصًا:
`assertCrmFileContextAccess`, `assertCrmFileRowAccess`, `canDownloadCrmFileCanonical` وأي client/workflow/share policy checks.

ممنوع لمس Google Drive OAuth/config/settings أو Backup/Integrations/WhatsApp/Tara/Meetings/Felfel/TAM.

بعدها شغّل:
```bash
pnpm exec tsx scripts/verify-advanced-permissions-phase3b-files-drive.ts
NODE_OPTIONS=--max-old-space-size=8192 pnpm check
NODE_OPTIONS=--max-old-space-size=8192 pnpm build
NODE_OPTIONS=--max-old-space-size=8192 pnpm test
```

لا commit/push/merge/reset/rebase.

في النهاية ابعت: files changed + exact file-route mapping + verify/check/build/test + git status/diff stat/name-only + تأكيد existing file security preserved + excluded surfaces untouched + no git operations. ثم توقف.