نفّذ فقط Phase 3A Review Fix على أحدث TCRM main.

Patch repo:
`mohamedamouseo-a11y/TCRM-main-patchs-`

Branch:
`phase3a-permissions-reviewed-fix-v1`

Folder:
`ADVANCED-PERMISSIONS-PHASE3A-REVIEW-FIX-V1`

نفّذ:
```bash
python3 ADVANCED-PERMISSIONS-PHASE3A-REVIEW-FIX-V1/APPLY_PATCH.py /var/www/TCRM-MAIN
cd /var/www/TCRM-MAIN
pnpm exec tsx scripts/verify-advanced-permissions-phase3a.ts
pnpm check
pnpm build
pnpm test
```

مهم:
- لا تنفذ Phase 3B.
- لا تغيّر أي mapping آخر.
- لا تغيّر users.role أو Legacy Roles.
- لا تعمل commit/push/merge/reset/rebase على main.
- لا تصلح failures قديمة غير مرتبطة بالباتش.

في النهاية ابعت تقرير مختصر بنتائج verify/check/build/test والـgit diff، ثم توقف.
