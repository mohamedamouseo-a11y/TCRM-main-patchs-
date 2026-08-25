# TCRM — Felfel Meeting Command V9 (AI Staff Phase 12)

Purpose: continue BUILD/IMPLEMENTATION work after Tara Sales Operations Command by giving Felfel a compact read-only meeting command layer that navigates the existing meeting-intelligence workspace without triggering meeting, analysis, CRM, task, follow-up, or archive actions.

## Canonical baseline

- Repository: `mohamedamouseo-a11y/TCRM-MAIN-Tamiyouz-CRM-`
- Branch: `main`
- Expected HEAD: `0096b738fc966868a671b099263e11abf85b7fa8`
- Guarded file: `client/src/pages/FelfelPage.tsx`
- Expected base blob: `4cd0b430e2c24e41d8aa7bed5204fdb6fec329b4`

## Exact scope

Changes exactly one application file:

- `client/src/pages/FelfelPage.tsx`

No Darwish, Zaghloul, Tara, backend, API, database, migrations, routes, permissions, meeting provider behavior, CRM behavior, refresh reliability, customer data, or `external/mautic` file is changed.

## Phase 12 implementation

### Meeting Command

Adds a compact read-only command card between the existing `Meeting Intelligence Workspace` summary and the existing four Felfel tabs.

Marker:

`data-felfel-meeting-command="v9"`

It exposes four live navigation signals using already-loaded state/query data:

1. **Live Meeting** → `live` — active session indicator from `status?.active`.
2. **Transcript** → `transcript` — transcript segment count from `transcript?.segments?.length`.
3. **Meeting Intelligence** → `intelligence` — extracted action-item count from `intelligence?.actionItems?.length`.
4. **Recent Meetings** → `history` — loaded meeting count from `meetingsQ.data?.length`.

Every tile is `type="button"`, updates only local `felfelWorkspace` state, and exposes `aria-pressed`. The command block contains no `.mutate()` call.

### Controlled workspace navigation

Adds local UI state:

`felfelWorkspace`

Default remains `live`.

The existing four Radix tabs become controlled by `value={felfelWorkspace}` and `onValueChange={setFelfelWorkspace}`, so both the existing tab bar and the new command tiles navigate the same workspace.

## Preservation requirements

Must remain unchanged:

- `data-felfel-workspace-summary="v8"`
- `data-felfel-workspace="meeting-intelligence-v8"`
- `data-ai-staff-refresh="felfel-v1"`
- `TCRM_FELFEL_REFRESH_COMPLETION_V1`
- six-second bounded manual refresh behavior
- four main tabs: Live meeting, Transcript, Felfel Intelligence, Recent meetings
- Phase 7 progressive-disclosure sections
- `createMeetingM`
- `leaveMeetingM`
- `analyzeMeetingM`
- `createApprovedTasksM`
- `createFollowUpM`
- `archiveMeetingM`
- `createCurrentFollowUp`
- `archiveCurrentMeeting`
- `submitApprovedActions`

No meeting is joined, left, analyzed, archived, or synced by the new command layer.

## Apply helper

From `/var/www/TCRM-MAIN` use `python3`:

```bash
python3 <PATCH_PATH>/apply_felfel_meeting_command_v9.py --check
python3 <PATCH_PATH>/apply_felfel_meeting_command_v9.py --apply
python3 <PATCH_PATH>/apply_felfel_meeting_command_v9.py --verify
```

## User-requested execution mode

This phase is BUILD/IMPLEMENTATION only.

Do not run final acceptance, responsive/mobile acceptance, DevTools Console acceptance, browser takeover, or the user's developer final acceptance test.

A production build is required. TCRM Developer Hub may run its mandatory built-in Verify/Tests/Build/Security/Remote Sync gates as part of the controlled push flow; do not launch a separate/manual acceptance suite.

## Deployment workflow

1. Apply only the ChatGPT-authored helper to `/var/www/TCRM-MAIN`.
2. Run guarded verify and production build.
3. Use TCRM Developer Hub Review Push from inside TCRM.
4. Only if mandatory gates pass, use Developer Hub Auto Push to canonical `main`.
5. No shell commit/push, no new branch, no force push, no rebase/stash/reset.
6. Reload only `tamiyouz-crm` if required.
7. Upload the final Markdown implementation report + ZIP evidence directly into the current ChatGPT conversation.

## Required report

`TCRM-AI-Staff-Phase12-Felfel-Meeting-Command-V9-Report.md`

Record baseline, target blob, exact changed files, command/state preservation checks, build, Developer Hub gates, final canonical HEAD, PM2 state, and explicit confirmation that no final/manual acceptance workflow was run.
