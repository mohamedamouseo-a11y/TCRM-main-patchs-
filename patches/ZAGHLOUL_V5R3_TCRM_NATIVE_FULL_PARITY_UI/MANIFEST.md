# ZAGHLOUL_V5R3_TCRM_NATIVE_FULL_PARITY_UI

Target: `/var/www/TCRM-MAIN`
Production repo: `mohamedamouseo-a11y/TCRM-MAIN-Tamiyouz-CRM-`
Baseline main: `c7ca52c5bb0495400ed327601d50cf6c7a363c73` (or descendant)
WACRM source pin: `6ed9191189e71d2e69d9380422f9415ecc589266`

## Goal
Make `/zaghloul` the native TCRM UI for the complete WACRM parity set already present under `apps/zaghloul-wacrm`.

This is implementation, not a parity badge/checklist phase.

## Non-negotiable architecture
- Native TCRM UI/layout/components; **no iframe** and no second standalone login.
- TCRM session/roles remain the auth authority.
- TCRM official WhatsApp/Meta adapter remains the **only outbound authority**.
- No second WhatsApp sender, webhook owner, token store, queue, or competing transport.
- Reuse existing TCRM services/data first. Add only namespaced additive schema/services when a real parity capability has no TCRM equivalent.
- No destructive migrations.
- No real WhatsApp/email/external webhook traffic during tests.
- `/zaghloul` and `/zaghloul-v5` stay on the V5 native page; `/zaghloul-legacy` remains available.

## Required operational parity — 15/15
1. `shared-inbox`
2. `contacts-tags-custom-fields-import-dedup`
3. `sales-pipelines-kanban-deals`
4. `broadcasts-templates-delivery-read-variables`
5. `automations-builder-triggers-branches-waits-tags-webhooks`
6. `flows-builder-buttons-branches-media`
7. `ai-agents-draft-auto-reply-kb-playground-handoff`
8. `realtime-dashboard-analytics-activity`
9. `team-accounts-roles-invites-ownership`
10. `account-management`
11. `public-rest-api-api-keys-scopes-rate-limits`
12. `outbound-event-webhooks-hmac`
13. `mcp-server`
14. `chat-actions-reactions-reply-copy`
15. `media-persistence-inbound-outbound`

## Native UI requirements
`/zaghloul` must expose usable TCRM-native surfaces for all parity capabilities. Embedded capabilities such as chat actions/media may live inside Inbox; REST/API keys, webhooks and MCP may live under Settings/Developer surfaces. They do not need 15 separate tabs, but every parity item must have a real reachable UI/control surface where applicable and real backend wiring.

Minimum primary sections:
- Overview / Analytics
- Inbox
- Contacts
- Pipelines / Deals
- Broadcasts / Templates
- Automations
- Flows
- AI Agents / Knowledge Base / Playground / Handoff
- Team
- Settings / Account
- Developer: API Keys / REST / Webhooks / MCP

## Existing gaps that MUST be eliminated
- `ZaghloulV5Page.tsx` must not remain a 4-tab shell only.
- `v5Service.ts` must not advertise features that are only flags/badges.
- `getZaghloulV5Automations()` must not remain an empty-array stub.
- `WACRM_PARITY.json status=complete` alone is not evidence of UI/runtime completion.

## Required implementation behavior
For every parity item:
- Native TCRM UI surface or embedded action.
- Authenticated TCRM runtime entrypoint.
- Real service/data path (not hard-coded demo data).
- Loading/empty/error states.
- Role/permission enforcement.
- Focused tests proving the path.

For outbound WhatsApp tests, reach the real Zaghloul/TCRM orchestration then intercept before external Meta network. Actual external Meta calls must be 0.

## Acceptance gates
- 15/15 feature proofs PASS.
- No known stub/placeholder backend for any declared complete feature.
- No iframe / second login / second sender.
- TSC introduces zero new errors versus preflight baseline.
- Focused tests PASS.
- Production build PASS.
- PM2 online after controlled reload.
- HTTP `/zaghloul`, `/zaghloul-v5`, `/zaghloul-legacy` = 200.
- No real external Meta/email/non-loopback webhook calls in verification.

Success marker:
`ZAGHLOUL_V5R3_TCRM_NATIVE_FULL_PARITY_UI_OK`
