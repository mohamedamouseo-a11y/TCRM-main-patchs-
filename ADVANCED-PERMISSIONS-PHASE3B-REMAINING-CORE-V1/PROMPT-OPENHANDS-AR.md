نفّذ فقط Advanced Permissions Phase 3B Remaining Core V1 على `/var/www/TCRM-MAIN`.

Patch branch: `phase3b-remaining-core-v1`
Folder: `ADVANCED-PERMISSIONS-PHASE3B-REMAINING-CORE-V1`
Baseline المطلوب: TCRM main عند/بعد `3a6551801a60c3f2763185f325b41185f5ec0228`.

1. اقرأ README.md بالكامل.
2. شغّل:
```bash
python3 ADVANCED-PERMISSIONS-PHASE3B-REMAINING-CORE-V1/APPLY_PATCH.py /var/www/TCRM-MAIN
```
3. عدّل `server/routers.ts` فقط بأقل diff ممكن، وأضف الـRBAC كطبقة إضافية فوق الحمايات الحالية:
   - Campaigns: view/create/edit/delete حسب README.
   - Reports: view/export حسب route الفعلي.
   - Notifications: view/manage حسب route الفعلي.
   - Audit Logs: view/export حسب route الفعلي.
4. لا تستبدل `adminProcedure` أو `mediaBuyerOrAdminProcedure` أو أي legacy guard. استخدم `.use(<scope>)` فوقه.
5. حدّث import من `./_core/trpc` لإضافة scope exports المطلوبة فقط.
6. لا تخترع Data Scope filters جديدة لهذه الموديولات في هذه الخطوة.
7. ممنوع لمس Meetings/Felfel/TAM، WhatsApp/Messenger/Tara، Integrations/Developer Hub، Backup، Files/Drive.
8. شغّل:
```bash
pnpm exec tsx scripts/verify-advanced-permissions-phase3b-remaining-core.ts
NODE_OPTIONS=--max-old-space-size=8192 pnpm check
NODE_OPTIONS=--max-old-space-size=8192 pnpm build
NODE_OPTIONS=--max-old-space-size=8192 pnpm test
```
9. لا commit/push/merge/reset/rebase، ولا تصلح failures قديمة غير مرتبطة.

في النهاية ابعت: files changed + exact route mapping + verify/check/build/test + failed files + git status/diff stat/name-only + أي manual adaptation + تأكيد no git operations، ثم توقف.