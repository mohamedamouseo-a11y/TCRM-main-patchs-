# TCRM TOS Directory Recovery V4.1

## Purpose

Emergency recovery for the live error in:

`Client Profile > Handover > TOS Project Team`

Observed production error:

`Unexpected token '<', "<html>..." is not valid JSON`

This means TCRM expected JSON from the TOS `team-directory` operational endpoint but received HTML instead (commonly a reverse-proxy 404/502 page, redirect/login page, or wrong upstream route).

## Goals

1. Restore the real TCRM -> TOS `team-directory` request so it returns JSON.
2. Preserve V4 full-directory behavior: all active employees are available by department, including Account Management.
3. Do not regress assignment permissions or existing TOS project memberships.
4. Harden TCRM parsing so a future HTML/non-JSON response produces a useful upstream error instead of a raw JSON parse exception.
5. Build, deploy, and smoke-test the existing production workflow.

## Files

- `APPLY_TCRM_HARDENING.py` — safe parsing/error-reporting hardening for `server/services/tosIntegrationService.ts`.
- `OPENHANDS_RECOVERY_PROMPT.md` — full live-server diagnosis, repair, build, deploy, and verification procedure.

## Important

The parser hardening is not a substitute for repairing the live TOS route/proxy. OpenHands must identify why the live endpoint returns HTML and fix that root cause first/alongside the hardening.

Do not git push from OpenHands. GitHub patch publication is handled separately.
