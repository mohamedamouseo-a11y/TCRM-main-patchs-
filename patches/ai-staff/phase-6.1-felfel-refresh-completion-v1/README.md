# TCRM — Phase 6.1 Felfel Refresh Completion V1

Purpose: correct the Phase 6 manual Refresh completion failure observed only on Felfel, while preserving the already-passing Phase 6 changes for Darwish, Zaghloul, and Tara in the live server worktree.

## Why this corrective patch exists

Phase 6 was intentionally stopped before Developer Hub because authenticated acceptance showed:

- Darwish Refresh: PASS
- Zaghloul Refresh: PASS
- Tara Refresh: PASS
- Felfel Refresh: FAIL — the button entered `Refreshing...` but did not return to its normal state within the observed interval, and no success feedback / Last updated appeared.

The original Phase 6 Felfel handler used one unbounded `Promise.all(...)` across all selected refetch promises. The evidence does not prove which individual Felfel query was slow or unresolved, so this corrective patch does **not** guess a specific endpoint. Instead it removes the failure mode where one unresolved read-only refetch can hold the entire manual Refresh UI pending indefinitely.

## Canonical Git baseline

Canonical `TCRM-MAIN/main` remains unchanged because Phase 6 correctly stopped before Developer Hub:

`b1dc75ff7bb825e99e859f1a379516e232091d9b`

## Expected live server worktree state

The live checkout must still contain the four uncommitted Phase 6 target files exactly as reported:

- `client/src/pages/DarwishPage.tsx` → `2779e41b24972ae96b69f898d53e04139bfa9d4e`
- `client/src/pages/ZaghloulV5Page.tsx` → `d1f97d0ea81390b0df93828acbf1facfa41e5ec0`
- `client/src/pages/TaraAgentPage.tsx` → `1354a816f999330e81486038232ee8c93df99cac`
- `client/src/pages/FelfelPage.tsx` → `ea2fee98503574dddac508080815166a3ea7fe22`

The corrective helper refuses to run if any of those four blobs differs. Do not reset/stash/discard the Phase 6 work.

## Exact corrective scope

The helper modifies **only**:

- `client/src/pages/FelfelPage.tsx`

Darwish, Zaghloul, and Tara must remain byte-for-byte at their Phase 6 target blobs until Developer Hub pushes all four Phase 6 files together.

## Felfel reliability correction

The existing manual Refresh button and `data-ai-staff-refresh="felfel-v1"` marker remain.

The corrected handler:

- remains read-only;
- contains no `.mutate()` call;
- keeps context-aware query selection;
- wraps each selected refetch in a bounded six-second completion guard;
- uses `Promise.all` only over bounded outcomes, so a single unresolved provider/query cannot leave `manualRefreshPending` stuck forever;
- re-enables the button in `finally`;
- records `Last updated` when at least one selected data source refreshed successfully;
- shows full success when all selected sources succeed;
- shows an explicit warning when core data refreshed but one or more sources timed out/failed;
- shows an error if none of the selected read-only sources refresh successfully.

Corrective marker:

`TCRM_FELFEL_REFRESH_COMPLETION_V1`

## Apply helper

From `/var/www/TCRM-MAIN`:

```bash
python <PATCH_PATH>/apply_felfel_refresh_completion_v1.py --check
python <PATCH_PATH>/apply_felfel_refresh_completion_v1.py --apply
python <PATCH_PATH>/apply_felfel_refresh_completion_v1.py --verify
```

## Required acceptance before Developer Hub

Re-test Felfel first:

1. open authenticated `/felfel` with no business action;
2. click only the top manual `Refresh data` button;
3. loading/spinner must appear;
4. the button must return to enabled state within the bounded refresh window (allow up to 10 seconds for browser/UI observation);
5. `Last updated` must appear when at least one source succeeds;
6. feedback must be either successful refresh or an explicit partial-refresh warning — never an indefinitely stuck `Refreshing...` state;
7. no join/leave/analyze/task/follow-up/archive mutation may run.

Then re-test the top manual Refresh once on Darwish, Zaghloul, and Tara to confirm their Phase 6 behavior is still PASS.

## Developer Hub push scope

After the corrective test passes, Developer Hub should see the original Phase 6 four-file worktree relative to canonical main:

1. `client/src/pages/DarwishPage.tsx`
2. `client/src/pages/ZaghloulV5Page.tsx`
3. `client/src/pages/TaraAgentPage.tsx`
4. `client/src/pages/FelfelPage.tsx`

Run Verify, Tests, Build, Security, and Remote Sync. Only after all gates PASS, use Developer Hub Auto Push from inside TCRM to push to canonical `main`.

No shell commit/push. No new branch. No force push. No rebase. Do not touch `external/mautic`, database, migrations, backend, permissions, customer data, or business mutations.

## Final delivery

Upload the final Markdown report plus ZIP evidence directly into the current ChatGPT conversation. If screenshot export is unavailable, provide real visual notes and do not fabricate PNG files.
