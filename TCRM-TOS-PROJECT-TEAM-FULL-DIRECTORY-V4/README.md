# TCRM TOS Project Team Full Directory V4

## Goal
Upgrade **Client Profile > Handover > Step 1: TOS Project Team** so the selector behaves as a real cross-department project-team picker.

Required behavior:
- Show the active TOS team members inside every department returned by the TOS directory.
- Include **Account Management** employees and show their names under the Account Manager department.
- A permitted TCRM user who can manage the TOS Project Team may assign **any active TOS employee from any department**.
- Remove the V3 regular-AccountManager `self only` restriction and the special `Assign myself` behavior.
- New TCRM selections continue to sync to TOS using the existing **Owner** flow.
- Existing actual TOS project memberships remain protected/read-only in TCRM and remain managed from TOS.
- Do not fabricate employee names. The TOS directory must use the real active employee/team source.

## Package
- `APPLY_TCRM_PATCH.py` — incremental TCRM patch intended for a server where V3/self-only code may already be present.
- `TOS_RUNTIME_SPEC.md` — requirements for the real live TOS `team-directory` endpoint.
- `OPENHANDS_PROMPT.md` — apply, verify, build and deploy instructions for OpenHands.

## Important
This V4 intentionally changes the previous V3 business rule.

V3 rule:
> Regular AccountManager can assign only themselves.

V4 rule:
> Any user who already has permission to manage the TOS Project Team can select any active TOS employee shown in the directory, from any department, including Account Management.

Backend must still validate submitted IDs against the trusted TOS directory so arbitrary/tampered employee IDs cannot be saved.
