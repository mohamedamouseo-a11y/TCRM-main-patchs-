كمّل من نفس working tree الحالي الذي عليه Phase 3B V1 بالفعل. نفّذ فقط Advanced Permissions Phase 3B V2 من هذا الفولدر على `/var/www/TCRM-MAIN`.

مهم: لا تعيد تطبيق V1 يدويًا. الـV2 applier أصبح يكتشف V1 الحالية ويكمل فوقها فقط.

1) اقرأ `README.md` بالكامل.
2) شغّل:
```bash
python3 ADVANCED-PERMISSIONS-PHASE3B-V2-TAS-STYLE/APPLY_PATCH.py /var/www/TCRM-MAIN
```
3) بعد الـAPPLY عدّل فقط `client/src/pages/RolesPermissions.tsx` حسب قسم **Required UI adaptation after APPLY_PATCH** في README:
   - Basic TAS-style module/action matrix + module scope.
   - Advanced mode يحافظ على per-action Allow/Deny/Inherit + scope.
   - User Overrides UI مربوطة بالـ3 APIs الجديدة.
4) ممنوع إعادة `ServiceAdvisor` أو `PartsAgent` أو `CrmFollowUp` كـactive/selectable roles. Legacy compatibility فقط مسموح.
5) لا تلمس Meetings/Felfel/TAM meeting flows.
6) لا تستبدل الحمايات القديمة؛ RBAC الجديدة additive.
7) شغّل:
```bash
pnpm exec tsx scripts/verify-advanced-permissions-phase3b-v2.ts
NODE_OPTIONS=--max-old-space-size=8192 pnpm check
NODE_OPTIONS=--max-old-space-size=8192 pnpm build
NODE_OPTIONS=--max-old-space-size=8192 pnpm test
```
8) لا commit/push/merge/reset/rebase، ولا تصلح failures قديمة غير مرتبطة.

في النهاية ابعت: files changed + verify/check/build/test + git status/diff stat/name-only + أي manual adaptations + تأكيد أن V1 لم تُعاد + تأكيد أن Automotive roles غير selectable + تأكيد أن Meetings/Felfel/TAM meetings لم تُمس، ثم توقف.
