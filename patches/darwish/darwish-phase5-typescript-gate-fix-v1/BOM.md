# TCRM — Darwish Phase 5 TypeScript Gate Fix V1 — BOM

## Purpose
Fix the two Phase 5 blocking TypeScript diagnostics in `client/src/pages/DarwishPage.tsx` without changing runtime behavior or any Darwish automation safety boundary.

## Baseline
- Production branch: `main`
- Production HEAD before Phase 5 commit: `0d5696b0946142c1836cefd601c597db5a3f4187`
- Phase 5 bundle must already be applied in the working tree.
- Phase 5 automation must remain disabled.

## Source files changed
1. `client/src/pages/DarwishPage.tsx`

## Exact defect
The Chatwoot health result is a structural union. Direct access to `.error` and `.reason` is not valid on every union member and produced:
- TS2339: Property `error` does not exist on type ...
- TS2339: Property `reason` does not exist on type ...

## Fix
Use TypeScript `in` narrowing before reading `error`, `reason`, or `url`.

## Safety impact
- No database changes.
- No migration.
- No worker behavior change.
- No policy change.
- No auto-approval.
- No auto-execution.
- No customer outbound.
- No WhatsApp/Chatwoot send.
- No environment changes.

## Expected validation
- The two DarwishPage TS2339 diagnostics disappear.
- `git diff --check` passes.
- Phase 5 policy tests pass.
- Darwish regressions pass.
- Build passes.
- Security passes.
- Overall project `pnpm check` may still contain known pre-existing non-Phase-5 diagnostics; acceptance requires `NEW_PHASE5_TYPESCRIPT_ERRORS=0` across the seven Phase 5 paths.
