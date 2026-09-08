Apply the deterministic TCRM Help Center Phase 1 patch only.

Patch source:
`mohamedamouseo-a11y/TCRM-main-patchs-/TCRM-HELP-CENTER-PHASE-1-UX-NAV-SEO-V1/APPLY_PATCH.py`

From the TCRM source repo root, fetch that exact file using the GitHub access already configured on the server, save it as `/tmp/tcrm-help-center-p1.py`, then run:

```bash
python3 /tmp/tcrm-help-center-p1.py
pnpm check && pnpm build
```

Rules:
- Do not explore the repo beyond what the patch/check commands require.
- Do not redesign, refactor, or edit anything manually.
- Do not modify any file except what `APPLY_PATCH.py` changes.
- Do not commit or push.
- If patch download/access fails, stop and report the exact error.
- If the patch script aborts, stop and report the exact error.
- If verification fails, report the exact TypeScript/build error only; do not improvise a fix.
- Final response only: `PATCH`, `CHECK`, `BUILD`, `CHANGED_FILES`.
