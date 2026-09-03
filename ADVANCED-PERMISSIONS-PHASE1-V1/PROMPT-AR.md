# برومبت تنفيذ ومراجعة Phase 1 — Advanced Permissions

أنت تعمل على مشروع:
`mohamedamouseo-a11y/TCRM-MAIN-Tamiyouz-CRM-`

ممنوع تمامًا عمل push مباشر على `main`.

مصدر الباتش موجود في:
`mohamedamouseo-a11y/TCRM-main-patchs-`

Branch:
`phase1-advanced-permissions-foundation-v1`

المجلد:
`ADVANCED-PERMISSIONS-PHASE1-V1`

## المطلوب

نفّذ Phase 1 فقط لنظام صلاحيات Advanced داخل TCRM مع الحفاظ الكامل على النظام الحالي وعدم كسر أي role أو router موجود.

### 1) طبّق الباتش

شغّل:

```bash
python3 ADVANCED-PERMISSIONS-PHASE1-V1/APPLY_PATCH.py /path/to/TCRM
```

أو طبّق محتواه يدويًا لو البيئة لا تسمح بتشغيل Python.

### 2) راجع الملفات الناتجة

لازم تكون الملفات التالية موجودة:

- `server/security/permissionCatalog.ts`
- `server/security/permissionEngine.ts`
- `server/security/permissionProcedure.ts`
- `scripts/apply-advanced-permissions-phase1-migration.ts`
- `scripts/verify-advanced-permissions-phase1.ts`

وتتأكد إن `package.json` يحتوي:

- `db:migrate:advanced-permissions-phase1`
- `verify:advanced-permissions-phase1`

وتتأكد إن `server/_core/trpc.ts` أصبح يصدر:

- `permissionProcedure(permission)`
- `anyPermissionProcedure(permissions)`

بدون تغيير سلوك `protectedProcedure` أو `adminProcedure` الحالي.

### 3) قاعدة البيانات

طبّق Migration التي تنشئ فقط الجداول الجديدة التالية:

- `roles`
- `permissions`
- `role_permissions`
- `user_roles`
- `user_permission_overrides`
- `permission_audit_logs`

ممنوع حذف أو تعديل `users.role` في Phase 1.

يجب عمل compatibility mapping للـroles القديمة الحالية، وعدم تعطيل أي user موجود.

### 4) قواعد Permission Engine

ترتيب الحسم يجب أن يكون:

1. Super Admin bypass.
2. User explicit deny.
3. User explicit allow.
4. Dynamic role grants/denies.
5. Legacy role mapping fallback.
6. Deny.

Explicit deny أعلى أولوية من أي grant عادي.

Data scopes المدعومة:

- `all`
- `team`
- `department`
- `own`
- `assigned`
- `created_by`
- `custom`
- `none`

في Phase 1 المطلوب إرجاع الـeffective scope فقط. لا تطبق filters على Leads/Deals/Clients الآن؛ ده Phase 3.

### 5) منع Lockout

اعتبر Super Admin bypass عند:

- `SuperAdmin` / `super_admin` role.
- Email موجود في env `PERMISSIONS_SUPER_ADMIN_EMAILS`.
- Legacy `Admin` مؤقتًا طالما `PERMISSIONS_LEGACY_ADMIN_BYPASS !== false`.

لا تشيل الـlegacy Admin bypass أثناء Phase 1.

### 6) Migration safety

لازم الـmigration تكون:

- idempotent قدر الإمكان.
- تستخدم `CREATE TABLE IF NOT EXISTS`.
- تستخدم unique indexes تمنع duplicate grants/assignments.
- تعيد تشغيلها بدون مضاعفة user_roles أو permissions.
- ما تعملش DROP لأي جدول حالي.
- ما تغيرش enum `users.role`.

### 7) Tests / verification

نفّذ:

```bash
pnpm db:migrate:advanced-permissions-phase1
pnpm verify:advanced-permissions-phase1
pnpm check
```

ولو المشروع يسمح:

```bash
pnpm test
```

اختبر على الأقل الحالات دي:

- Super Admin → allow + scope all.
- User deny override → deny حتى لو role يسمح.
- User allow override → allow.
- Multiple roles → effective strongest allowed scope، إلا لو فيه deny.
- No permission → deny.
- Existing Admin routes ما تتكسرش.
- Existing Moderator/Developer protections في `server/_core/trpc.ts` تفضل شغالة زي ما هي.

### 8) ممنوع في Phase 1

لا تعمل:

- Roles & Permissions UI.
- Sidebar hiding.
- Field-level permissions.
- تحويل كل routers للصلاحيات الجديدة.
- تعديل behavior الحالي للـmodules.
- حذف legacy roles.
- push على `main`.

### 9) نتيجة التنفيذ المطلوبة

في النهاية اعرض تقرير مختصر يحتوي:

- الملفات التي اتضافت/اتعدلت.
- نتيجة migration.
- نتيجة verification.
- نتيجة TypeScript check.
- أي compatibility issue اكتشفته.
- اسم branch المستخدم.
- تأكيد صريح أن `main` لم يتم تعديله.
