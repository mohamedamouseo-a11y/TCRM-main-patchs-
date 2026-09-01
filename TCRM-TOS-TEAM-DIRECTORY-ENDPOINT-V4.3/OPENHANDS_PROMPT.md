# OpenHands Prompt — Implement Real TOS Team Directory V4.3

You are working on the production/application server. Your job is to implement the **missing TOS operational team-directory endpoint**, verify it with live data, then rebuild/restart only the required services.

Do NOT git push.
Do NOT change the V4 TCRM assignment rules unless required for compatibility.
Do NOT hardcode employee names.
Do NOT create duplicate project/member storage.

## Patch source
Repository:
`mohamedamouseo-a11y/TCRM-main-patchs-`

Package:
`TCRM-TOS-TEAM-DIRECTORY-ENDPOINT-V4.3`

Read first:
- `README.md`
- `TOS_TEAM_DIRECTORY_SPEC.md`

## Current state
TCRM V4.2 no longer crashes if the TOS directory response is HTML, but it falls back to an empty directory.

Observed root cause from previous verification:
TOS returned the SPA HTML for the attempted team-directory URL instead of JSON.

That fallback is NOT the finished feature. We need a real API endpoint.

## Phase 1 — Find the exact operational API base
Do NOT assume `/team-directory` at hostname root is correct.

Inspect the current TCRM integration configuration/source and determine the exact URL used for existing successful operational requests such as:
- projects
- project-tasks
- tasks/events if applicable

The TCRM URL builder removes a trailing `/projects` from the configured API URL and appends sibling paths.

Safely report the operational base URL without exposing the API key.

Reproduce authenticated requests to existing sibling endpoints and identify which service/process handles them.

## Phase 2 — Locate the REAL TOS operational route source
Search the running server trees, focusing on the source that actually handles existing operational endpoints:

```bash
rg -n --hidden --glob '!node_modules' --glob '!dist' \
  'project-tasks|X-API-Key|UPSERT_BY_CRM_CLIENT_ID|crmClientId|projectOwners' \
  /var/www /opt /srv 2>/dev/null
```

Also inspect:
- PM2 process definitions
- working directories
- nginx proxy rules for the operational API base

Do not patch a generic SPA route if the operational API is served by another process/service.

## Phase 3 — Inspect existing TOS directory data
The TOS application already has department/employee data. Verify production schema/source before coding.

Expected concepts include:
- departments
- employees
- employee isActive
- employee name/email/position/department

Determine the canonical TOS identifier used by the existing project owner/member logic.

CRITICAL:
Never assume employee.id == user.id.
Use the exact identifier already accepted/returned by the project membership implementation.

## Phase 4 — Implement GET team-directory
Implement adjacent to existing operational routes and before any SPA/static fallback.

Route contract:

`GET <operational-base>/team-directory?crmClientId=118&includeAccountManagement=1`

Authentication:
- same `X-API-Key` validation as existing projects/project-tasks routes
- unauthorized response JSON 401/403

Directory:
- all ACTIVE TOS employees
- grouped by real department
- Account Management included when `includeAccountManagement=1`
- no hardcoded people
- directory must not be limited to current project members

Member identity fields:
- tosUserId
- name
- email
- jobTitle/position
- departmentKey
- departmentName

Use canonical/trusted database values.

## Phase 5 — Project and current project memberships
When `crmClientId` is supplied:
- use the SAME linked-project lookup used by existing project-tasks / UPSERT_BY_CRM_CLIENT_ID logic
- do not create another mapping
- return current project object
- return current projectMembers with real projectRole values

Existing TOS project members must remain unchanged by this read endpoint.

Expected response shape:

```json
{
  "departments": [],
  "projectMembers": [],
  "project": null,
  "excludedDepartment": null,
  "generatedAt": "ISO timestamp"
}
```

Follow `TOS_TEAM_DIRECTORY_SPEC.md` exactly.

## Phase 6 — Prove the route does not hit SPA fallback
Test authenticated live request.

For client 118 + includeAccountManagement=1 verify:
- status = 200
- Content-Type contains application/json
- body starts with JSON, not `<!doctype` / `<html>`

Also test invalid/missing API key:
- JSON 401/403
- never HTML SPA

Do not print the API key.

## Phase 7 — Verify department population
Report counts and representative names (safe employee names/emails are okay, no credentials) for:
- Management
- Sales
- Account Management / Account Manager
- SEO
- Design
- Media Buying
- Social Media
- Web Development
- any additional departments

If a department is zero, verify whether TOS actually has zero active employees there. Do not manufacture data.

Account Management must contain real AM names if active AM employees exist.

## Phase 8 — Verify current project members
For client 118:
- project must resolve if linked
- existing projectMembers must still appear
- roles must match TOS actual roles

Do not modify memberships during this read verification.

## Phase 9 — Build and deploy TOS
Use the existing build/deployment commands of the actual service you changed.

If the changed service is the main TOS app, inspect package.json and run at minimum the project's available equivalents of:

```bash
npm run check
npm run build
```

If historical type errors exist, identify whether changed files introduce new errors; do not fix unrelated project-wide errors.

Restart only the service that owns the operational endpoint.
Do not redesign nginx/PM2 architecture.
If a proxy change is genuinely required, back up config first and run `nginx -t` before reload.

## Phase 10 — Re-test from TCRM
After TOS endpoint is live:

1. Load client 118 TOS Project Team.
2. Confirm names appear under populated departments.
3. Confirm Account Management names appear.
4. Confirm no HTML/JSON parse error.
5. Confirm existing linked members still display.

Then functional assignment test with an authorized TCRM account if credentials/session are available:
- choose one Account Manager
- choose one employee from another department
- Save Project Team
- confirm existing sync adds selected users as Owner
- confirm old project members remain intact

If no authenticated browser credentials are available, do not falsely claim the assignment test passed; report it NOT TESTED.

## Phase 11 — Backend tamper protection
If authenticated TCRM test access exists, submit fake/non-directory `tosUserId` directly to `saveTosProjectTeam`.
Expected: FORBIDDEN.

If credentials are unavailable, report NOT TESTED rather than PASS.

## Important cleanup regarding V4.2 fallback
Once the real endpoint is proven stable, keep the TCRM safe-parse protection. Do not reintroduce direct `response.json()` crashes.

However, do not let an HTML upstream response masquerade as a successful populated directory. It is acceptable for the UI to show a clear upstream-directory error if the TOS API fails again.

Do not destabilize TCRM while implementing this TOS fix.

## Final report
Return only:

OPERATIONAL BASE:
ROUTE SOURCE PATH:
AUTH REUSED: PASS/FAIL
TOS HTTP: PASS/FAIL
TOS CONTENT-TYPE: PASS/FAIL
SPA FALLBACK REMOVED: PASS/FAIL
MANAGEMENT: <count + names>
SALES: <count + names>
ACCOUNT MANAGEMENT: <count + names>
SEO: <count + names>
DESIGN: <count + names>
MEDIA BUYING: <count + names>
SOCIAL MEDIA: <count + names>
WEB DEVELOPMENT: <count + names>
PROJECT 118: PASS/FAIL/NOT LINKED
PROJECT MEMBERS: PASS/FAIL
TOS BUILD: PASS/FAIL
TOS RESTART: PASS/FAIL
TCRM CLIENT 118 DIRECTORY: PASS/FAIL
CROSS-DEPARTMENT ASSIGN: PASS/FAIL/NOT TESTED
FAKE ID BLOCKED: PASS/FAIL/NOT TESTED
ERRORS: none / exact error
FINAL: SUCCESS/BLOCKED

Do NOT report SUCCESS unless the live authenticated TOS team-directory returns JSON and the TCRM client 118 directory visibly loads real employee names.