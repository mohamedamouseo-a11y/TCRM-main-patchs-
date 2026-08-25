# TCRM — Darwish Supervisor Priority Command V4 (AI Staff Phase 9)

Purpose: continue BUILD/IMPLEMENTATION work after Phase 8 by making Darwish faster to operate for supervisors without adding any business automation or changing existing backend behavior.

## Canonical baseline

- Repository: `mohamedamouseo-a11y/TCRM-MAIN-Tamiyouz-CRM-`
- Branch: `main`
- Expected HEAD: `727a87ac74f2f5a5d9c74e447b932cc9cd70fce7`
- Guarded file: `client/src/pages/DarwishPage.tsx`
- Expected base blob: `f90ee0ad2c3f73663e914e3ddad93963795d215f`

## Exact scope

Changes exactly one application file:

- `client/src/pages/DarwishPage.tsx`

No Zaghloul, Tara, Felfel, backend, API, database, migrations, routes, permissions, customer data, action execution, refresh handler, or `external/mautic` file is changed.

## Phase 9 implementation

### Supervisor Priority Command

Adds a compact read-only command card immediately under the six KPI cards and above the existing Supervisor Workspace summary.

Marker:

`data-darwish-priority-command="v4"`

The command card shows four live supervisor signals using already-loaded query data:

1. Customer Intelligence — urgent signals
2. Supervision — active alerts
3. Actions & Automation — proposals awaiting human decision
4. Operations & Mapping — unmapped clients

Each tile is a navigation control only. It switches the existing Darwish top-level workspace tab and never calls a mutation, action execution, mapping save, or customer operation.

### Controlled Supervisor Workspace navigation

The existing four Radix tabs become controlled by local UI state:

`darwishWorkspace`

The default remains `intelligence`.

Both the existing sticky tab navigation and the new Priority Command tiles update the same state, so the supervisor can jump directly to the relevant workspace without scrolling/searching.

Preserved workspaces:

- Customer Intelligence
- Supervision
- Actions & Automation
- Operations & Mapping

All Phase 5 progressive-disclosure sections remain untouched.

## Safety preservation

This phase does not change:

- `refreshDarwishData`
- `refreshActionsM`
- `draftReplyM`
- `approveActionM`
- `rejectActionM`
- `executeActionM`
- `upsertM`
- `deleteM`

The new navigation controls contain no `.mutate()` call and do not alter query/refetch behavior.

## Apply helper

From `/var/www/TCRM-MAIN`:

```bash
python <PATCH_PATH>/apply_darwish_supervisor_priority_command_v4.py --check
python <PATCH_PATH>/apply_darwish_supervisor_priority_command_v4.py --apply
python <PATCH_PATH>/apply_darwish_supervisor_priority_command_v4.py --verify
```

## User-requested execution mode

This is BUILD/IMPLEMENTATION work only.

Do **not** run final acceptance, responsive/device acceptance, browser takeover, DevTools Console acceptance, or the user's developer final test in this phase.

A production build is still required. If TCRM Developer Hub automatically executes mandatory internal Verify/Tests/Build/Security/Remote Sync gates as part of its controlled push flow, allow those built-in gates to run; do not launch any separate/manual test suite.

## Deployment workflow

1. Apply only the ChatGPT-authored helper to `/var/www/TCRM-MAIN`.
2. Run guarded verify and `pnpm build`.
3. Use TCRM Developer Hub Review Push from inside TCRM.
4. If the mandatory Developer Hub gates pass, use Developer Hub Auto Push to canonical `main`.
5. No shell commit/push, no new branch, no force push, no rebase.
6. Reload only `tamiyouz-crm` if required.
7. Upload the implementation report/evidence directly into the current ChatGPT conversation.

## Required implementation report

Report:

`TCRM-AI-Staff-Phase9-Darwish-Supervisor-Priority-Command-V4-Report.md`

Record baseline, target blob, changed files, build status, Developer Hub gate status, final main HEAD, PM2 state, and explicit confirmation that no manual/final acceptance test was run.
