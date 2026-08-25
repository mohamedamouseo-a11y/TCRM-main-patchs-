# TCRM — AI Staff Refresh Reliability V1 (Phase 6)

Purpose: make the manual Refresh control reliable, visible, and consistent across Darwish, Zaghloul, Tara, and Felfel without triggering any mutation or business/customer action.

## Canonical baseline

- Repository: `mohamedamouseo-a11y/TCRM-MAIN-Tamiyouz-CRM-`
- Branch: `main`
- Expected HEAD: `b1dc75ff7bb825e99e859f1a379516e232091d9b`

Guarded page blobs:

- `client/src/pages/DarwishPage.tsx` → `02214a9bdb3db6771edb0832737d996ef2ad21ec`
- `client/src/pages/ZaghloulV5Page.tsx` → `1cf4947be082609706008da5c8d4112f89f2829c`
- `client/src/pages/TaraAgentPage.tsx` → `20f124868c997f17079c39ec97de655efe799ec2`
- `client/src/pages/FelfelPage.tsx` → `bc7fc40786d3c37944e5a51ebd33e0c6399cfddd`

## Exact scope

Changes exactly four frontend page files:

1. `client/src/pages/DarwishPage.tsx`
2. `client/src/pages/ZaghloulV5Page.tsx`
3. `client/src/pages/TaraAgentPage.tsx`
4. `client/src/pages/FelfelPage.tsx`

No backend, API procedure, database, migration, route, permission, Mautic, customer data, action approval, meeting mutation, campaign mutation, outbound action, or automation behavior is changed.

## Reliability contract

Each agent gets one explicit manual refresh control with:

- awaited query `refetch()` calls rather than fire-and-forget behavior;
- loading lock while refresh is running;
- spinning Refresh icon and `Refreshing...` / Arabic equivalent;
- success/error feedback;
- visible `Last updated` timestamp after a successful refresh;
- no `.mutate()` call inside the manual refresh handler.

### Darwish

The existing top Refresh control is upgraded from fire-and-forget calls to an awaited refresh handler. It refreshes all current top-level Darwish query results and invalidates the Darwish router so mounted intelligence child panels are refreshed too.

It does **not** alter `Refresh proposals`. That remains a separate, explicit mutation inside the Human Action Queue with its existing safety semantics.

Marker:

`data-ai-staff-refresh="darwish-v1"`

### Zaghloul

Zaghloul currently has no explicit top-level data refresh action. Phase 6 adds one and refreshes the complete set of V5 page queries: health, features, inbox, contacts, pipelines, deals, broadcasts/templates, automations, flows, AI agents, dashboard, team, settings, API keys, webhooks, and MCP status.

Marker:

`data-ai-staff-refresh="zaghloul-v1"`

### Tara

The existing Tara Refresh button is upgraded to an awaited manual refresh handler with UI feedback. The existing silent `refresh()` helper used after save/delete mutations remains unchanged so existing post-mutation behavior is preserved.

The manual refresh also invalidates Tara cached queries so provider/voice/social child surfaces become stale/refetch correctly when opened.

Marker:

`data-ai-staff-refresh="tara-v1"`

### Felfel

The current Vexa Lite badge uses a Refresh icon but is not itself a refresh action. Phase 6 keeps the Vexa Lite badge and adds a clear manual `Refresh data` button.

The manual refresh is context-aware:
- always refreshes health, capabilities, and meeting history;
- refreshes meeting status/transcript only when a meeting is selected;
- refreshes CRM client data only when intelligence exists;
- refreshes deal/follow-up/archive queries only when a CRM client is selected.

No join/leave/analyze/task/follow-up/archive mutation is invoked.

Marker:

`data-ai-staff-refresh="felfel-v1"`

## Apply helper

Run from the live TCRM checkout:

```bash
python apply_ai_staff_refresh_reliability_v1.py --check
python apply_ai_staff_refresh_reliability_v1.py --apply
python apply_ai_staff_refresh_reliability_v1.py --verify
```

The helper refuses to apply unless all four guarded blobs exactly match the baseline above.

## Required functional acceptance

For each route `/darwish`, `/zaghloul`, `/tara`, `/felfel`:

1. click only the top/manual Refresh data control;
2. confirm it immediately enters a disabled loading state;
3. confirm the Refresh icon spins;
4. confirm the control returns to enabled state;
5. confirm success feedback;
6. confirm `Last updated` appears/changes;
7. confirm no business/customer mutation is triggered;
8. confirm page identity, KPI/navigation/workspace UI remains intact.

For Darwish, do **not** click `Refresh proposals`.
For Tara, do **not** save settings/process queue/test provider.
For Felfel, do **not** join/leave/analyze/create/archive anything.
For Zaghloul, do **not** create/edit/send/run anything.

## Standing deployment workflow

1. ChatGPT authors and pushes this guarded patch/helper to `TCRM-main-patchs-`.
2. Manus applies it directly on `/var/www/TCRM-MAIN`.
3. Manus builds and runs TCRM Developer Hub Review Push gates.
4. Only if Verify, Tests, Build, Security, and Remote Sync all pass, Manus uses **Developer Hub Auto Push from inside TCRM** to push the live checkout to canonical `TCRM-MAIN/main`.
5. No shell commit, no shell push, no new branch, no force push, no rebase.
6. Manus performs authenticated read-only refresh acceptance and uploads the final Markdown report + ZIP evidence into the current ChatGPT conversation.
7. The user's developer final acceptance remains deferred until all AI Staff phases are complete.
