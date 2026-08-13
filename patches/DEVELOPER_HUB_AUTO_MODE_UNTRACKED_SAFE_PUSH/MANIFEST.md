# DEVELOPER_HUB_AUTO_MODE_UNTRACKED_SAFE_PUSH

Target: `/var/www/TCRM-MAIN`

## Problem
Developer Hub Auto Push blocks every untracked file with `unexpected untracked file is not allowed in Auto mode`. This prevents legitimate new source trees (current case: Zaghloul/WACRM) from being reviewed and pushed.

## Goal
Keep Auto mode fail-closed, but allow **safe new source files** after classification and security checks.

## Required behavior
- Preserve existing tracked-file flow and Verify / Tests / Build gates.
- Read Git status robustly (prefer porcelain `-z`).
- Honor `.gitignore`.
- New files must be regular files only; reject symlinks/special files.
- Reject secrets/credentials and sensitive names: `.env`, private keys/certs, tokens/credentials, or existing secret-scanner matches. Never print secret values.
- Reject generated/runtime/cache/temp/log/upload/build artifacts as appropriate.
- If any candidate is unsafe, block the **entire** push.
- Stage only the exact reviewed safe paths. Never use `git add -A` or broad equivalent.
- Verify staged paths exactly equal the reviewed candidate set before commit/push.
- Paths with spaces/Unicode and large sets (>=441 files) must work.
- No force push or policy bypass.

## Scope
Patch only Developer Hub Git synchronization/push logic and focused tests/helpers needed for this fix. Do not modify Zaghloul, migrations, dependencies, package manifests, or lockfiles.

## Deployment safety
- `APPLY.sh` is preflight only and does not mutate source.
- OpenHands must back up the exact files it edits under the temporary workspace before mutation and provide rollback.
- `VERIFY.sh` must independently rerun fixture tests, compare TSC diagnostics to baseline, build, reload the existing PM2 process only after all gates pass, verify HTTP, and prove no Git commit/push happened during patching.

## Required fixture proofs
1. tracked modified file accepted
2. safe untracked source accepted
3. `.env` rejected
4. private key/credential rejected
5. symlink rejected
6. ignored/runtime files not staged
7. mixed safe + unsafe set blocks all
8. spaces + Unicode paths work
9. >=441 safe new files work
10. exact staged-set equality
11. no broad `git add -A`/equivalent
12. no real Git push during fixtures

Success only when:
`DEVELOPER_HUB_AUTO_MODE_UNTRACKED_SAFE_PUSH_OK`
