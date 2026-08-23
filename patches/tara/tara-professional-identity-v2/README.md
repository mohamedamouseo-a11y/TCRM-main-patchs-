# Tara Professional Identity V2.1

This patch upgrades Tara from a generic AI-tool header into a professional AI staff profile and is compatible with the current Premium V1 Tara page structure.

## Included
- AI-generated professional real-person avatar for Tara.
- English job title: `AI Telesales & Lead Qualification Specialist`.
- Arabic job title: `أخصائي المبيعات الهاتفية وتأهيل العملاء المحتملين بالذكاء الاصطناعي`.
- Localized role summary and expertise tags.
- Live enabled/disabled status retained.
- Premium profile/name-tag hero treatment.
- Existing Premium V1 KPI cards, navigation, settings, APIs, permissions, database, routes, and Tara business logic remain unchanged.

## Compatibility fix
V2.1 no longer assumes that `busy` appears immediately after the Tara dashboard `counts` declaration. It safely inserts the identity binding after the `counts` line, preserving the existing Premium V1 `metricCards` block.

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
