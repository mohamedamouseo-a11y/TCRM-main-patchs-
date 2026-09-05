# Sales Agent Client Assignment Hotfix V1

Target: `/var/www/TCRM-MAIN`
Baseline: `78273711727e834ca88029e39ff0f6ae302d427a`

Fix only the confirmed backend authorization gap in `server/services/accountManagementOperationSecurity.ts`.

For `SalesAgent` and `ColdSalesAgent`, keep existing owner access, and if the actor is not `leadOwnerId`, allow `workflow.read` only when the Client's linked Lead has an active `lead_assignments` row for that user (`leadId`, `userId`, `isActive=1`).

Requirements:
- Do not change Account Manager / SalesManager / TAM / after-sales logic.
- Do not broaden access beyond the linked Lead's active assignment.
- Reuse an existing assignment helper if safe; otherwise add the smallest local helper.
- Add focused tests: owner allowed, active assignee allowed, inactive assignee denied, unrelated agent denied.
- Preserve current local Evolution API changes; no reset/discard.
- Run focused tests + build.
- No commit/push/merge/reset/rebase.
