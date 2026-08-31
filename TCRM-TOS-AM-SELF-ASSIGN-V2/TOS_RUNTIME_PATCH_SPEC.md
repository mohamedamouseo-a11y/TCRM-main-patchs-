# TOS Runtime Patch Spec — Account Management in Team Directory

## Why this file exists
TCRM currently calls the TOS operational endpoint:

`GET <TOS_API>/team-directory?crmClientId=<id>`

The current TCRM source does **not** filter Account Management itself. The exclusion is coming from the TOS operational endpoint/runtime. The production endpoint implementation is not present in the current GitHub `mohamedamouseo-a11y/TOS` `main` tree, so do not invent a fake file path.

## Required backward-compatible change
Add support for this optional query parameter:

`includeAccountManagement=1`

Behavior:

- Missing / false parameter: preserve the current behavior exactly, including Account Management exclusion. This protects task-assignment flows that use the same directory service.
- `includeAccountManagement=1`: return the Account Management department and its active employees in `departments`.
- Preserve existing `projectMembers` behavior.
- Do not expose inactive/deleted users if the endpoint currently excludes them.
- Do not change the API key authentication (`X-API-Key`).
- Do not change response keys or rename existing fields.

## Expected department/member shape
TCRM already accepts the existing flexible member id aliases. The returned AM members should follow the same shape as other departments, ideally:

```json
{
  "key": "account_management",
  "name": "Account Management",
  "members": [
    {
      "tosUserId": "...",
      "name": "...",
      "email": "...",
      "jobTitle": "...",
      "departmentKey": "account_management",
      "departmentName": "Account Management"
    }
  ]
}
```

`email` is required for the self-only authorization mapping in TCRM. Use the canonical employee email already stored in TOS; do not synthesize or trust an email supplied by TCRM.

## How the execution agent should locate the runtime source
On the server, search the **actual TOS deployment working tree** for any of these anchors:

```bash
rg -n --hidden --glob '!node_modules' 'team-directory|projectMembers|Account Management|account_management|X-API-Key' /var/www /opt /srv 2>/dev/null
```

Then identify the route that serves the same base URL configured in TCRM's TOS integration settings. Confirm it by comparing the live endpoint response before editing.

## Required implementation pattern
Pseudo-code only; adapt to the real source:

```ts
const includeAccountManagement = ["1", "true", "yes"].includes(
  String(req.query.includeAccountManagement ?? "").trim().toLowerCase(),
);

const departments = allDepartments
  .filter((department) => includeAccountManagement || !isAccountManagement(department))
  .map(...existingMapping);
```

Prefer using the endpoint's existing department key/id instead of matching display text if available.

## Verification
Run both:

```bash
curl -fsS -H "X-API-Key: $TOS_API_KEY" \
  "$TOS_API_URL/team-directory?crmClientId=<CLIENT_ID>"
```

Expected: existing behavior remains unchanged.

Then:

```bash
curl -fsS -H "X-API-Key: $TOS_API_KEY" \
  "$TOS_API_URL/team-directory?crmClientId=<CLIENT_ID>&includeAccountManagement=1"
```

Expected: response contains Account Management with active AM employees and valid email identities.

## Do not do
- Do not globally stop excluding Account Management for every directory consumer.
- Do not remove API authentication.
- Do not return secrets.
- Do not create a second duplicate endpoint unless the existing runtime architecture absolutely requires it.
- Do not change project membership removal semantics: current TOS memberships remain managed by TOS.
