# TCRM → TOS Client Brief Mapping V1 — Sender R2

Target: real TCRM project only: `/var/www/TCRM-MAIN`.

This patch adds a sanitized structured `crmHandoverBrief` object to the existing TCRM → TOS project payload. It uses the existing approved `SALES_BRIEF_FIELDS` allow-list plus sanitized `accountManagerBrief`, keeps the JSON below 45,000 chars, and sends `null` when there is no current brief so TOS can explicitly clear stale structured brief data.

Preserved unchanged:
- existing `salesBrief`
- existing root `accountManagerBrief`
- `crmProjectId` and `crmClientId`
- project owner ADD_ONLY behavior
- database/schema

Excluded from the structured brief:
- contact fields
- payment status
- submitter/updater metadata
- timestamps
- TOS project owner assignments

The corresponding TOS receiver must already be deployed before enabling this sender.

Use `OPENHANDS_PROMPT.md` for implementation and verification. Do not deploy or sync during the patch-application phase.
