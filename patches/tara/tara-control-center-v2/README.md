# TCRM — Tara Control Center V2 (AI Staff UX Phase 4)

Purpose: reduce Tara's control-center density and make the admin workspace easier to scan without changing any Tara query, mutation, provider, voice, moderator, campaign, qualification, knowledge, follow-up, social-channel, test, logs, permissions, or business behavior.

## Canonical baseline

- Repository: `mohamedamouseo-a11y/TCRM-MAIN-Tamiyouz-CRM-`
- Branch: `main`
- Expected HEAD: `6a3cbb0b8c2c0a8a65e5de7f276e143f214763d0`
- Guarded `client/src/pages/TaraAgentPage.tsx` blob: `96e08eb01adfb6e7428aa585a0e2712e1fb20331`

## Exact scope

Changes exactly one application file:

- `client/src/pages/TaraAgentPage.tsx`

No Darwish, Zaghloul, Felfel, backend, API, database, migrations, routes, permissions, provider logic, voice logic, moderator logic, campaigns, CRM data, or `external/mautic` files are changed.

## UX changes

The existing Tara premium hero, professional portrait, bilingual identity, Enabled state, four skill chips and six KPI cards remain unchanged.

### 1. Grouped primary workspace navigation

The existing eleven Tara destinations remain intact and keep the same `TabsTrigger` values and `TabsContent` bindings, but they are visually grouped into four categories:

1. **Profile & Runtime** — Settings, AI Providers, Voice & ElevenLabs, Moderator (when authorized)
2. **Sales Operations** — Campaigns, Qualification, Follow-ups, Social Channels
3. **Knowledge** — Knowledge
4. **Diagnostics** — Test, Logs

The navigation remains horizontally scrollable on narrower screens. `Settings` remains the default tab unless the existing `?tab=social` deep-link is used.

Marker:

`data-tara-workspace="control-center-v2"`

### 2. Settings form hierarchy

The long Tara Settings form is reorganized into three native collapsible sections while keeping all inputs mounted and all existing state/save behavior unchanged:

- **Profile & Language** — open by default
- **Runtime Policy** — collapsed by default
- **Automation & Handoff** — collapsed by default and visually marked as sensitive

The existing sticky action bar remains outside the collapsible groups and still contains the same Save Settings, Test Connection and Process Queue controls. No handler or payload is changed.

Settings section markers:

- `data-tara-settings-section="profile-language"`
- `data-tara-settings-section="runtime-policy"`
- `data-tara-settings-section="automation-safety"`

## Apply helper

Use the supplied guarded helper from the live TCRM checkout:

```bash
python apply_tara_control_center_v2.py --check
python apply_tara_control_center_v2.py --apply
python apply_tara_control_center_v2.py --verify
```

The helper refuses to apply unless the exact guarded Tara blob is present. It verifies that all eleven original tab triggers and tab contents remain exactly once, all three settings sections exist, the legacy flat navigation is gone, and core Tara source markers/handlers remain present.

## Standing validation workflow

1. ChatGPT authors and pushes the patch/helper to `TCRM-main-patchs-`.
2. Manus applies it directly on `/var/www/TCRM-MAIN` on the live server.
3. Manus runs production build and TCRM Developer Hub controlled Review Push gates.
4. Only if Verify, Tests, Build, Security and Remote Sync pass, Manus uses **Developer Hub Auto Push from inside TCRM** to push the live server checkout to canonical `TCRM-MAIN/main`.
5. No shell commit/push, no new branch, no force push, no rebase.
6. Manus reloads only the existing `tamiyouz-crm` process if required, performs read-only authenticated visual acceptance, and uploads the Markdown report + ZIP evidence into the current ChatGPT session.
7. The user's developer final cross-agent acceptance test stays deferred until all AI Staff UX/UI phases are complete.
