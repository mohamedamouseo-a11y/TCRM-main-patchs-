# TCRM — Tara Sales Operations Command V3 (AI Staff Phase 11)

Purpose: continue BUILD/IMPLEMENTATION after Phase 10 by giving Tara a compact navigation-only sales command layer without changing backend behavior, refresh logic, settings semantics, campaigns, qualification, follow-up, knowledge, social, provider, moderator, or queue execution logic.

## Canonical baseline

- Repository: `mohamedamouseo-a11y/TCRM-MAIN-Tamiyouz-CRM-`
- Branch: `main`
- Expected HEAD: `d1eaf61c68bb09d32348ea9da8147b45665df11d`
- Guarded file: `client/src/pages/TaraAgentPage.tsx`
- Expected base blob: `7a804f534d2be5ee1dd3da2d535ff4bf6c16724b`

## Exact scope

Changes exactly one application file:

- `client/src/pages/TaraAgentPage.tsx`

No Darwish, Zaghloul, Felfel, backend, API, database, migrations, routes, permissions, customer data, provider behavior, moderation behavior, queue processing, or `external/mautic` file is changed.

## Phase 11 implementation

Adds a compact `Sales Operations Command` below Tara's six KPI cards and above the existing grouped Control Center navigation.

Marker:

`data-tara-sales-command="v3"`

The four read-only navigation signals use data already loaded by the page:

1. Campaigns → `campaigns` → `campaigns.length`
2. Qualification → `qualification` → `(fieldsQ.data || []).length`
3. Follow-ups → `followups` → `(followupsQ.data || []).length`
4. Knowledge → `knowledge` → `(knowledgeQ.data || []).length`

The command is scope-aware: the visible counts for qualification/follow-up/knowledge reflect the current `scopeId` query scope already used by Tara.

## Controlled workspace navigation

The existing Tara top-level Tabs become controlled by local UI state:

`taraWorkspace`

Initial value remains the existing `initialTab`, preserving the current URL behavior where `?tab=social` opens Social Channels and otherwise Settings opens first.

Both grouped navigation and the new Sales Operations Command update the same state.

## Safety preservation

The new command buttons are `type="button"`, set only `taraWorkspace`, expose `aria-pressed`, and contain no `.mutate()` calls.

This phase does not change existing handlers including:

- `refreshTaraData`
- `saveSettingsM`
- `testProviderM`
- `saveCampaignM` / `deleteCampaignM`
- `saveFieldM` / `deleteFieldM`
- `saveKnowledgeM` / `deleteKnowledgeM`
- `saveFollowupM` / `deleteFollowupM`
- `testAgentM`
- `processQueueM`

Existing Control Center groups remain:

- Profile & Runtime
- Sales Operations
- Knowledge
- Diagnostics

Existing Settings progressive sections remain unchanged.

## Apply helper

From `/var/www/TCRM-MAIN`:

```bash
python3 <PATCH_PATH>/apply_tara_sales_operations_command_v3.py --check
python3 <PATCH_PATH>/apply_tara_sales_operations_command_v3.py --apply
python3 <PATCH_PATH>/apply_tara_sales_operations_command_v3.py --verify
```

## User-requested execution mode

This is BUILD/IMPLEMENTATION only.

Do not run final acceptance, responsive/mobile acceptance, DevTools acceptance, browser takeover, or the user's final developer test.

A production build is required. Developer Hub mandatory built-in Verify/Tests/Build/Security/Remote Sync gates may run as part of the controlled Review Push/Auto Push workflow; do not launch a separate manual acceptance suite.

## Deployment workflow

1. Apply only the ChatGPT-authored helper to `/var/www/TCRM-MAIN`.
2. Run guarded verify and `pnpm build`.
3. Use TCRM Developer Hub Review Push from inside TCRM.
4. If mandatory Developer Hub gates pass, use Developer Hub Auto Push to canonical `main`.
5. No shell commit/push, no new branch, no force push, no rebase.
6. Reload only `tamiyouz-crm` if required.
7. Upload the implementation report/evidence directly into the current ChatGPT conversation.

## Required report

`TCRM-AI-Staff-Phase11-Tara-Sales-Operations-Command-V3-Report.md`
