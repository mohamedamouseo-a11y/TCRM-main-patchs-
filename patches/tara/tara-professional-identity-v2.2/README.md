# Tara Professional Identity V2.2

Corrective patch for the production portrait rendering issue found after V2.1.

## Fix
The Tara portrait is no longer referenced as `/ai-staff/tara-avatar.jpg` from `public/`. The patch installs it at:

`client/src/assets/ai-staff/tara-avatar.jpg`

and imports it in `TaraAgentPage.tsx`, allowing Vite to fingerprint and bundle the image into the production build. This avoids the HTTPS/static route returning the SPA HTML fallback instead of the JPEG.

## Identity retained
- English: `AI Telesales & Lead Qualification Specialist`
- Arabic: `أخصائي المبيعات الهاتفية وتأهيل العملاء المحتملين بالذكاء الاصطناعي`
- Professional real-person AI-generated portrait
- Localized role summary and expertise tags
- Enabled/disabled indicator and Refresh control
- Premium V1 KPI cards, tabs, settings and existing Tara actions

## Scope
Frontend UX/UI only. No backend, API, DB, permissions, routes or Tara business logic changes.

## Run
```bash
node <PATCH_REPO>/patches/tara/tara-professional-identity-v2.2/apply.mjs --check
node <PATCH_REPO>/patches/tara/tara-professional-identity-v2.2/apply.mjs --apply
node <PATCH_REPO>/patches/tara/tara-professional-identity-v2.2/apply.mjs --verify
npm run check
npm run build
```
