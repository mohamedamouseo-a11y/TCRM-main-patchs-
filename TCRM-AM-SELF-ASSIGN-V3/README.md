# TCRM AM Self-Assign V3

Final patch package for **Client Profile > Handover > TOS Project Team**.

## Required behavior
- Account Management must be visible in the Handover TOS Project Team directory.
- A regular `AccountManager` can add/select only their own TOS employee identity.
- Self identity is matched by trusted TCRM email / centralEmail to the canonical TOS employee email. Do not assume TCRM numeric user id equals TOS user id.
- A regular AccountManager cannot add another employee or remove/modify existing non-self pending owners.
- Existing TOS project memberships remain managed by TOS.
- `Admin` and `AccountManagerLead` keep their existing broader permissions.
- Backend is the source of truth; frontend restrictions are UX only.

## Files
- `APPLY_PATCH.py` — deterministic TCRM source patcher based on current `main` structure.
- `TOS_RUNTIME_SPEC.md` — backward-compatible requirement for the live TOS `team-directory` endpoint.
- `OPENHANDS_PROMPT.md` — production-server apply/build/test/deploy instructions.

## Source baseline inspected
TCRM main files inspected before preparing this package:
- `client/src/components/TosProjectTeamSelector.tsx`
- `client/src/pages/ClientProfile.tsx`
- `server/routers.ts`
- `server/services/tosIntegrationService.ts`

The current TCRM service calls TOS `team-directory`, while the current UI text explicitly states Account Management is excluded. This package opts the Handover flow into Account Management without changing task-directory consumers.

## Important
Do not use the older V1 package for this requirement. V3 is the package to apply.
