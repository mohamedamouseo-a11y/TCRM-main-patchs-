# OpenHands Task — ZAGHLOUL_V5R3_TCRM_NATIVE_FULL_PARITY_UI

Target: `/var/www/TCRM-MAIN`
Patch: `patches/ZAGHLOUL_V5R3_TCRM_NATIVE_FULL_PARITY_UI`

Implement the MANIFEST completely.

## Order
1. Run `APPLY.sh`.
2. Inspect current `/zaghloul` V5 page/router/service, `server/services/zaghloul-v5/*`, and `apps/zaghloul-wacrm`.
3. Map all 15 parity items to native TCRM UI + real authenticated runtime paths.
4. Implement only what is missing. Reuse TCRM services first; reuse/adapt WACRM implementation where TCRM has no equivalent.
5. Keep `/zaghloul` native inside TCRM. No iframe/second login/second WhatsApp sender.
6. Remove/replace stubs that claim complete functionality without a real runtime path, including empty automation source.
7. Add focused tests for every parity capability or grouped UI/runtime surface. External Meta/email/non-loopback webhook calls must be intercepted.
8. Run `VERIFY.sh`; fix failures and rerun until success.

## Hard rules
- Do not weaken TCRM auth/roles.
- Do not create a second Meta token store/sender/webhook owner/queue.
- No destructive DB migration.
- No force push.
- Do not push Git from OpenHands.
- No fake/demo data to satisfy verification.
- A badge, manifest entry, grep match, or source-file existence is not runtime proof.

## Required result file
Create `/tmp/ZAGHLOUL_V5R3_TCRM_NATIVE_FULL_PARITY_UI/results.json` with:
- `baseline_head`
- `candidate_head`
- `auth_mode` = `TCRM_SESSION`
- `second_whatsapp_sender` = `NO`
- `iframe` = `NO`
- `external_meta_calls` = 0
- `external_email_calls` = 0
- `non_loopback_webhook_calls` = 0
- `features`: exactly 15 objects `{id,status,ui_surface,runtime_entrypoint,proof}`

Every status must be `PASS`.

## Final output only
BASELINE_HEAD
CANDIDATE_HEAD
PATCHED_FILES
AUTH_MODE
IFRAME
SECOND_WHATSAPP_SENDER
FEATURE_PASS_COUNT
FEATURE_FAIL_COUNT
STUBS_REMAINING
TSC_NEW_ERROR_COUNT
TESTS
BUILD
PM2
HTTP_ZAGHLOUL
HTTP_ZAGHLOUL_V5
HTTP_ZAGHLOUL_LEGACY
META_EXTERNAL_CALLS
EMAIL_EXTERNAL_CALLS
NON_LOOPBACK_WEBHOOK_CALLS
FINAL_MARKER
