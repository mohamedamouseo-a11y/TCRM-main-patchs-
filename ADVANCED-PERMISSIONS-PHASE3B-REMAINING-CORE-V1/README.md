# Advanced Permissions Phase 3B — Remaining Core V1

Baseline: TCRM main `3a6551801a60c3f2763185f325b41185f5ec0228`.

This package continues Phase 3B after Leads/Deals/Clients + Activities/Tasks/Contracts + TAS-style role UX/user overrides.

## Scope of this package

Apply backend permission enforcement to the next low-risk core modules only:

- Campaigns
- Reports
- Notifications
- Audit Logs

These modules already have legacy/Admin/MediaBuyer guards. The new RBAC layer is **additive** and must never replace those guards.

## Explicitly out of scope in this package

- Meetings / Felfel / TAM meeting flows
- WhatsApp / Messenger / Tara / Moderator messaging
- Integrations / technical settings / Developer Hub
- Backup/restore
- Files/Drive
- Phase 4 field permissions
- Phase 5 hardening

Those areas have special security semantics and should be handled in a separate reviewed package.

## Permission mapping

### Campaigns
- list / distinctNames / detail reads -> `campaigns.view`
- create -> `campaigns.create`
- update -> `campaigns.edit`
- delete/archive -> `campaigns.delete`
- export if present -> `campaigns.export`

Keep `mediaBuyerOrAdminProcedure` (or any current legacy guard) and add the RBAC middleware on top.

### Reports
- report queries / dashboards -> `reports.view`
- export/download -> `reports.export`

Keep existing Admin/manager restrictions where present.

### Notifications
- read/list/config display -> `notifications.view`
- add/update/delete/config mutations -> `notifications.manage`

Keep existing admin restrictions where present.

### Audit Logs
- list/detail/read -> `audit.view`
- export/download -> `audit.export`
- destructive/special actions such as undo remain under existing legacy/admin security; do not weaken them.

## Data scopes

This package is action-enforcement only. Do not invent row-scope semantics for Campaigns/Reports/Notifications/Audit in this step. Existing legacy/query scoping remains authoritative. Permission engine scope is still evaluated for allow/deny, but no new custom row filter is introduced here.

## Apply

```bash
python3 ADVANCED-PERMISSIONS-PHASE3B-REMAINING-CORE-V1/APPLY_PATCH.py /var/www/TCRM-MAIN
```

The applier installs the reusable Phase3B remaining-core middleware exports and verifier. Then OpenHands must make the smallest safe edits in `server/routers.ts` following the mapping above.

## Validation

```bash
pnpm exec tsx scripts/verify-advanced-permissions-phase3b-remaining-core.ts
NODE_OPTIONS=--max-old-space-size=8192 pnpm check
NODE_OPTIONS=--max-old-space-size=8192 pnpm build
NODE_OPTIONS=--max-old-space-size=8192 pnpm test
```

No commit/push/merge/reset/rebase. Stop and report.