# OpenHands Task — DEVELOPER_HUB_AUTO_MODE_UNTRACKED_SAFE_PUSH

Target: `/var/www/TCRM-MAIN`
Patch repo: `https://github.com/mohamedamouseo-a11y/TCRM-main-patchs-`

Goal: fix Developer Hub Auto Push so safe untracked source files can pass review/push without weakening existing safeguards.

1. Run `APPLY.sh`; stop on failure.
2. Patch only the exact Developer Hub Review/Push code that blocks `unexpected untracked file is not allowed in Auto mode`, plus focused helpers/tests.
3. Auto mode must: safely parse Git status; honor `.gitignore`; allow regular safe untracked source/config/docs; reject symlinks/special files, `.env`/keys/certs/credentials/tokens/secret matches, generated/runtime/cache/log/temp/upload/build artifacts; block the entire set if any candidate is unsafe; stage exact approved paths only; prove staged set equality. No broad `git add`, force, or bypass.
4. Preserve tracked flow and existing Verify/Tests/Build gates. Do not touch Zaghloul, DB, dependencies, package manifests or lockfiles.
5. Add focused Vitest fixtures for all 12 MANIFEST cases, including spaces/Unicode and >=441 safe files. Fixtures must use temp repos and never real push.
6. Before editing each existing file copy it to `/tmp/DEVELOPER_HUB_AUTO_MODE_UNTRACKED_SAFE_PUSH/backups/<relative-path>`; list every changed/new file in `patched-files.txt`, new files in `new-files.txt`, and test files in `test-files.txt` in that workspace.
7. Fixture tests must write this exact result file when `DEVHUB_FIXTURE_RESULTS` is set:
`FIXTURE_TESTS=PASS`, `UNTRACKED_SAFE_ALLOW=PASS`, `SECRET_BLOCK=PASS`, `SYMLINK_BLOCK=PASS`, `RUNTIME_BLOCK=PASS`, `MIXED_SET_ATOMIC_BLOCK=PASS`, `LARGE_SET_441=PASS`, `EXACT_STAGE_SET=PASS`, `GIT_PUSH_DURING_FIXTURES=NONE`.
8. Do not commit/push production Git during patching. Run `VERIFY.sh`; success only on final marker.

Final output only:
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
