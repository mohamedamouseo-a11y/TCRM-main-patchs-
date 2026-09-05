# Sales Agent Client Profile Assignment Hotfix V2

Target: `/var/www/TCRM-MAIN`
Main baseline inspected: `78273711727e834ca88029e39ff0f6ae302d427a`
Apply on top of the current local working tree, including the already-applied V1 Sales Agent assignment hotfix and existing Evolution/waGateway changes. Do not reset, stash, discard, or overwrite unrelated local work.

## Confirmed root cause

`ClientProfile.tsx` opens `/clients/:id` and calls `trpc.accountManagement.getClientProfile`.
That endpoint currently calls:

`assertAccountManagementClientAccess(ctx, input.id, "client.read.full")`

The V1 hotfix only extended `assertWorkflowOperationAllowed(..., "workflow.read")`, so it never runs on the actual Client Profile path.

## Required surgical fix

Modify only the Account Management client-read authorization path so a `SalesAgent` or `ColdSalesAgent` can perform `client.read.full` when either:

1. they are the direct owner of the Client's linked Lead, OR
2. they have an active `lead_assignments` row for that linked Lead (`userId` matches actor and `isActive = 1`).

Use the existing V1 helper `hasActiveLeadAssignmentForClientActor` (or its exact local equivalent/signature) rather than introducing duplicate assignment logic.

Implementation requirements:

- Extend `canRolePerformClientOperation` for `SalesAgent` / `ColdSalesAgent` to include `client.read.full` in addition to the operations they already have.
- In `assertClientOperationAllowed`, preserve the existing direct-owner path first.
- Only allow the active-assignment fallback for `operation === "client.read.full"`.
- Do NOT let an assigned non-owner inherit `brief.sales.submit`, `project_team.manage`, update, delete, contract, payment, or any other operation through this fallback.
- Do NOT alter AccountManager, AccountManagerLead, SalesManager, TAM, after-sales, legacy admin, Phase 3 scope, or permission-engine behavior.
- Do NOT change `getClientProfile` response shape or frontend code unless compilation proves it is strictly required.
- Preserve deny-by-default behavior for inactive, deleted, unrelated, or missing assignments.

## Tests

Add focused regression coverage proving:

1. SalesAgent direct lead owner + `client.read.full` => ALLOW.
2. SalesAgent active assigned non-owner + `client.read.full` => ALLOW.
3. ColdSalesAgent active assigned non-owner + `client.read.full` => ALLOW.
4. Inactive assignment => DENY.
5. Unrelated agent => DENY.
6. Active assigned non-owner does NOT gain `brief.sales.submit` or `project_team.manage` through the assignment fallback.
7. Existing AccountManager / SalesManager behavior remains unchanged.

Run the focused security tests and build. Compare failures against the current local baseline; do not fix unrelated failures.

After a successful build, reload/restart only the existing TCRM PM2 app (`tamiyouz-crm`) so the running backend actually uses the applied code, then verify the process is healthy. Do not change PM2 configuration.

## Git safety

No commit, push, merge, reset, rebase, stash, checkout of project branches, or cleanup of unrelated files.

## Report

Return only:

- `ROOT_CAUSE_CONFIRMED=YES/NO`
- `FILES_CHANGED=`
- `DIRECT_OWNER=PASS/FAIL`
- `ACTIVE_ASSIGNEE=PASS/FAIL`
- `INACTIVE_ASSIGNEE=PASS/FAIL`
- `UNRELATED_AGENT=PASS/FAIL`
- `NO_PRIVILEGE_BROADENING=PASS/FAIL`
- `FOCUSED_TESTS=`
- `BUILD=`
- `PM2_RELOAD=`
- `RUNTIME_HEALTH=`
- `GIT_OPS=NONE`
- `DIFF_STAT=`
