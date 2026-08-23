# Tara Professional Identity V2

This patch upgrades Tara from a generic AI-tool header into a professional AI staff profile.

## Included
- AI-generated professional real-person avatar for Tara.
- English job title: `AI Telesales & Lead Qualification Specialist`.
- Arabic job title: `أخصائي المبيعات الهاتفية وتأهيل العملاء المحتملين بالذكاء الاصطناعي`.
- Localized role summary and expertise tags.
- Live enabled/disabled status retained.
- Premium profile/name-tag hero treatment.
- Existing KPI cards, navigation, settings, APIs, permissions, database, routes, and Tara business logic remain unchanged.

## Target
`client/src/pages/TaraAgentPage.tsx`

The patch also installs the avatar to:
`public/ai-staff/tara-avatar.jpg`

## Run
From the TCRM Main project root:

```bash
node <PATCH_REPO>/patches/tara/tara-professional-identity-v2/apply.mjs --check
node <PATCH_REPO>/patches/tara/tara-professional-identity-v2/apply.mjs --apply
node <PATCH_REPO>/patches/tara/tara-professional-identity-v2/apply.mjs --verify
npm run check
```

## Scope
UX/UI only. Manus should apply and test this patch; it should not rewrite the implementation.
