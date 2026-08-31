# TCRM / TOS Account Manager Self-Assign V2

## Goal
Fix the Handover > TOS Project Team selector so Account Management employees are visible and a regular TCRM `AccountManager` can add only their own TOS identity as a project `Owner`.

## Security model
- Regular `AccountManager`: may add only themselves to the TOS project-owner draft.
- Regular `AccountManager`: cannot add another Account Manager or operational employee through this self-only flow.
- Existing draft owners must be preserved.
- Existing actual TOS project memberships remain managed by TOS and are not removed.
- `Admin` / `AccountManagerLead` keep the existing broader project-team management behavior.
- Backend validation is mandatory; frontend disabling is only UX.

## Package
- `APPLY_TCRM_PATCH.py` — deterministic TCRM patcher for the current main-code structure.
- `TOS_RUNTIME_PATCH_SPEC.md` — exact requirement for the TOS `team-directory` runtime endpoint. The endpoint used by production is not present in the current GitHub `TOS/main` source tree, so this package intentionally does not invent a fake source path.
- `MANUS_APPLY_TEST_PROMPT_V2.md` — OpenHands / Manus execution and QA prompt.

## Important
Do **not** use the obsolete V1 patch at:

`patches/2026-08-31-am-self-assign-tos-team.patch`

That older patch implemented TCRM client Account Manager assignment. V2 fixes the requested behavior: **TOS Project Team self-assignment**.

## Apply order
1. Patch the real TOS `team-directory` source on the server according to `TOS_RUNTIME_PATCH_SPEC.md`.
2. Run `APPLY_TCRM_PATCH.py` against `/var/www/TCRM-MAIN`.
3. Build/typecheck both systems.
4. Verify the API and UI scenarios in `MANUS_APPLY_TEST_PROMPT_V2.md`.
