# TCRM TEM Phase 4 — Production Activation

Target: `/var/www/TCRM-MAIN`

This patch moves TEM from the safe Mautic foundation into a production-ready, explicitly gated sending state without committing secrets and without exposing raw Mautic publicly.

## Baseline

Expected TCRM TEM baseline is the version pushed after the TEM sanitization/security cleanup. The patch does **not** switch branches, pull, reset, rebase, commit, or push.

Pinned upstream Mautic:
- Version: `7.1.3`
- Commit: `27a76aff64aed8e50f6dd784ea86ec95d45d4616`
- Runtime remains internal on `127.0.0.1:8089`

## Changes

1. `server/tem/temRouter.ts`
   - production status without exposing secrets
   - bounded/idempotent BD contact batch sync (max 100/request)
   - bounded legacy suppression migration into Mautic Do-Not-Contact (max 100/request)
   - controlled single-recipient test send only; recipient must exactly match `TEM_CONTROLLED_TEST_RECIPIENT`
   - no bulk-send API is added

2. `server/emailMarketing.ts`
   - legacy campaign sender is blocked when `TEM_PRIMARY_EMAIL_ENGINE=YES`
   - tracking/unsubscribe/history remain intact
   - emergency override exists only through runtime flag `LEGACY_EMAIL_MARKETING_SEND_OVERRIDE=YES`

3. `services/tem-mautic/docker-compose.yml`
   - mailer DSN becomes runtime-env driven; default remains `null://null`
   - worker remains opt-in and also joins the `production` profile
   - production scheduler is added using the official required Mautic commands (`mautic:segments:update`, `mautic:campaigns:update`, `mautic:campaigns:trigger`, `mautic:messages:send`)
   - scheduled broadcast sending runs only when `TEM_BULK_SEND_APPROVED=YES`

4. Runtime helpers
   - `services/tem-mautic/phase4-activate.sh`
   - `services/tem-mautic/phase4-disable.sh`

## Required runtime flags

Secrets stay outside Git. The scripts read `/etc/tcrm-tem/tem.env` and `/etc/tcrm-tem/tcrm.env`.

Required before controlled test preparation:
- `MAUTIC_MAILER_DSN=<real provider DSN>` in `tem.env`
- `TEM_PRODUCTION_ACTIVATION_APPROVED=YES`
- `TEM_CONTROLLED_TEST_RECIPIENT=<one controlled email>`
- `TEM_PRIMARY_EMAIL_ENGINE=YES`

Optional migration gates:
- `TEM_PHASE4_CONTACT_SYNC_APPROVED=YES`
- `TEM_PHASE4_SUPPRESSION_SYNC_APPROVED=YES`

Required before starting production workers/scheduler:
- `TEM_CONTROLLED_TEST_PASSED=YES`
- `TEM_BULK_SEND_APPROVED=YES`

The activation script never prints DSNs, passwords, API credentials, or the controlled recipient value.

## Apply

```bash
bash patches/TCRM_TEM_PHASE4_PRODUCTION_ACTIVATION/APPLY.sh
```

Expected marker:

```text
FINAL_MARKER=TCRM_TEM_PHASE4_PATCH_APPLIED_OK
```

## Controlled activation

After applying the patch and setting the runtime flags/secrets:

```bash
bash services/tem-mautic/phase4-activate.sh prepare
```

This recreates only the Mautic app with the configured live transport, keeps worker/scheduler stopped, backs up the Mautic DB, and leaves bulk sending disabled.

Perform the controlled single-recipient test through the new TEM production API. Only the exact configured controlled recipient is accepted.

After the controlled test is verified, set `TEM_CONTROLLED_TEST_PASSED=YES` and `TEM_BULK_SEND_APPROVED=YES`, then:

```bash
bash services/tem-mautic/phase4-activate.sh enable
```

## Disable production processing

```bash
bash services/tem-mautic/phase4-disable.sh
```

This stops the worker/scheduler and restores the backed-up runtime Compose file when available. It does not delete data.

## Verify

```bash
bash patches/TCRM_TEM_PHASE4_PRODUCTION_ACTIVATION/VERIFY.sh
```

Expected marker:

```text
FINAL_MARKER=TCRM_TEM_PHASE4_VERIFY_OK
```

## Rollback patch source changes

```bash
bash patches/TCRM_TEM_PHASE4_PRODUCTION_ACTIVATION/ROLLBACK.sh
```

Expected marker:

```text
FINAL_MARKER=TCRM_TEM_PHASE4_ROLLBACK_OK
```

## Safety

- No real recipient is hard-coded.
- No SMTP/API/database secret is committed.
- No raw Mautic public route is created.
- No legacy history/table is dropped or deleted.
- Migrations are bounded and opt-in.
- Full Mautic upstream source remains ignored by the TCRM Git repository.
- No GitHub push is performed by this patch.