# TCRM — AI Staff UX/UI Phase 1 Audit V1.1

Purpose: establish the current screenshot-backed UX/UI baseline for the live AI Staff pages before any structural redesign.

## Canonical TCRM main baseline

- Repository: `mohamedamouseo-a11y/TCRM-MAIN-Tamiyouz-CRM-`
- Branch: `main`
- Required HEAD at Phase 1.1 start: `1fe3097b59bd9fc2fed984005ab23f07ead385a4`
- Parent baseline: `0d5696b0946142c1836cefd601c597db5a3f4187`
- Current Darwish Phase 5 commit: `feat(darwish): add phase 5 limited safe automation`

The previous Phase 1 audit baseline is obsolete because Darwish Phase 5 changed `client/src/pages/DarwishPage.tsx` and added the limited-safe-automation surface. Phase 1.1 must audit the current live UI at `1fe3097...` so the redesign is based on the actual production structure.

## Pages in scope

1. `/darwish` — highest priority. Audit the now-current page including the new limited automation surface, total page length, information density, duplicated status/KPI information, hierarchy, scanability, and opportunities to group content into a concise Supervisor Workspace without removing any capability.
2. `/zaghloul` — audit premium identity consistency, information architecture, workspace navigation, KPI hierarchy, density, and lower-section organization.
3. `/tara` — audit AI Staff identity consistency, KPI hierarchy, tab structure, settings/control-center organization, and UX drift.
4. `/felfel` — audit AI Staff identity consistency, KPI hierarchy, meeting workspace, intelligence sections, tab structure, and UX drift.

## Phase 1.1 is audit-only

No application source changes. No backend, API, database, migration, permissions, environment, Mautic, customer data, or production behavior changes.

## Required evidence

For every route capture authenticated desktop screenshots of:

- hero / identity area
- KPI row
- primary navigation/tabs
- every major content section in top-to-bottom order
- enough sequential captures to reconstruct the full information architecture

For Darwish additionally capture every major intelligence/operations/automation block separately and report approximate total vertical screenfuls.

## Darwish-specific audit

Report:

- exact current section order
- `DARWISH_SCREENFULS`
- duplicated KPIs/statuses/summaries
- sections that must remain always visible
- sections appropriate for top-level tabs
- sections appropriate for grouped sub-tabs
- sections appropriate for accordion/details
- sections that can be consolidated into one Supervisor Workspace
- the new limited automation surface and where it should live in the future hierarchy
- excessive scrolling/density/whitespace
- heading/card/spacing inconsistencies
- recommended information architecture without removing functionality

## Cross-agent audit

For Zaghloul, Tara, and Felfel compare:

- hero dimensions
- portrait treatment
- bilingual title hierarchy
- status presentation
- skills chips
- KPI density
- tab treatment
- spacing/page width
- section hierarchy
- loading/empty states
- RTL behavior

Separate output into:

- `SHARED_AI_STAFF_DESIGN_RULES`
- `AGENT_SPECIFIC_EXCEPTIONS`

## Source mapping

Read-only report per agent:

- `ROUTE`
- `PAGE_FILE`
- `MAJOR_CHILD_COMPONENTS`
- `TOP_KPI_DATA_SOURCES`
- `TAB_IMPLEMENTATION`

## Safety

`CODE_CHANGED=NO`
`COMMIT=NO`
`PUSH=NO`
`DATABASE_CHANGED=NO`
`MIGRATIONS_RUN=NO`
`MAUTIC_FILES_TOUCHED=0`

Marker: `TCRM_AI_STAFF_PHASE_1_UX_AUDIT_V1_1`
