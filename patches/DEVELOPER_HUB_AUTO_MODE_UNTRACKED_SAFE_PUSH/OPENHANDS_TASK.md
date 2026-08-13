# OpenHands Task — DEVELOPER_HUB_AUTO_MODE_UNTRACKED_SAFE_PUSH

Target: `/var/www/TCRM-MAIN`
Patch repo: `https://github.com/mohamedamouseo-a11y/TCRM-main-patchs-`

Goal: fix Developer Hub Auto Push so safe untracked source files can pass review/push without weakening existing safeguards.

## Do
1. Run this patch `APPLY.sh`; stop if preflight fails.
2. Locate the exact Developer Hub code that emits `unexpected untracked file is not allowed in Auto mode` / handles Review+Push.
3. Change only that sync/push path plus focused tests/helpers.
4. Auto mode behavior:
   - parse Git status safely (NUL-delimited preferred)
   - keep tracked-file behavior unchanged
   - classify untracked files; honor `.gitignore`
   - allow only regular safe source/config/docs files after secret/runtime checks
   - reject symlink/special files, `.env`, key/cert/credential/token files, secret-scanner matches, generated/runtime/cache/log/temp/upload/build artifacts
   - any unsafe candidate blocks the whole push
   - stage exact reviewed paths only; no `git add -A`, `git add .`, `git add --all`, or broad equivalent
   - after staging, prove staged set exactly equals approved set before commit/push
5. Add focused fixture tests proving all 12 cases from MANIFEST.md, including >=441 safe untracked files and spaces/Unicode.
6. Do not push production Git during implementation/testing.
7. Do not modify Zaghloul, DB, dependencies, package manifests or lockfiles.
8. Run `VERIFY.sh`; success only on its final marker.

Required final output only:
PRECHECK
PATCHED_FILES
FIXTURE_TESTS
UNTRACKED_SAFE_ALLOW
SECRET_BLOCK
SYMLINK_BLOCK
RUNTIME_BLOCK
MIXED_SET_ATOMIC_BLOCK
LARGE_SET_441
EXACT_STAGE_SET
BROAD_GIT_ADD
TSC_NEW_ERROR_COUNT
BUILD
PM2
HTTP
GIT_PUSH_DURING_PATCH
FINAL_MARKER
