# OpenHands / Manus Prompt — TCRM TOS Account Manager Self-Assign V2

You are working on the production TCRM/TOS server. Implement the patch package exactly, but inspect the live code and current git state before changing anything.

## Source package
GitHub repository:
`mohamedamouseo-a11y/TCRM-main-patchs-`

Package folder:
`TCRM-TOS-AM-SELF-ASSIGN-V2`

Read these files first:
1. `README.md`
2. `APPLY_TCRM_PATCH.py`
3. `TOS_RUNTIME_PATCH_SPEC.md`

## Business requirement
In **Client Profile > Handover > Step 1: TOS Project Team**:

- Account Management employees must be visible.
- A regular `AccountManager` can select **only their own TOS employee identity**.
- They must not be able to add another Account Manager or any other employee.
- Backend authorization must enforce the same rule; UI-only protection is not acceptable.
- `Admin`, `AccountManagerLead`, Sales Manager, and existing authorized Sales owner behavior must not regress.
- Existing TOS project memberships remain managed inside TOS.
- New TCRM selections continue to sync to TOS as `Owner` using the existing sync flow.
- Do not convert this into TCRM `client.accountManagerId` assignment. This patch is for **TOS Project Team membership**.

## Phase 1 — Safety / discovery
1. Locate the real TCRM main working tree and confirm its remote is:
   `mohamedamouseo-a11y/TCRM-MAIN-Tamiyouz-CRM-`
2. Fetch latest `origin/main`.
3. Show `git status --short` and current HEAD.
4. Do not reset, delete, or overwrite unrelated local work.
5. Locate the actual TOS deployment that serves the API base URL configured in TCRM.
6. Capture the current live `team-directory` behavior before editing.

## Phase 2 — Apply TCRM patch
From a temporary clone/copy of the patch repository, run:

```bash
python3 TCRM-TOS-AM-SELF-ASSIGN-V2/APPLY_TCRM_PATCH.py /PATH/TO/TCRM-MAIN
```

If an anchor does not match, STOP and inspect the current equivalent code. Port the same behavior manually; do not force a blind replacement.

Expected TCRM files changed:
- `server/services/tosIntegrationService.ts`
- `server/routers.ts`
- `client/src/components/TosProjectTeamSelector.tsx`
- `client/src/pages/ClientProfile.tsx`

Review the diff before continuing.

## Phase 3 — Patch the real TOS runtime endpoint
Follow `TOS_RUNTIME_PATCH_SPEC.md`.

The production TOS endpoint must support:

`includeAccountManagement=1`

Rules:
- Without the parameter, preserve current behavior.
- With the parameter, include Account Management and active employee emails.
- Preserve `projectMembers`.
- Preserve `X-API-Key` authentication.
- Do not globally expose Account Management to task-directory consumers.

Important: the production `team-directory` implementation was not found in the current GitHub `TOS/main` tree when this package was prepared. Search the actual deployment and patch the real route. Do not invent a source file path.

## Phase 4 — Build / tests
Run the repository's real scripts after inspecting `package.json`. At minimum run the available equivalents of:

```bash
npm run check
npm run build
```

Also run relevant tests if present.

Do not ignore TypeScript/build errors introduced by this patch.

## Phase 5 — Functional QA
Use a safe test client/project.

### A. TOS API compatibility
1. Call `team-directory?crmClientId=<id>` without the new parameter.
   - Account Management should remain excluded if that was the previous behavior.
2. Call `team-directory?crmClientId=<id>&includeAccountManagement=1`.
   - Account Management must be present.
   - AM employees must include canonical TOS email + user id.

### B. Admin / AM Lead
- Account Management is visible.
- Existing full team-selection behavior still works.
- Save syncs successfully.

### C. Regular assigned AccountManager
- Account Management is visible.
- Their own row is selectable if TCRM email/centralEmail matches the TOS employee email.
- Other employees are disabled.
- Selecting themselves and saving adds/syncs them as TOS `Owner`.
- Existing other pending owner selections are preserved.

### D. Backend tamper test — mandatory
As a regular AccountManager, bypass the UI and call `accountManagement.saveTosProjectTeam` with a different employee's `tosUserId`.

Expected: request is rejected (`FORBIDDEN`) and no other employee is added/removed.

Also attempt to remove another existing pending owner from the payload.

Expected: rejected.

### E. Identity mismatch
If the regular AM's TCRM email/centralEmail does not match a TOS Account Management employee email:
- UI must not allow another person's checkbox.
- Save must fail with a clear mapping/precondition error.
- Do not fall back to matching by display name.

### F. Regression
Verify the existing task-assignment directory behavior is unchanged and did not start exposing Account Management globally.

## Phase 6 — Deploy and git
Only after all checks pass:
1. Commit the TCRM changes with a focused message, e.g.:
   `fix(handover): allow secure AM self-assignment to TOS project team`
2. Push using the repository's normal production workflow. Do not force-push.
3. If the TOS runtime is backed by a separate git repository, commit/push its change in that correct repository as a separate focused commit. If it is not tracked by a known remote, do not fabricate one; document exactly where the runtime change lives.
4. Restart only the required services using the server's existing service manager/process workflow.
5. Re-run the smoke tests after restart.

## Final report
Create `TCRM-TOS-AM-SELF-ASSIGN-V2-REPORT.md` containing:
- TCRM before/after commit SHAs
- TOS repository/working-tree path and commit SHA if applicable
- exact files changed
- build/test commands and results
- API verification result with and without `includeAccountManagement=1`
- UI QA results for Admin/AM Lead/regular AccountManager
- backend tamper-test result
- deployment/restart result
- any identity mapping issue found

Do not report success unless the backend tamper test and post-deploy smoke test both pass.
