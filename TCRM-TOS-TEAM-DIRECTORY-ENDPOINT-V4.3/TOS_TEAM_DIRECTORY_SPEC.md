# TOS Team Directory Endpoint — V4.3 Contract

## Route
Register beside the existing TCRM↔TOS operational API routes, before static/SPA fallback:

`GET <operational-base>/team-directory`

Query parameters:
- `crmClientId` — optional positive TCRM client id used to resolve the linked TOS project.
- `includeAccountManagement=1` — include Account Management department members. Missing/false may preserve older exclusion behavior for other consumers.

## Authentication
Use the **same X-API-Key validation** already used by the production `projects`, `project-tasks`, `tasks`, or equivalent TCRM↔TOS operational routes.

Never introduce a second API key or weaker authentication path.

Unauthorized requests must return JSON with 401/403, never the HTML SPA.

## Directory source of truth
Use TOS production employee + department data.

Directory rules:
- include only active employees (`isActive = true`),
- group by real TOS department,
- do not derive directory membership from current project members,
- do not hardcode names,
- preserve departments with zero active employees if the existing UI expects stable department cards.

Each returned member must contain enough trusted identity for TCRM validation:

```json
{
  "tosUserId": "<canonical id used by TOS project membership/projectOwners>",
  "name": "Employee Name",
  "email": "canonical@email",
  "jobTitle": "Position",
  "departmentKey": "stable-department-key-or-id",
  "departmentName": "Department Name"
}
```

### Critical ID rule
Do not invent `tosUserId` mapping.
Inspect the existing production `/projects` project-owner/member handling and use the exact identifier type it accepts and returns for TOS users/members. If project membership uses `users.id`, use that. If it uses employee ids, use that. The directory and project member response must use the same canonical identifier.

## Account Management
When `includeAccountManagement=1`, Account Management / Account Manager employees MUST be returned normally with real names, emails, ids, and positions.

Department matching may normalize forms such as:
- Account Management
- Account Manager
- account_management

Do not special-case individual people.

## Linked project lookup
If `crmClientId` is provided, resolve the linked TOS project using the **same production lookup/storage used by `project-tasks` and project UPSERT_BY_CRM_CLIENT_ID**.

Do not create a second project mapping table.

Return a `project` object consistent with the current operational API. At minimum expose when available:

```json
{
  "id": "...",
  "projectId": "...",
  "crmClientId": "118",
  "name": "...",
  "status": "...",
  "stage": "..."
}
```

If no project is linked, return `project: null` (or the established project-not-found shape if TCRM already supports it) and `projectMembers: []`.

## Project members
`projectMembers` represents **current memberships on the linked TOS project**, not the whole directory.

Reuse the same membership storage and role rules used by TOS project operations.

Each member should include:

```json
{
  "tosUserId": "...",
  "name": "...",
  "email": "...",
  "departmentKey": "...",
  "departmentName": "...",
  "jobTitle": "...",
  "projectRole": "OWNER|MANAGER|MEMBER"
}
```

Existing memberships must remain read-only from the TCRM selector and must not be deleted or downgraded by this endpoint.

## Response shape

```json
{
  "departments": [
    {
      "key": "...",
      "name": "Sales",
      "members": []
    }
  ],
  "projectMembers": [],
  "project": null,
  "excludedDepartment": null,
  "generatedAt": "2026-09-01T00:00:00.000Z"
}
```

When Account Management is intentionally excluded for a non-opt-in consumer, `excludedDepartment` may identify it. When included, prefer `null`.

## HTTP / JSON behavior
All API outcomes must be JSON:
- 200 valid response
- 400 invalid query
- 401/403 API key failure
- 500/503 real server/database failure

Never let the SPA/index.html answer this route.
Set `Content-Type: application/json`.

## TCRM compatibility
TCRM currently builds sibling operational URLs by taking its configured TOS API URL, removing trailing `/projects`, then appending `team-directory`.
Therefore OpenHands must confirm the **actual configured operational base** before registering the route.

Do not assume the correct URL is hostname root `/team-directory`.

## Verification acceptance
For client 118, live authenticated request must prove:
- HTTP 200
- application/json
- Account Management names populated if active AM employees exist
- other populated departments show active names
- current projectMembers still returned
- valid cross-department selection saves/syncs
- fake/non-directory tosUserId remains blocked by TCRM backend
