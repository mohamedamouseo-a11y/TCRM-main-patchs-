# TOS Runtime Spec — Full Project-Team Directory V4

## Endpoint
TCRM uses the TOS operational directory endpoint equivalent to:

`GET <TOS_API>/team-directory?crmClientId=<id>&includeAccountManagement=1`

Authentication must remain the existing `X-API-Key` flow.

## Required response behavior
For the Handover Project Team selector, `departments` must represent the **real active TOS employee directory grouped by department**, not only employees who already belong to the current project.

Expected conceptual shape:

```json
{
  "departments": [
    {
      "key": "sales",
      "name": "Sales",
      "members": [
        {
          "tosUserId": "...",
          "name": "...",
          "email": "...",
          "departmentKey": "sales",
          "departmentName": "Sales",
          "jobTitle": "..."
        }
      ]
    }
  ],
  "projectMembers": [],
  "project": {}
}
```

## Departments
Return the real active employees for every department available in the TOS employee/team source, including the departments shown in the TCRM UI such as:
- Management
- Sales
- Account Manager / Account Management
- SEO
- Design
- Media Buying
- Social Media
- Web Development
- any other active department

Do not invent members. If a department truly has zero active employees in the source of truth, `members: []` is valid.

## Account Management
When `includeAccountManagement=1`:
- Account Management must NOT be filtered out.
- Active Account Management employees must be included under their proper department.
- Each employee must expose a usable TOS user id and canonical email.

If the option is missing/false, preserve the existing behavior for unrelated consumers if backward compatibility requires it.

## Project membership separation
`departments[].members` = directory of active employees available to select.

`projectMembers` = users already attached to the specific project with their current TOS project role.

Do not filter the employee directory down to `projectMembers`.

## Eligibility
Use the real live TOS employee/team source and include active eligible employees only.
- Exclude deleted/deactivated users.
- Preserve canonical department membership.
- Preserve canonical employee id/email/name from TOS.

## Safety
- Do not alter existing API-key authentication.
- Do not log secrets.
- Do not change unrelated task-assignment endpoints unless they share the same route implementation and the change is required.
- Preserve current `projectMembers` behavior and response contract.

## Verification
Before deploy, show department counts from the live endpoint with `includeAccountManagement=1` and confirm that names appear for departments that actually have active employees.

After deploy, verify TCRM Handover shows those same employees in the corresponding department cards.
