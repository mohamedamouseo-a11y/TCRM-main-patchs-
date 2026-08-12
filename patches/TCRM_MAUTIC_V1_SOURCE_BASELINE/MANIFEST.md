# TCRM_MAUTIC_V1_SOURCE_BASELINE

Target: `/var/www/TCRM-MAIN`

## Purpose
Import a pinned, reviewable Mautic source baseline into TCRM Main at `external/mautic` so TCRM can build a customized marketing edition from upstream source without activating Mautic in production yet.

## Upstream lock
- Project: `mautic/mautic`
- Version/tag: `7.1.2`
- Commit: `789364ee4aaf8aef5e6d91642336c1f446d5521b`
- License: GPL-3.0
- Reason for 7.1.2: security release containing fixes for multiple published vulnerabilities, including SQL injection, SSRF, SSTI, path traversal, authorization bypass, and stored XSS issues addressed after 7.1.1.

## What APPLY.sh changes
- Requires a clean TCRM Main git worktree.
- Requires PHP 8.2+, Composer, Node/npm, pnpm, Git, and at least 1 GiB free disk space.
- Runs `pnpm check` and `pnpm build` before any mutation.
- Shallow-clones the exact Mautic `7.1.2` tag from the official upstream repository.
- Verifies the clone resolves to the exact locked commit.
- Validates Mautic Composer metadata and GPL-3.0 license metadata.
- Removes only the nested `.git` directory so the parent TCRM repository can track the imported source.
- Adds a bounded `.gitignore` exception for `external/mautic` and verifies every upstream-tracked source file remains trackable, while Mautic runtime `vendor/` and `node_modules/` remain ignored.
- Adds `external/mautic/TCRM_UPSTREAM.lock` with immutable provenance metadata.
- Runs TCRM typecheck/build again after import.
- Leaves Mautic unconfigured and unexposed.

## Explicit non-changes
- No TCRM database migration.
- No Mautic database creation or migration.
- No Nginx/Apache change.
- No systemd/PM2/process change.
- No cron change.
- No SMTP/mail change.
- No secrets or credentials are created, read, copied, or committed.
- No TCRM application route or UI is changed.
- No automatic push to GitHub.

## Rollback
`ROLLBACK.sh` removes only the V1 source baseline and refuses to run if a later patch has marked the source as customized.

## Production gate
This patch is intentionally a source-foundation patch. `RUNTIME_ACTIVATED=NO` is required for success. Production exposure will be a separate patch after database, web-server, TLS, queue/cron, backup, and integration design are reviewed independently.

## Success marker
`TCRM_MAUTIC_V1_SOURCE_BASELINE_OK`
