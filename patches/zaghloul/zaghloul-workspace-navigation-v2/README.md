# TCRM — Zaghloul Workspace Navigation V2 (AI Staff UX Phase 3)

Purpose: reduce Zaghloul's navigation density without changing any workspace capability, route, query, mutation, permission, backend behavior, or data flow.

## Canonical baseline

- Repository: `mohamedamouseo-a11y/TCRM-MAIN-Tamiyouz-CRM-`
- Branch: `main`
- Expected HEAD: `ad5f3b0467c17f5add2d8a847b58cf7498421bd1`
- Guarded `client/src/pages/ZaghloulV5Page.tsx` blob: `ee9cde356d999519e95a594a501175fd80039b1b`

## Scope

Changes exactly one application file:

- `client/src/pages/ZaghloulV5Page.tsx`

No Darwish, Tara, Felfel, backend, API, database, migrations, routes, permissions, team data, settings data, developer API behavior, automation logic, or `external/mautic` paths are changed.

## UX change

The existing premium Zaghloul hero, portrait, bilingual identity, health badges, skills, Workspace Capabilities panel, all eleven existing tabs, all tab contents, and all existing live data remain unchanged.

The single flat eleven-item tab strip is reorganized visually into four labeled groups inside the same Radix Tabs workspace:

1. **Core workspace** — Dashboard, Contacts, Pipelines
2. **Engagement** — Inbox, Broadcasts
3. **Automation** — Automations, Flows, AI Agents
4. **Administration** — Team, Settings, Developer

The grouped navigation remains horizontally scrollable on narrow screens and preserves the exact same tab values and content bindings. Dashboard remains the default tab.

Marker:

`data-zaghloul-workspace="grouped-nav-v2"`

## Apply helper

Use the supplied helper from the live TCRM checkout:

```bash
python apply_zaghloul_workspace_navigation_v2.py --check
python apply_zaghloul_workspace_navigation_v2.py --apply
python apply_zaghloul_workspace_navigation_v2.py --verify
```

The helper refuses to apply unless the exact guarded Zaghloul baseline blob is present. Verification confirms:

- the grouped navigation marker exists;
- the legacy flat navigation block is gone;
- all four group labels exist;
- every one of the eleven existing `TabsTrigger` values exists exactly once;
- every trigger still has its matching `TabsContent`;
- the premium identity, Workspace Capabilities, portrait, and WACRM integration surface remain present.

## Validation workflow

This phase follows the standing TCRM workflow:

1. ChatGPT authors and pushes the guarded patch/helper to `TCRM-main-patchs-`.
2. Manus applies it directly on `/var/www/TCRM-MAIN` on the server.
3. Manus runs build and Developer Hub controlled Review Push gates.
4. If all gates pass, Manus uses **TCRM Developer Hub Auto Push from inside the system** to push the server checkout to canonical `TCRM-MAIN/main`.
5. No shell commit/push, no new branch, no force push.
6. Manus deploys/reloads only as required, performs read-only authenticated visual acceptance, then uploads the Markdown report and ZIP evidence into the current ChatGPT session.

The user's developer final acceptance test remains deferred until all AI Staff UX/UI phases are complete.
