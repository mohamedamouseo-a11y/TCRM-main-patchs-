# EVOLUTION TEST SUITE REPAIR V1

Target TCRM baseline: `8cb75b753c84e9e5a14e41f207fb7dc83cb5e14e`

Purpose: repair only the four broken WhatsApp/Evolution test files that were accidentally pushed with malformed TypeScript. Do not change production implementation.

## Allowed files only

- `server/services/waGatewayContactSync.test.ts`
- `server/services/waGatewayEvolutionContract.test.ts`
- `server/services/waGatewayLidContactIdentity.test.ts`
- `server/services/waGatewayLidPhoneBackfill.test.ts`

## Required repairs

1. Fix malformed Vitest `it(...)` descriptions by using proper quoted strings.
2. Quote all JID/name/message literals such as `123@lid`, `123@s.whatsapp.net`, `Alice`, `WhatsApp`, etc.
3. In `waGatewayEvolutionContract.test.ts`, align tests with the current `collectEvolutionPages()` return shape `{ items, truncated }`; use valid deterministic record IDs such as `${index + 1}@s.whatsapp.net`.
4. In `waGatewayLidPhoneBackfill.test.ts`, add only the missing test imports required by the existing assertions (`resolveWAGatewayPhoneFromPayload`, `extractWAGatewayRemoteJid`) from `./waGatewayContactSync`.
5. Preserve the intended assertions. Do not weaken/delete failing assertions merely to make tests green.
6. If any test becomes syntactically valid but then fails because production behavior disagrees with the assertion, STOP and report the semantic failure. Do not modify production code in this task.

## Validation

Run the four focused test files together. Then run `npm run build`.

## Safety

- No changes outside the four test files.
- No production source edits.
- No DB changes.
- No reset/stash/clean/checkout/rebase/commit/push.
- Preserve permission fixes and current Evolution production files exactly.

## Report

`BASELINE_HEAD=`
`FILES_CHANGED=`
`SYNTAX_REPAIRED=YES/NO`
`FOCUSED_TESTS=`
`TEST_RESULT=`
`SEMANTIC_FAILURES=`
`BUILD=`
`PRODUCTION_FILES_CHANGED=NO`
`GIT_OPS=NONE`
