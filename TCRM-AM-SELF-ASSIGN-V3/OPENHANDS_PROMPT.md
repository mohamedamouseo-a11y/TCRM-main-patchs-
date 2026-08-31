# OpenHands Prompt — Apply TCRM AM Self-Assign V3

You are working directly on the production/application server. Your job is to **apply, verify, build, and deploy** the patch on the server. **Do not push anything to GitHub.** GitHub push is handled outside OpenHands.

## Patch source
Patch repository:
`mohamedamouseo-a11y/TCRM-main-patchs-`

Package:
`TCRM-AM-SELF-ASSIGN-V3`

Read first:
- `README.md`
- `APPLY_PATCH.py`
- `TOS_RUNTIME_SPEC.md`

## Target TCRM working tree
Expected server path:
`/var/www/TCRM-MAIN`

If the real path differs, locate the currently running TCRM working tree and use that. Do not treat the server path itself as a GitHub repository name.

## Required business behavior
In **Client Profile > Handover > Step 1: TOS Project Team**:

1. Account Management employees must appear.
2. A regular `AccountManager` must be able to assign/select **only themselves**.
3. The current AM must be resolved to the TOS employee using trusted email identity (`email` / `centralEmail` -> canonical TOS employee email).
4. Never assume TCRM numeric user id equals TOS numeric/user id.
5. A regular AM must not be able to add another AM or another department employee.
6. Existing non-self pending project owners must be preserved.
7. Existing actual TOS project memberships remain managed by TOS.
8. Admin and AccountManagerLead retain their existing broader permissions.
9. Backend validation is mandatory; frontend restrictions alone are not sufficient.

## Phase 1 — Inspect server state

```bash
cd /var/www/TCRM-MAIN
git status --short
git rev-parse --show-toplevel
git rev-parse HEAD
```

Do not reset, delete, stash, or overwrite unrelated work.

If the same feature is already partially implemented locally, compare it against V3 requirements. Keep correct existing work and port only missing V3 behavior. Do not blindly duplicate code.

## Phase 2 — Obtain patch package
Use the normal read-only method already available on this server/system to obtain the package from:

`mohamedamouseo-a11y/TCRM-main-patchs-/TCRM-AM-SELF-ASSIGN-V3`

Do **not** configure new GitHub credentials and do **not** perform `git push`.

## Phase 3 — Apply TCRM patch
Run:

```bash
python3 /PATH/TO/TCRM-AM-SELF-ASSIGN-V3/APPLY_PATCH.py /var/www/TCRM-MAIN
```

If the patcher stops because an anchor changed:
- inspect the current equivalent code,
- implement the same V3 behavior manually,
- do not force string replacements,
- do not refactor unrelated code.

Expected TCRM files touched by V3:
- `server/services/tosIntegrationService.ts`
- `server/routers.ts`
- `client/src/components/TosProjectTeamSelector.tsx`
- `client/src/pages/ClientProfile.tsx`

Then review:

```bash
git diff --check
git diff --stat
git diff -- \
  server/services/tosIntegrationService.ts \
  server/routers.ts \
  client/src/components/TosProjectTeamSelector.tsx \
  client/src/pages/ClientProfile.tsx
```

## Phase 4 — Verify/patch live TOS team-directory
The TCRM patch requests:

`includeAccountManagement=1`

Follow `TOS_RUNTIME_SPEC.md`.

First test the live TOS endpoint. If it already supports this option correctly, do not rewrite it.

If it does not, patch the **real live TOS route source** so:
- default request keeps old behavior,
- `includeAccountManagement=1` includes Account Management,
- active AM employees expose canonical email and usable TOS user id,
- `X-API-Key` remains required,
- `projectMembers` behavior remains unchanged.

Do not globally expose Account Management to unrelated task-directory consumers.

Do not print API keys or credentials.

## Phase 5 — Backend security verification
For a regular `AccountManager`, verify all of the following:

### Allowed
- Add/select own matched TOS Account Management identity.
- Remove own pending selection before save if desired.

### Not allowed
- Add another Account Manager.
- Add a Sales/SEO/Design/other employee.
- Replace another user's identity by editing payload metadata.
- Remove or overwrite existing non-self pending owners.

Perform at least one direct/tampered request against `accountManagement.saveTosProjectTeam`, bypassing the UI.

Expected result for adding a new non-self id: `FORBIDDEN`.

Also verify identity mismatch behavior:
- if TCRM email/centralEmail does not match a TOS Account Management employee email, self-assignment must fail clearly;
- do not fall back to display-name matching.

## Phase 6 — UI verification
Using a safe client:

### Regular AccountManager
- Account Management section is visible.
- Own AM row is identifiable/selectable.
- `Assign myself` button is visible when the current TOS identity is found.
- Other employee checkboxes are disabled for the regular AM.
- Save succeeds for self.

### Admin / AccountManagerLead
- Existing team-management behavior remains available.
- Account Management is visible.
- Existing TOS project members still render with their real roles.

## Phase 7 — Build and typecheck
Inspect `package.json` and use the project's real scripts. At minimum run the available equivalents of:

```bash
npm run check
npm run build
```

Both must finish successfully. Do not report "build running"; report final exit status.

Fix only errors caused by this patch.

## Phase 8 — Deploy on server
After all checks pass:

1. Use the server's existing deployment/process workflow.
2. Restart only the required TCRM/TOS services.
3. Do not invent a new PM2/systemd/nginx setup.
4. Verify the service is listening on its expected port.
5. Smoke-test the public Client Profile Handover page and the TOS directory call after restart.

**Do not git push.**

## Final report
Return a concise report containing:
- TCRM path and HEAD before patch
- exact files changed
- whether TOS runtime required a change and its real server path
- identity mapping used
- tamper-test result
- `npm run check` result
- `npm run build` result
- restart/deploy result
- post-deploy smoke-test result
- final status: `SUCCESS` or `BLOCKED`

Do not mark SUCCESS unless build, backend tamper test, and post-deploy smoke test all pass.
