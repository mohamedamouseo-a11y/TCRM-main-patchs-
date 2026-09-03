نفّذ Advanced Permissions Phase 2 فقط على أحدث نسخة محلية من TCRM main.

مصدر الباتش:
- Repo: mohamedamouseo-a11y/TCRM-main-patchs-
- Branch: phase2-advanced-permissions-ui-v1-validated
- Folder: ADVANCED-PERMISSIONS-PHASE2-V1

قبل التنفيذ اقرأ README.md داخل نفس المجلد، ثم طبّق:

python3 ADVANCED-PERMISSIONS-PHASE2-V1/APPLY_PATCH.py /var/www/TCRM-MAIN

مهم:
- لا تعمل push/commit/merge/reset/rebase على main.
- لا تنفذ Phase 3.
- لا تغيّر users.role أو Legacy Roles.
- لو marker تغيّر في أحدث main، طبّق نفس التعديل يدويًا بأقل diff ممكن بدل replace أعمى.
- حافظ على كل الحمايات الحالية في trpc كما هي.

بعد التنفيذ شغّل:

pnpm exec tsx scripts/verify-advanced-permissions-phase2.ts
pnpm check
pnpm build
pnpm test

ثم اعمل smoke test سريع لـ /settings/roles-permissions: فتح الصفحة، إنشاء Custom Role، Save/Reload لـ Allow + Explicit Deny + Scope، Duplicate Role، ومنع Disable/Delete للـSystem Roles.

في النهاية أرسل فقط تقريرًا مختصرًا: الملفات المضافة/المعدلة، نتائج verify/check/build/tests، نتائج smoke test، أي conflict تم حله، وتأكيد عدم تنفيذ Phase 3 وعدم لمس main بـ git operations.