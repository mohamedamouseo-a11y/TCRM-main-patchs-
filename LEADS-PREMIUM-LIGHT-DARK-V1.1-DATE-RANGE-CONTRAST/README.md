# LEADS-PREMIUM-LIGHT-DARK-V1.1-DATE-RANGE-CONTRAST

Incremental UI-only hotfix for the Premium Leads patch.

## Problem
The shared `DateRangePicker` trigger hardcodes `text-white` and white SVG icons. On the Premium Leads Light Mode surface, the placeholder/value and calendar/chevron icons become too faint and hard to read.

## Fix
This hotfix adds Leads-page-scoped overrides to `client/src/leads-premium.css`:
- Light Mode date-range trigger text: near-black `#181827`
- Light Mode date-range icons: slate `#5b6170`
- Placeholder remains slightly muted but clearly readable
- Dark Mode explicitly remains light/white for contrast

## Scope
- UI only
- Leads page only
- No React logic changes
- No API/backend/database/business-logic changes

## Target
- Server project root: `/var/www/TCRM-MAIN`
- Requires `LEADS-PREMIUM-LIGHT-DARK-V1` already installed.

## Usage
```bash
node apply.mjs --check --root=/var/www/TCRM-MAIN
node apply.mjs --apply --root=/var/www/TCRM-MAIN
node apply.mjs --verify --root=/var/www/TCRM-MAIN
```
