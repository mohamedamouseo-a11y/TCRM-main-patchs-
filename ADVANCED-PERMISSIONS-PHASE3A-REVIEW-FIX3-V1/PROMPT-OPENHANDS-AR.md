نفّذ فقط Phase 3A Review Fix 3 على نفس working tree بعد Fix 1 وFix 2.

Patch repo: mohamedamouseo-a11y/TCRM-main-patchs-
Branch: phase3a-permissions-reviewed-fix3-v1
Folder: ADVANCED-PERMISSIONS-PHASE3A-REVIEW-FIX3-V1

شغّل:
python3 ADVANCED-PERMISSIONS-PHASE3A-REVIEW-FIX3-V1/APPLY_PATCH.py /var/www/TCRM-MAIN
cd /var/www/TCRM-MAIN
pnpm exec tsx scripts/verify-advanced-permissions-phase3a-fix2.ts
pnpm check
pnpm build
pnpm test

مهم:
- Fix 3 verifier-only؛ ممنوع تعديل production code.
- لا Phase 3B.
- لا تصلح failures قديمة غير مرتبطة.
- لا commit/push/merge/reset/rebase.

في النهاية ابعت verify/check/build/test + git diff ثم توقف.
