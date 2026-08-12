# TCRM_MAUTIC_V1_SOURCE_BASELINE

Target: `/var/www/TCRM-MAIN`

## Purpose
Import a pinned, reviewable Mautic source baseline into TCRM Main at `external/mautic` so TCRM can build a customized marketing edition from upstream source without activating Mautic in production yet.

## Upstream lock
- Project: `mautic/mautic`
- Version/tag: `7.1.3`
- Commit: `27a76aff64aed8e50f6dd784ea86ec95d45d4616`
- License: GPL-3.0
- Reason for 7.1.3: current latest stable Mautic release as of 2026-08-12. It includes the 7.1.2 security fixes plus subsequent campaign, API, email, segment, builder, and reliability bug fixes from the 7.1.3 release.

## What APPLY.sh changes
- Requires a clean TCRM Main git worktree.
- Requires PHP 8.2–8.5, the official required PHP extensions (`xml`, MySQL via `mysqli` or `pdo_mysql`, `imap`, `zip`, `intl`, `curl`, `gd`, `mbstring`, `bcmath`), Composer, Node/npm, pnpm, Git, and at least 1 GiB free disk space.
- Runs `pnpm check` and `pnpm build` before any mutation and requires those checks to leave the TCRM worktree clean.
- Shallow-clones the exact Mautic `7.1.3` tag from the official upstream repository.
- Verifies the clone resolves to the exact locked commit.
- Validates Mautic Composer metadata and GPL-3.0 license metadata.
- Removes only the nested `.git` directory so the parent TCRM repository can track the imported source.
- Adds a bounded `.gitignore` exception for `external/mautic` and verifies every upstream-tracked source file remains trackable, while Mautic runtime `vendor/` and `node_modules/` remain ignored.
- Adds `external/mautic/TCRM_UPSTREAM.lock` with immutable provenance metadata and `TCRM_SOURCE_BASELINE.sha256` covering every upstream-tracked source file.
- Runs TCRM typecheck/build again after import and fails if either check creates any unexpected tracked or untracked source changes.
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

## Verification and rollback
`VERIFY.sh` checks the full SHA-256 source manifest, Mautic/TCRM prerequisites, TCRM typecheck/build, Git visibility, and that runtime dependency folders remain ignored. `ROLLBACK.sh` removes only an intact V1 source baseline and refuses to run if files drifted or a later patch has marked the source as customized.

## Production gate
This patch is intentionally a source-foundation patch. `RUNTIME_ACTIVATED=NO` is required for success. Production exposure will be a separate patch after database, web-server, TLS, queue/cron, backup, and integration design are reviewed independently.

## Success marker
`TCRM_MAUTIC_V1_SOURCE_BASELINE_OK`
