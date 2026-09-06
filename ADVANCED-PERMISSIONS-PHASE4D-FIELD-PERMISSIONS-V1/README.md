# Advanced Permissions Phase 4D — Field Permissions V1

Target baseline:
`3e0aa9de85e55253dba928b5dedf96098286bec8`

Target project path on server:
`/var/www/TCRM-MAIN`

## Scope
This phase activates field-level permissions using the existing `scope_config` JSON columns already present on `role_permissions` and `user_permission_overrides`.

No DB schema, DDL, or migration is added.

It changes only:
- `server/security/permissionEngine.ts`
- `server/routers.ts`
- `client/src/pages/RolesPermissions.tsx`

## Field policy model
Field policy is stored under the existing permission row `scope_config`:

```json
{
  "fields": {
    "allow": ["name", "phone", "stage"],
    "deny": ["mediaBuyerNotes"]
  }
}
```

Rules:
- Missing `scope_config.fields` = unrestricted fields. Existing roles/users therefore keep current behavior.
- `deny` always wins over `allow` for the same field.
- If `allow` is present, only listed fields are visible/writable, except technical identifiers explicitly preserved by the router.
- An empty `allow` array intentionally means no business fields are allowed.
- User Override precedence remains unchanged and therefore its field policy overrides role-level policy when the user override grants that permission.
- Role inheritance from Phase 4C remains unchanged: the effective direct/inherited role grant is resolved first, then its field policy participates.
- With multiple effective role grants, field grants remain additive while configured deny lists are unioned for safety.
- Super Admin bypass remains unrestricted.

## Backend enforcement
Field rules are enforced server-side, not only in the UI.

### Leads
- `leads.list` read filtering
- `leads.byId` read filtering
- `leads.create` write validation
- `leads.update` write validation
- `leads.export` output filtering, preferring the effective `leads.view` field policy when available

### Deals
- `deals.byLead` read filtering
- `deals.byUser` read filtering
- `deals.create` write validation
- `deals.update` write validation

### Clients
- `accountManagement.listClients` read filtering
- `accountManagement.getClient` read filtering
- `accountManagement.createClient` write validation
- `accountManagement.updateClient` field validation when the current user has an effective `clients.edit` Advanced Permission decision
- `accountManagement.createClientWithCourseSubscription` field validation when the current user has an effective `clients.create` Advanced Permission decision

Specialized/nested workflow resources such as Deal Payments, Client Tasks, Handover Briefs, Contracts, and narrow Sales Handover locators keep their existing guards and are intentionally outside Field Permissions V1.

## UI
In Advanced Roles & Permissions:
- Leads / Clients / Deals `view`, `create`, and `edit` permissions get a Field Access editor.
- The same Field Access editor is available for User Overrides.
- Modes: All fields / Only selected fields / All except selected fields.
- Existing `scopeConfig` keys are preserved; the editor only owns `scopeConfig.fields`.
- Bulk role actions preserve an existing field policy instead of silently discarding it.
- Permission Tester shows the effective field policy returned by the engine.

## Must NOT change
- DB schema or migrations.
- Permission precedence.
- Row-level scope semantics.
- Role inheritance semantics.
- User Override / Temporary Access timing semantics.
- Sales/TAM/TOS/Account Management legacy guards.
- Tara / WhatsApp / Messenger / Meetings / Felfel flows.
- Nested sub-resource authorization behavior.

## Apply
From a checkout of this patch branch:

```bash
python3 ADVANCED-PERMISSIONS-PHASE4D-FIELD-PERMISSIONS-V1/APPLY_PATCH.py /var/www/TCRM-MAIN
python3 ADVANCED-PERMISSIONS-PHASE4D-FIELD-PERMISSIONS-V1/VERIFY.py /var/www/TCRM-MAIN
```

Then from `/var/www/TCRM-MAIN`:

```bash
NODE_OPTIONS=--max-old-space-size=8192 pnpm check
NODE_OPTIONS=--max-old-space-size=8192 pnpm build
pm2 reload tamiyouz-crm --update-env
```

`pnpm check` may still show the known unrelated pre-existing TypeScript errors. Report them without fixing them.

## Safety
- Do not create or alter DB tables/columns/indexes.
- Do not create test users/roles/permission rows just for verification.
- Do not modify unrelated dirty files.
- No commit/push/pull/merge/rebase in `/var/www/TCRM-MAIN`.
- Do not run git clean/reset/restore/checkout/stash.
- Do not delete any project file.

## Expected report

```text
HEAD_BEFORE=
FILES_CHANGED=
UNTRACKED_FILES=
PATCH_APPLIED=
VERIFY=
CHECK=
BUILD=
PM2_RELOAD=
FIELD_POLICY_ENGINE=YES/NO
ROLE_FIELD_UI=YES/NO
USER_OVERRIDE_FIELD_UI=YES/NO
LEADS_READ_ENFORCED=YES/NO
LEADS_WRITE_ENFORCED=YES/NO
LEADS_EXPORT_ENFORCED=YES/NO
DEALS_READ_ENFORCED=YES/NO
DEALS_WRITE_ENFORCED=YES/NO
CLIENTS_READ_ENFORCED=YES/NO
CLIENTS_WRITE_ENFORCED=YES/NO
DEFAULT_UNRESTRICTED=YES/NO
SUPER_ADMIN_UNCHANGED=YES/NO
PRECEDENCE_UNCHANGED=YES/NO
DB_CHANGES=YES/NO
NEEDS_ADAPTATION=YES/NO
GIT_OPS=NONE
STATUS=
```
