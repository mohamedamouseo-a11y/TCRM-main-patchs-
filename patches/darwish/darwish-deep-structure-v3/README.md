# TCRM — Darwish Deep Structure V3 (AI Staff UX Phase 5)

Purpose: take the already-approved Darwish Supervisor Workspace V2 and reduce vertical density further without deleting any capability or changing any Darwish query, mutation, approval rule, automation rule, mapping behavior, route, permission, backend logic, or customer data.

## Canonical baseline

- Repository: `mohamedamouseo-a11y/TCRM-MAIN-Tamiyouz-CRM-`
- Branch: `main`
- Expected HEAD: `e1575590a2e24448284295b991e7b1445c825e2e`
- Guarded `client/src/pages/DarwishPage.tsx` blob: `dd8a66589f74d79331a26a319eb6222d7a937393`

## Exact scope

Changes exactly one application file:

- `client/src/pages/DarwishPage.tsx`

No Tara, Zaghloul, Felfel, backend, API, database, migrations, routes, permissions, refresh/reliability logic, customer data, or `external/mautic` paths are changed.

## UX change

The premium hero, professional portrait, bilingual role, six KPI cards, and four primary Supervisor Workspace tabs remain intact and visible as before.

This phase adds **progressive disclosure inside each workspace** so Darwish no longer presents every detailed card at once.

### Customer Intelligence

All existing capabilities remain, but become focused expandable sections:

- Voice of Customer — open by default
- Demand & Problems
- Customer Memory
- Handling Intelligence
- Management Intelligence
- Latest Intelligence

### Supervision

The five supervisor summary metrics stay visible. Detailed content becomes:

- Alerts & Team Performance — open by default
- Management Digest

### Actions & Automation

The action status metrics stay visible. Detailed workflow becomes:

- Limited Safe Automation — open by default
- Human Action Queue — open by default

Human approval semantics, Admin-only actions, and outbound safety remain unchanged.

### Operations & Mapping

The six health/mapping summary cards stay visible. Detailed setup/operational content becomes:

- Data Readiness
- Link Group to Client
- Current Mappings — open by default
- Recent Group Jobs

## Markers

Primary workspace marker:

`data-darwish-workspace="supervisor-v3"`

Section markers use:

`data-darwish-section="..."`

The helper verifies fourteen required section markers and confirms that Limited Safe Automation remains exactly once.

## Apply helper

```bash
python apply_darwish_deep_structure_v3.py --check
python apply_darwish_deep_structure_v3.py --apply
python apply_darwish_deep_structure_v3.py --verify
```

The helper refuses to apply unless the exact guarded Darwish base blob is present. It performs only guarded JSX structure changes and preserves all existing source capabilities and mutation handlers.

## Important phase boundary

This phase is **structure/UX only**.

The user separately reported that AI Staff Refresh buttons are not working. Refresh reliability is intentionally deferred to **Phase 6**, where Darwish, Zaghloul, Tara, and Felfel refresh behavior will be audited and fixed functionally across the family.

## Standing workflow

1. ChatGPT authors and pushes this guarded helper/spec to `TCRM-main-patchs-`.
2. Manus applies it directly to `/var/www/TCRM-MAIN` on the live server.
3. Manus runs the production build and the TCRM Developer Hub controlled Review Push gates.
4. Only after Verify, Tests, Build, Security, and Remote Sync all pass, Manus uses **Developer Hub Auto Push from inside TCRM** to push the live server checkout to canonical `TCRM-MAIN/main`.
5. No shell commit/push, no new branch, no force push, no rebase.
6. Manus performs read-only authenticated visual acceptance and uploads the Markdown report + ZIP evidence directly into the current ChatGPT session.
7. The user's developer final cross-agent acceptance test remains deferred until all UX/UI and refresh-reliability phases are complete.
