# Manus — TCRM Darwish Phase 5 TypeScript Gate Fix V1 — APPLY + TEST ONLY

Project: `/var/www/TCRM-MAIN`

Required branch: `main`

Expected HEAD before commit: `0d5696b0946142c1836cefd601c597db5a3f4187`

Patch repository: `mohamedamouseo-a11y/TCRM-main-patchs-`

Patch path: `patches/darwish/darwish-phase5-typescript-gate-fix-v1/01-darwish-page-health-union-fix.patch`

## Current known state

The Phase 5 Limited Safe Automation bundle is ALREADY APPLIED in the live worktree. Do not reapply it.

The prior validation passed policy tests, Darwish regressions, build, security, PM2, HTTP, UI, and DB safety. It was blocked only because the project TypeScript check included two TS2339 diagnostics in `client/src/pages/DarwishPage.tsx` for direct union access to `health.chatwoot.error` and `health.chatwoot.reason`.

## Strict rules

- Do NOT create a branch.
- Do NOT reapply Phase 5 bundle parts 01-04.
- Do NOT write or edit code manually.
- Apply ONLY the supplied TypeScript gate fix patch.
- Do NOT enable `DARWISH_LIMITED_AUTOMATION_ENABLED`.
- Do NOT configure `DARWISH_AUTOMATION_ACTOR_USER_ID`.
- Keep `DARWISH_APPROVED_OUTBOUND_ENABLED` disabled/unset.
- Do NOT approve, reject, or execute production proposals.
- Do NOT send WhatsApp or Chatwoot customer messages.
- Do NOT run migrations.
- Do NOT commit.
- Do NOT push.

## 1. Precheck

Run:

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
- worktree contains the same seven Phase 5 paths already reported
- no unrelated paths
- `git diff --check` PASS

## 2. Verify patch integrity

Obtain the patch from the patch repository and verify SHA-256:

`bac1f73e018374df0ef5c3ba534b08fb54663e701088c75650e9beae3c9276b9`

Then:

```bash
git apply --check 01-darwish-page-health-union-fix.patch
git apply 01-darwish-page-health-union-fix.patch
git diff --check
```

No manual source edits.

## 3. TypeScript gate

Run:

```bash
NODE_OPTIONS=--max-old-space-size=3072 pnpm check > /tmp/tcrm-phase5-pnpm-check-after-fix.txt 2>&1 || true
```

The overall project may still contain known pre-existing TypeScript diagnostics in unrelated TOS/Zaghloul/legacy files. Do not attempt to repair them in this task.

The Phase 5 acceptance gate is:

`NEW_PHASE5_TYPESCRIPT_ERRORS=0`

Check the current TypeScript output for diagnostics in ALL seven Phase 5 paths:

- `client/src/pages/DarwishPage.tsx`
- `server/services/darwish/chatwoot/darwishActionService.ts`
- `server/services/darwish/chatwoot/darwishConfig.ts`
- `server/services/darwish/chatwoot/darwishWorker.ts`
- `client/src/components/darwish/DarwishLimitedAutomationCard.tsx`
- `server/services/darwish/chatwoot/darwishAutomationPolicy.test.ts`
- `server/services/darwish/chatwoot/darwishAutomationPolicy.ts`

Required:
- the previous DarwishPage TS2339 `error` diagnostic = GONE
- the previous DarwishPage TS2339 `reason` diagnostic = GONE
- diagnostics across all seven Phase 5 paths = 0

Record unrelated existing diagnostics separately as baseline-only. Do not modify them.

## 4. Tests

Run:

```bash
pnpm vitest run \
  server/services/darwish/chatwoot/darwishAutomationPolicy.test.ts \
  server/services/darwish/chatwoot/darwishActionService.test.ts \
  server/services/darwish/chatwoot/darwishCustomerMemoryService.test.ts
```

Then run the same Darwish regression suite used in the previous Phase 5 validation.

Required:
- Phase 5 policy tests PASS
- Phase 4 regression PASS
- Phase 3 regression PASS

## 5. Build + security

Run:

```bash
NODE_OPTIONS=--max-old-space-size=3072 pnpm build
```

Then run the existing Developer Hub security verification.

Required:
- BUILD=PASS
- SECURITY=PASS
- BLOCKED_FINDINGS=0

## 6. Safety configuration

Confirm without printing secrets:

- `DARWISH_LIMITED_AUTOMATION_ENABLED` = unset/false
- `DARWISH_AUTOMATION_ACTOR_USER_ID` = unset
- `DARWISH_APPROVED_OUTBOUND_ENABLED` = unset/false

## 7. Runtime verification

Restart ONLY:

```bash
pm2 restart tamiyouz-crm
```

Verify:
- PM2 online
- port 3001 listening
- local `/darwish` HTTP 200 repeatedly
- public `/darwish` HTTP 200 repeatedly
- Phase 5 worker marker present
- UI still displays Limited Automation disabled
- Automation Actor not configured
- Customer outbound disabled

## 8. DB safety — SELECT only

Do not mutate any proposal.

Confirm:
- approved = 0
- executing = 0
- execution_uncertain = 0
- executed = 0
- customer_reply = 0
- task-attributable auto approvals = 0
- task-attributable auto executions = 0
- WhatsApp messages sent by task = 0
- Chatwoot customer replies sent by task = 0

Proposal count may remain 130 or increase normally from Phase 4 proposal generation; do not delete or modify proposals.

## Final report

Return:

```text
PHASE5_FIX_STATUS=
BRANCH=
HEAD=
PATCH_SHA256=
PATCH_APPLY_CHECK=
DIFF_CHECK=
DARWISH_PAGE_TS2339_ERROR_FIXED=
DARWISH_PAGE_TS2339_REASON_FIXED=
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

`TCRM_DARWISH_PHASE5_TYPESCRIPT_GATE_FIX_VALIDATED=PASS`

STOP after report. Do not commit or push.