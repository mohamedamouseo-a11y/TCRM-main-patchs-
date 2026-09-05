# Sales Leads Own-or-Assigned Scope Hotfix V1

Target: `/var/www/TCRM-MAIN`
Main baseline verified: `78273711727e834ca88029e39ff0f6ae302d427a`

## Confirmed root cause
`leads.view` for SalesAgent/ColdSalesAgent is currently granted with `data_scope=assigned`, but `server/security/phase3ScopeFilters.ts` defines Lead `assigned` as active `lead_assignments` ONLY. The Sales list's legacy role filter already treats SalesAgent/ColdSalesAgent visibility as owner OR active assignment. This mismatch causes owned leads to disappear and direct-owner Lead Profile access to fail `assertRowScope` when no active assignment row exists.

## Fix scope
Modify ONLY the Lead scope evaluation for `SalesAgent` and `ColdSalesAgent` so an effective Lead scope of `assigned` means:

`lead.ownerId == user.id OR active lead_assignments(leadId,userId,isActive=1)`

Apply the same rule consistently in BOTH:
- `buildLeadScopeCondition(...)` (SQL/list filtering)
- `isRowInScope(...)` for `kind === "lead"` (single-row/byId checks)

Do NOT change generic assigned semantics for Deals, Clients, or other roles. Do NOT change permission catalog/schema/UI or role_permissions data. Do NOT add a new scope enum.

## Required regression coverage
Add focused tests proving:
1. SalesAgent + assigned scope + direct owner/no assignment => ALLOW.
2. SalesAgent + assigned scope + active assignment/not owner => ALLOW.
3. SalesAgent + assigned scope + unrelated/no assignment => DENY.
4. SalesAgent + inactive assignment/not owner => DENY.
5. ColdSalesAgent has the same owner-or-active-assignment behavior.
6. A non-sales role using assigned Lead scope keeps assignment-only behavior.
7. Deal/client assigned scope behavior is unchanged.

Verify the real Mohamed Hamed scenario after reload:
- userId=130
- owned leads=424
- active assigned leads=54
- union expected visible count=430
- Lead 2147 ownerId=130 with no active assignment must pass Lead row-scope access.

## Safety
- Preserve existing local V1/V2 Client Profile hotfix changes.
- Preserve all Evolution/waGateway dirty changes; no reset/stash/discard.
- Do not touch Inbox/notification stale-link behavior in this patch.
- No unrelated fixes.
- No git commit/push/merge/reset/rebase/stash in `/var/www/TCRM-MAIN`.

## Validation
Run focused scope tests and any relevant Leads tests. Run build/typecheck as safely possible; if full-project `tsc` OOMs, report it separately and prove no new focused errors. Reload PM2 `tamiyouz-crm` only after focused validation passes, then verify runtime health and the two real checks above.

## Report
Return only:

ROOT_CAUSE_CONFIRMED=
FILES_CHANGED=
SALES_OWNER_ALLOWED=
SALES_ACTIVE_ASSIGNEE_ALLOWED=
SALES_UNRELATED_DENIED=
SALES_INACTIVE_DENIED=
COLD_SALES_PARITY=
NON_SALES_ASSIGNED_UNCHANGED=
DEAL_CLIENT_SCOPES_UNCHANGED=
FOCUSED_TESTS=
MOHAMED_VISIBLE_COUNT=
LEAD_2147_ACCESS=
BUILD=
PM2_RELOAD=
RUNTIME_HEALTH=
GIT_OPS=NONE
DIFF_STAT=
