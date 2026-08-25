# TCRM — Darwish Supervisor Workspace V2 (AI Staff UX Phase 2)

Purpose: reorganize the current Darwish AI Staff page from one very long vertical page into a focused **Supervisor Workspace**, while preserving the already-approved premium hero, portrait, bilingual identity, six KPI cards, every existing intelligence panel, Phase 5 Limited Safe Automation, human approval controls, mappings, jobs, queries, mutations, permissions, and business behavior.

## Canonical baseline

- Repository: `mohamedamouseo-a11y/TCRM-MAIN-Tamiyouz-CRM-`
- Branch: `main`
- Expected HEAD: `1fe3097b59bd9fc2fed984005ab23f07ead385a4`
- Guarded `client/src/pages/DarwishPage.tsx` blob: `372246b4fc4f4adf3f6b7b8c3f2a1ac12dfbac2e`

## Scope

Changes exactly one application file:

- `client/src/pages/DarwishPage.tsx`

No backend, API, database, migration, Mautic, permissions, routes, Darwish operational logic, or customer data are changed.

## UX / information architecture

The premium **Hero + six KPI cards stay always visible**.

The long body becomes four primary work areas:

1. **Customer Intelligence** — Voice of Customer, Demand & Problem Intelligence, Customer Memory, Handling Intelligence, Management Intelligence, and Latest Darwish Intelligence.
2. **Supervision** — supervisor risk metrics, alerts, Account Manager performance, and Daily Management Digest.
3. **Actions & Automation** — Phase 5 Limited Safe Automation, action-state metrics, and the Human Action Queue. Human approval semantics are unchanged.
4. **Operations & Mapping** — Chatwoot/Worker/WhatsApp/mapping status, internal Data Readiness, group/client linking, current mappings, and recent group jobs.

Customer Intelligence is the default workspace. The navigation is horizontally scrollable on smaller screens and sticky within the workspace. Darwish page width is aligned with the wider premium AI Staff workspace (`max-w-[1660px]`) to reduce unnecessary vertical density.

## Apply helper

`apply_darwish_supervisor_workspace_v2.py` supports:

```bash
python apply_darwish_supervisor_workspace_v2.py --check
python apply_darwish_supervisor_workspace_v2.py --apply
python apply_darwish_supervisor_workspace_v2.py --verify
```

The helper refuses to apply unless the exact guarded baseline blob is present. It also verifies that Limited Safe Automation remains exactly once and that all four workspace tabs plus all existing major Darwish capabilities remain present.

Marker:

`data-darwish-workspace="supervisor-v2"`

## Validation policy

This phase is not the user's final developer acceptance test. Manus should still run the normal build and Developer Hub controlled Review/Auto Push gates. The user's developer performs the final cross-agent acceptance only after all UX/UI phases are complete.
