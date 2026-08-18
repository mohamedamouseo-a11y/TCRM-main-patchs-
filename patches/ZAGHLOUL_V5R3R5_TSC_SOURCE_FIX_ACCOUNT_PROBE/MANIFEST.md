# ZAGHLOUL_V5R3R5_TSC_SOURCE_FIX_ACCOUNT_PROBE

Target: `/var/www/TCRM-MAIN`
Parent: `ZAGHLOUL_V5R3R4_FULL_DIAGNOSTIC_ACCOUNT_PROBE`
Pinned baseline: `c7ca52c5bb0495400ed327601d50cf6c7a363c73`

## Confirmed blockers from R4
R4 exposed 10 candidate-only TypeScript diagnostics:

### 6 invalid Next.js-page diagnostics
`client/src/pages/zaghloul-v5/automations/[id]/logs/page.tsx`

The file imports Next.js/WACRM-only modules (`next/navigation`, `next-intl`, `@/lib/automations/trigger-meta`, `@/types`) inside the native TCRM Vite/Wouter client tree. It is not a valid TCRM-native page and duplicates WACRM source that belongs under `apps/zaghloul-wacrm`.

R5 removes this misplaced file from the TCRM client tree **only if** it contains Next.js-only imports, after backing it up under `/tmp/ZAGHLOUL_V5R3R5_TSC_SOURCE_FIX_ACCOUNT_PROBE/backup/`.

### 4 incorrect WA Gateway result-shape diagnostics
`server/services/zaghloul-v5/v5Service.ts`

The actual TCRM WA Gateway contracts are cursor-based:
- `listWAGatewayChatsPage()` returns `items`, `nextCursor`, `hasMore`; it does not return `total`.
- `getWAGatewayInboxCounts()` returns `totalUnread`, `totalConversations`, `bySession`.
- `listWAGatewayMessagesPage()` returns `items`, not `messages`.

R5 updates the V5 adapter to consume the real TCRM contracts instead of invented WACRM-shaped fields.

## Required source behavior
- Inbox total derives from `counts.totalConversations` with page-item fallback.
- Unread counter uses `counts.totalUnread`.
- Open/Closed/Archived page counters are derived from returned native V5 items when no authoritative aggregate exists.
- Messages map from `result.items`.
- `authMode: "TCRM_SESSION"` remains in the real V5 settings result.
- No second login, Next.js runtime, sender, or Meta transport is introduced.

## Verification
- Same dependency environment for pinned baseline and candidate.
- Local TypeScript compiler only; 16GB heap; reject OOM/signal exits.
- Location-independent multiset diagnostic comparison.
- Require `TSC_NEW_ERROR_COUNT=0`.
- Require misplaced Next.js page absent from TCRM client tree.
- Real `getZaghloulV5Settings()` probe via local `tsx`, forced process exit after result, hard timeout.
- Require `ACCOUNT_MANAGEMENT=PASS` and `AUTH_MODE=TCRM_SESSION`.
- Production build PASS.
- Controlled PM2 reload and `/zaghloul`, `/zaghloul-v5`, `/zaghloul-legacy` HTTP 200.

No DB migration or dependency install.

Success marker:
`ZAGHLOUL_V5R3R5_TSC_SOURCE_FIX_ACCOUNT_PROBE_OK`
