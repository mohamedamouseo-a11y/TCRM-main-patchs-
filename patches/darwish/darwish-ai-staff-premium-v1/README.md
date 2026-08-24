# TCRM — Darwish AI Staff Premium V1

Purpose: redesign **Darwish** to match the premium AI Staff identity level used by Tara/Felfel while preserving all existing Darwish queries, actions, data panels, permissions, and human-approval behavior.

## Scope

Changes exactly one application file:

- `client/src/pages/DarwishPage.tsx`

No backend, database, migration, Mautic, routing, permissions, customer data, or Darwish operational logic is changed.

## Design

- Premium cyan/deep-blue AI Staff hero
- Dedicated Darwish portrait-style identity illustration
- Bilingual role: `AI Customer Support Supervisor` / `مشرف دعم العملاء بالذكاء الاصطناعي`
- Skills: Voice of Customer, Customer Memory, Handling Intelligence, Management Intelligence
- Six premium KPI cards driven only by existing live Darwish queries
- Human-approved status remains explicit
- Existing operational status cards, readiness, intelligence panels, action queue, mappings, and jobs remain intact
- Removes the older duplicated five-card intelligence KPI strip because the same live values are promoted into the new six-card premium KPI row

## Guarded blobs

- Base `client/src/pages/DarwishPage.tsx`: `533122a4696f011f710de521dd70e45805b1f688`
- Target: `532bba1845ffd1b84e8f4a4fe37164960e2a88c6`
- Expected main HEAD at preparation: `5e91f9557707297a741c0d9ff6d49e3351a5a6a5`

## Apply

```bash
git hash-object client/src/pages/DarwishPage.tsx
git apply --check /path/to/darwish-ai-staff-premium-v1.patch
git apply /path/to/darwish-ai-staff-premium-v1.patch
git hash-object client/src/pages/DarwishPage.tsx
```

Expected final blob: `532bba1845ffd1b84e8f4a4fe37164960e2a88c6`

Marker: `TCRM_DARWISH_AI_STAFF_PREMIUM_V1`
