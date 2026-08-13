# OpenHands Task — ZAGHLOUL_V5R2R1_RUNTIME_PARITY_VERIFICATION

Target: `/var/www/TCRM-MAIN`

Patch repo: `https://github.com/mohamedamouseo-a11y/TCRM-main-patchs-`

Goal: independently prove whether the V5R2 WACRM parity claim is operational inside TCRM at runtime. Do not implement missing features in this task. This task is verification-only. A failed feature must be reported as FAIL, not patched, bypassed, marked complete, or hidden.

## 0. Preflight
Run:
`patches/ZAGHLOUL_V5R2R1_RUNTIME_PARITY_VERIFICATION/APPLY.sh`

Stop immediately if PREFLIGHT is not PASS.

Use only this temporary workspace for the harness and results:
`/tmp/ZAGHLOUL_V5R2R1_RUNTIME_PARITY_VERIFICATION`

Do not create or edit files inside `/var/www/TCRM-MAIN`.

## 1. Harness rules
Create a temporary runtime test harness outside production source. It may import production modules and invoke localhost endpoints, but it must not alter source or dependency files.

No installs. No package-manager lockfile changes. No PM2 reload/restart. No git checkout/reset/clean. No git push.

Use existing dependencies only. If a required runtime dependency is unavailable, that feature fails verification rather than installing anything.

All test identities and rows must use a unique prefix such as `zv5r2r1_<timestamp>_` and must be deleted/rolled back before final verification.

Capture evidence for every feature in the result JSON. Runtime evidence must include the actual invoked entrypoint/endpoint/service and an observed result. File existence/grep/manifest/UI labels alone are invalid evidence.

## 2. Safe external-boundary policy
Absolutely no real customer/contact sends.

### WhatsApp
Exercise the real integrated Zaghloul path down to the TCRM official Meta adapter boundary. Intercept/mock only the final outbound network transport so no request reaches Meta. Record adapter invocation and payload class, not secrets or message content. `META_EXTERNAL_CALLS` must be 0. Confirm no second sender/queue/webhook authority is active.

### AI
Stub only the final external LLM provider call. Real orchestration for draft, auto-reply policy, KB retrieval/playground, and handoff must execute.

### Email/invites
Stub only the final mail transport. Team/invite authorization and lifecycle logic must execute.

### Outbound webhooks
Use a loopback listener only (`127.0.0.1`). Verify event delivery and HMAC signature. Any non-loopback outbound request fails the run.

## 3. Mandatory 15 runtime probes
Each feature must produce exactly one top-level PASS/FAIL record and may contain subchecks.

1. `shared-inbox`
- Load/list conversations through the integrated Zaghloul runtime service/endpoint.
- Verify assignment/status/notes action path with isolated data or reversible transaction.

2. `contacts-tags-custom-fields-import-dedup`
- Create/import isolated contacts through the operational path.
- Verify tags/custom fields and duplicate prevention/merge behavior.
- Cleanup all rows.

3. `sales-pipelines-kanban-deals`
- Create isolated pipeline/deal, move stage through the real mutation path, read it back, cleanup.

4. `broadcasts-templates-delivery-read-variables`
- Create an isolated broadcast/template-variable execution through Zaghloul.
- Intercept before external Meta network call.
- Verify recipient variable resolution and delivery/read event processing logic using synthetic webhook/event input.

5. `automations-builder-triggers-branches-waits-tags-webhooks`
- Create an isolated automation definition and invoke its engine with a synthetic supported trigger.
- Prove branch execution and at least two action types, including wait scheduling semantics and loopback webhook/tag action where supported.
- Cleanup.

6. `flows-builder-buttons-branches-media`
- Execute a saved/temporary flow with branch/button/media semantics through its runtime interpreter/executor, not only serialization.

7. `ai-agents-draft-auto-reply-kb-playground-handoff`
- Execute draft generation orchestration with external LLM stub.
- Prove KB retrieval/playground path, auto-reply policy path, and human handoff transition.

8. `realtime-dashboard-analytics-activity`
- Invoke analytics/dashboard runtime queries and activity feed generation.
- If realtime subscription infrastructure is present, prove subscription/event propagation without external services; otherwise report FAIL rather than treating static queries as realtime parity.

9. `team-accounts-roles-invites-ownership`
- Exercise role enforcement using temporary identities/fixtures.
- Prove forbidden action rejection for a lower role and permitted action for an authorized role.
- Exercise invite/ownership logic with mail transport stub; cleanup.

10. `account-management`
- Exercise an account-management mutation/read path under TCRM session mapping without exposing or changing a real user's credentials.
- Use isolated fixture/test user only. Prove no second login is required.

11. `public-rest-api-api-keys-scopes-rate-limits`
- Use localhost HTTP against the integrated runtime API.
- Create a temporary API key through the real key-management path.
- Prove successful scoped request, 403/missing-scope rejection, revocation rejection, and rate-limit behavior safely.
- Never reveal the full key in output. Cleanup/revoke.

12. `outbound-event-webhooks-hmac`
- Register a temporary loopback webhook through the real runtime path.
- Trigger a supported event and verify body + HMAC at local listener.
- Cleanup.

13. `mcp-server`
- Start the preserved/adapted MCP server temporarily without production daemon changes.
- Complete protocol initialization and invoke at least one safe read-only CRM tool against the integrated runtime.
- Stop process and cleanup.

14. `chat-actions-reactions-reply-copy`
- Exercise runtime handlers for reply/context, reaction, and copy/data retrieval semantics using isolated message fixture where required.

15. `media-persistence-inbound-outbound`
- Exercise inbound media persistence using a local synthetic payload/file and outbound media orchestration down to the official adapter boundary with network intercept.
- Verify metadata/storage readback and cleanup.

## 4. Cross-cutting runtime checks
- `/zaghloul` HTTP 200 and integrated V5 route.
- TCRM session/auth adapter is authoritative: `AUTH_MODE=TCRM_SESSION`.
- No second login flow is required for integrated users.
- Exactly one WhatsApp outbound authority: official TCRM Meta adapter.
- No production source mutation.
- No PM2 reload.
- No remaining test records/files/processes.

## 5. Results schema
Write exactly:
`/tmp/ZAGHLOUL_V5R2R1_RUNTIME_PARITY_VERIFICATION/RUNTIME_PARITY_RESULTS.json`

Required shape:
```json
{
  "version": 1,
  "patch": "ZAGHLOUL_V5R2R1_RUNTIME_PARITY_VERIFICATION",
  "target_head": "<sha>",
  "upstream_pin": "6ed9191189e71d2e69d9380422f9415ecc589266",
  "auth_mode": "TCRM_SESSION",
  "second_whatsapp_sender": "NO",
  "meta_external_calls": 0,
  "email_external_calls": 0,
  "non_loopback_webhook_calls": 0,
  "test_rows_remaining": 0,
  "db_cleanup": "PASS",
  "pm2_reload": "NONE",
  "features": [
    {
      "id": "shared-inbox",
      "status": "PASS",
      "runtime_entrypoint": "...",
      "observed": "...",
      "subchecks": ["..."]
    }
  ]
}
```

Requirements:
- exactly 15 unique expected IDs
- status only PASS or FAIL
- `runtime_entrypoint` and `observed` must be non-empty
- do not put secrets, tokens, private message contents, customer data, or credentials in evidence

## 6. Final verification
Run:
`patches/ZAGHLOUL_V5R2R1_RUNTIME_PARITY_VERIFICATION/VERIFY.sh`

Do not claim success unless VERIFY.sh prints:
`FINAL_MARKER=ZAGHLOUL_V5R2R1_RUNTIME_PARITY_VERIFICATION_OK`

If any feature fails, return the failed IDs and their observed reason exactly; do not modify production to make the verifier pass.

## Final output only
Return:
PREFLIGHT
TARGET_HEAD
UPSTREAM_PIN
AUTH_MODE
RUNTIME_PARITY_PASS_COUNT
RUNTIME_PARITY_FAIL_COUNT
FAILED_FEATURES
META_EXTERNAL_CALLS
EMAIL_EXTERNAL_CALLS
NON_LOOPBACK_WEBHOOK_CALLS
SECOND_WHATSAPP_SENDER
TEST_ROWS_REMAINING
DB_CLEANUP
SOURCE_MUTATION
PM2_RELOAD
HTTP_ZAGHLOUL
RESULT_SCHEMA
FINAL_MARKER
