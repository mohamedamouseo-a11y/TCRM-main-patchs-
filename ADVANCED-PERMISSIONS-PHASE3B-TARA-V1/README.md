# Advanced Permissions Phase 3B — Tara V1

Baseline: TCRM main at/after `78273711727e834ca88029e39ff0f6ae302d427a`.

## Goal
Add a dedicated Tara permission module instead of reusing WhatsApp or Integrations permissions.

## Permission model
Add these keys to `PHASE1_PERMISSION_CATALOG`:
- `tara.view` — dashboards, lists, logs, context, read-only operational/voice/social/provider status.
- `tara.operate` — normal day-to-day Tara actions such as generating/sending/retrying replies, conversation status updates, queue processing, lead creation from Tara conversations, and non-credential operational tests/previews.
- `tara.moderate` — moderator workflow actions: moderator notes, assignments, moderation replies/retries/sends, moderator conversation updates, KB suggestions.
- `tara.manage` — Tara configuration and administration: settings, campaigns, qualification fields, follow-up rules, knowledge base maintenance, provider config, social channel/API/OAuth settings, TikTok Business settings, Meta WhatsApp technical/operational settings, and voice settings/accounts.

The catalog remains flat and dynamic; no new DB table is required. Running the existing Phase1 migration is enough to upsert the new permission rows.

## Enforcement rules
- Existing procedures and all role/service-level checks remain authoritative and MUST NOT be replaced.
- Add RBAC with `.use(tara...Scope)` on top of existing procedures.
- `tara.manage` MUST NOT weaken Admin/Developer/SuperAdmin or any existing technical-secret guard.
- `tara.moderate` is additive to current moderator/profile/service checks; it does not replace them.
- Do not invent fake row scopes for Tara. V1 is action-level; existing Tara service authorization remains responsible for conversation/account/channel ownership or assignment checks.

## Explicit exclusions
Do NOT modify:
- WhatsApp gateway routes already covered by Phase 3B WhatsApp V1
- Messenger
- Meta Ads / TikTok Ads / Google Ads campaign modules outside Tara
- TFS / TOS / Google Drive / Backup
- THRS
- Developer Hub
- Meetings / Felfel / TAM
- Tara service implementation files

## Deterministic apply
Run:
```bash
python3 ADVANCED-PERMISSIONS-PHASE3B-TARA-V1/APPLY_PATCH.py /var/www/TCRM-MAIN
```

The deterministic step adds Tara catalog keys, Tara scope exports, and the verifier. Then inspect the actual `tara` router inventory and wire only Tara routes in `server/routers.ts` with the smallest additive diff.

## Validation
```bash
pnpm exec tsx scripts/verify-advanced-permissions-phase3b-tara.ts
NODE_OPTIONS=--max-old-space-size=8192 pnpm check
NODE_OPTIONS=--max-old-space-size=8192 pnpm build
NODE_OPTIONS=--max-old-space-size=8192 pnpm test
```
Compare test failures with the same baseline HEAD. No commit/push/merge/reset/rebase.
