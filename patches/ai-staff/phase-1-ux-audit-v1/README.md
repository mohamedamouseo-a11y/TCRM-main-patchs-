# TCRM — AI Staff UX/UI Phase 1 Audit V1

Purpose: establish a screenshot-backed UX/UI baseline for the live AI Staff pages before any structural redesign.

## Canonical TCRM main baseline

- Repository: `mohamedamouseo-a11y/TCRM-MAIN-Tamiyouz-CRM-`
- Branch: `main`
- Expected HEAD at Phase 1 start: `0d5696b0946142c1836cefd601c597db5a3f4187`

## Pages in scope

1. `/darwish` — priority page; specifically audit excessive page length, information density, duplicated status/KPI information, section hierarchy, scanability, and opportunities for grouping into tabs/accordions/workspaces without losing any current capability.
2. `/zaghloul` — audit premium identity consistency, information architecture, workspace navigation, KPI hierarchy, page density, and lower-section organization.
3. `/tara` — audit premium AI Staff identity consistency, KPI hierarchy, tab structure, settings/control-center organization, and any visual/UX drift.
4. `/felfel` — audit premium AI Staff identity consistency, KPI hierarchy, meeting workspace, intelligence sections, tab structure, and any visual/UX drift.

## Phase 1 is audit-only

No application source is changed in this phase. No backend, API, database, migration, permissions, Mautic, business data, or production behavior is changed.

The deliverable is a complete authenticated screenshot set plus a structured UX/UI audit report that ChatGPT will use to author the Phase 2 patch.

## Required screenshot set

For every page:

- hero / identity area
- KPI row
- main navigation/tabs
- every major content section, captured by scrolling in logical checkpoints
- full-page visual sequence sufficient to reconstruct the current information architecture

For Darwish additionally capture each major intelligence/operations block separately and record the approximate number of vertical screenfuls from top to bottom.

## Audit dimensions

For each page report:

- current visible structure in order
- sections that deserve primary navigation vs secondary detail
- repeated/duplicated metrics or status information
- sections that can be grouped
- sections that should remain always visible
- excessive vertical whitespace or excessive density
- inconsistent card styles, spacing, headings, tabs, or status patterns
- desktop scanability
- bilingual/RTL issues if visible
- recommended future information architecture

Do not redesign or edit code during Phase 1.

Marker: `TCRM_AI_STAFF_PHASE_1_UX_AUDIT_V1`
