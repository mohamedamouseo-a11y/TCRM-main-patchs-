# TCRM / TOS Project Team — Real Team Directory Endpoint V4.3

## Purpose
V4.2 stopped TCRM from crashing when TOS returned HTML, but it intentionally fell back to an empty directory. That means the business feature is still incomplete.

V4.3 fixes the root cause: add a real authenticated TOS operational `GET team-directory` endpoint next to the existing TCRM↔TOS operational endpoints (`projects`, `project-tasks`, etc.).

## Required result
`GET <operational-base>/team-directory?crmClientId=<id>&includeAccountManagement=1`

must return JSON containing:
- all active TOS employees grouped under their real departments,
- Account Management employees when `includeAccountManagement=1`,
- the currently linked TOS project,
- current project memberships and their real project roles.

New TCRM selections continue to sync as Owners through the existing `projectOwners` / `ADD_ONLY` flow.

## Important architecture rule
Do not blindly add `/team-directory` to whichever TOS web app answers the hostname. First locate the **actual service/source that already handles the configured operational `projects` and `project-tasks` endpoints** and register the new route there, before SPA/static fallback.

## Files
- `TOS_TEAM_DIRECTORY_SPEC.md` — exact API/data/security contract.
- `OPENHANDS_PROMPT.md` — server implementation, verification, build, deployment, and live QA instructions.

## No schema migration expected
TOS already contains department and employee directory data. The endpoint must reuse existing production project/member storage and lookup logic rather than create duplicate project tables.
