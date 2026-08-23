# Tara Professional Identity V2.3

Corrective frontend patch for the partially-rendered Tara portrait seen after V2.2.

## Root cause addressed
The production page successfully loaded an `image/jpeg`, but the visible portrait rendered only partially. V2.3 replaces the portrait payload with a fresh, smaller, verified baseline JPEG and validates both JPEG start/end markers before and after installation. It also separates the status indicator from the clipped image container so the portrait itself is never covered by an overlay.

## UI improvement
- Portrait grows from 76px to 88px.
- Uses a clean circular professional avatar treatment.
- The image itself is the only element inside the clipped container.
- Online/offline status sits outside the clipping layer.
- Face framing is centered with `object-[50%_22%]`.
- Existing Tara name, bilingual job title, summary, expertise tags, KPIs, tabs, settings, and all functionality remain unchanged.

## Files changed by the patch
- `client/src/pages/TaraAgentPage.tsx`
- `client/src/assets/ai-staff/tara-avatar.jpg`

## Scope
Frontend UX/UI only. No backend, API, DB, routing, permissions, or Tara business-logic changes.

## Run
```bash
node <PATCH_REPO>/patches/tara/tara-professional-identity-v2.3/apply.mjs --check
node <PATCH_REPO>/patches/tara/tara-professional-identity-v2.3/apply.mjs --apply
node <PATCH_REPO>/patches/tara/tara-professional-identity-v2.3/apply.mjs --verify
npm run build
```
