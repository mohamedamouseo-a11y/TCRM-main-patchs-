نفّذ فقط Phase 3A Review Fix 2 على نفس working tree بعد Fix 1.

Patch repo: mohamedamouseo-a11y/TCRM-main-patchs-
Branch: phase3a-permissions-reviewed-fix-v1
Folder: ADVANCED-PERMISSIONS-PHASE3A-REVIEW-FIX2-V1

شغّل:
python3 ADVANCED-PERMISSIONS-PHASE3A-REVIEW-FIX2-V1/APPLY_PATCH.py /var/www/TCRM-MAIN
cd /var/www/TCRM-MAIN
pnpm exec tsx scripts/verify-advanced-permissions-phase3a-fix2.ts
pnpm check
pnpm build
pnpm test

ممنوع Phase 3B أو أي تعديل آخر أو git commit/push/merge/reset/rebase.
لا تصلح failures غير مرتبطة. في النهاية ابعت verify/check/build/test + git diff ثم توقف.
