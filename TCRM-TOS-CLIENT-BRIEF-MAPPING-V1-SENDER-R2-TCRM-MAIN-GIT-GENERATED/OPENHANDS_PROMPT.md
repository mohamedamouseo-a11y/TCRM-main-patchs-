# TCRM → TOS Client Brief Mapping V1 — Sender R2 (Real TCRM Main)

Run this only on the real TCRM server/project:

`/var/www/TCRM-MAIN`

Do not touch `/var/www/TTCRM`.

## Goal

Add a sanitized structured `crmHandoverBrief` object to the existing TCRM → TOS project payload while preserving existing `salesBrief`, `accountManagerBrief`, client identity mapping, project owners behavior, database schema, and runtime behavior.

## Instructions

```text
TCRM → TOS CLIENT BRIEF MAPPING V1 — SENDER R2 REAL TCRM MAIN

PROJECT_PATH=/var/www/TCRM-MAIN
MODE=IMPLEMENTATION_WITH_VERIFICATION

Important:
- This is the real TCRM project.
- /var/www/TTCRM is a different project. Do not enter or modify it.
- TOS is on another server and its crmHandoverBrief receiver is already deployed.
- Do not deploy or sync in this phase.

1) Pre-check

cd /var/www/TCRM-MAIN

Print:
pwd
git rev-parse HEAD
git status --short

Confirm:
PROJECT_PATH=/var/www/TCRM-MAIN

Inspect:
server/services/tosIntegrationService.ts

Confirm all of these exist:
- const VERIFIED_PROJECT_SYNC_VERSION = "TCRM_TOS_LEAD_NAME_VERIFIED_SYNC_AM_TASKS_V3";
- const SALES_BRIEF_FIELDS:
- function redactBriefText(value: unknown)
- function buildSalesBriefSummary(brief: any)
- function buildProjectPayloadFromClientProfile(profile: any, handoverBrief: any = null)
- crmProjectId: `crm-client-${client.id}`
- crmClientId: String(client.id)
- projectOwnersSyncMode: "ADD_ONLY"

Confirm structured crmHandoverBrief is NOT already present in the outbound payload.

If baseline differs, STOP and report BASELINE_MISMATCH. Do not modify manually.

2) Download patch

curl -fsSL \
https://raw.githubusercontent.com/mohamedamouseo-a11y/TCRM-main-patchs-/5769cb5f92cd29c818b1643f09bbbbd8395bf8f6/TCRM-TOS-CLIENT-BRIEF-MAPPING-V1-SENDER-R2-TCRM-MAIN-GIT-GENERATED/apply_patch.py \
-o /tmp/tcrm_client_brief_sender_r2.py

3) Apply

TCRM_REPO=/var/www/TCRM-MAIN \
python3 /tmp/tcrm_client_brief_sender_r2.py

If STATUS=ABORT, stop immediately. Do not patch manually.

4) Verification

Run:

git diff -- server/services/tosIntegrationService.ts
npm run build

Verify the diff does only the following:

- Adds CRM_HANDOVER_BRIEF_SYNC_VERSION = TCRM_CLIENT_HANDOVER_BRIEF_V1.
- Adds a strict structured brief builder based on SALES_BRIEF_FIELDS.
- Adds sanitized accountManagerBrief into the structured object.
- Adds crmHandoverBrief to the root project payload.
- Sends crmHandoverBrief=null when no current handover brief exists, so TOS can clear stale structured data explicitly.
- Keeps the structured JSON under 45000 chars, below the TOS 50000 receiver guard.
- Does NOT add contact fields as structured fields.
- Does NOT add paymentStatus as a structured field.
- Does NOT add submitter/updater IDs, names, timestamps, or tosProjectOwners into crmHandoverBrief.
- Existing salesBrief behavior remains unchanged.
- Existing accountManagerBrief root field remains unchanged.
- crmProjectId / crmClientId logic remains unchanged.
- projectOwners and ADD_ONLY behavior remain unchanged.
- No database/schema changes.

5) Forbidden

Do NOT:
- deploy
- restart services
- run TCRM → TOS sync
- run batch/cron sync
- change database or schema
- modify TOS
- touch /var/www/TTCRM
- git pull/fetch/push/reset/checkout/clean/rebase/merge

6) Final report

PATCH=TCRM-TOS-CLIENT-BRIEF-MAPPING-V1-SENDER-R2-TCRM-MAIN-GIT-GENERATED
MODE=IMPLEMENTATION_WITH_VERIFICATION
PROJECT_PATH=
LOCAL_HEAD=
TCRM_REAL_PROJECT=YES|NO
TTCRM_TOUCHED=NO

BASELINE_CONFIRMED=YES|NO
PATCH_RUNNER_STATUS=APPLIED|ALREADY_APPLIED|ABORT

CRM_HANDOVER_BRIEF_ROOT_PAYLOAD=YES|NO
CRM_HANDOVER_BRIEF_SCHEMA_VERSION=TCRM_CLIENT_HANDOVER_BRIEF_V1|NO
ALLOWLIST_BASE=SALES_BRIEF_FIELDS|NO
ACCOUNT_MANAGER_BRIEF_INCLUDED=YES|NO
NULL_CLEAR_BEHAVIOR=YES|NO

CONTACT_FIELDS_ADDED_AS_STRUCTURED_FIELDS=NO|YES
PAYMENT_STATUS_ADDED_AS_STRUCTURED_FIELD=NO|YES
INTERNAL_METADATA_ADDED_AS_STRUCTURED_FIELDS=NO|YES
TOS_PROJECT_OWNERS_INCLUDED_IN_BRIEF=NO|YES
MAX_JSON_CHARS=45000|NO

EXISTING_SALES_BRIEF_PRESERVED=YES|NO
EXISTING_AM_BRIEF_PRESERVED=YES|NO
CLIENT_IDENTITY_MAPPING_PRESERVED=YES|NO
PROJECT_OWNERS_MAPPING_PRESERVED=YES|NO

FILES_CHANGED=
BUILD=PASS|FAIL
DATABASE_SCHEMA_CHANGED=NO
PROJECT_DATA_CHANGED=NO
SYNC_EXECUTED=NO
DEPLOY=NOT_RUN
SERVICE_RESTART=NO
GIT_PUSH=NO
FINAL_STATUS=PASS|FAIL

Finally print:
git diff -- server/services/tosIntegrationService.ts
```
