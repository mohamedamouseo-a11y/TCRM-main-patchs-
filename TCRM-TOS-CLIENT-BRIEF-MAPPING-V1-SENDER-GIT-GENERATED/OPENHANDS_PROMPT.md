# TCRM → TOS Client Brief Mapping V1 — Sender

MODE=IMPLEMENTATION_WITH_VERIFICATION

You are already inside the live TCRM project on the TCRM server at `/var/www/TCRM-MAIN`.
TOS is on a different server and its receiver/database migration has already been deployed.

## Goal
Add the structured Client Handover Brief to the existing TCRM → TOS project payload only.

The sender must:
- keep the current `salesBrief` and `accountManagerBrief` behavior unchanged;
- add root payload field `crmHandoverBrief` when a handover brief exists;
- use a strict allow-list based on the existing `SALES_BRIEF_FIELDS` plus sanitized `accountManagerBrief`;
- exclude contact fields, payment fields, submitter/internal metadata, timestamps, and `tosProjectOwners` from this JSON brief;
- reuse the existing brief redaction/sanitization logic;
- keep JSON under the TOS receiver limit;
- make no DB/schema changes.

Do not deploy or run a real sync yet.

## 1. Pre-check

From `/var/www/TCRM-MAIN`, inspect:

`server/services/tosIntegrationService.ts`

Confirm these live baseline anchors exist:

- `VERIFIED_PROJECT_SYNC_VERSION = "TCRM_TOS_LEAD_NAME_VERIFIED_SYNC_AM_TASKS_V3"`
- `SALES_BRIEF_FIELDS`
- `redactBriefText`
- `buildSalesBriefSummary`
- `buildProjectPayloadFromClientProfile`
- `const handoverBrief = await getHandoverBrief(clientId);`
- root payload currently contains `salesBrief` and `accountManagerBrief`
- root payload does NOT already contain `crmHandoverBrief`

If any required baseline is different, STOP and report `BASELINE_MISMATCH`. Do not manually adapt the patch.

## 2. Apply patch

```bash
cd /var/www/TCRM-MAIN

curl -fsSL \
https://raw.githubusercontent.com/mohamedamouseo-a11y/TCRM-main-patchs-/fc72d773fdd18c8144a4ec45045cc15a630dd091/TCRM-TOS-CLIENT-BRIEF-MAPPING-V1-SENDER-GIT-GENERATED/apply_patch.py \
-o /tmp/tcrm_tos_client_brief_sender_v1.py

TCRM_REPO=/var/www/TCRM-MAIN \
python3 /tmp/tcrm_tos_client_brief_sender_v1.py
```

If the runner prints `STATUS=ABORT`, stop immediately. Do not edit manually to bypass its guards.

## 3. Verification

Inspect the changed source and run:

```bash
cd /var/www/TCRM-MAIN
npm run build
git diff -- server/services/tosIntegrationService.ts
```

Confirm all of the following:

1. `crmHandoverBrief` is added at the root of the TOS project payload only when a structured brief exists.
2. `schemaVersion` is `TCRM_CLIENT_HANDOVER_BRIEF_V1`.
3. The structured brief uses the existing `SALES_BRIEF_FIELDS` allow-list.
4. `accountManagerBrief` is included only after the existing redaction/sanitization.
5. These are NOT copied into `crmHandoverBrief`:
   - `id`
   - `clientId`
   - `submittedByUserId`
   - `submittedByName`
   - contact person / phone / WhatsApp fields
   - `paymentStatus`
   - account-manager updater IDs/names/timestamps
   - `createdAt` / `updatedAt`
   - `tosProjectOwners`
6. Existing `salesBrief` stays unchanged.
7. Existing `accountManagerBrief` stays unchanged.
8. Existing project name, client identity, owners, status/stage and verification logic stay unchanged.
9. No DB/schema files changed.
10. No sync was executed.

## 4. Do not do

Do NOT:
- deploy
- restart services
- execute a TCRM → TOS sync
- run batch/cron sync
- modify DB data
- modify schema/migrations
- change TOS server/code
- git fetch/pull/push/reset/checkout/clean/rebase/merge

## 5. Final report

Return:

```text
PATCH=TCRM-TOS-CLIENT-BRIEF-MAPPING-V1-SENDER-GIT-GENERATED
MODE=IMPLEMENTATION_WITH_VERIFICATION
PROJECT_PATH=...
LOCAL_HEAD=...

BASELINE_CONFIRMED=YES|NO
PATCH_RUNNER_STATUS=APPLIED|ALREADY_APPLIED|ABORT

CRM_HANDOVER_BRIEF_ROOT_PAYLOAD=YES|NO
CRM_HANDOVER_BRIEF_SCHEMA_VERSION=TCRM_CLIENT_HANDOVER_BRIEF_V1|NO
ALLOWLIST_BASE=SALES_BRIEF_FIELDS|NO
ACCOUNT_MANAGER_BRIEF_INCLUDED=YES|NO
CONTACT_FIELDS_INCLUDED=NO|YES
PAYMENT_FIELDS_INCLUDED=NO|YES
INTERNAL_METADATA_INCLUDED=NO|YES
TOS_PROJECT_OWNERS_INCLUDED_IN_BRIEF=NO|YES
MAX_JSON_CHARS=45000|NO

EXISTING_SALES_BRIEF_PRESERVED=YES|NO
EXISTING_AM_BRIEF_PRESERVED=YES|NO
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
