# OpenHands Task — ZAGHLOUL_V5R2_WACRM_PARITY_COMPLETION

Target production source:
`/var/www/TCRM-MAIN`

Patch repository:
`https://github.com/mohamedamouseo-a11y/TCRM-main-patchs-`

Authoritative upstream WACRM source:
`https://github.com/ArnasDon/wacrm`
Pinned upstream commit:
`6ed9191189e71d2e69d9380422f9415ecc589266`

## Goal
Complete Zaghloul V5 as a full native WACRM integration inside TCRM. Do not merely add feature badges, placeholders, or adapter stubs. Preserve WACRM functionality and integrate it safely with existing TCRM auth and the existing official Meta WhatsApp transport.

## Phase 0 — inspect before mutation
1. Verify `/var/www/TCRM-MAIN` and record current Git HEAD, App/V5 blobs, PM2 process/port, clean/dirty state.
2. Confirm `/zaghloul`, `/zaghloul-v5`, `/zaghloul-legacy` current behavior.
3. Run baseline TSC using increased heap and record normalized errors. Accepted ceiling is 191; do not create new errors.
4. Inspect current official WhatsApp implementation. Treat `taraMetaWhatsAppService` / Meta Cloud API path as candidate official transport; prove the active path from source/config before adapter work. Do not assume waGateway is official Meta transport.
5. Clone/fetch exact WACRM commit into temp only:
   `git clone https://github.com/ArnasDon/wacrm`
   then checkout `6ed9191189e71d2e69d9380422f9415ecc589266`.
6. Record WACRM source file count and feature inventory from source, README, routes, services, migrations, API and MCP code.

## Phase 1 — preserve full upstream source
Create isolated internal source at:
`apps/zaghloul-wacrm/`

Copy the pinned WACRM product source preserving functional code and MIT license. Exclude only generated/runtime artifacts such as `.git`, `node_modules`, `.next`, local secrets and caches.

Create:
`apps/zaghloul-wacrm/.wacrm-upstream-commit`
with exactly:
`6ed9191189e71d2e69d9380422f9415ecc589266`

Do not simplify WACRM down to four tabs.

## Phase 2 — TCRM adapters
Implement explicit adapter boundaries so the WACRM-derived module operates under TCRM:

### Auth adapter
- Reuse TCRM authenticated user/session.
- No second login screen for normal TCRM Zaghloul users.
- Map TCRM roles to equivalent Zaghloul permissions without weakening existing restrictions.

### Official WhatsApp adapter
- Exactly one outbound authority for Zaghloul.
- Reuse TCRM official Meta Cloud API transport, credentials, template policies and webhook ownership.
- Do not create duplicate Meta tokens, sender pools or competing outbound queues.
- Preserve opt-in/consent, approved templates, opt-out/suppression, quality safeguards, rate limits and human handoff.

### Data adapters/migrations
- Prefer adapters over destructive schema replacement.
- Any new storage must be additive.
- Create migrations with dry-run and idempotency guards.
- No destructive Supabase/Postgres migration may be applied blindly to TCRM's existing DB.

## Phase 3 — required parity
Operationally complete every feature in the parity manifest:
1. Shared inbox
2. Contacts/tags/custom fields/import/dedup
3. Sales pipelines/Kanban/deals
4. Broadcasts/templates/delivery/read/variables
5. No-code automations builder
6. Flows builder
7. AI agent/draft/auto-reply/KB/playground/handoff
8. Realtime dashboard/analytics/activity
9. Team accounts/roles/invites/ownership
10. Account management
11. Public REST API/API keys/scopes/rate limits
12. Outbound event webhooks/HMAC
13. MCP server
14. Chat actions/reactions/reply/copy
15. Media persistence

For each item, add concrete evidence to:
`server/services/zaghloul-v5/WACRM_PARITY.json`

Each entry must have:
- `id`
- `status` exactly `complete`
- `evidence` array of source paths/endpoints

No item may be marked complete based only on UI text or a feature flag.

## Phase 4 — UX
- `/zaghloul` remains primary route.
- Keep `/zaghloul-legacy` untouched as safety fallback.
- Integrate the full Zaghloul/WACRM UX natively; no iframe final solution.
- Brand visible WACRM product text as Zaghloul/زغلول where appropriate while keeping MIT attribution in source/license notices.

## Phase 5 — verification
Before success:
1. Secret scan for copied source.
2. Migration dry-run if migrations exist.
3. TSC baseline/candidate comparison; `TSC_NEW_ERROR_COUNT=0`.
4. Build must pass.
5. Relevant tests must pass.
6. PM2 reload only after successful build.
7. HTTP 200 for `/zaghloul`, `/zaghloul-v5`, `/zaghloul-legacy`.
8. Verify `/zaghloul` loads integrated full UX, not the prior facade-only page.
9. Verify no second active WhatsApp sender/queue/webhook authority was created.
10. Verify all 15 parity JSON items are `complete` with evidence.

If any production mutation fails verification, rollback all files changed by this operation and restore the previous working production state.

## Forbidden
- No feature deletion for convenience.
- No fake feature flags.
- No placeholder-only completion.
- No iframe final architecture.
- No number rotation, ban bypass or policy evasion.
- No production Git push unless separately requested by the user.

## Final output only
Return:

WACRM_SOURCE_COMMIT
WACRM_FILE_COUNT
WACRM_FEATURE_COUNT
FEATURES_COMPLETE
ZAGHLOUL_SOURCE_PATH
AUTH_ADAPTER
WHATSAPP_ADAPTER
DB_MIGRATION
TSC_BASELINE_ERROR_COUNT
TSC_CANDIDATE_ERROR_COUNT
TSC_NEW_ERROR_COUNT
TESTS
BUILD
PM2
HTTP_ZAGHLOUL
HTTP_ZAGHLOUL_V5
HTTP_ZAGHLOUL_LEGACY
PARITY_COMPLETE_COUNT
SECOND_WHATSAPP_SENDER
ROLLBACK
FINAL_MARKER

Success only when:
`ZAGHLOUL_V5R2_WACRM_PARITY_COMPLETION_OK`
