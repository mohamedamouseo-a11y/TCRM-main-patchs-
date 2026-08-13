# ZAGHLOUL_V5R2_WACRM_PARITY_COMPLETION

Target: `/var/www/TCRM-MAIN`

## Baseline
Production GitHub baseline after the accepted V5R1/V5R1R2 switchover:
- production commit: `53c60f016b2cd656c7a786b8924030fee145a5e7`
- `client/src/App.tsx`: `242bd67ff1766f00decf66d7a91fcb2c83552856`
- `client/src/pages/ZaghloulV5Page.tsx`: `a7b7d15671c9f8a6fed17608d8b07adad62920b8`
- `server/services/zaghloul-v5/v5Service.ts`: `ad265d6774c3fac47c66adb20ef0d077ee60bac4`
- accepted repository TSC ceiling before this phase: `191`
- `/zaghloul`, `/zaghloul-v5`, `/zaghloul-legacy`: HTTP 200

## Authoritative upstream source
Repository: `ArnasDon/wacrm`
Pinned commit: `6ed9191189e71d2e69d9380422f9415ecc589266`
Package version at that commit: `0.8.0`
License: MIT

Do not use floating `main` during implementation. Clone/fetch the exact pinned commit and record its file inventory before modification.

## Why this patch exists
The current Zaghloul V5 is an adapter facade, not full WACRM parity. Current UI exposes Inbox, Contacts, Pipelines and Automations. The current `v5Service.ts` also contains placeholder/incomplete mappings (including an empty automations source) and metadata that claims features such as broadcasts/templates/AI/analytics without proving those modules are actually functional.

This phase must complete the full-source integration rather than adding a few cosmetic tabs or declaring feature flags `enabled` without operational evidence.

## Required WACRM parity set
Every item below must be operational and represented in `server/services/zaghloul-v5/WACRM_PARITY.json` with `status: "complete"` and concrete evidence:
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

## Integration invariants
- Preserve the complete upstream WACRM source in an isolated internal location, preferred: `apps/zaghloul-wacrm/`.
- Preserve MIT attribution/license.
- Branding may change from WACRM to Zaghloul/زغلول, but functionality may not be removed to simplify integration.
- Primary UX remains `AI Staff → زغلول` and `/zaghloul`.
- No iframe final architecture.
- Reuse TCRM authentication and role model through a dedicated auth/SSO adapter. Do not expose a second login flow to TCRM users.
- Do not create a second WhatsApp sender, token rotation system, parallel webhook authority, or competing outbound queue. Reuse the already-active official Meta Cloud API integration in TCRM through one adapter boundary.
- Do not assume `waGateway` is the official Meta transport. Detect and use the active official TCRM Meta Cloud API path.
- Preserve consent/opt-in, approved-template rules, opt-out/suppression, quality/rate safeguards and human handoff.
- No number rotation, ban bypass or policy evasion.
- Any DB change must be additive, migration-backed, dry-run first, and rollback-safe.
- Secrets must stay outside source control.
- Do not delete `/zaghloul-legacy` until parity is proven and separately approved.

## Required artifacts in production source after implementation
- `apps/zaghloul-wacrm/` containing the preserved/adapted pinned WACRM source.
- `apps/zaghloul-wacrm/.wacrm-upstream-commit` containing exactly the pinned SHA.
- `apps/zaghloul-wacrm/LICENSE` preserving upstream MIT license text.
- `server/services/zaghloul-v5/WACRM_PARITY.json` with all 15 required items complete and evidence.
- Explicit TCRM auth adapter evidence.
- Explicit official-WhatsApp adapter evidence.

## Verification
`VERIFY.sh` is intentionally a final gate, not an implementation engine. OpenHands must first execute `OPENHANDS_TASK.md`, then run `APPLY.sh`/`VERIFY.sh`.

Success is forbidden if any feature is placeholder-only, falsely marked enabled, inaccessible from the integrated UX, or backed by a second competing WhatsApp sender.

## Success marker
`ZAGHLOUL_V5R2_WACRM_PARITY_COMPLETION_OK`
