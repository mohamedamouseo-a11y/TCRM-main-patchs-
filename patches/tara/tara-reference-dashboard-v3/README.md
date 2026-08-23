# TCRM — Tara Reference Dashboard V3

Visual-only redesign for `client/src/pages/TaraAgentPage.tsx`, aligned to the approved Tara mockup supplied in the design review.

## What changes

- Larger realistic circular Tara portrait with online status indicator.
- AI Staff employee-style hero profile.
- Bilingual professional role identity:
  - `AI Telesales & Lead Qualification Specialist`
  - `أخصائي المبيعات الهاتفية وتأهيل العملاء المحتملين بالذكاء الاصطناعي`
- Professional summary and four expertise chips.
- Premium enabled/disabled status and refresh controls.
- Six redesigned KPI cards using the existing live dashboard counts only; no fake trend data is introduced.
- Cleaner premium top-level tabs with underline-style active state.
- Existing Tara settings, providers, voice, moderator, campaign, qualification, knowledge, follow-up, social, test and logs functionality is preserved.

## Scope

Application source changed by the patch:

- `client/src/pages/TaraAgentPage.tsx`

Existing portrait asset used:

- `client/src/assets/ai-staff/tara-avatar.jpg`

If that asset is missing, the patch restores the previously approved Tara portrait payload from `tara-professional-identity-v2.3`.

No API, database, routes, permissions, settings semantics, or Tara business logic are changed.

## Apply

From the TCRM project root:

```bash
node <PATCH_REPO>/patches/tara/tara-reference-dashboard-v3/apply.mjs --check
node <PATCH_REPO>/patches/tara/tara-reference-dashboard-v3/apply.mjs --apply
node <PATCH_REPO>/patches/tara/tara-reference-dashboard-v3/apply.mjs --verify
```

Then run the project validation/build commands and visually test Tara in both English and Arabic/RTL.
