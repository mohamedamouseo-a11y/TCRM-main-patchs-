نفّذ Advanced Permissions Phase 3B فقط على أحدث TCRM main.

Patch repo:
mohamedamouseo-a11y/TCRM-main-patchs-

Branch:
phase3b-core-operations-v1

Folder:
ADVANCED-PERMISSIONS-PHASE3B-V1

اقرأ README.md ثم نفّذ:

python3 ADVANCED-PERMISSIONS-PHASE3B-V1/APPLY_PATCH.py /var/www/TCRM-MAIN

cd /var/www/TCRM-MAIN
pnpm exec tsx scripts/verify-advanced-permissions-phase3b.ts
NODE_OPTIONS=--max-old-space-size=8192 pnpm check
NODE_OPTIONS=--max-old-space-size=8192 pnpm build
NODE_OPTIONS=--max-old-space-size=8192 pnpm test

مهم:
- Phase 3B هنا = Activities + Client Tasks + Contracts فقط.
- لا تلمس Meetings/Felfel/TAM meeting flows.
- حافظ على كل الحمايات الحالية ولا تستبدلها؛ permission layer الجديدة تضيف منعًا إضافيًا فقط.
- راجع git diff بعد APPLY_PATCH. لو أي marker في أحدث main تغيّر، نفّذ نفس المقصود يدويًا بأقل diff بدل replace أعمى.
- تأكد أن tasks.assign مطلوب فقط عند تغيير assignedTo.
- department/created_by/custom/none = deny-by-default في هذه الوحدات.
- لا Phase 4 أو Phase 5.
- لا تغيّر users.role أو Legacy Roles.
- لا commit/push/merge/reset/rebase.
- لا تصلح failures قديمة غير مرتبطة بالباتش.

في النهاية ابعت تقرير مختصر: الملفات المعدلة/المضافة، scope mapping، نتائج verify/check/build/test، أي conflict أو manual adaptation، وgit diff/status، ثم توقف.