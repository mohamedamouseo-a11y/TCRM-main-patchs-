# OpenHands Prompt — TCRM TOS Project Team Full Directory V4

You are working on the application server. Apply, verify, build, and deploy this V4 change. **Do not push anything to GitHub.**

## Patch source
Repository:
`mohamedamouseo-a11y/TCRM-main-patchs-`

Package:
`TCRM-TOS-PROJECT-TEAM-FULL-DIRECTORY-V4`

Read first:
- `README.md`
- `APPLY_TCRM_PATCH.py`
- `TOS_RUNTIME_SPEC.md`

## Target TCRM path
Expected:
`/var/www/TCRM-MAIN`

Inspect the real running working tree first. Do not reset or overwrite unrelated work.

## New business requirement
This V4 intentionally replaces the previous V3 self-only behavior.

In **Client Profile > Handover > TOS Project Team**:

1. Show the real team member names inside every TOS department.
2. Populate the **Account Manager / Account Management** department with the real active AM employees.
3. A user who already has permission to manage TOS Project Team must be able to select **any active employee from any department**.
4. Do not restrict a regular AccountManager to themselves anymore.
5. Existing actual TOS project members remain read-only/managed inside TOS.
6. New selections continue through the existing TCRM -> TOS Owner sync flow.
7. Do not fabricate employee names or hardcode a roster.

## Phase 1 — Inspect current server state

```bash
cd /var/www/TCRM-MAIN
git status --short
git rev-parse HEAD
git branch --show-current
```

The server may already contain V3 code such as:
- `sanitizeRegularAccountManagerTosOwners`
- `isSelfMember`
- `Assign myself`
- self-only checkbox restrictions

Do not roll back unrelated V3 fixes such as `includeAccountManagement=1`.

## Phase 2 — Apply TCRM V4

Obtain the package using the normal read-only method available on the server/system.

Run:

```bash
python3 /PATH/TO/TCRM-TOS-PROJECT-TEAM-FULL-DIRECTORY-V4/APPLY_TCRM_PATCH.py /var/www/TCRM-MAIN
```

If an anchor differs from the current live code, inspect the equivalent current implementation and port the same V4 behavior manually. Do not force replacements.

Expected TCRM behavior after patch:

### Frontend
- Every employee returned in `departments[].members` is selectable unless they are already an actual TOS project member or the whole control is disabled by normal page permissions.
- No `self only` restriction.
- Other Account Managers are selectable.
- Sales, SEO, Design, Media Buying, Social Media, Web Development, Management and other department employees are selectable.
- Account Management names appear when returned by TOS.
- Existing actual TOS project members remain checked/read-only.

The `Assign myself` button may be removed or retained only as a convenience shortcut, but it must NOT imply or enforce self-only behavior.

### Backend
For a regular `AccountManager`, do not trust arbitrary payload IDs.

Replace self-only validation with trusted-directory validation:
- request TOS directory with `includeAccountManagement: true`,
- build a trusted map of all active returned employees across all departments,
- each submitted `tosUserId` must exist in that directory,
- canonicalize name/email/department metadata from the TOS response,
- reject arbitrary/non-directory IDs with `FORBIDDEN`,
- allow valid employees from any department.

Admin and AccountManagerLead existing permissions must remain unchanged.

## Phase 3 — Fix the REAL TOS directory source

This is mandatory because the screenshot currently shows several department cards with `0` employees.

Follow `TOS_RUNTIME_SPEC.md`.

Locate the real live implementation of the TOS `team-directory` endpoint used by TCRM.

Test:

`GET team-directory?crmClientId=<safe-client>&includeAccountManagement=1`

Do not print API keys.

The response must use the actual TOS active employee/team source and return employees grouped by department.

Important distinction:
- `departments[].members` = active employee directory available for assignment.
- `projectMembers` = employees already assigned to this specific project.

Do NOT make `departments[].members` equal only to current project members.

Verify real employee counts/names for departments that have active staff, including Account Management.

If TOS already has the employees but the endpoint filters them out, fix that filter.
If TOS truly has no active employees in a department, do not invent names.

Preserve backward compatibility for unrelated consumers where necessary.

## Phase 4 — Security tests

Using a regular AccountManager with project-team manage access, bypass the UI and test backend payloads.

Expected allowed:
- valid Account Management employee
- valid Sales employee
- valid SEO/Design/Media/Social/Web employee

Expected forbidden:
- random fake `tosUserId`
- deleted/inactive employee not in trusted TOS directory
- spoofed id that is not returned by directory

Also verify submitted name/email metadata cannot override trusted TOS canonical metadata.

## Phase 5 — UI QA

Open a safe Client Profile > Handover > TOS Project Team.

Confirm:
- department cards show actual names where active employees exist,
- Account Manager section contains AM names,
- checkbox selection works for employees in every populated department,
- regular AccountManager can select another AM and employees from other departments,
- selected new employees show as Owner/pending Owner according to existing UI,
- Save Project Team succeeds,
- existing project members remain present and are not removed.

## Phase 6 — Build / regression checks

Run the project's actual scripts. At minimum:

```bash
git diff --check
npm run check
npm run build
```

The repository may have historical TypeScript errors. Do not fix unrelated errors. Confirm the V4 changed files introduce no new TypeScript errors.

`npm run build` must finish successfully before deploy.

## Phase 7 — Deploy

If all required checks pass:
- use the existing server deployment workflow,
- restart only the required TCRM/TOS services,
- do not invent new PM2/systemd/nginx configuration,
- do not git push.

Post-deploy smoke-test the public Handover page and live TOS directory.

## Final report
Return:
- TCRM path and branch/HEAD before change
- exact TCRM files changed
- actual live TOS route/source file changed (if any)
- live TOS department counts after change
- confirmation that Account Management contains real names
- backend validation results for valid cross-department assignments and fake IDs
- `npm run check` result / regression assessment
- `npm run build` result
- deploy/restart result
- post-deploy UI smoke result
- final status: `SUCCESS` or `BLOCKED`

Do not report SUCCESS unless populated departments display real names, Account Management is populated when active AM employees exist, cross-department assignment works, fake IDs are rejected, build passes, and post-deploy smoke test passes.
