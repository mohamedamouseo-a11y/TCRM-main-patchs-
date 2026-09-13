# TCRM → TOS Client Brief Mapping V1 — Sender

This patch updates only:

`server/services/tosIntegrationService.ts`

It adds a sanitized structured `crmHandoverBrief` object to the existing TCRM → TOS project payload.

Behavior:
- existing `salesBrief` remains unchanged;
- existing `accountManagerBrief` remains unchanged;
- structured brief uses the existing `SALES_BRIEF_FIELDS` allow-list plus sanitized `accountManagerBrief`;
- contact/payment/internal metadata and TOS project-owner selections are excluded from the structured brief;
- `schemaVersion = TCRM_CLIENT_HANDOVER_BRIEF_V1`;
- sender caps the structured JSON below the TOS receiver limit;
- no DB/schema changes;
- no sync, deploy, restart, or git push is performed by the patch runner.

The patch is intended to be applied on the live TCRM server only after the TOS `crmHandoverBrief` JSON receiver field/migration has been deployed.
