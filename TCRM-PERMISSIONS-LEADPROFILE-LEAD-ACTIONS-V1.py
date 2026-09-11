#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('/var/www/TCRM-MAIN')
BASELINE = 'ee21876d72164827f939adcadd682961f9136fe8'
PATCH = 'TCRM-PERMISSIONS-LEADPROFILE-LEAD-ACTIONS-V1'


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


def replace_count(text: str, old: str, new: str, expected: int, label: str) -> str:
    if old not in text and new in text:
        return text
    count = text.count(old)
    if count != expected:
        raise SystemExit(f'ANCHOR_ERROR={label}:expected={expected}:actual={count}')
    return text.replace(old, new)


# ---------------------------------------------------------------------------
# 1) Server: map LeadProfile collaboration/transfer routers to lead permissions.
#    Existing row/TAM/business authorization remains additive and untouched.
# ---------------------------------------------------------------------------
rel = 'server/security/corePermissionPolicy.ts'
text = read(rel)

header_old = '''// TCRM_PERMISSIONS_OPERATIONAL_MODULES_V2
// TCRM_PERMISSIONS_DASHBOARD_FILES_API_V1
// TCRM_PERMISSIONS_CAMPAIGNS_API_V1
import type { PermissionKey } from "./permissionCatalog";
'''
header_new = '''// TCRM_PERMISSIONS_OPERATIONAL_MODULES_V2
// TCRM_PERMISSIONS_DASHBOARD_FILES_API_V1
// TCRM_PERMISSIONS_CAMPAIGNS_API_V1
// TCRM_PERMISSIONS_LEADPROFILE_LEAD_ACTIONS_V1
import type { PermissionKey } from "./permissionCatalog";
'''
text = replace_once(text, header_old, header_new, 'policy_header')

anchor = '''  // TCRM_PERMISSIONS_DASHBOARD_FILES_API_V1
  // Dashboard currently exposes read-only protected queries. Preserve any future
'''
block = '''  // TCRM_PERMISSIONS_LEADPROFILE_LEAD_ACTIONS_V1
  // Lead collaboration and handover live outside leads.* but operate on a lead.
  // Keep their existing row/TAM/business rules additive; this only adds the
  // effective permission decision at the protectedProcedure boundary.
  if (root === "assignments") {
    if (type === "query" || type === "subscription") return "leads.view";
    return "leads.assign";
  }

  if (root === "transfers") {
    if (type === "query" || type === "subscription") return "leads.view";
    return "leads.reassign";
  }

'''
if block not in text:
    text = replace_once(text, anchor, block + anchor, 'leadprofile_aliases')
write(rel, text)


# ---------------------------------------------------------------------------
# 2) Server tests for actual LeadProfile router paths.
# ---------------------------------------------------------------------------
rel = 'server/security/corePermissionPolicy.test.ts'
test = read(rel)
insert_before = '''  it("maps campaigns through the effective permission catalog", () => {\n'''
new_tests = '''  it("maps LeadProfile assignment and transfer routers to lead permissions", () => {\n    expect(resolveCorePermissionKey("assignments.byLead", "query")).toBe("leads.view");\n    expect(resolveCorePermissionKey("assignments.history", "query")).toBe("leads.view");\n    expect(resolveCorePermissionKey("assignments.create", "mutation")).toBe("leads.assign");\n    expect(resolveCorePermissionKey("assignments.remove", "mutation")).toBe("leads.assign");\n    expect(resolveCorePermissionKey("transfers.byLead", "query")).toBe("leads.view");\n    expect(resolveCorePermissionKey("transfers.create", "mutation")).toBe("leads.reassign");\n  });\n\n'''
if 'maps LeadProfile assignment and transfer routers to lead permissions' not in test:
    test = replace_once(test, insert_before, new_tests + insert_before, 'leadprofile_policy_tests')
write(rel, test)


# ---------------------------------------------------------------------------
# 3) Frontend permission request: request only the lead action keys this page uses.
# ---------------------------------------------------------------------------
rel = 'client/src/contexts/PermissionContext.tsx'
ctx = read(rel)
ctx = replace_once(
    ctx,
    '''  "leads.view",\n  "leads.create",\n  "leads.delete",\n''',
    '''  "leads.view",\n  "leads.create",\n  "leads.edit",\n  "leads.delete",\n  "leads.assign",\n  "leads.reassign",\n''',
    'permission_context_lead_keys',
)
write(rel, ctx)


# ---------------------------------------------------------------------------
# 4) LeadProfile: gate only lead-specific actions. Deals/activities/files remain
#    untouched for later dedicated phases; no broad canEdit replacement.
# ---------------------------------------------------------------------------
rel = 'client/src/pages/LeadProfile.tsx'
page = read(rel)

page = replace_once(
    page,
    'import { useLanguage } from "@/contexts/LanguageContext";\n',
    'import { useLanguage } from "@/contexts/LanguageContext";\nimport { usePermissions } from "@/contexts/PermissionContext";\n',
    'leadprofile_permission_import',
)

page = replace_once(
    page,
    '  const { user } = useAuth();\n\n  const [editMode, setEditMode] = useState(false);\n',
    '  const { user } = useAuth();\n  const { can } = usePermissions();\n\n  const [editMode, setEditMode] = useState(false);\n',
    'leadprofile_permission_hook',
)

page = replace_once(
    page,
    '''  const canEditDealPayments = normalizedUserRole === "Admin";\n  const isAdmin = normalizedUserRole === "Admin";\n  const isSalesRole = isSalesAgentRole(normalizedUserRole);\n''',
    '''  const canEditDealPayments = normalizedUserRole === "Admin";\n  const isAdmin = normalizedUserRole === "Admin";\n  const canEditLead = canEdit && can("leads.edit");\n  const canDeleteLead = can("leads.delete");\n  const canAssignLead = can("leads.assign");\n  const canReassignLead = can("leads.reassign");\n  const isSalesRole = isSalesAgentRole(normalizedUserRole);\n''',
    'leadprofile_permission_flags',
)

page = replace_once(
    page,
    '  const canAssignTam = isLostLead && (isManagerRole(normalizedUserRole) || isOwnedLostLead);\n',
    '  const canAssignTam = canAssignLead && isLostLead && (isManagerRole(normalizedUserRole) || isOwnedLostLead);\n',
    'leadprofile_tam_assign_gate',
)

page = replace_count(
    page,
    '{canEdit && lead.stage !== "Won" && lead.stage !== "Lost" && (',
    '{canEditLead && lead.stage !== "Won" && lead.stage !== "Lost" && (',
    2,
    'leadprofile_stage_actions',
)

page = replace_once(
    page,
    '''{canEdit && (\n                            editMode ? (''',
    '''{canEditLead && (\n                            editMode ? (''',
    'leadprofile_edit_action',
)

page = replace_once(
    page,
    '                            {a.role !== "owner" && canEdit && (\n',
    '                            {a.role !== "owner" && canAssignLead && (\n',
    'leadprofile_remove_assignment_gate',
)

page = replace_once(
    page,
    '                      onAction={canEdit ? () => openAssignDialog(canAssignTam ? "technical_account_manager" : "collaborator") : undefined}\n',
    '                      onAction={canAssignLead ? () => openAssignDialog(canAssignTam ? "technical_account_manager" : "collaborator") : undefined}\n',
    'leadprofile_empty_assignment_gate',
)

page = replace_once(
    page,
    '                  {canEdit && (leadAssignments as any[])?.length > 0 && (\n',
    '                  {canAssignLead && (leadAssignments as any[])?.length > 0 && (\n',
    'leadprofile_add_assignment_gate',
)

page = replace_once(
    page,
    '                                  onClick={() => setShowTransfer(true)}\n',
    '                                  onClick={() => setShowTransfer(true)}\n                                  disabled={!canReassignLead}\n',
    'leadprofile_handover_button_gate',
)

page = replace_once(
    page,
    '<Dialog open={showTransfer} onOpenChange={(o) => { setShowTransfer(o); if (!o) { setTransferToUserId(0); transferReset(); } }}>\n',
    '<Dialog open={showTransfer && canReassignLead} onOpenChange={(o) => { setShowTransfer(o && canReassignLead); if (!o) { setTransferToUserId(0); transferReset(); } }}>\n',
    'leadprofile_handover_dialog_gate',
)

page = replace_once(
    page,
    '              <Button type="submit" className="gap-1.5 text-white rounded-xl text-sm h-9" style={{ background: "#3b82f6" }} disabled={transferLead.isPending}>\n',
    '              <Button type="submit" className="gap-1.5 text-white rounded-xl text-sm h-9" style={{ background: "#3b82f6" }} disabled={!canReassignLead || transferLead.isPending}>\n',
    'leadprofile_handover_submit_gate',
)

page = replace_once(
    page,
    '<Dialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>\n',
    '<Dialog open={showDeleteConfirm && canDeleteLead} onOpenChange={(open) => setShowDeleteConfirm(open && canDeleteLead)}>\n',
    'leadprofile_delete_dialog_gate',
)

page = replace_once(
    page,
    '              <Button variant="destructive" className="gap-1.5 rounded-xl text-sm h-9" onClick={() => deleteLead.mutate({ id: leadId })} disabled={deleteLead.isPending}>\n',
    '              <Button variant="destructive" className="gap-1.5 rounded-xl text-sm h-9" onClick={() => deleteLead.mutate({ id: leadId })} disabled={!canDeleteLead || deleteLead.isPending}>\n',
    'leadprofile_delete_submit_gate',
)

write(rel, page)


# ---------------------------------------------------------------------------
# 5) Static post-checks: exact scope only, no CSS/UI structure rewrite.
# ---------------------------------------------------------------------------
checks = {
    'server/security/corePermissionPolicy.ts': [
        'TCRM_PERMISSIONS_LEADPROFILE_LEAD_ACTIONS_V1',
        'if (root === "assignments")',
        'return "leads.assign";',
        'if (root === "transfers")',
        'return "leads.reassign";',
    ],
    'server/security/corePermissionPolicy.test.ts': [
        'assignments.byLead',
        'assignments.create',
        'transfers.byLead',
        'transfers.create',
    ],
    'client/src/contexts/PermissionContext.tsx': [
        '"leads.edit"',
        '"leads.assign"',
        '"leads.reassign"',
    ],
    'client/src/pages/LeadProfile.tsx': [
        'usePermissions',
        'const canEditLead = canEdit && can("leads.edit")',
        'const canDeleteLead = can("leads.delete")',
        'const canAssignLead = can("leads.assign")',
        'const canReassignLead = can("leads.reassign")',
        'showTransfer && canReassignLead',
        'showDeleteConfirm && canDeleteLead',
    ],
}
for rel, needles in checks.items():
    data = read(rel)
    missing = [needle for needle in needles if needle not in data]
    if missing:
        raise SystemExit(f'POSTCHECK_FAILED={rel}:{missing}')

print(f'PATCH={PATCH}')
print(f'BASELINE={BASELINE}')
print('MODULES=leads,assignments,transfers')
print('SERVER_ASSIGNMENTS_GATE=leads.view,leads.assign')
print('SERVER_TRANSFERS_GATE=leads.view,leads.reassign')
print('LEADPROFILE_EDIT_GATE=leads.edit')
print('LEADPROFILE_DELETE_GATE=leads.delete')
print('LEADPROFILE_ASSIGN_GATE=leads.assign')
print('LEADPROFILE_REASSIGN_GATE=leads.reassign')
print('DEALS_ACTIVITY_FILES_GATING_CHANGED=NO')
print('EXISTING_TAM_ROW_BUSINESS_GUARDS_PRESERVED=YES')
print('CSS_CHANGED=NO')
print('DB_SCHEMA_CHANGED=NO')
print('DATA_CHANGED=NO')
print('FILES_CHANGED=server/security/corePermissionPolicy.ts,server/security/corePermissionPolicy.test.ts,client/src/contexts/PermissionContext.tsx,client/src/pages/LeadProfile.tsx')
