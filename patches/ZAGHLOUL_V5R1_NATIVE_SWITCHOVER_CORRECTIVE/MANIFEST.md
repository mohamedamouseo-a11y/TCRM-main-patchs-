# ZAGHLOUL_V5R1_NATIVE_SWITCHOVER_CORRECTIVE

Target: `/var/www/TCRM-MAIN`
Baseline source commit reviewed: `afae21e453453cd273be9910ad28d6808758725c`

## Purpose
- Fix the V5 route wiring created by the Zaghloul V5 integration commit.
- Make `/zaghloul` and `/zaghloul-v5` render the actual `ZaghloulV5Page`.
- Preserve the previous Zaghloul UI as an explicit fallback at `/zaghloul-legacy`.
- Replace the V5 placeholder-only tabs with live read-only views backed by the existing `trpc.zaghloulV5` adapters for Inbox, Contacts, Pipelines/Deals and Automations.
- Keep existing WACRM/TCRM server adapters, DB schema, WhatsApp infrastructure and dependencies unchanged.

## Files
- `files/client/src/pages/ZaghloulV5Page.tsx` — corrected V5 UI using existing V5 tRPC adapters.
- `App.routes.patch` — surgical route/import change for `client/src/App.tsx`.
- `APPLY.sh` — guarded cumulative apply, TSC delta gate, build, PM2 reload, HTTP readiness and rollback.

## Strict baseline guards
`APPLY.sh` refuses to modify production unless these source blobs still match the reviewed baseline:
- `client/src/App.tsx`: `d9d9b2bf8c48c565888798055e5f2b244a9e30c0`
- `client/src/pages/ZaghloulV5Page.tsx`: `d3a11a1f199ae0a3d9558ba5784d6661a92a3540`

## Non-scope
- No dependency install/update.
- No DB migration or destructive DB operation.
- No WhatsApp credentials/config changes.
- No Git push from the production server.
- No deletion of the legacy Zaghloul implementation.

## Success marker
`ZAGHLOUL_V5R1_NATIVE_SWITCHOVER_CORRECTIVE_OK`
