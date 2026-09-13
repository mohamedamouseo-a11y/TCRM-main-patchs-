# TCRM → TOS Client Brief Mapping V1 Sender R1 — Live Baseline

This patch is a live-baseline follow-up for `/var/www/TTCRM` after the earlier sender patch aborted on stale anchors.

It changes only `server/services/tosIntegrationService.ts` and adds a structured `crmHandoverBrief` to the root TOS project payload.

Safety characteristics:
- uses existing `SALES_BRIEF_FIELDS` as the structured allow-list,
- includes sanitized `accountManagerBrief`,
- does not add contact/payment/internal metadata fields as structured fields,
- caps the structured JSON at 45,000 characters,
- preserves existing sales brief / AM brief / identity / owner logic,
- no DB or schema changes,
- no sync, deploy, restart, or git push.

Runner commit pinned by the OpenHands prompt: `d1a88f2cb88bc39526c0b120001f82d8b61c54fc`.
