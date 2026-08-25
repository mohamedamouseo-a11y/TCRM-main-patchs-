# TCRM — Felfel Workspace Polish V8 (AI Staff UX Phase 7)

Purpose: polish Felfel's meeting-intelligence workspace after Refresh Reliability V1, reduce visual density in the Intelligence tab, and improve empty-state guidance without changing any meeting, CRM, archive, follow-up, task, refresh, backend, API, database, permission, or business behavior.

## Canonical baseline

- Repository: `mohamedamouseo-a11y/TCRM-MAIN-Tamiyouz-CRM-`
- Branch: `main`
- Expected HEAD: `66d102caf442c394894d6719118ea037abdba698`
- Guarded `client/src/pages/FelfelPage.tsx` blob: `a0bf37f53ef8d657793d8b4afa2b366133ed7e28`

## Exact scope

Changes exactly one application file:

- `client/src/pages/FelfelPage.tsx`

No Darwish, Zaghloul, Tara, backend, API, database, migrations, routes, permissions, meeting mutation, CRM mutation, refresh reliability handler, or `external/mautic` file is changed.

## UX changes

### 1. Meeting Intelligence Workspace summary

A compact read-only workspace summary appears between the KPI row and the existing four tabs. It shows at a glance:

- active/no active session;
- transcript segment count;
- analysis ready/awaiting analysis;
- CRM linked/not linked.

Markers:

- `data-felfel-workspace-summary="v8"`
- `data-felfel-workspace="meeting-intelligence-v8"`

### 2. Intelligence progressive disclosure

The generated intelligence summary, decisions, and action items stay directly visible.

The operational sections that make the Intelligence tab long are kept intact but placed inside native expandable sections:

- CRM Context & Approved Actions — collapsed by default
- Follow-up Planner — collapsed by default
- Meeting Archive & Google Drive — collapsed by default
- Felfel's Take — open by default

Markers:

- `data-felfel-section="crm-approved-actions"`
- `data-felfel-section="follow-up-planner"`
- `data-felfel-section="meeting-archive"`
- `data-felfel-section="felfel-take"`

No mutation button, payload, handler, validation, approval step, CRM-selection rule, or archive/follow-up behavior is removed or changed.

### 3. Premium empty states

The generic dashed empty state is upgraded to a premium, bilingual meeting-intelligence empty state with clearer guidance. It remains informational only and does not navigate, mutate, auto-select, or trigger any meeting/CRM action.

## Refresh Reliability preservation

Phase 6/6.1 behavior must remain byte-for-byte functional.

Required markers/handlers preserved:

- `data-ai-staff-refresh="felfel-v1"`
- `TCRM_FELFEL_REFRESH_COMPLETION_V1`
- `refreshFelfelData`

Do not change the six-second bounded refresh guard in this phase.

## Apply helper

From `/var/www/TCRM-MAIN`:

```bash
python <PATCH_PATH>/apply_felfel_workspace_polish_v8.py --check
python <PATCH_PATH>/apply_felfel_workspace_polish_v8.py --apply
python <PATCH_PATH>/apply_felfel_workspace_polish_v8.py --verify
```

## Required acceptance

Read-only authenticated visual checks should confirm:

1. premium Felfel hero/portrait/title remain unchanged;
2. six KPI cards remain visible;
3. Refresh data still works and shows Last updated;
4. compact workspace summary renders correctly;
5. all four main tabs remain and work;
6. Live Meeting remains structurally unchanged;
7. Transcript/history empty states look intentional and helpful;
8. after selecting an existing meeting with intelligence data, the Intelligence tab keeps summary/decisions/action items visible while the four operational sections use progressive disclosure;
9. opening each expandable section exposes the original controls/content;
10. no meeting, task, follow-up, archive, or CRM mutation is triggered during acceptance.

## Standing deployment workflow

1. ChatGPT authors and pushes the patch/helper to `TCRM-main-patchs-`.
2. Manus applies it directly on `/var/www/TCRM-MAIN`.
3. Manus builds and runs the TCRM Developer Hub Review Push gates.
4. Only if Verify, Tests, Build, Security, and Remote Sync all pass, Manus uses **Developer Hub Auto Push from inside TCRM** to push the live checkout to canonical `TCRM-MAIN/main`.
5. No shell commit, no shell push, no new branch, no force push, no rebase.
6. Manus performs read-only authenticated visual acceptance and uploads the Markdown report + ZIP evidence directly into the current ChatGPT conversation.
7. The user's developer final cross-agent acceptance test remains deferred until Phase 8 cross-agent consistency is completed.
