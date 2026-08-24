# Darwish Phase 5 TypeScript Gate Fix V1

Apply this only after the Phase 5 Limited Safe Automation V1 bundle is already present in the TCRM `main` working tree.

Apply:

`01-darwish-page-health-union-fix.patch`

This patch fixes only the two Phase 5-blocking TS2339 diagnostics in `DarwishPage.tsx` by narrowing the Chatwoot health union before reading `error`, `reason`, or `url`.

It does not enable automation, change worker execution policy, alter the database, or enable customer outbound.
