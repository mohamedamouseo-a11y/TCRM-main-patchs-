# Manus — TCRM Darwish Phase 5 TypeScript Gate Fix V3 — APPLY + FINAL VALIDATION ONLY

Project: `/var/www/TCRM-MAIN`

Required branch: `main`

Expected HEAD before Phase 5 commit: `0d5696b0946142c1836cefd601c597db5a3f4187`

Patch repository: `mohamedamouseo-a11y/TCRM-main-patchs-`

Bundle: `patches/darwish/darwish-phase5-typescript-gate-fix-v3/`

Patch: `01-darwish-page-evolution-health-union-fix-v3.patch`

Expected SHA-256:
`7a32c002e3407fa424572d36af4e446f9b4e12ee77e3b9a36a07917ec3aafddd`

## Current known state

- Phase 5 Limited Safe Automation is already applied.
- V2 Chatwoot TypeScript union fix is already applied.
- V2 validation passed patch integrity, tests, build, security, runtime, UI and DB safety.
- Exactly two Phase 5 TS2339 diagnostics remain in `client/src/pages/DarwishPage.tsx`, for `health.evolution.error` and `health.evolution.reason`.
- Do NOT reapply Phase 5 bundle parts 01-04.
- Do NOT reapply V2.

## Strict rules

- Do NOT create a branch.
- Do NOT manually edit source.
- Apply ONLY V3.
- Do NOT enable `DARWISH_LIMITED_AUTOMATION_ENABLED`.
- Do NOT configure `DARWISH_AUTOMATION_ACTOR_USER_ID`.
- Keep `DARWISH_APPROVED_OUTBOUND_ENABLED` disabled/unset.
- Do NOT approve, reject, or execute production proposals.
- Do NOT send WhatsApp or Chatwoot customer messages.
- Do NOT run migrations.
- Do NOT commit.
- Do NOT push.

## 1. Sync patch repository

Fast-forward the existing local `TCRM-main-patchs-` checkout to `origin/main` without discarding local changes.

If the patch repo worktree is dirty, STOP.

Confirm the V3 bundle exists.

## 2. Verify patch integrity

From the V3 bundle calculate:

```bash
sha256sum 01-darwish-page-evolution-health-union-fix-v3.patch
```

Read `MANIFEST.json`.

Both must equal:

`7a32c002e3407fa424572d36af4e446f9b4e12ee77e3b9a36a07917ec3aafddd`

Required:
`HASH_MATCH=YES`

## 3. Production precheck

```bash
cd /var/www/TCRM-MAIN
git branch --show-current
git rev-parse HEAD
git status --short
git diff --check
```

Required:
- branch = `main`
- HEAD = `0d5696b0946142c1836cefd601c597db5a3f4187`
- worktree contains only the existing seven Phase 5 paths
- V2 Chatwoot narrowing is already present
- direct Evolution expression still contains the two reported TS2339 accesses before V3
- `git diff --check` = PASS

If the V3 fix is already present, STOP and report rather than reapply.

## 4. Apply V3 only

```bash
git apply --check 01-darwish-page-evolution-health-union-fix-v3.patch
git apply 01-darwish-page-evolution-health-union-fix-v3.patch
git diff --check
```

Required:
- `PATCH_APPLY_CHECK=PASS`
- `DIFF_CHECK=PASS`
- `MANUAL_SOURCE_EDITS=NO`

## 5. Final Phase 5 TypeScript gate

```bash
NODE_OPTIONS=--max-old-space-size=3072 pnpm check > /tmp/tcrm-phase5-pnpm-check-after-v3.txt 2>&1 || true
```

Check diagnostics across the seven Phase 5 paths only.

Required:
- Chatwoot TS2339 diagnostics remain gone.
- Evolution `error` TS2339 = gone.
- Evolution `reason` TS2339 = gone.
- `client/src/pages/DarwishPage.tsx` diagnostics = 0.
- `NEW_PHASE5_TYPESCRIPT_ERRORS=0`.

Do NOT repair unrelated historical TypeScript diagnostics in TOS/Zaghloul/legacy Darwish files. Record them separately as baseline-only.

## 6. Tests

Run:

```bash
pnpm vitest run \
  server/services/darwish/chatwoot/darwishAutomationPolicy.test.ts \
  server/services/darwish/chatwoot/darwishActionService.test.ts \
  server/services/darwish/chatwoot/darwishCustomerMemoryService.test.ts
```

Then run the same full Darwish Chatwoot regression suite from V2 validation.

Required:
- policy/action/customer-memory = PASS
- full Darwish regression = PASS

## 7. Build and security

```bash
NODE_OPTIONS=--max-old-space-size=3072 pnpm build
```

Run existing Developer Hub controlled-push security verification and security test suite.

Required:
- BUILD=PASS
- SECURITY=PASS
- BLOCKED_FINDINGS=0

## 8. Safety configuration

Confirm without printing secrets:
- `DARWISH_LIMITED_AUTOMATION_ENABLED` = unset/false
- `DARWISH_AUTOMATION_ACTOR_USER_ID` = unset
- `DARWISH_APPROVED_OUTBOUND_ENABLED` = unset/false

Do not change them.

## 9. Runtime validation

Restart ONLY:

```bash
pm2 restart tamiyouz-crm
```

Verify:
- PM2 online
- port 3001 listening
- local `/darwish` HTTP 200 repeatedly
- public `/darwish` stabilizes at HTTP 200
- Phase 5 worker marker present
- Limited Automation card still disabled
- Automation Actor not configured
- Customer outbound disabled

A single transient 502 immediately after restart is not a persistent routing failure; recheck until readiness is established.

## 10. DB safety — SELECT only

Required:
- proposed may remain/increase normally
- approved = 0
- executing = 0
- execution_uncertain = 0
- executed = 0
- customer_reply = 0
- task-attributable auto approvals = 0
- task-attributable auto executions = 0
- WhatsApp messages sent by task = 0
- Chatwoot customer replies sent by task = 0

Do not mutate proposals or events.

## Final report

Return:

```text
PHASE5_V3_FIX_STATUS=
BRANCH=
HEAD=
PATCH_SHA256=
HASH_MATCH=
PATCH_APPLY_CHECK=
DIFF_CHECK=
CHATWOOT_TS2339_STILL_FIXED=
EVOLUTION_TS2339_ERROR_FIXED=
EVOLUTION_TS2339_REASON_FIXED=
DARWISH_PAGE_TYPESCRIPT_ERRORS=
NEW_PHASE5_TYPESCRIPT_ERRORS=
UNRELATED_BASELINE_TYPESCRIPT_ERRORS=
POLICY_TESTS=
DARWISH_REGRESSION=
BUILD=
SECURITY=
BLOCKED_FINDINGS=
PM2=
LOCAL_HTTP=
PUBLIC_DARWISH_HTTP=
PHASE5_WORKER_MARKER=
LIMITED_AUTOMATION_ENABLED=
AUTOMATION_ACTOR_CONFIGURED=
CUSTOMER_OUTBOUND_ENABLED=
AUTO_APPROVALS_BY_TASK=
AUTO_EXECUTIONS_BY_TASK=
WHATSAPP_MESSAGES_SENT=
CHATWOOT_CUSTOMER_REPLIES_SENT=
MANUAL_SOURCE_EDITS=NO
COMMIT=NO
PUSH=NO
```

Expected final marker:

`TCRM_DARWISH_PHASE5_TYPESCRIPT_GATE_FIX_V3_VALIDATED=PASS`

STOP after the report. Do not commit or push.
