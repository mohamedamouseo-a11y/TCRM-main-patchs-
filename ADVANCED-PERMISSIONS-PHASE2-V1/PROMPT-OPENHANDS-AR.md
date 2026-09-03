# Prompt — تنفيذ Advanced Permissions Phase 2 فقط

أنت تعمل على مشروع TCRM المحلي، والمرجع الذي بُني عليه هذا الباتش هو أحدث `main` تمت مراجعته عند commit:

`5fe3f9b81fdcc9f032cdd80d65e45a941d8f85d8`

مصدر الباتش:

- Repository: `mohamedamouseo-a11y/TCRM-main-patchs-`
- Branch: `phase2-advanced-permissions-ui-v1`
- Folder: `ADVANCED-PERMISSIONS-PHASE2-V1`

## قواعد إلزامية

1. ممنوع عمل push/commit/merge/rebase/reset على `TCRM main` تلقائيًا.
2. نفّذ **Phase 2 فقط**.
3. لا تعِد تنفيذ Phase 1 إذا كانت ملفاتها وجداولها موجودة.
4. لا تعدل `users.role` ولا legacy role enum.
5. لا تطبق Data Scope على استعلامات Leads/Deals/Clients في هذه المرحلة.
6. لا تضف Field-level permissions أو User Overrides UI أو Temporary Permissions أو Role Inheritance UI.
7. لا تغيّر السلوك الحالي للـModerator/Developer/central audit/protectedProcedure/adminProcedure.
8. لو `main` المحلي أحدث من baseline المذكور، راجع الـdiff أولًا وادمج الباتش بأقل تعديل ممكن، ولا تمس أي feature خارج نطاق Phase 2.

## قبل التطبيق

نفّذ:

```bash
cd /var/www/TCRM-MAIN
git status --short
git branch --show-current
git log -1 --oneline
```

ثم تأكد أن Phase 1 موجودة:

```bash
test -f server/security/permissionCatalog.ts
test -f server/security/permissionEngine.ts
grep -n "export const permissionProcedure" server/_core/trpc.ts
```

لا تنظف working tree ولا تعمل reset لأي تغييرات تخص المستخدم.

## تطبيق الباتش

اجلب patch branch/folder ثم شغّل:

```bash
python3 ADVANCED-PERMISSIONS-PHASE2-V1/APPLY_PATCH.py /var/www/TCRM-MAIN
```

إذا تعذر استخدام الـapplier بسبب تغير بسيط في markers نتيجة تحديث حديث في `main`، لا تكتب الملفات بشكل أعمى. راجع الملفات الحالية وطبّق نفس التغييرات يدويًا بأقل diff ممكن.

## النتيجة المطلوبة

يجب إضافة:

```text
server/security/permissionAdminService.ts
server/permissionsAdminRouter.ts
client/src/pages/RolesPermissions.tsx
scripts/verify-advanced-permissions-phase2.ts
```

ويجب تعديل فقط عند الحاجة:

```text
server/routers.ts
client/src/App.tsx
client/src/components/CRMLayout.tsx
client/src/lib/i18n.ts
```

### Backend

أضف router باسم:

`permissionsAdmin`

بالعمليات:

- `catalog`
- `listRoles`
- `getRole`
- `createRole`
- `updateRole`
- `duplicateRole`
- `replacePermissions`
- `setActive`
- `deleteRole`

استخدم صلاحيات Phase 1 الفعلية فقط:

- `roles.view`
- `roles.create`
- `roles.edit`
- `roles.delete`
- `roles.assign_permissions`

ممنوع invent permission keys جديدة.

كل mutations يجب أن تكتب audit في `permission_audit_logs`.

System roles:

- يمكن عرضها وتعديل display metadata والصلاحيات حسب guards الحالية.
- لا يمكن تعطيلها.
- لا يمكن حذفها.

Custom roles:

- يمكن إنشاؤها/تعديلها/نسخها.
- يمكن تعطيلها.
- لا يمكن حذفها إذا كانت مسندة لمستخدمين active.

### UI

المسار:

`/settings/roles-permissions`

يجب أن يحتوي على:

- قائمة Roles
- System/Custom indication
- Active/Inactive state
- User count
- Permission count
- Create Role
- Edit Role
- Duplicate Role
- Delete custom role safely
- Search permissions
- Filter by module
- Permission Matrix
- ثلاث حالات لكل permission: Not assigned / Allow / Explicit deny
- Data Scope لكل Allow
- Clear All
- View Only
- Full Access
- Save

Scopes المسموحة فقط:

```text
all
team
department
own
assigned
created_by
custom
none
```

يجب توضيح في الـUI أن الـscope يتم حفظه وحسابه فقط حاليًا، لكن Query Enforcement سيكون في Phase 3.

أضف رابط Admin-only إلى الصفحة بجوار Settings، لكن لا تعتبر إخفاء الرابط Security. الـBackend guard هو المرجع النهائي.

## Verification

بعد التطبيق شغّل:

```bash
cd /var/www/TCRM-MAIN
pnpm exec tsx scripts/verify-advanced-permissions-phase2.ts
pnpm check
pnpm build
pnpm test
```

اعمل smoke test يدوي أو automated قدر الإمكان للحالات التالية:

1. Admin/Super Admin يفتح `/settings/roles-permissions`.
2. إنشاء custom role.
3. إضافة Allow permission مع scope ثم Save/Reload ويظل محفوظًا.
4. إضافة Explicit Deny ثم Save/Reload ويظل محفوظًا.
5. View Only preset يعمل.
6. Full Access preset يعمل.
7. Duplicate Role ينسخ permission assignments.
8. System Role لا يمكن تعطيله أو حذفه.
9. Custom Role مسند لمستخدم active لا يمكن حذفه.
10. مستخدم لا يملك `roles.view` يأخذ FORBIDDEN من API.
11. لا يوجد أي Query filtering جديد على Leads/Deals/Clients.
12. `users.role` كما هو بدون تغيير.

الاختبار المعروف من baseline:

`twsCollaborationRouter.v2c.test.ts` → `User access is inactive`

لو ظل بنفس السبب فقط، سجله كـpre-existing. أي failure جديد متعلق بالصلاحيات يعتبر regression ويجب إصلاحه.

## التقرير النهائي المطلوب

أرسل تقريرًا يحتوي على:

1. الـcommit/branch المحلي الذي طبقت عليه.
2. الملفات المضافة.
3. الملفات المعدلة.
4. Diff summary.
5. نتيجة Phase 2 verifier.
6. نتيجة TypeScript check مع فصل الأخطاء القديمة عن الجديدة.
7. نتيجة build.
8. نتيجة tests.
9. نتيجة smoke tests.
10. تأكيد أن Phase 3 لم يُنفذ.
11. تأكيد أن `users.role` لم يتغير.
12. تأكيد أنه لم يحدث push/commit/merge/reset/rebase على `main`.
13. أي conflict مع تحديثات أحدث من baseline وكيف تم حله.

بعد التقرير توقّف. لا تبدأ Phase 3 من نفسك.
