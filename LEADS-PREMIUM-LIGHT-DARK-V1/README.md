# LEADS-PREMIUM-LIGHT-DARK-V1

Premium UX/UI-only patch for the TCRM `/leads` workspace.

## Scope
- Premium Light Mode: white/lavender surfaces, refined purple accent hierarchy, cleaner filters/table/buttons.
- Premium Dark Mode: deep navy surfaces, purple depth and restrained gold CTA accents.
- Improves hero, filter command center, table density, status readability, hover/focus states, scrollbar and responsive behavior.
- Keeps existing data fetching, filters, export, New Lead, routing, dialogs, backend, API, DB and business logic unchanged.

## Target
- App repo: `mohamedamouseo-a11y/TCRM-MAIN-Tamiyouz-CRM-`
- Intended server root: `/var/www/TCRM`
- Original baseline inspected: `04734de921eca880b099d647496fc25f87eed68a`

## Patch files
- `leads-premium.css` — official stylesheet asset.
- `apply.mjs` — idempotent checker/applicator/verifier with backup protection.

## Usage
```bash
node apply.mjs --check --root=/var/www/TCRM
node apply.mjs --apply --root=/var/www/TCRM
node apply.mjs --verify --root=/var/www/TCRM
```

The applicator changes only:
- `client/src/leads-premium.css`
- `client/index.html`

Before applying it checks the current Leads page DOM signature and refuses to overwrite a different existing `leads-premium.css`. During apply it backs up target files under `.patch-backups/LEADS-PREMIUM-LIGHT-DARK-V1/`.
