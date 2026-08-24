# Darwish Phase 5 — Limited Safe Automation V1

Ready-to-apply patch bundle.

## Target

- Application repo: `mohamedamouseo-a11y/TCRM-MAIN-Tamiyouz-CRM-`
- Branch: `main`
- Baseline: `0d5696b0946142c1836cefd601c597db5a3f4187`

## Apply order

```text
01-config-policy.patch
02-policy-tests-action-service.patch
03-worker-ui-card.patch
04-darwish-page.patch
```

Verify hashes using `MANIFEST.json`.

From `/var/www/TCRM-MAIN`, for each part in order:

```bash
git apply --check <part>
git apply <part>
```

Then:

```bash
git diff --check
```

## Initial deployment mode

Do **not** enable automation during initial apply/test.

```text
DARWISH_LIMITED_AUTOMATION_ENABLED=false
DARWISH_APPROVED_OUTBOUND_ENABLED=false
```

Do not configure/change `DARWISH_AUTOMATION_ACTOR_USER_ID` during initial deployment validation.

See `BOM.md` for exact scope and safety boundaries.
