# TCRM — Felfel Premium Reference UX/UI V1

Target: `mohamedamouseo-a11y/TCRM-MAIN-Tamiyouz-CRM-` → `main`  
Page: `client/src/pages/FelfelPage.tsx`

This patch rebuilds the Felfel page around the supplied premium reference while preserving the existing Felfel APIs and workflows.

## Changes
- Large AI Staff hero with the supplied Felfel portrait, online state, Vexa Lite status, role description, and capability chips.
- Six live metric cards using current real UI data only (no hardcoded fake totals).
- New two-column Live Meeting workspace: meeting join form + live status panel.
- Four workflow summary cards for transcript/intelligence, action items, CRM follow-ups, and archive.
- Premium tabs styling while preserving the current Transcript, Intelligence, and History flows.
- Responsive Arabic/English and RTL/LTR behavior.

## Safety scope
UI/UX and bundled portrait only. Do not modify server APIs, database schema, permissions, Vexa integration, meeting processing, task approvals, follow-up rules, or archive rules.

## Apply from TCRM main root
```bash
node /path/to/TCRM-main-patchs-/patches/felfel/felfel-premium-reference-v1/apply.mjs --check
node /path/to/TCRM-main-patchs-/patches/felfel/felfel-premium-reference-v1/apply.mjs --apply
npm run check
node /path/to/TCRM-main-patchs-/patches/felfel/felfel-premium-reference-v1/apply.mjs --verify
```

After the build passes, visually verify desktop + mobile, then commit and push directly to the existing `main` branch. Do not create a new branch.
