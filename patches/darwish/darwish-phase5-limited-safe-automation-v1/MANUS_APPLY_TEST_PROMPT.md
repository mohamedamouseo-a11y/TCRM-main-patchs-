TCRM — DARWISH PHASE 5 — LIMITED SAFE AUTOMATION V1
APPLY + TEST ONLY

TARGET PROJECT:
/var/www/TCRM-MAIN

TARGET REPOSITORY:
mohamedamouseo-a11y/TCRM-MAIN-Tamiyouz-CRM-

REQUIRED BRANCH:
main

EXPECTED BASE HEAD:
0d5696b0946142c1836cefd601c597db5a3f4187

PATCH REPOSITORY:
mohamedamouseo-a11y/TCRM-main-patchs-

PATCH BUNDLE:
patches/darwish/darwish-phase5-limited-safe-automation-v1/

APPLY ORDER:
1. 01-config-policy.patch
2. 02-policy-tests-action-service.patch
3. 03-worker-ui-card.patch
4. 04-darwish-page.patch

EXPECTED SHA256:
01-config-policy.patch: f93253b0677e0623898d31f44692844400b5408a54613b2f57eae97957b61494
02-policy-tests-action-service.patch: 29414d24f30d3e9d1e059f4536174436ad273e0abbdc42c62f8a12cc925d7f80
03-worker-ui-card.patch: 6d18ffe28efbf02939949f127b830d7222c4c3dd698fd28657caa0184c923218
04-darwish-page.patch: 5faa660e1fc1e0342645a9a6345e1f2345921b74daa83a432201d2ecaad52e8e

GOAL:
Apply and validate Darwish Phase 5 code only.
DO NOT author, redesign or manually fix code.

STRICT RULES:
- DO NOT create a new branch.
- DO NOT modify any patch part.
- DO NOT manually rewrite source.
- DO NOT enable Phase 5 automation.
- DO NOT change DARWISH_LIMITED_AUTOMATION_ENABLED.
- DO NOT configure/change DARWISH_AUTOMATION_ACTOR_USER_ID.
- DO NOT enable DARWISH_APPROVED_OUTBOUND_ENABLED.
- DO NOT send WhatsApp messages.
- DO NOT send Chatwoot customer replies.
- DO NOT approve/reject/execute existing production proposals.
- DO NOT delete/clean existing proposals.
- DO NOT perform destructive DB operations.
- DO NOT commit.
- DO NOT push.

1 — PRECHECK

cd /var/www/TCRM-MAIN

Run:
git branch --show-current
git rev-parse HEAD
git status --short

Required:
BRANCH=main
HEAD=0d5696b0946142c1836cefd601c597db5a3f4187
WORKTREE=CLEAN

If HEAD differs:
STOP.
Do not adapt the patches.

2 — FETCH + VERIFY PATCH BUNDLE

Obtain all four files from the patch repository main branch.

Verify each SHA-256 exactly against MANIFEST.json and the values above.

If any mismatch:
STOP.

3 — SAFETY BASELINE

SELECT-only verify current Darwish action state.

Previous authoritative state:
- total proposals = 130
- proposed = 130
- approved = 0
- executing = 0
- execution_uncertain = 0
- executed = 0
- rejected = 0
- customer_reply = 0

Do not assume the total must still be exactly 130 if normal Phase 4 proposal generation has added new proposed rows since that verification.

Required safety state:
- approved = 0 unless a real human action occurred outside this task
- executing = 0
- execution_uncertain = 0
- executed by Phase 5 = 0
- customer outbound remains disabled

Confirm:
DARWISH_APPROVED_OUTBOUND_ENABLED is false/unset.

4 — PATCH CHECK + APPLY

For each part in exact order 01 → 04:

git apply --check <part>

Only if PASS:

git apply <part>

After all four:

git diff --check
git status --short

No manual edits.

5 — CONFIG SAFETY

Verify without printing secrets:

DARWISH_LIMITED_AUTOMATION_ENABLED must be FALSE / unset.
DARWISH_APPROVED_OUTBOUND_ENABLED must be FALSE / unset.

Do NOT configure the automation actor during this initial deployment.

Expected health/config:
- limitedAutomation.enabled = false
- customerReplyEnabled = false
- maxRisk = medium by default
- actorConfigured = false unless it was legitimately configured before this task

If limited automation is already enabled:
STOP before service restart and report it.

6 — TESTS

Run:

pnpm vitest run \
  server/services/darwish/chatwoot/darwishAutomationPolicy.test.ts \
  server/services/darwish/chatwoot/darwishActionService.test.ts \
  server/services/darwish/chatwoot/darwishCustomerMemoryService.test.ts

Also run relevant existing Darwish regression tests.

Required:
PHASE5_POLICY_TESTS=PASS
PHASE4_TESTS=PASS
PHASE3_TESTS=PASS

7 — BUILD

NODE_OPTIONS=--max-old-space-size=3072 pnpm build

Required:
BUILD=PASS

8 — RUNTIME

Restart ONLY:

pm2 restart tamiyouz-crm

Verify:
- PM2 online
- port 3001 listening
- local HTTP 200
- public /darwish healthy
- Phase 5 worker marker present
- Limited Safe Automation UI card visible
- card says Disabled by default
- customer outbound says Disabled

If a transient 502 appears immediately during restart, recheck repeatedly before classification.

9 — POST-DEPLOY SAFETY COUNTS

SELECT-only recheck action state.

Because Phase 5 master switch is disabled:

- automation_executed events added by this task = 0
- automatic executions by this task = 0
- automatic approvals by this task = 0
- WhatsApp messages sent = 0
- Chatwoot customer replies sent = 0

Normal Phase 4 proposal generation may add new proposed rows. That is not a Phase 5 failure.

No proposal may move to executed because of Phase 5 while the master switch is disabled.

10 — FINAL REPORT

Return:

PHASE5_APPLY_STATUS=
BRANCH=
HEAD_BEFORE=
PATCH_PARTS_VERIFIED=
PATCH_SCOPE=
GIT_APPLY_CHECKS=
GIT_DIFF_CHECK=
PHASE5_POLICY_TESTS=
PHASE4_TESTS=
PHASE3_TESTS=
REGRESSION_TESTS=
BUILD=
PM2=
LOCAL_HTTP=
PUBLIC_DARWISH_HTTP=
PHASE5_WORKER_MARKER=
LIMITED_AUTOMATION_ENABLED=
AUTOMATION_ACTOR_CONFIGURED=
CUSTOMER_REPLY_AUTOMATION=
APPROVED_OUTBOUND_ENABLED=
PROPOSALS_BEFORE=
PROPOSALS_AFTER=
AUTO_EXECUTIONS_BY_TASK=
AUTO_APPROVALS_BY_TASK=
WHATSAPP_MESSAGES_SENT=
CHATWOOT_CUSTOMER_REPLIES_SENT=
SOURCE_FILES_MANUALLY_EDITED=
COMMIT=
PUSH=

Expected final marker:

TCRM_DARWISH_PHASE5_CODE_DEPLOYED_AUTOMATION_DISABLED_VALIDATED

STOP after report.
DO NOT COMMIT.
DO NOT PUSH.
