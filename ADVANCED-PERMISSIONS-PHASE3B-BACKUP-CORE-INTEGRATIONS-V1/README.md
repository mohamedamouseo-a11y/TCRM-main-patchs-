# Advanced Permissions Phase 3B — Backup Center + Core Integrations V1

Baseline: TCRM main at/after `a1051a4c6a6d85c9109844ab08fdd1e9454cb365`.

## Scope

This phase wires Advanced Permissions into:

### Backup Center
- read/list/status/settings-read -> `backup.view`
- run/create/manual backup/retry job -> `backup.run`
- restore artifact / restore log operation -> `backup.restore`
- settings mutation / retention / archive/delete/manage operations -> `backup.manage`

Existing Admin/SuperAdmin/security/audit checks MUST remain. RBAC is additive only.

### Core Integrations only
This V1 covers technical integration surfaces for:
- TFS integration
- TOS integration
- Google Drive file-storage technical connection/settings

Mapping:
- status/read/config-for-ui/directory/sync-status -> `integrations.view`
- save settings, test connection, connect/disconnect OAuth, credential/config mutation, manual/bulk send/sync execution -> `integrations.manage`

Important product rule: do not weaken legacy guards. Sensitive settings must keep their existing Admin/Developer/Moderator protections even when `integrations.manage` is allowed.

## Explicitly excluded in this package

Do NOT wire or modify:
- Meta Ads / TikTok / Google Ads campaign operations or credentials
- WhatsApp / Messenger / Tara
- THRS
- Developer Hub
- Meetings / Felfel / TAM meeting flows
- Backup implementation/services themselves
- TFS/TOS/Google Drive service implementation files

Those surfaces need separate reviews because business-operation permissions and technical-secret permissions overlap.

## Apply deterministic part

```bash
python3 ADVANCED-PERMISSIONS-PHASE3B-BACKUP-CORE-INTEGRATIONS-V1/APPLY_PATCH.py /var/www/TCRM-MAIN
```

Then modify only `server/routers.ts` with the smallest additive diff.

Use `.use(backup...Scope)` / `.use(integrations...Scope)` on top of the existing procedure/guard. Never replace `adminProcedure`, `protectedProcedure`, role-specific procedures, service authorization, audit, or developer/moderator protections.

Before editing, inventory the exact route names for Backup Center, TFS, TOS and Google Drive storage and include the mapping in the final report.

## Validation

```bash
pnpm exec tsx scripts/verify-advanced-permissions-phase3b-backup-core-integrations.ts
NODE_OPTIONS=--max-old-space-size=8192 pnpm check
NODE_OPTIONS=--max-old-space-size=8192 pnpm build
NODE_OPTIONS=--max-old-space-size=8192 pnpm test
```

Compare test failures against the same HEAD baseline. No commit/push/merge/reset/rebase.
