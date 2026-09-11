#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('/var/www/TCRM-MAIN')
BASELINE = '0d41a4cd81faab629715e02d60c6da41bf03a1c9'
PATCH = 'TCRM-PERMISSIONS-LEADPROFILE-DEALS-ACTIONS-V1'


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.exists():
        raise SystemExit(f'MISSING_FILE={rel}')
    return path.read_text(encoding='utf-8')


def write(rel: str, content: str):
    path = ROOT / rel
    before = path.read_text(encoding='utf-8')
    if before == content:
        print(f'SKIP={rel}:already_current')
        return
    path.write_text(content, encoding='utf-8')
    print(f'UPDATED={rel}')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'ANCHOR_ERROR={label}:expected=1:actual={count}')
    return text.replace(old, new, 1)


# ---------------------------------------------------------------------------
# 1) Permission context: request deal decisions used by LeadProfile.
# ---------------------------------------------------------------------------
rel = 'client/src/contexts/PermissionContext.tsx'
ctx = read(rel)
ctx = replace_once(
    ctx,
    '''  "leads.import",\n  "clients.view",\n''',
    '''  "leads.import",\n  "deals.view",\n  "deals.create",\n  "deals.edit",\n  "deals.delete",\n  "clients.view",\n''',
    'permission_context_deal_keys',
)
write(rel, ctx)


# ---------------------------------------------------------------------------
# 2) Lock the actual current server mappings used by LeadProfile deals.
#    This is test-only; runtime server policy is already enforced centrally.
# ---------------------------------------------------------------------------
rel = 'server/security/corePermissionPolicy.test.ts'
test = read(rel)
insert_before = '''  it("maps campaigns through the effective permission catalog", () => {\n'''
new_test = '''  it("maps LeadProfile deal and payment operations to current effective permissions", () => {\n    expect(resolveCorePermissionKey("deals.byLead", "query")).toBe("deals.view");\n    expect(resolveCorePermissionKey("deals.create", "mutation")).toBe("deals.create");\n    expect(resolveCorePermissionKey("deals.addPayment", "mutation")).toBe("deals.create");\n    expect(resolveCorePermissionKey("deals.update", "mutation")).toBe("deals.edit");\n    expect(resolveCorePermissionKey("deals.updatePayment", "mutation")).toBe("deals.edit");\n    expect(resolveCorePermissionKey("deals.cancel", "mutation")).toBe("deals.edit");\n    expect(resolveCorePermissionKey("deals.deletePayment", "mutation")).toBe("deals.delete");\n  });\n\n'''
if 'maps LeadProfile deal and payment operations to current effective permissions' not in test:
    test = replace_once(test, insert_before, new_test + insert_before, 'deal_mapping_test')
write(rel, test)


# ---------------------------------------------------------------------------
# 3) LeadProfile: gate deal read/query and deal actions with effective perms,
#    while preserving the existing role/business restrictions additively.
# ---------------------------------------------------------------------------
rel = 'client/src/pages/LeadProfile.tsx'
page = read(rel)

page = replace_once(
    page,
    '''  const { user } = useAuth();\n  const { can } = usePermissions();\n\n  const [editMode, setEditMode] = useState(false);\n''',
    '''  const { user } = useAuth();\n  const { can } = usePermissions();\n  const canViewDeal = can("deals.view");\n\n  const [editMode, setEditMode] = useState(false);\n''',
    'deal_view_flag',
)

page = replace_once(
    page,
    '''  const { data: deal, refetch: refetchDeal } = trpc.deals.byLead.useQuery({ leadId }, { enabled: Number.isFinite(leadId) && !!lead, retry: false });\n''',
    '''  const { data: deal, refetch: refetchDeal } = trpc.deals.byLead.useQuery({ leadId }, { enabled: Number.isFinite(leadId) && !!lead && canViewDeal, retry: false });\n''',
    'deal_query_view_gate',
)

page = replace_once(
    page,
    '''  const normalizedUserRole = normalizeUserRole(user?.role);\n  const canEdit = !["MediaBuyer", "AccountManager", "AccountManagerLead", "TechnicalAccountManager"].includes(normalizedUserRole);\n  const canEditDealFinancials = isManagerRole(normalizedUserRole);\n  const canEditDealPayments = normalizedUserRole === "Admin";\n  const isAdmin = normalizedUserRole === "Admin";\n''',
    '''  const normalizedUserRole = normalizeUserRole(user?.role);\n  const canEdit = !["MediaBuyer", "AccountManager", "AccountManagerLead", "TechnicalAccountManager"].includes(normalizedUserRole);\n  const canCreateDeal = canEdit && can("deals.create");\n  const canEditDeal = canEdit && can("deals.edit");\n  const canAddDealPayment = canEdit && can("deals.create");\n  const canEditDealFinancials = isManagerRole(normalizedUserRole) && can("deals.edit");\n  const canEditDealPayments = normalizedUserRole === "Admin" && can("deals.edit");\n  const canDeleteDealPayments = normalizedUserRole === "Admin" && can("deals.delete");\n  const canUseDealPaymentDialog = editingDealPayment ? canEditDealPayments : canAddDealPayment;\n  const isAdmin = normalizedUserRole === "Admin";\n''',
    'deal_action_flags',
)

page = replace_once(
    page,
    '''              {/* ── Deal Section ── */}\n              <Card className="rounded-2xl border-border/40 shadow-sm overflow-hidden">\n''',
    '''              {/* ── Deal Section ── */}\n              {canViewDeal && (\n              <Card className="rounded-2xl border-border/40 shadow-sm overflow-hidden">\n''',
    'deal_card_open_gate',
)

page = replace_once(
    page,
    '''              </Card>\n\n              {/* ── Team & Stakeholders ── */}\n''',
    '''              </Card>\n              )}\n\n              {/* ── Team & Stakeholders ── */}\n''',
    'deal_card_close_gate',
)

page = replace_once(
    page,
    '''                      onAction={canEdit ? () => setShowDeal(true) : undefined}\n''',
    '''                      onAction={canCreateDeal ? () => setShowDeal(true) : undefined}\n''',
    'deal_create_empty_action',
)

page = replace_once(
    page,
    '''                        {canEdit && Number((deal as any).remainingAmount || 0) > 0 && (\n''',
    '''                        {canAddDealPayment && Number((deal as any).remainingAmount || 0) > 0 && (\n''',
    'deal_add_payment_button',
)

page = replace_once(
    page,
    '''                                  {canEditDealPayments && (\n                                    <div className="flex shrink-0 gap-1">\n                                      <Button type="button" size="icon" variant="ghost" className="h-7 w-7" onClick={() => onEditDealPayment(payment)}>\n                                        <Edit size={12} />\n                                      </Button>\n                                      <Button type="button" size="icon" variant="outline" className="h-7 w-7 rounded-lg border-red-200/70 bg-red-50/50 text-red-600 shadow-none transition-colors hover:border-red-300 hover:bg-red-100 hover:text-red-700 disabled:cursor-not-allowed disabled:border-red-100 disabled:bg-red-50/30 disabled:text-red-300 dark:border-red-900/60 dark:bg-red-950/20 dark:text-red-400 dark:hover:border-red-800 dark:hover:bg-red-950/40" onClick={() => onDeleteDealPayment(payment)} disabled={deleteDealPaymentMutation.isPending} title={isRTL ? "حذف الدفعة" : "Delete payment"} aria-label={isRTL ? "حذف الدفعة" : "Delete payment"}>\n                                        <Trash2 size={12} />\n                                      </Button>\n                                    </div>\n                                  )}\n''',
    '''                                  {(canEditDealPayments || canDeleteDealPayments) && (\n                                    <div className="flex shrink-0 gap-1">\n                                      {canEditDealPayments && (\n                                        <Button type="button" size="icon" variant="ghost" className="h-7 w-7" onClick={() => onEditDealPayment(payment)}>\n                                          <Edit size={12} />\n                                        </Button>\n                                      )}\n                                      {canDeleteDealPayments && (\n                                        <Button type="button" size="icon" variant="outline" className="h-7 w-7 rounded-lg border-red-200/70 bg-red-50/50 text-red-600 shadow-none transition-colors hover:border-red-300 hover:bg-red-100 hover:text-red-700 disabled:cursor-not-allowed disabled:border-red-100 disabled:bg-red-50/30 disabled:text-red-300 dark:border-red-900/60 dark:bg-red-950/20 dark:text-red-400 dark:hover:border-red-800 dark:hover:bg-red-950/40" onClick={() => onDeleteDealPayment(payment)} disabled={deleteDealPaymentMutation.isPending} title={isRTL ? "حذف الدفعة" : "Delete payment"} aria-label={isRTL ? "حذف الدفعة" : "Delete payment"}>\n                                          <Trash2 size={12} />\n                                        </Button>\n                                      )}\n                                    </div>\n                                  )}\n''',
    'deal_payment_edit_delete_controls',
)

page = replace_once(
    page,
    '''                      {canEdit && (\n                        <div className="rounded-lg border border-border/40 p-2">\n                          <Label className="text-[10px] uppercase tracking-wider text-muted-foreground">{t("dealStatus")}</Label>\n''',
    '''                      {canEditDeal && (\n                        <div className="rounded-lg border border-border/40 p-2">\n                          <Label className="text-[10px] uppercase tracking-wider text-muted-foreground">{t("dealStatus")}</Label>\n''',
    'deal_status_services_gate',
)

page = replace_once(
    page,
    '''                      {canEdit && (\n                        <Button\n                          size="sm"\n                          variant="outline"\n                          className="w-full gap-1.5 rounded-lg h-7 text-xs border-red-200/80 bg-red-50/70 text-red-600 shadow-none transition-colors hover:border-red-300 hover:bg-red-100 hover:text-red-700 disabled:cursor-not-allowed disabled:border-red-100 disabled:bg-red-50/40 disabled:text-red-300 dark:border-red-900/60 dark:bg-red-950/20 dark:text-red-400 dark:hover:border-red-800 dark:hover:bg-red-950/40 dark:hover:text-red-300"\n''',
    '''                      {canEditDeal && (\n                        <Button\n                          size="sm"\n                          variant="outline"\n                          className="w-full gap-1.5 rounded-lg h-7 text-xs border-red-200/80 bg-red-50/70 text-red-600 shadow-none transition-colors hover:border-red-300 hover:bg-red-100 hover:text-red-700 disabled:cursor-not-allowed disabled:border-red-100 disabled:bg-red-50/40 disabled:text-red-300 dark:border-red-900/60 dark:bg-red-950/20 dark:text-red-400 dark:hover:border-red-800 dark:hover:bg-red-950/40 dark:hover:text-red-300"\n''',
    'deal_cancel_current_server_gate',
)

page = replace_once(
    page,
    '''      <Dialog open={showDeal} onOpenChange={setShowDeal}>\n''',
    '''      <Dialog open={showDeal && canCreateDeal} onOpenChange={(open) => setShowDeal(open && canCreateDeal)}>\n''',
    'deal_create_dialog_gate',
)

page = replace_once(
    page,
    '''                <Button type="submit" style={{ background: tokens.primaryColor }} className="text-white" disabled={createDeal.isPending}>\n''',
    '''                <Button type="submit" style={{ background: tokens.primaryColor }} className="text-white" disabled={!canCreateDeal || createDeal.isPending}>\n''',
    'deal_create_submit_gate',
)

page = replace_once(
    page,
    '''      <Dialog open={showDealEdit} onOpenChange={(o) => { setShowDealEdit(o); if (!o) dealEditReset(); }}>\n''',
    '''      <Dialog open={showDealEdit && canEditDealFinancials} onOpenChange={(o) => { setShowDealEdit(o && canEditDealFinancials); if (!o) dealEditReset(); }}>\n''',
    'deal_financial_dialog_gate',
)

page = replace_once(
    page,
    '''              <Button type="submit" style={{ background: tokens.primaryColor }} className="text-white" disabled={updateDeal.isPending}>\n''',
    '''              <Button type="submit" style={{ background: tokens.primaryColor }} className="text-white" disabled={!canEditDealFinancials || updateDeal.isPending}>\n''',
    'deal_financial_submit_gate',
)

page = replace_once(
    page,
    '''      <Dialog open={showPayment} onOpenChange={(o) => { setShowPayment(o); if (!o) { setEditingDealPayment(null); paymentReset(); } }}>\n''',
    '''      <Dialog open={showPayment && canUseDealPaymentDialog} onOpenChange={(o) => { setShowPayment(o && canUseDealPaymentDialog); if (!o) { setEditingDealPayment(null); paymentReset(); } }}>\n''',
    'deal_payment_dialog_gate',
)

page = replace_once(
    page,
    '''              <Button type="submit" style={{ background: tokens.primaryColor }} className="text-white" disabled={addDealPayment.isPending || updateDealPaymentMutation.isPending}>\n''',
    '''              <Button type="submit" style={{ background: tokens.primaryColor }} className="text-white" disabled={!canUseDealPaymentDialog || addDealPayment.isPending || updateDealPaymentMutation.isPending}>\n''',
    'deal_payment_submit_gate',
)

write(rel, page)


# ---------------------------------------------------------------------------
# 4) Static post-checks. No runtime server/CSS/data changes in this phase.
# ---------------------------------------------------------------------------
checks = {
    'client/src/contexts/PermissionContext.tsx': [
        '"deals.view"',
        '"deals.create"',
        '"deals.edit"',
        '"deals.delete"',
    ],
    'server/security/corePermissionPolicy.test.ts': [
        'deals.byLead',
        'deals.addPayment',
        'deals.updatePayment',
        'deals.cancel',
        'deals.deletePayment',
    ],
    'client/src/pages/LeadProfile.tsx': [
        'const canViewDeal = can("deals.view")',
        'const canCreateDeal = canEdit && can("deals.create")',
        'const canEditDeal = canEdit && can("deals.edit")',
        'const canAddDealPayment = canEdit && can("deals.create")',
        'const canEditDealFinancials = isManagerRole(normalizedUserRole) && can("deals.edit")',
        'const canEditDealPayments = normalizedUserRole === "Admin" && can("deals.edit")',
        'const canDeleteDealPayments = normalizedUserRole === "Admin" && can("deals.delete")',
        'const canUseDealPaymentDialog = editingDealPayment ? canEditDealPayments : canAddDealPayment',
        '!!lead && canViewDeal',
        '{canViewDeal && (',
        'showDeal && canCreateDeal',
        'showDealEdit && canEditDealFinancials',
        'showPayment && canUseDealPaymentDialog',
    ],
}
for rel, needles in checks.items():
    data = read(rel)
    missing = [needle for needle in needles if needle not in data]
    if missing:
        raise SystemExit(f'POSTCHECK_FAILED={rel}:{missing}')

print(f'PATCH={PATCH}')
print(f'BASELINE={BASELINE}')
print('MODULES=deals')
print('DEAL_VIEW_QUERY_GATE=deals.view')
print('DEAL_CREATE_UI_GATE=deals.create+existing_canEdit')
print('DEAL_EDIT_UI_GATE=deals.edit+existing_canEdit')
print('DEAL_FINANCIAL_EDIT_GATE=deals.edit+existing_manager_guard')
print('DEAL_ADD_PAYMENT_GATE=deals.create+existing_canEdit')
print('DEAL_EDIT_PAYMENT_GATE=deals.edit+existing_admin_guard')
print('DEAL_DELETE_PAYMENT_GATE=deals.delete+existing_admin_guard')
print('DEAL_CANCEL_UI_GATE=deals.edit(current_server_mapping)+existing_canEdit')
print('EXISTING_DEAL_SERVER_GATE_PRESERVED=YES')
print('SERVER_RUNTIME_POLICY_CHANGED=NO')
print('LEADS_ACTIVITIES_FILES_GATING_CHANGED=NO')
print('CSS_CHANGED=NO')
print('DB_SCHEMA_CHANGED=NO')
print('DATA_CHANGED=NO')
print('FILES_CHANGED=client/src/contexts/PermissionContext.tsx,client/src/pages/LeadProfile.tsx,server/security/corePermissionPolicy.test.ts')
