# OpenHands Recovery Prompt — TOS Project Team V4.1

You are repairing a production regression on the TCRM server.

## Evidence from live UI

The live Handover > TOS Project Team screen currently shows:

`Could not load the TOS team: Unexpected token '<', "<html>..." is not valid JSON`

This means the TCRM backend expected JSON from the TOS operational `team-directory` request but received HTML.

## Patch source

Repository:
`mohamedamouseo-a11y/TCRM-main-patchs-`

Package:
`TCRM-TOS-DIRECTORY-RECOVERY-V4.1`

Target TCRM application path:
`/var/www/TCRM-MAIN`

Do NOT git push. Do NOT change GitHub credentials.

## Objective

Restore the live TOS Project Team directory while preserving V4 behavior:

- show active employees grouped by all TOS departments,
- include Account Management names,
- allow permitted users to select any valid active directory employee,
- preserve existing TOS project memberships,
- reject fake/non-directory `tosUserId` values,
- do not regress other TOS integrations.

## Phase 1 — Reproduce and capture the exact upstream failure

Inspect the current TCRM code and process first:

```bash
cd /var/www/TCRM-MAIN
git status --short
git rev-parse HEAD
pm2 status
```

Do not reset/stash/delete unrelated work.

Locate the exact current `getTosProjectTeamDirectory()` implementation and `buildOperationalUrl()` implementation.

Determine the exact TOS operational URL being called for `team-directory` WITHOUT printing API keys or secrets.

Use the existing TOS integration configuration to make the same server-to-server request as TCRM, including the existing `X-API-Key`, but never echo the key.

Capture only:
- request URL/path (without secrets),
- HTTP status,
- `Content-Type`,
- redirect `Location` if any,
- first safe 200 characters of response body.

Test both:
- base/default directory request,
- directory request with `crmClientId=118&includeAccountManagement=1`.

Do NOT declare success from a 401 request that omits application auth/API-key context.

## Phase 2 — Identify why HTML is returned

Classify the failure precisely:

### If 301/302/307/308
Find the redirect target. Fix the route/base URL or reverse-proxy behavior so the server-to-server operational API returns JSON directly. Do not route the API through a browser login page.

### If 404 HTML
Locate the real live `team-directory` route/source and compare it with the URL built by TCRM. Correct the route or TCRM operational URL construction. Do not invent a duplicate API unless the existing deployment genuinely lacks the endpoint.

### If 502/503 HTML
Inspect the existing nginx/reverse-proxy upstream and the TOS process/port. Restore the current intended upstream; do not redesign nginx or create a new service architecture.

### If 200 HTML
Determine whether nginx SPA fallback/login middleware is swallowing the API route. Fix route precedence/proxying so `/team-directory` reaches the operational API and returns JSON.

### If TOS route exists but query handling is wrong
Ensure `includeAccountManagement=1` is supported and preserves backward compatibility:
- missing flag: existing default behavior,
- flag = 1: include active Account Management employees,
- return `departments[].members` with usable TOS user id, name, canonical email, and department info,
- preserve `projectMembers` behavior.

Do not hardcode employee names.

## Phase 3 — Apply TCRM defensive parsing hardening

After/while fixing the upstream root cause, apply:

```bash
python3 /PATH/TO/TCRM-TOS-DIRECTORY-RECOVERY-V4.1/APPLY_TCRM_HARDENING.py /var/www/TCRM-MAIN
```

If the patcher stops because the live implementation has diverged, port the same behavior manually.

Required behavior in `server/services/tosIntegrationService.ts`:
- read response body as text once,
- check HTTP status,
- parse JSON explicitly,
- if the response is HTML/non-JSON, throw a controlled upstream error containing status/content-type and only a short safe response preview,
- never leak API keys/secrets.

This hardening is NOT a substitute for fixing the upstream route.

## Phase 4 — Verify directory data before rebuilding TCRM

Using a valid authenticated server-to-server TOS request for client 118, verify the response is JSON and report counts + employee names for:

- Management
- Sales
- Account Manager / Account Management
- SEO
- Design
- Media Buying
- Social Media
- Web Development
- any additional returned department

The names must come from TOS active employee directory data.

Also verify `projectMembers` still identifies currently linked project members separately from the directory.

If known active TOS employees exist but departments remain empty, trace the TOS query/filter and fix it before deployment.

## Phase 5 — Build and deploy

Run:

```bash
cd /var/www/TCRM-MAIN
git diff --check
npm run build
```

If the repository has a practical targeted typecheck/test command for these files, run it. Do not fix unrelated historical errors.

`npm run build` must finish with exit code 0.

Then use the EXISTING production deployment process only.
Restart only the required existing TCRM/TOS processes.
Do not invent new nginx/PM2/systemd architecture.

## Phase 6 — Post-deploy smoke test

Verify from production:

1. `/clients/118` loads.
2. Handover > TOS Project Team loads WITHOUT the `<html>` JSON parsing error.
3. Account Management contains real names when active AM employees exist.
4. Other populated departments contain real names.
5. Existing linked project members still display.
6. Selecting a valid directory employee and saving succeeds.
7. A fake/non-directory `tosUserId` is still rejected by backend.
8. Logs contain no new TOS directory errors.

If you can use the currently authenticated real browser/session, perform UI QA. If not, perform the authenticated server/API verification and state the exact remaining browser-only check.

## Final report

Return only:

ROOT CAUSE: <exact cause>
TOS HTTP STATUS: <status>
TOS CONTENT-TYPE: <content-type>
TOS JSON: PASS/FAIL
ACCOUNT MANAGEMENT NAMES: PASS/FAIL
OTHER DEPARTMENT NAMES: PASS/FAIL
BUILD: PASS/FAIL
DEPLOY: PASS/FAIL
CLIENT 118 DIRECTORY: PASS/FAIL
FAKE ID BLOCKED: PASS/FAIL/NOT TESTED
ERRORS: none / exact remaining error
FINAL: SUCCESS/BLOCKED

Do not mark SUCCESS while the live `/clients/118` directory still returns HTML/non-JSON.
