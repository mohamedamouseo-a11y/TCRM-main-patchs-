# TCRM — Sales Agent Service Handover Card V1.1

Corrective patch for the missing **Complete Service Handover / إكمال تسليم الخدمات** card for the owning `SalesAgent` / `ColdSalesAgent`.

## Why V1 still returned 403

V1 added the correct scoped authorization branch inside `accountManagement.getClientByLeadId`, but the procedure still used `clientOpsProcedure`.

`clientOpsProcedure` itself rejects any role outside:

- Admin
- SalesManager
- AccountManager
- AccountManagerLead

with `FORBIDDEN: Client read access required` **before the handler executes**.

Therefore the V1 SalesAgent branch and `workflow.read` owner check were unreachable.

## V1.1 fix

Only `accountManagement.getClientByLeadId` is changed from:

`clientOpsProcedure`

to:

`protectedProcedure`

The handler then performs its own existing role-specific authorization:

- SalesManager → existing summary path.
- SalesAgent / ColdSalesAgent → existing `workflow.read` owner authorization and narrow DTO only.
- Admin / AccountManager / AccountManagerLead → existing `client.read.full` authorization.
- Other authenticated roles → denied by the existing in-handler access guard.

The SalesAgent response remains limited to:

- `id`
- `handoverStatus`
- `briefStatus`

No global client permission is broadened.

## Scope

Application source changed:

- `server/routers.ts`

No frontend changes, DB changes, migrations, global permission changes, or Account Management list-access changes.

## Apply

From the live TCRM project root:

```bash
node <PATCH_REPO>/patches/sales/sales-agent-service-handover-card-v1.1/apply.mjs --check
node <PATCH_REPO>/patches/sales/sales-agent-service-handover-card-v1.1/apply.mjs --apply
node <PATCH_REPO>/patches/sales/sales-agent-service-handover-card-v1.1/apply.mjs --verify
```

Then build/reload with the existing production procedure.

## Required tests

1. Mohamed Hamed (SalesAgent 130) on owned Won Lead 1995 receives client 115 narrow handover DTO and sees the Service Handover card.
2. `/clients/115/workflow` continues to open for Mohamed.
3. Another SalesAgent cannot retrieve a client converted from a Lead they do not own.
4. Admin behavior remains unchanged.
5. SalesManager summary behavior remains unchanged when a valid SalesManager test account is available.
6. `client.read.full` and `client.read.summary` are still not granted globally to SalesAgent/ColdSalesAgent.
