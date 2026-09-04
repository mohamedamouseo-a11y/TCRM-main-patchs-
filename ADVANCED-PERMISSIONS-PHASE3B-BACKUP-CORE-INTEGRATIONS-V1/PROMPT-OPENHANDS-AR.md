نفّذ فقط Advanced Permissions Phase 3B Backup Center + Core Integrations V1 على `/var/www/TCRM-MAIN`.

Patch repo:
`mohamedamouseo-a11y/TCRM-main-patchs-`

Branch:
`phase3b-backup-core-integrations-v1`

Folder:
`ADVANCED-PERMISSIONS-PHASE3B-BACKUP-CORE-INTEGRATIONS-V1`

Baseline:
`a1051a4c6a6d85c9109844ab08fdd1e9454cb365`

1) اقرأ README.md بالكامل.
2) شغّل:
```bash
python3 ADVANCED-PERMISSIONS-PHASE3B-BACKUP-CORE-INTEGRATIONS-V1/APPLY_PATCH.py /var/www/TCRM-MAIN
```
3) بعد ذلك عدّل فقط `server/routers.ts` بأقل diff ممكن.
4) قبل التعديل اعمل inventory للroutes الفعلية الخاصة بـ Backup Center وTFS وTOS وGoogle Drive file-storage technical settings.
5) اربط:
   - Backup read/list/status/settings-read -> `backupViewScope`
   - Backup run/create/manual/retry -> `backupRunScope`
   - Backup restore -> `backupRestoreScope`
   - Backup settings/delete/archive/manage -> `backupManageScope`
   - TFS/TOS/Google Drive status/read/config-for-ui -> `integrationsViewScope`
   - TFS/TOS/Google Drive settings/test/connect/disconnect/manual or bulk sync/send -> `integrationsManageScope`
6) استخدم `.use(...)` فوق الـprocedure الحالي. ممنوع استبدال legacy guards.
7) Sensitive settings تظل خاضعة لأي Admin/Developer/Moderator/security guard موجود بالفعل.
8) ممنوع لمس Meta Ads/TikTok/Google Ads، WhatsApp/Messenger/Tara، THRS، Developer Hub، Meetings/Felfel/TAM، أو service implementations.
9) شغّل:
```bash
pnpm exec tsx scripts/verify-advanced-permissions-phase3b-backup-core-integrations.ts
NODE_OPTIONS=--max-old-space-size=8192 pnpm check
NODE_OPTIONS=--max-old-space-size=8192 pnpm build
NODE_OPTIONS=--max-old-space-size=8192 pnpm test
```
10) قارن test failures مع baseline لنفس HEAD.
11) لا commit/push/merge/reset/rebase ولا تصلح failures قديمة غير مرتبطة.

في النهاية ابعت: files changed + exact route mapping + verify/check/build/test + baseline regression comparison + git status/diff stat/name-only + legacy guards preserved + excluded surfaces untouched + no git operations، ثم توقف.
