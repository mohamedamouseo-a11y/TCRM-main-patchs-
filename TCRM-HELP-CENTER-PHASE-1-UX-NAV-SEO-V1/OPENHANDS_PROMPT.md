Apply the deterministic TCRM Help Center Phase 1 patch only.

From the TCRM source repo root:

```bash
python3 <TCRM-main-patchs-path>/TCRM-HELP-CENTER-PHASE-1-UX-NAV-SEO-V1/APPLY_PATCH.py
pnpm check && pnpm build
```

Rules:
- Do not redesign, refactor, or edit anything manually.
- Do not modify any file except what `APPLY_PATCH.py` changes.
- Do not commit or push.
- If the patch script aborts, stop and report the exact error.
- If verification fails, report the exact TypeScript/build error only; do not improvise a fix.
- Final response only: `PATCH`, `CHECK`, `BUILD`, `CHANGED_FILES`.
