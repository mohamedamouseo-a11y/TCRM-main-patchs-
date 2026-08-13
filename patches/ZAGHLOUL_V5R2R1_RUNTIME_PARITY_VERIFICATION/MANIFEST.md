# ZAGHLOUL_V5R2R1_RUNTIME_PARITY_VERIFICATION

Target: `/var/www/TCRM-MAIN`

Purpose: prove that the 15 WACRM parity items reported by V5R2 are operational inside TCRM at runtime, not merely present as source files, feature flags, manifest entries, or HTTP 200 shells.

This is verification-only. It must not modify production source, install dependencies, reload PM2, push Git, send real WhatsApp messages, send real email invites, or leave test rows/data behind.

Authoritative upstream pin:
`6ed9191189e71d2e69d9380422f9415ecc589266`

Required runtime parity set:
1. shared-inbox
2. contacts-tags-custom-fields-import-dedup
3. sales-pipelines-kanban-deals
4. broadcasts-templates-delivery-read-variables
5. automations-builder-triggers-branches-waits-tags-webhooks
6. flows-builder-buttons-branches-media
7. ai-agents-draft-auto-reply-kb-playground-handoff
8. realtime-dashboard-analytics-activity
9. team-accounts-roles-invites-ownership
10. account-management
11. public-rest-api-api-keys-scopes-rate-limits
12. outbound-event-webhooks-hmac
13. mcp-server
14. chat-actions-reactions-reply-copy
15. media-persistence-inbound-outbound

Runtime evidence rules:
- Every item must execute a real integrated code path from TCRM/Zaghloul into the adapted WACRM functionality.
- Static path existence, grep, manifest status, UI text, badges, or feature flags do not count as runtime proof.
- Data-changing probes must use a transaction/isolated test namespace and clean up completely.
- WhatsApp probes may traverse the real Zaghloul/TCRM orchestration but must intercept before the external Meta network call at the official TCRM Meta adapter boundary. External Meta calls must equal zero.
- AI probes may stub only the external model-provider network boundary; real Zaghloul orchestration, KB retrieval, draft/auto-reply/handoff logic must execute.
- Email/invite probes may stub only the external mail transport boundary.
- Webhook probes may send only to a loopback listener and must validate HMAC.
- MCP must be started and spoken to over its real protocol transport, then execute at least one safe read tool.
- Public REST API must be exercised over localhost HTTP with a temporary key, including scope rejection and revocation; rate-limit behavior must be verified without affecting real integrations.
- `/zaghloul` must remain the primary route and use TCRM auth; no second login and no second WhatsApp sender.

Required guardrails:
- `SOURCE_MUTATION=NONE`
- `PM2_RELOAD=NONE`
- `META_EXTERNAL_CALLS=0`
- `EMAIL_EXTERNAL_CALLS=0`
- `NON_LOOPBACK_WEBHOOK_CALLS=0`
- `TEST_ROWS_REMAINING=0`
- `DB_CLEANUP=PASS`
- `SECOND_WHATSAPP_SENDER=NO`
- `AUTH_MODE=TCRM_SESSION`
- `RUNTIME_PARITY_PASS_COUNT=15`
- `RUNTIME_PARITY_FAIL_COUNT=0`

The verification workspace is temporary:
`/tmp/ZAGHLOUL_V5R2R1_RUNTIME_PARITY_VERIFICATION`

Run `APPLY.sh` first to record immutable pre-probe fingerprints. OpenHands then builds/runs the temporary runtime probe harness according to `OPENHANDS_TASK.md`, writes `RUNTIME_PARITY_RESULTS.json`, and finally runs `VERIFY.sh`.

Success only when:
`ZAGHLOUL_V5R2R1_RUNTIME_PARITY_VERIFICATION_OK`
