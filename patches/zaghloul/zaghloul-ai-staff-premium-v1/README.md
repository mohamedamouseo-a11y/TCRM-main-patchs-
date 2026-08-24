# TCRM — Zaghloul AI Staff Premium V1

Purpose: redesign **Zaghloul** to match the premium AI Staff identity level used by Tara/Felfel while preserving the complete V5 workspace and its current live data/API behavior.

## Scope

Changes exactly one application file:

- `client/src/pages/ZaghloulV5Page.tsx`

No backend, database, migration, Mautic, routing, team data, settings, developer API behavior, or automation logic is changed.

## Design

- Premium violet/indigo AI Staff hero
- Dedicated Zaghloul portrait-style identity illustration
- Bilingual role: `AI Outreach & Engagement Specialist` / `أخصائي التفاعل والتواصل الخارجي بالذكاء الاصطناعي`
- Skills: Outreach, Conversations, Automation, Customer Journey
- Replaces customer-facing `V5` identity emphasis with business-role/status identity
- Six premium KPI cards: Contacts, Broadcasts, Conversations, Unread, Automations, AI Agents
- Premium active-tab treatment while retaining all existing eleven tabs
- Existing workspace capabilities, inbox, contacts, pipelines, broadcasts, automations, flows, AI agents, team, settings, and developer content remain intact

## Guarded blobs

- Base `client/src/pages/ZaghloulV5Page.tsx`: `7040f1be7cf0b8aea5ef58fa37bc85967aa2eb70`
- Target: `ce591fa4a94571d89e079995ca7873645336d861`
- Expected main HEAD at preparation: `5e91f9557707297a741c0d9ff6d49e3351a5a6a5`

## Apply

```bash
git hash-object client/src/pages/ZaghloulV5Page.tsx
git apply --check /path/to/zaghloul-ai-staff-premium-v1.patch
git apply /path/to/zaghloul-ai-staff-premium-v1.patch
git hash-object client/src/pages/ZaghloulV5Page.tsx
```

Expected final blob: `ce591fa4a94571d89e079995ca7873645336d861`

Marker: `TCRM_ZAGHLOUL_AI_STAFF_PREMIUM_V1`
