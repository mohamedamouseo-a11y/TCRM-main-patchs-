# TCRM — Zaghloul Engagement Command V3 (AI Staff Phase 10)

Purpose: continue BUILD/IMPLEMENTATION work after Phase 9 by making Zaghloul faster to operate without changing any backend, sending, automation, data, permission, or refresh behavior.

## Canonical baseline

- Repository: `mohamedamouseo-a11y/TCRM-MAIN-Tamiyouz-CRM-`
- Branch: `main`
- Expected HEAD: `7705a52647e4eba90dfabccb5477eb2af08c65cb`
- Guarded file: `client/src/pages/ZaghloulV5Page.tsx`
- Expected base blob: `ad2fa7ce229e4826dc6c22d524b30d28f43d76a7`

## Exact scope

Changes exactly one application file:

- `client/src/pages/ZaghloulV5Page.tsx`

No Darwish, Tara, Felfel, backend, API, database, migrations, routes, permissions, sending logic, automation logic, customer data, developer credentials, or `external/mautic` file is changed.

## Phase 10 implementation

Adds a compact read-only `Engagement Command` card between Workspace Capabilities and the existing grouped navigation.

Marker:

`data-zaghloul-engagement-command="v3"`

It exposes four live navigation signals using already-loaded queries:

1. Audience → `contacts` using total contacts.
2. Inbox Attention → `inbox` using unread messages.
3. Automation → `automations` using available automations.
4. Team & Admin → `team` using total team members.

The existing Tabs become controlled by local UI state `zaghloulWorkspace`, defaulting to `dashboard`. Both the existing grouped 11-destination navigation and the new command tiles update the same state.

All 11 existing destinations remain exactly once:

- Dashboard
- Inbox
- Contacts
- Pipelines
- Broadcasts
- Automations
- Flows
- AI Agents
- Team
- Settings
- Developer

## Safety

The new command buttons are `type="button"`, call only `setZaghloulWorkspace(key)`, and expose `aria-pressed`. They do not send broadcasts, edit contacts, run automations/flows, modify settings, create keys/webhooks, or execute any mutation.

Preserve:

- `data-zaghloul-workspace="grouped-nav-v2"`
- `data-ai-staff-refresh="zaghloul-v1"`
- `data-ai-staff-shell="consistency-v1"`
- `refreshZaghloulData`
- existing query and mutation behavior

## Execution mode

BUILD / IMPLEMENTATION only.

Do not run final acceptance, responsive/mobile acceptance, DevTools acceptance, browser takeover, or the user's developer final test.

Use `python3` on the server:

```bash
python3 <PATCH_PATH>/apply_zaghloul_engagement_command_v3.py --check
python3 <PATCH_PATH>/apply_zaghloul_engagement_command_v3.py --apply
python3 <PATCH_PATH>/apply_zaghloul_engagement_command_v3.py --verify
```

Then run production build and TCRM Developer Hub controlled Review Push/Auto Push. Mandatory Developer Hub internal gates may run; do not launch separate manual acceptance suites.

No shell commit/push, no new branch, no force push, no rebase, no stash/reset/discard, and never touch `external/mautic`.

Upload the final implementation report/evidence directly into the current ChatGPT conversation.