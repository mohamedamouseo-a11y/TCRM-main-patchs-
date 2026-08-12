# ZAGHLOUL_V5R1R1_POST_APPLY_RECONCILIATION

Target: `/var/www/TCRM-MAIN`

## Purpose
Lock the patch archive to the exact verified post-apply Zaghloul V5 production state after the manual V5R1 switchover.

## Verified production blobs
- `client/src/App.tsx`: `242bd67ff1766f00decf66d7a91fcb2c83552856`
- `client/src/pages/ZaghloulV5Page.tsx`: `a7b7d15671c9f8a6fed17608d8b07adad62920b8`

## Required routing state
- `/zaghloul` -> `ZaghloulV5Page`
- `/zaghloul-v5` -> `ZaghloulV5Page`
- `/zaghloul-legacy` -> `ZaghloulAgentPage`
- V5 page first line must be `// @ts-nocheck`.
- V5 page must use Inbox, Contacts, Pipelines, Deals and Automations tRPC adapters.

## Behavior
This reconciliation is intentionally verification-only. It does not overwrite current production source. If either source blob differs from the verified post-apply state, it stops with `RECONCILIATION_GUARD=FAIL` so a later corrective can be generated from the new real state instead of silently reverting newer work.

It runs:
- exact source blob guards
- static route/adapter verification
- clean TypeScript verification using `pnpm exec tsc --noEmit --incremental false`
- production build
- PM2 process discovery by target cwd
- HTTP readiness for `/zaghloul`, `/zaghloul-v5`, `/zaghloul-legacy`

## Non-scope
- no source mutation
- no DB changes
- no dependency install/update
- no WhatsApp config changes
- no WACRM feature expansion
- no production Git push

## Success marker
`ZAGHLOUL_V5R1R1_POST_APPLY_RECONCILIATION_OK`
