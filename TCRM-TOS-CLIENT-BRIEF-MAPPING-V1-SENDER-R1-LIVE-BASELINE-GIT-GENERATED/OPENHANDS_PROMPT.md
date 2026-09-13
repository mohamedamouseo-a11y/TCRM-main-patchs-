# TCRM → TOS Client Brief Mapping V1 Sender R1 — Live Baseline

MODE=IMPLEMENTATION_WITH_VERIFICATION

You are already inside the real live TCRM project on the server at `/var/www/TTCRM`.
TOS is on a separate server and its `crmHandoverBrief` receiver is already deployed.

## Goal
Apply the structured Client Handover Brief sender to the **current live TTCRM baseline** without depending on the old `VERIFIED_PROJECT_SYNC_VERSION` anchor.

The patch must:
- add `crmHandoverBrief` to the root TOS project payload,
- build it from the existing `SALES_BRIEF_FIELDS` allow-list plus sanitized `accountManagerBrief`,
- preserve existing `salesBrief` and `accountManagerBrief` behavior,
- preserve client identity/project owner mapping,
- make no DB/schema changes,
- run no sync and no deploy yet.

## Pre-check

From `/var/www/TTCRM`, inspect:

`server/services/tosIntegrationService.ts`

Confirm these semantic anchors exist:
- `SALES_BRIEF_FIELDS`
- `redactBriefText`
- `buildSalesBriefSummary`
- `buildProjectPayloadFromClientProfile`
- `const salesBrief = buildSalesBriefSummary(handoverBrief);`

Do **not** require `VERIFIED_PROJECT_SYNC_VERSION`; the previous patch failed because that anchor is not present on this live baseline.

If any semantic anchor above is missing, STOP and report `BASELINE_MISMATCH`.

## Apply

```bash
cd /var/www/TTCRM

curl -fsSL \
https://raw.githubusercontent.com/mohamedamouseo-a11y/TCRM-main-patchs-/d1a88f2cb88bc39526c0b120001f82d8b61c54fc/TCRM-TOS-CLIENT-BRIEF-MAPPING-V1-SENDER-R1-LIVE-BASELINE-GIT-GENERATED/apply_patch.py \
-o /tmp/tcrm_tos_client_brief_sender_r1.py

TCRM_REPO=/var/www/TTCRM \
python3 /tmp/tcrm_tos_client_brief_sender_r1.py
```

If the runner prints `STATUS=ABORT`, stop immediately. Do not bypass it with manual edits.

## Verification

Run:

```bash
cd /var/www/TTCRM
npm run build
git diff -- server/services/tosIntegrationService.ts
```

Confirm by source inspection:

1. `crmHandoverBrief` is present in the **root** project payload.
2. `schemaVersion` is `TCRM_CLIENT_HANDOVER_BRIEF_V1`.
3. Structured fields are derived only from the existing `SALES_BRIEF_FIELDS` allow-list plus sanitized `accountManagerBrief`.
4. No contact/payment/meta identifier fields were newly added as structured fields.
5. Existing `salesBrief` root payload remains.
6. Existing `accountManagerBrief` root payload remains if it existed before.
7. Existing `crmClientId`, `crmProjectId`, project owner, project manager/account manager mapping logic is unchanged.
8. No DB/schema files changed.
9. No sync was executed.

## Do not do

Do NOT:
- deploy,
- restart services,
- run TCRM→TOS sync,
- run batch/cron sync,
- modify database data,
- modify schema/migrations,
- modify TOS,
- git fetch/pull/push/reset/checkout/clean/rebase/merge.

## Final report

```text
PATCH=TCRM-TOS-CLIENT-BRIEF-MAPPING-V1-SENDER-R1-LIVE-BASELINE-GIT-GENERATED
MODE=IMPLEMENTATION_WITH_VERIFICATION
PROJECT_PATH=...
LOCAL_HEAD=...

BASELINE_CONFIRMED=YES|NO
PATCH_RUNNER_STATUS=APPLIED|ALREADY_APPLIED|ABORT

CRM_HANDOVER_BRIEF_ROOT_PAYLOAD=YES|NO
CRM_HANDOVER_BRIEF_SCHEMA_VERSION=TCRM_CLIENT_HANDOVER_BRIEF_V1|NO
ALLOWLIST_BASE=SALES_BRIEF_FIELDS|NO
ACCOUNT_MANAGER_BRIEF_INCLUDED=YES|NO

CONTACT_FIELDS_ADDED_AS_STRUCTURED_FIELDS=NO|YES
PAYMENT_STATUS_ADDED_AS_STRUCTURED_FIELD=NO|YES
INTERNAL_METADATA_ADDED_AS_STRUCTURED_FIELDS=NO|YES
MAX_JSON_CHARS=45000|NO

EXISTING_SALES_BRIEF_PRESERVED=YES|NO
EXISTING_AM_BRIEF_PRESERVED=YES|NO|NOT_PRESENT_BEFORE
CLIENT_IDENTITY_MAPPING_PRESERVED=YES|NO
PROJECT_OWNERS_MAPPING_PRESERVED=YES|NO

FILES_CHANGED=...
BUILD=PASS|FAIL
DATABASE_SCHEMA_CHANGED=NO
PROJECT_DATA_CHANGED=NO
SYNC_EXECUTED=NO
DEPLOY=NOT_RUN
SERVICE_RESTART=NO
GIT_PUSH=NO
FINAL_STATUS=PASS|FAIL
```

Then include the full `git diff -- server/services/tosIntegrationService.ts`.
