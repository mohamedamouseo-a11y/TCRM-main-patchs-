# TCRM → TOS Project Integration Audit V1

A **read-only production audit** for tracing the real TCRM → TOS project synchronization path before fixing duplicate projects.

## Approved TCRM baseline

- Repository: `mohamedamouseo-a11y/TCRM-MAIN-Tamiyouz-CRM-`
- Branch: `main`
- Expected HEAD: `b016f9ada07e334b47bf95a19a59e667b7351b1b`

The runner aborts safely if the server HEAD is different. Unrelated dirty files are allowed and are never reset.

## What this audit inspects

- Current TCRM source tree for TOS/project-sync sender code.
- Candidate endpoint/payload construction.
- `crmProjectId`, `crmDealId`, `crmClientId` identity clues.
- Retry/backfill/batch/force/replay code clues.
- Durable TOS-project mapping clues.
- Git log/reflog around 2026-08-15.
- Read-only PM2/systemd/Docker inventory when available.
- Sanitized relevant log evidence when readable.
- `.env` **key names only**; values are never exported.

## What it does NOT do

- No source edits.
- No TCRM/TOS data edits.
- No SQL execution.
- No mutating HTTP requests.
- No build or deploy.
- No service restart.
- No git commit/push/reset/checkout.
- No sync/backfill/force script execution.

The audit writes only sanitized temporary reports under `/tmp`.

## Files

- `run_tcrm_tos_project_integration_audit_v1.py` — self-contained read-only runner.
- `OPENHANDS_PROMPT.md` — exact OpenHands execution instructions.
- `README.md` — this document.

## Expected output

The evidence should let the next phase distinguish between:

1. TCRM sending a genuinely new stable project identity.
2. TCRM retry/backfill using unstable identifiers.
3. TOS receiving a stable identity but failing to reconcile an existing legacy project because no prior mapping exists.
4. A mixed case involving both sender behavior and TOS reconciliation.

This patch is evidence-only. **Do not create a cleanup or prevention patch until this audit result is reviewed.**
