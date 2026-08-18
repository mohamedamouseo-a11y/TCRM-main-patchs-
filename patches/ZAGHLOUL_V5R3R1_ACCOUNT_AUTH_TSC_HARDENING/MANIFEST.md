# ZAGHLOUL_V5R3R1_ACCOUNT_AUTH_TSC_HARDENING

Target: `/var/www/TCRM-MAIN`
Parent: `ZAGHLOUL_V5R3_TCRM_NATIVE_FULL_PARITY_UI`

## Purpose
Close the two remaining V5R3 acceptance blockers:

1. `account-management` runtime returned `authMode=undefined`.
2. TypeScript verification exited `137` (OOM), so `TSC_NEW_ERROR_COUNT=0` was not valid evidence.

## Source fix
The real Zaghloul V5 settings/account runtime contract must expose:

`authMode: "TCRM_SESSION"`

This is added at the service layer (`getZaghloulV5Settings`) rather than faking the probe/result file. Existing TCRM protected-procedure/session enforcement remains the authority; no second login/session implementation is introduced.

## TSC hardening
Verification MUST:
- run baseline from a detached git worktree at the baseline HEAD;
- run candidate from the live target;
- use `NODE_OPTIONS=--max-old-space-size=16384`;
- preserve and report both exit codes;
- reject OOM/signal exits (`137`, `134`, `9`) and exits outside normal TypeScript statuses (`0`, `1`, `2`);
- compare normalized baseline vs candidate TS diagnostics;
- require `TSC_NEW_ERROR_COUNT=0`.

## Safety
- Back up every modified source file before mutation.
- No database migration.
- No dependency install.
- No git commit/push.
- No external Meta/email/webhook traffic.
- No second auth system or second WhatsApp sender.

Success marker:
`ZAGHLOUL_V5R3R1_ACCOUNT_AUTH_TSC_HARDENING_OK`
