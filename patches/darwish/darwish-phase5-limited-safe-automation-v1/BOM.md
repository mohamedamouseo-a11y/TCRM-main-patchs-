# BOM — Darwish Phase 5 — Limited Safe Automation V1

## Baseline

- Target application repository: `mohamedamouseo-a11y/TCRM-MAIN-Tamiyouz-CRM-`
- Target branch: `main`
- Baseline HEAD: `0d5696b0946142c1836cefd601c597db5a3f4187`
- Patch bundle path: `patches/darwish/darwish-phase5-limited-safe-automation-v1/`
- Database migration: **NONE**
- Default runtime enablement: **OFF**

## Patch Bundle — Apply in This Exact Order

- `01-config-policy.patch` — `f93253b0677e0623898d31f44692844400b5408a54613b2f57eae97957b61494` (7476 bytes)
- `02-policy-tests-action-service.patch` — `29414d24f30d3e9d1e059f4536174436ad273e0abbdc42c62f8a12cc925d7f80` (12872 bytes)
- `03-worker-ui-card.patch` — `6d18ffe28efbf02939949f127b830d7222c4c3dd698fd28657caa0184c923218` (7514 bytes)
- `04-darwish-page.patch` — `5faa660e1fc1e0342645a9a6345e1f2345921b74daa83a432201d2ecaad52e8e` (2676 bytes)

Combined monolithic development artifact SHA-256:

`c6b73e65faa860ab8d7ae331a2e3bd5a0d112328f327458a68a125b6e73cfae8`

The repository artifact is intentionally split into four independently valid patch parts. Apply them sequentially; do not reorder or edit them.

## Files

### Added
1. `server/services/darwish/chatwoot/darwishAutomationPolicy.ts`
2. `server/services/darwish/chatwoot/darwishAutomationPolicy.test.ts`
3. `client/src/components/darwish/DarwishLimitedAutomationCard.tsx`

### Modified
4. `server/services/darwish/chatwoot/darwishConfig.ts`
5. `server/services/darwish/chatwoot/darwishActionService.ts`
6. `server/services/darwish/chatwoot/darwishWorker.ts`
7. `client/src/pages/DarwishPage.tsx`

## Functional Scope

Phase 5 introduces a deterministic, fail-closed policy engine for **limited automatic execution of internal actions only**.

Eligible action types:
- `internal_note`
- `follow_up_reminder`

Explicitly never auto-executed:
- `customer_reply`
- WhatsApp messages
- Chatwoot customer replies
- high/critical-risk actions above configured limit
- untrusted sources
- actions with missing required context
- actions after `execution_uncertain`

## Default Configuration

```text
DARWISH_LIMITED_AUTOMATION_ENABLED=false
DARWISH_AUTO_INTERNAL_NOTE_ENABLED=true
DARWISH_AUTO_FOLLOWUP_REMINDER_ENABLED=true
DARWISH_AUTO_MAX_RISK=medium
DARWISH_AUTO_MAX_ACTIONS_PER_HOUR=25
DARWISH_AUTO_MAX_ACTIONS_PER_CLIENT_PER_DAY=5
DARWISH_AUTO_MAX_ACTIONS_PER_MANAGER_PER_HOUR=10
DARWISH_AUTO_REQUIRE_CLIENT_CONTEXT=true
DARWISH_AUTO_REQUIRE_ACCOUNT_MANAGER=true
DARWISH_AUTOMATION_ACTOR_USER_ID=<required before enablement>
DARWISH_APPROVED_OUTBOUND_ENABLED=false
```

## Safety Design

- Master Phase 5 switch defaults to `false`.
- Customer reply automation is hard-blocked by the policy engine.
- Existing Phase 4 human Approve/Reject/Execute workflow is preserved.
- Automatic execution uses a separate atomic claim path; it does not fake a human approval.
- Execution failure transitions the proposal to `execution_uncertain`.
- Automatic retry after uncertainty is blocked.
- Global, per-client, and per-account-manager rate limits are enforced.
- Only `source_type=supervisor_alert` is trusted for Phase 5 auto-execution.
- Automation requires a configured system actor before becoming eligible.
- Audit events record `automation_execution_started`, `automation_executed`, and `automation_execution_uncertain`.
- No schema migration is required; existing Phase 4 action/audit tables are reused.

## Validation Performed Before Publishing Patch

- Current baseline blobs verified:
  - `darwishConfig.ts`: `f870685230710e2e100f48f4c514dc263eb14af0`
  - `darwishActionService.ts`: `9b8a923cd42ca57de009a9355e08e05b10864a2a`
  - `darwishWorker.ts`: `0fbe165946b599446475aa82e51f6691c4697b3b`
  - `DarwishPage.tsx`: `ba373c088236256e3e671676939334b485f60d3f`
- Sequential `git apply --check` for parts 01 → 04: **PASS**
- Sequential apply simulation for parts 01 → 04: **PASS**
- TypeScript/TSX transpile syntax check: **PASS**
- Policy smoke assertions: **PASS**

## Required Server Validation

- Verify branch is `main`.
- Verify HEAD still matches expected baseline or stop.
- Verify worktree is clean.
- Verify every part hash against `MANIFEST.json`.
- Run `git apply --check` and apply each part in exact order 01 → 04.
- Keep `DARWISH_LIMITED_AUTOMATION_ENABLED=false`.
- Keep `DARWISH_APPROVED_OUTBOUND_ENABLED=false`.
- Do not set/change `DARWISH_AUTOMATION_ACTOR_USER_ID` during initial apply/test.
- Run targeted Phase 5 + Phase 4 + Phase 3 tests.
- Run production build.
- Restart only `tamiyouz-crm` if required for runtime validation.
- Confirm public `/darwish` healthy.
- Confirm no Phase 5 automatic execution occurs while the master switch is disabled.
- Confirm zero customer messages, zero auto approvals, and zero auto executions during this initial deployment validation.
