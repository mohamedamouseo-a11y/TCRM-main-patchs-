# TCRM — AI Staff Cross-Agent Consistency V1 (Phase 8)

Purpose: complete the AI Staff UX/UI program with a final, frontend-only consistency pass across Darwish, Zaghloul, Tara, and Felfel while preserving each agent's role-specific workspace and all functional behavior.

## Canonical baseline

- Repository: `mohamedamouseo-a11y/TCRM-MAIN-Tamiyouz-CRM-`
- Branch: `main`
- Expected HEAD: `5290e36ae9fb701b7f38ef875b73ba6ac2b05873`

Guarded page blobs:

- `client/src/pages/DarwishPage.tsx` → `2779e41b24972ae96b69f898d53e04139bfa9d4e`
- `client/src/pages/ZaghloulV5Page.tsx` → `d1f97d0ea81390b0df93828acbf1facfa41e5ec0`
- `client/src/pages/TaraAgentPage.tsx` → `1354a816f999330e81486038232ee8c93df99cac`
- `client/src/pages/FelfelPage.tsx` → `fa4377ec27166a606398c23201b229d3055f8901`

## Exact scope

Changes exactly four frontend page files:

1. `client/src/pages/DarwishPage.tsx`
2. `client/src/pages/ZaghloulV5Page.tsx`
3. `client/src/pages/TaraAgentPage.tsx`
4. `client/src/pages/FelfelPage.tsx`

No backend, API, database, migrations, routes, permissions, provider logic, CRM logic, meeting logic, campaign logic, refresh handler logic, approval logic, automation logic, or `external/mautic` file is changed.

## Consistency changes

### Shared shell

All four pages receive the marker:

`data-ai-staff-shell="consistency-v1"`

The desktop page shell is normalized to the same maximum width and spacing rhythm:

- `max-w-[1660px]`
- outer spacing/gap equivalent to 1rem
- `p-4 md:p-5 xl:p-6`

This removes the previous mismatch where Zaghloul and Tara used materially larger desktop padding than Darwish/Felfel.

### Hero family

Preserve the existing agent identities/colors/portraits, while aligning the family geometry:

- 28px hero radius for all four agents;
- shared headline scale;
- shared role-title hierarchy;
- consistent hero spacing rhythm.

Darwish and Zaghloul already match the target treatment and only receive the shared shell marker.

Tara receives visual-only class normalization:

- 28px hero radius;
- 152px portrait footprint on the admin AI Staff page;
- vertically centered desktop hero layout;
- AI STAFF eyebrow typography aligned to the other agents;
- role title moved to the same strong foreground hierarchy;
- top manual refresh label becomes `Refresh data` / `تحديث البيانات` for naming consistency.

Felfel receives visual-only class/content hierarchy normalization:

- 28px hero radius;
- shared H1 tracking/size treatment;
- strong primary role title;
- a secondary bilingual role line, matching Darwish/Zaghloul/Tara's bilingual hierarchy.

### Agent-specific structures are preserved

Do **not** flatten the agents into one identical workspace. Preserve:

- Darwish `data-darwish-workspace="supervisor-v3"` and progressive disclosure;
- Zaghloul `data-zaghloul-workspace="grouped-nav-v2"` and all 11 destinations;
- Tara `data-tara-workspace="control-center-v2"` and settings sections;
- Felfel `data-felfel-workspace="meeting-intelligence-v8"` and Phase 7 progressive disclosure.

### Refresh reliability is frozen

Phase 8 must not alter any manual refresh handler.

Preserve:

- `data-ai-staff-refresh="darwish-v1"`
- `data-ai-staff-refresh="zaghloul-v1"`
- `data-ai-staff-refresh="tara-v1"`
- `data-ai-staff-refresh="felfel-v1"`
- `TCRM_FELFEL_REFRESH_COMPLETION_V1`

All four top manual refresh controls must still complete and show `Last updated` after the patch.

## Apply helper

From `/var/www/TCRM-MAIN`:

```bash
python <PATCH_PATH>/apply_ai_staff_cross_agent_consistency_v1.py --check
python <PATCH_PATH>/apply_ai_staff_cross_agent_consistency_v1.py --apply
python <PATCH_PATH>/apply_ai_staff_cross_agent_consistency_v1.py --verify
```

The helper refuses to apply unless all four guarded blobs exactly match the baseline above.

## Acceptance intent

Authenticated visual review should compare the four agents side-by-side and confirm:

1. same outer page width/padding rhythm;
2. hero radius and hierarchy feel like one AI Staff family;
3. portraits and names remain agent-specific;
4. role title hierarchy is bilingual and consistent;
5. six KPI rows remain intact;
6. top refresh controls remain visible and functional;
7. each agent's specialized navigation/workspace remains intact;
8. RTL remains clean;
9. no business/customer mutation is triggered during acceptance.

## Standing workflow

1. ChatGPT authors/pushes this guarded patch to `TCRM-main-patchs-`.
2. Manus applies it directly on `/var/www/TCRM-MAIN`.
3. Manus builds and performs authenticated visual/read-only acceptance.
4. Manus runs TCRM Developer Hub Review Push gates.
5. Only if Verify, Tests, Build, Security, and Remote Sync pass, Manus uses Developer Hub Auto Push from inside TCRM to canonical `main`.
6. No shell commit/push, no new branch, no force push, no rebase.
7. Final Markdown report + ZIP evidence must be uploaded directly into the current ChatGPT conversation.
8. Only after Phase 8 PASS should the user's developer perform the single final cross-agent acceptance test.