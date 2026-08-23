# TCRM — Sales Agent Service Handover Card V1

Fix for the missing **Complete Service Handover / إكمال تسليم الخدمات** card on a Won Lead when the owning user is `SalesAgent` or `ColdSalesAgent`.

## Confirmed production root cause

`client/src/pages/LeadProfile.tsx` renders the handover card only when `clientByLeadQ.data` exists. That query calls `accountManagement.getClientByLeadId`.

The existing router requested `client.read.full`, but the Account Management policy intentionally does not grant `client.read.full` to Sales Agents. The policy check happened before the valid lead-owner relationship could help, so the owning Sales Agent received a `FORBIDDEN` response and the handover card disappeared.

The separate workflow route already authorizes the same Sales Agent as `sales_owner` for `workflow.read` and `workflow.submit`.

## Fix design

The patch changes only `server/routers.ts`.

For `SalesAgent` / `ColdSalesAgent`, `accountManagement.getClientByLeadId` now:

1. Reuses the existing `workflow.read` authorization check for the converted client.
2. Requires the caller to satisfy the existing sales-owner relationship.
3. Returns only the narrow fields the Lead Profile needs:
   - `id`
   - `handoverStatus`
   - `briefStatus`

It does **not** grant `client.read.full`, `client.read.summary`, or broader Account Management visibility to Sales Agents.

All other roles keep their existing behavior.

## Application source changed

- `server/routers.ts`

No frontend, database, migration, Google Drive, workflow, or global role-policy changes are required.

## Apply

From the TCRM project root:

```bash
node <PATCH_REPO>/patches/sales/sales-agent-service-handover-card-v1/apply.mjs --check
node <PATCH_REPO>/patches/sales/sales-agent-service-handover-card-v1/apply.mjs --apply
node <PATCH_REPO>/patches/sales/sales-agent-service-handover-card-v1/apply.mjs --verify
```

Then run the normal project typecheck/build and production deployment procedure.

## Required regression tests

- Owning Sales Agent on a Won Lead sees the Service Handover card and can open the workflow.
- Admin behavior is unchanged.
- Sales Manager behavior is unchanged.
- A Sales Agent requesting a converted client that belongs to another Sales Agent remains denied.
- No broader Account Management client access is introduced.
