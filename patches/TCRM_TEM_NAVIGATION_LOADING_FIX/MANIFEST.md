# TCRM — TEM Navigation Loading Fix

## Problem

The Business Development submenu uses native `<a href>` navigation for its entries, including `/tem`, while the application is a Wouter SPA and the other sidebar groups use Wouter `<Link>`.

A native anchor causes a full document reload. During that reload `CRMLayout` has no cached auth state yet and renders its full-screen authentication loading state until `auth.me` resolves. This matches the recorded behavior: clicking TEM blanks the whole application before the page appears.

## Fix

Change only the two Business Development submenu navigation wrappers (expanded and collapsed sidebar variants) from native `<a>` to Wouter `<Link>`.

No TEM API, Mautic, SMTP, Phase 4/5, database, worker, scheduler, authentication, or route definitions are changed.

## Target

- Checkout: `/var/www/TCRM-MAIN`
- File: `client/src/components/CRMLayout.tsx`
- Expected baseline Git blob: `9f9dbee77fa8a755f98d16df88c9f18bd0ff2bf8`

## Expected effect

Clicking `Business Development → TEM` becomes client-side SPA navigation. The existing CRM shell remains mounted instead of reloading the full document, so the full-screen auth loading state is not triggered by the navigation itself.

## Files

- `APPLY.sh` — guarded source fix + build
- `VERIFY.sh` — verifies SPA link semantics and safety boundary
- `ROLLBACK.sh` — restores the backed-up `CRMLayout.tsx`

## Safety

- No branch switch.
- No pull/reset/rebase.
- No DB mutation.
- No runtime secret access.
- No SMTP/email action.
- No worker/scheduler changes.
- No Git commit or push.
- Fails closed if `CRMLayout.tsx` has drifted from the reviewed baseline or has local modifications.

## Success marker

`FINAL_MARKER=TCRM_TEM_NAVIGATION_LOADING_FIX_OK`
