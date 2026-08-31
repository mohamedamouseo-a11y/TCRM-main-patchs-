# TOS Runtime Requirement — Handover Account Management Directory

TCRM Handover calls the operational TOS endpoint:

`GET <TOS_API>/team-directory?crmClientId=<id>`

The current production behavior may exclude Account Management. The V3 TCRM patch opts in using:

`includeAccountManagement=1`

## Required behavior

The live TOS endpoint must support this optional query parameter in a backward-compatible way.

### Without the parameter
Preserve the existing behavior exactly. This is important because task-assignment flows may use the same directory and should not change unintentionally.

### With `includeAccountManagement=1`
Return the Account Management department and its active employees in `departments` using the same member structure as other departments.

Each AM employee must expose a canonical TOS identity, preferably:

```json
{
  "tosUserId": "TOS_USER_ID",
  "name": "Employee Name",
  "email": "canonical@company.com",
  "jobTitle": "Account Manager",
  "departmentKey": "account_management",
  "departmentName": "Account Management"
}
```

The email must come from TOS data. Do not trust an email supplied by TCRM for authorization.

## Preserve
- Existing `X-API-Key` authentication.
- Existing response keys.
- Existing `projectMembers` behavior.
- Existing inactive/deleted employee filtering.
- Existing task-directory behavior when `includeAccountManagement` is not requested.

## Recommended implementation
Adapt to the real route source:

```ts
const includeAccountManagement = ["1", "true", "yes"].includes(
  String(req.query.includeAccountManagement ?? "").trim().toLowerCase(),
);

const departments = allDepartments.filter((department) =>
  includeAccountManagement || !isAccountManagementDepartment(department)
);
```

Prefer the real department key/id rather than display-name matching if the runtime has it.

## Discovery on server
If the real endpoint source is not obvious, locate the implementation serving the API configured in TCRM. Search the deployed application trees, excluding dependencies:

```bash
rg -n --hidden --glob '!node_modules' --glob '!dist' \
  'team-directory|projectMembers|Account Management|account_management|X-API-Key' \
  /var/www /opt /srv 2>/dev/null
```

Confirm the candidate route by checking the live response before editing.

## Verification
Test the same client id both ways.

Without opt-in:

```bash
curl -fsS -H "X-API-Key: $TOS_API_KEY" \
  "$TOS_API_URL/team-directory?crmClientId=<CLIENT_ID>"
```

With opt-in:

```bash
curl -fsS -H "X-API-Key: $TOS_API_KEY" \
  "$TOS_API_URL/team-directory?crmClientId=<CLIENT_ID>&includeAccountManagement=1"
```

The second response must contain Account Management employees with canonical email + usable TOS user id.

Do not print the API key in logs or the final report.
