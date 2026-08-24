# TCRM — Tara Validation Stale Expectations V1

Purpose: fix the three confirmed stale Tara test expectations reported by the read-only validation diagnostic, without changing Tara runtime behavior.

## Scope

Changes exactly two test files:

- `server/services/tara/taraProviderSecurity.test.ts`
- `server/services/tara/taraSocialUnification.test.ts`

No application source, Felfel source, backend runtime logic, migration, database state, Mautic runtime tree, branch, or deployment behavior is changed.

## Confirmed root causes

### Provider SSRF tests

The existing test supplied `provider: "openai_compatible"` with `https://provider.example/v1`, but the current runtime contract accepts only the fixed built-in provider/host pairs before DNS evaluation. The test therefore failed at `TARA_PROVIDER_HOST_MISMATCH` and never reached the DNS-private-address assertion.

The patch keeps the original SSRF purpose and uses the supported OpenAI contract instead:

- provider: `openai`
- URL: `https://api.openai.com/v1`
- injected resolver still returns the controlled public/private test addresses

No provider security guard is relaxed.

### Social-unification scope test

The existing negative regex also matched any occurrence of the generic text `elevenlabs`, including the pre-existing hardening marker `TARA_PRODUCTION_HARDENING_V1_ITEM2_TARA_VOICE_ELEVENLABS`. The patch narrows the assertion to the actual service identifiers it intends to prohibit:

- `rakanActionService`
- `elevenLabsService`

This preserves the integration boundary while avoiding marker/comment false positives.

## Guarded base blobs

- `server/services/tara/taraProviderSecurity.test.ts` = `38b35e977bd72506b1f54118bbd099689e37f1f6`
- `server/services/tara/taraSocialUnification.test.ts` = `1a6038ef9e89fbaa49423ed6197dabab0d7cd30e`

## Apply

From the TCRM project root:

```bash
python3 /path/to/apply_tara_validation_stale_expectations_v1.py --check
python3 /path/to/apply_tara_validation_stale_expectations_v1.py --apply
python3 /path/to/apply_tara_validation_stale_expectations_v1.py --verify
```

Then run:

```bash
pnpm run test:tara-general-agent-v1.1.1
```

Expected result: all Tara targeted test files and tests pass.

## TypeScript gate note

The diagnostic also proved `pnpm check` currently has 1,033 pre-existing diagnostics on canonical `main`, including 785 in `ChatPanel.tsx`, 34 in `automation.ts`, and 214 elsewhere. No Felfel file appears in that diagnostic set. This patch intentionally does not suppress or rewrite those unrelated production type errors. Treat them as a separate technical-debt repair stream rather than weakening `tsconfig`, adding `@ts-nocheck`, or excluding active source trees.

Marker: `TCRM_TARA_VALIDATION_STALE_EXPECTATIONS_V1`
