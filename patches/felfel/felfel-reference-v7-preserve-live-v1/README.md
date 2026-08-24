# TCRM — Felfel Reference V7 Preserve Live V1

Purpose: preserve the exact currently-approved live `FelfelPage.tsx` visual state before synchronizing production to the canonical GitHub `main`.

## Scope

This patch changes exactly one application source file:

- `client/src/pages/FelfelPage.tsx`

The avatar is intentionally **not** changed. GitHub `main` already contains the approved avatar blob:

- `client/public/ai-staff/felfel-avatar.webp`
- Git blob: `21e7557ee99908b5a9893bb5503d0e662c23d7b1`

## Guarded hashes

Expected GitHub-main base Felfel page blob:

`cd541f5ff161fad39ca0e98b0791917bca4243ac`

Preserved live reference-v7 target blob:

`bc7fc40786d3c37944e5a51ebd33e0c6399cfddd`

The helper refuses to apply unless the base page and avatar match the approved hashes.

## Change classification

The extracted live-vs-main diff was reviewed. Changes are visual/UX only:

- hero styling and portrait framing
- KPI card shadows
- tabs presentation
- new-meeting card/button styling
- live-meeting empty state styling
- intelligence summary cards styling
- service capabilities card styling
- adds the `Puzzle` icon import used by the capabilities card

No API wiring, meeting workflow, transcript logic, intelligence logic, CRM mapping, follow-up logic, archive logic, backend, database, or permission behavior is changed.

## Usage

Run from the TCRM project root after the checkout is synchronized to the guarded canonical-main base:

```bash
python3 /path/to/apply_felfel_reference_v7_preserve_live_v1.py --check
python3 /path/to/apply_felfel_reference_v7_preserve_live_v1.py --apply
python3 /path/to/apply_felfel_reference_v7_preserve_live_v1.py --verify
```

Then run the normal build/tests and use TCRM Developer Hub Review/Auto to commit/push the single approved `FelfelPage.tsx` change to `main`.

## Safety

- No branch creation.
- No force push.
- No Mautic path changes.
- No DB or migration changes.
- No customer/business action.
- Does not modify the avatar.

Marker: `TCRM_FELFEL_REFERENCE_V7_PRESERVE_LIVE_V1`
