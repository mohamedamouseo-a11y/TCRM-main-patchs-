Apply the deterministic TCRM Help Center Phase 1 patch only.

The patch repository is PUBLIC. Do not use GitHub API, SSH, PATs, GH CLI, or any stored GitHub credentials.

From the TCRM source repo root, download the patch directly from the public raw URL:

```bash
rm -f /tmp/tcrm-help-center-p1.py
curl -q -fsSL --retry 2 \
  https://raw.githubusercontent.com/mohamedamouseo-a11y/TCRM-main-patchs-/main/TCRM-HELP-CENTER-PHASE-1-UX-NAV-SEO-V1/APPLY_PATCH.py \
  -o /tmp/tcrm-help-center-p1.py
python3 /tmp/tcrm-help-center-p1.py
pnpm check
pnpm build
```

Rules:
- Do not use `GITHUB_PERSONAL_ACCESS_TOKEN`, `GITHUB_TOKEN`, `GH_TOKEN`, GitHub API, SSH, or `gh`.
- Do not explore the repo beyond what the patch/check/build commands require.
- Do not redesign, refactor, or edit anything manually.
- Do not modify any file except what `APPLY_PATCH.py` changes.
- Do not commit or push.
- If the raw download fails, stop and report the exact curl error.
- If the patch script aborts, stop and report the exact patch error.
- If check/build fails, report the exact error only; do not improvise a fix.
- Final response only:

PATCH=
CHECK=
BUILD=
CHANGED_FILES=
ERROR=
