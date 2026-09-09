# OpenHands — TCRM → TOS Project Integration Audit V1

Execute this exactly. This is a **READ-ONLY audit**, not a fix.

## Goal

Find the real TCRM → TOS project-sync execution path and produce evidence for why duplicate TOS projects can be created.

We specifically need evidence for:

1. Exact TCRM source file(s) and function(s) that send/sync projects to TOS.
2. Exact TOS endpoint/request path and payload fields.
3. Where `crmProjectId`, `crmDealId`, and `crmClientId` come from, if present.
4. Whether there is any batch/backfill/force/retry/replay behavior.
5. Whether retries use a stable idempotent identity or can produce a different identity.
6. Whether TCRM stores a durable `tosProjectId` / TOS mapping.
7. Any safe log/git/runtime evidence around **2026-08-15** that may explain a bulk sync/retry.
8. Whether live server source/runtime evidence differs from the approved GitHub HEAD.

## Absolute rules

- DO NOT edit any TCRM file.
- DO NOT edit any TOS file.
- DO NOT run build.
- DO NOT deploy.
- DO NOT restart any service/container/process.
- DO NOT run database mutation.
- DO NOT run `INSERT`, `UPDATE`, `DELETE`, `CREATE`, `ALTER`, `DROP`, `TRUNCATE`, `REPLACE`, `MERGE`, `GRANT`, or `REVOKE`.
- DO NOT execute any sync/force/backfill/retry script even if you find one. Read/grep only.
- DO NOT send POST/PUT/PATCH/DELETE requests.
- DO NOT run `git reset`, `checkout`, `restore`, `clean`, `pull`, `merge`, `rebase`, `commit`, or `push`.
- DO NOT reset unrelated dirty files. Dirty files are allowed and must be preserved.
- DO NOT print `.env` values, tokens, passwords, API keys, authorization headers, JWTs, emails, or phone numbers.
- Production audit evidence must never be committed to GitHub.

## Approved baseline

Expected TCRM `main` HEAD:

`b016f9ada07e334b47bf95a19a59e667b7351b1b`

The runner is pinned to the approved patch commit:

`80ba3a534fa97beabe2a68cf4272a6101828da2a`

## Execute

Run from the TCRM server:

```bash
curl -fsSL \
  https://raw.githubusercontent.com/mohamedamouseo-a11y/TCRM-main-patchs-/80ba3a534fa97beabe2a68cf4272a6101828da2a/TCRM-TOS-PROJECT-INTEGRATION-AUDIT-V1-GIT-GENERATED/run_tcrm_tos_project_integration_audit_v1.py \
  -o /tmp/run_tcrm_tos_project_integration_audit_v1.py

python3 /tmp/run_tcrm_tos_project_integration_audit_v1.py
```

The runner auto-detects the TCRM repo. If needed, supply only the repository path:

```bash
TCRM_REPO=/actual/path/to/TCRM python3 /tmp/run_tcrm_tos_project_integration_audit_v1.py
```

Do not set or expose any other environment values.

## If baseline mismatch happens

STOP immediately.

Do not modify anything and do not try to make the server match the expected commit.
Return exactly the mismatch plus `git status --porcelain` summary already produced by the runner.

## Reports

The only files this audit is allowed to write are:

- `/tmp/tcrm_tos_project_integration_audit_v1.txt`
- `/tmp/tcrm_tos_project_integration_audit_v1.json`
- `/tmp/run_tcrm_tos_project_integration_audit_v1.py`

Do not copy those reports into the repository.

After the runner finishes, read the sanitized text report:

```bash
cat /tmp/tcrm_tos_project_integration_audit_v1.txt
```

## Final response required

Paste a concise sanitized Final Report containing:

```text
PATCH=TCRM-TOS-PROJECT-INTEGRATION-AUDIT-V1-GIT-GENERATED
MODE=READ_ONLY
HEAD=...
BASELINE=PASS|FAIL
DIRTY_FILES_ALLOWED=...

TCRM_TO_TOS_SENDER_FILES=...
TCRM_TO_TOS_SENDER_FUNCTIONS=...
TOS_ENDPOINT=...
PAYLOAD_ID_FIELDS=...
CRM_PROJECT_ID_SOURCE=...
CRM_DEAL_ID_SOURCE=...
CRM_CLIENT_ID_SOURCE=...
DURABLE_TOS_PROJECT_MAPPING=YES|NO|UNKNOWN
RETRY_OR_BACKFILL_FOUND=YES|NO|UNKNOWN
RETRY_IDEMPOTENCY=STABLE|UNSTABLE|UNKNOWN
AUG_15_EVIDENCE=...
LIVE_VS_GITHUB_EVIDENCE=...

MOST_LIKELY_DUPLICATE_PATH=...
EVIDENCE_CONFIDENCE=HIGH|MEDIUM|LOW

SOURCE_CHANGES=NO
DB_MUTATION=NO
BUILD=NOT_RUN
DEPLOY=NOT_RUN
SERVICE_RESTART=NO
GIT_PUSH=NO
AUDIT_STATUS=PASS_READ_ONLY|ABORTED_BASELINE_MISMATCH
```

For conclusions that the runner cannot prove, write `UNKNOWN`. Do not guess.

Also include the top relevant source locations as `file:line` references and only short sanitized snippets. Do not paste secrets or production personal data.
