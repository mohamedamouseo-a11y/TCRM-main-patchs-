# Manus — TCRM Darwish Phase 5 TypeScript Gate Fix V2 — APPLY + TEST ONLY

Project: `/var/www/TCRM-MAIN`

Required branch: `main`

Expected production HEAD before Phase 5 commit: `0d5696b0946142c1836cefd601c597db5a3f4187`

Patch repository: `mohamedamouseo-a11y/TCRM-main-patchs-`

Bundle: `patches/darwish/darwish-phase5-typescript-gate-fix-v2/`

Patch: `01-darwish-page-health-union-fix-v2.patch`

## Important
V1 is obsolete and MUST NOT be used. It was blocked as a malformed/corrupt patch.

Phase 5 itself is ALREADY APPLIED in the live worktree. Do not reapply Phase 5 parts 01-04.

## Strict rules
- No new branch.
- No manual source edits.
- Apply only the supplied V2 fix patch.
- Do not enable limited automation.
- Do not configure automation actor.
- Keep customer outbound disabled.
- Do not approve/reject/execute production proposals.
- Do not run migrations.
- Do not send WhatsApp or Chatwoot customer messages.
- Do not commit.
- Do not push.

## 1. Sync patch repository
Fast-forward the existing local `TCRM-main-patchs-` checkout to current `origin/main`.
The patch repository worktree must be clean before sync.

After sync, verify the V2 bundle exists.

## 2. Verify V2 patch integrity
Calculate SHA-256 of the patch and compare with `MANIFEST.json`.

Required exact SHA-256:
`4479d05f491ca66cc552795c7be8600d18f24aa8e6586b66edda0da47871b819`

Required:
`HASH_MATCH=YES`

If not, STOP.

## 3. Production precheck
```bash
cd /var/www/TCRM-MAIN
git branch --show-current
git rev-parse HEAD
git status --short
git diff --check
```

Required:
- branch `main`
- HEAD `0d5696b0946142c1836cefd601c597db5a3f4187`
- worktree contains only the existing seven Phase 5 paths
- `git diff --check` PASS

## 4. Apply V2 fix
Using the newly synced V2 patch:
```bash
git apply --check 01-darwish-page-health-union-fix-v2.patch
git apply 01-darwish-page-health-union-fix-v2.patch
git diff --check
```

Required:
- `PATCH_APPLY_CHECK=PASS`
- `DIFF_CHECK=PASS`
- `MANUAL_SOURCE_EDITS=NO`

## 5. TypeScript gate
```bash
NODE_OPTIONS=--max-old-space-size=3072 pnpm check > /tmp/tcrm-phase5-pnpm-check-after-v2.txt 2>&1 || true
```

Check diagnostics for the seven Phase 5 paths only:
- `client/src/pages/DarwishPage.tsx`
- `client/src/components/darwish/DarwishLimitedAutomationCard.tsx`
- `server/services/darwish/chatwoot/darwishActionService.ts`
- `server/services/darwish/chatwoot/darwishConfig.ts`
- `server/services/darwish/chatwoot/darwishWorker.ts`
- `server/services/darwish/chatwoot/darwishAutomationPolicy.ts`
- `server/services/darwish/chatwoot/darwishAutomationPolicy.test.ts`

Required:
- DarwishPage TS2339 `error` diagnostic = GONE
- DarwishPage TS2339 `reason` diagnostic = GONE
- `NEW_PHASE5_TYPESCRIPT_ERRORS=0`

Do not fix unrelated baseline errors elsewhere.

## 6. Tests
```bash
pnpm vitest run \
  server/services/darwish/chatwoot/darwishAutomationPolicy.test.ts \
  server/services/darwish/chatwoot/darwishActionService.test.ts \
  server/services/darwish/chatwoot/darwishCustomerMemoryService.test.ts
```

Then run the same full Darwish regression suite used in the previous Phase 5 validation.

Required:
- policy tests PASS
- Darwish regression PASS

## 7. Build + security
```bash
NODE_OPTIONS=--max-old-space-size=3072 pnpm build
```
Run existing Developer Hub security verification.

Required:
- BUILD=PASS
- SECURITY=PASS
- BLOCKED_FINDINGS=0

## 8. Safety configuration
Confirm without changing:
- `DARWISH_LIMITED_AUTOMATION_ENABLED` unset/false
- `DARWISH_AUTOMATION_ACTOR_USER_ID` unset
- `DARWISH_APPROVED_OUTBOUND_ENABLED` unset/false

## 9. Runtime
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
- Limited Automation disabled
- Automation Actor not configured
- Customer outbound disabled

## 10. DB safety — SELECT only
Confirm:
- approved=0
- executing=0
- execution_uncertain=0
- executed=0
- customer_reply=0
- task auto approvals=0
- task auto executions=0
- task WhatsApp sends=0
- task Chatwoot customer replies=0

Do not delete or modify the 130 existing proposals.

## Final report
```text
PHASE5_FIX_V2_STATUS=
PATCH_REPO_HEAD=
PATCH_SHA256=
MANIFEST_SHA256=
HASH_MATCH=
BRANCH=
HEAD=
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

Expected marker:
`TCRM_DARWISH_PHASE5_TYPESCRIPT_GATE_FIX_V2_VALIDATED=PASS`

STOP after report. Do not commit or push.
