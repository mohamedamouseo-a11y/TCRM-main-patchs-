# Advanced Permissions Phase 3B — WhatsApp + Messenger V1

Baseline: TCRM main at/after `6e2f41199f3a6aba2dccfb5e51289b586750f41f`.

## Why Tara is deferred
The current permission catalog contains `whatsapp.*` and `messenger.*` keys, but no dedicated `tara.*` keys. Do not force Tara onto the wrong permission namespace. Tara needs a separate permission-model decision/review.

## Scope
Wire Advanced Permissions into:

### WhatsApp gateway operational surface
- read/list/status/chat/message/read-only operations -> `whatsapp.view`
- send/forward/retry-send operations -> `whatsapp.send`
- account creation/access/routing/state/pin/sync/qr/reconnect/logout/delete/admin-management operations -> `whatsapp.manage`

Existing actor/account/client authorization and Admin guards MUST remain. RBAC is additive only.

### Internal Messenger
- history/reminders/conversation meta/read operations -> `messenger.view`
- send message/reaction/ack/reminder/personal message interaction operations -> `messenger.send`
- room creation, edit/delete/restore/pin and admin conversation-management operations -> `messenger.manage`

Preserve all existing DB/service authorization and `adminProcedure` restrictions.

## Explicitly excluded
Do NOT modify or wire:
- Tara settings/providers/social/voice/moderator/Meta WhatsApp AI surfaces
- Meta Ads / TikTok / Google Ads
- TFS / TOS / Google Drive integration settings
- Backup
- Meetings / Felfel / TAM
- WhatsApp service implementation files
- Messenger DB implementation files

## Apply
```bash
python3 ADVANCED-PERMISSIONS-PHASE3B-WHATSAPP-MESSENGER-V1/APPLY_PATCH.py /var/www/TCRM-MAIN
```

Then make the smallest additive wiring changes only in:
- `server/routers.ts`
- `server/modules/messenger/router.messenger.ts`

Use `.use(...)` on top of current procedures; never replace an existing procedure/guard.

## Validate
```bash
pnpm exec tsx scripts/verify-advanced-permissions-phase3b-whatsapp-messenger.ts
NODE_OPTIONS=--max-old-space-size=8192 pnpm check
NODE_OPTIONS=--max-old-space-size=8192 pnpm build
NODE_OPTIONS=--max-old-space-size=8192 pnpm test
```

Compare failures with the same HEAD baseline. No commit/push/merge/reset/rebase.