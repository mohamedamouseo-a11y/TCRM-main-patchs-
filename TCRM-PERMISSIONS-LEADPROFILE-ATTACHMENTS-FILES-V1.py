#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('/var/www/TCRM-MAIN')
BASELINE = 'b608887466baebe78c08a2445c4972324457fcf1'
PATCH = 'TCRM-PERMISSIONS-LEADPROFILE-ATTACHMENTS-FILES-V1'


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
# 1) Central server permission mapping for the Lead Attachments alias.
#    Keep the existing fileStorage mapping and row/TAM/business guards additive.
# ---------------------------------------------------------------------------
rel = 'server/security/corePermissionPolicy.ts'
policy = read(rel)
policy = replace_once(
    policy,
    '''  const module = moduleFromPath(path);\n''',
    '''  // TCRM_PERMISSIONS_LEADPROFILE_ATTACHMENTS_FILES_V1\n  // LeadProfile stores attachment metadata under attachments.* while the file\n  // bytes are handled by fileStorage.*. Map both layers to the same files\n  // permission catalog so metadata aliases cannot bypass effective permissions.\n  if (root === "attachments") {\n    if (type === "query" || type === "subscription") return "files.view";\n    if (operation === "create") return "files.upload";\n    if (operation === "delete") return "files.delete";\n\n    // Any future protected attachment mutation fails closed behind files.edit.\n    return "files.edit";\n  }\n\n  const module = moduleFromPath(path);\n''',
    'attachments_files_policy',
)
write(rel, policy)


# ---------------------------------------------------------------------------
# 2) Lock the alias mapping with a focused regression test.
# ---------------------------------------------------------------------------
rel = 'server/security/corePermissionPolicy.test.ts'
test = read(rel)
anchor = '''  it("does not hijack sales contract handover", () => {\n'''
new_test = '''  it("maps LeadProfile attachment metadata routes to files permissions", () => {\n    expect(resolveCorePermissionKey("attachments.byLead", "query")).toBe("files.view");\n    expect(resolveCorePermissionKey("attachments.create", "mutation")).toBe("files.upload");\n    expect(resolveCorePermissionKey("attachments.delete", "mutation")).toBe("files.delete");\n    expect(resolveCorePermissionKey("attachments.update", "mutation")).toBe("files.edit");\n  });\n\n'''
if 'maps LeadProfile attachment metadata routes to files permissions' not in test:
    test = replace_once(test, anchor, new_test + anchor, 'attachments_files_mapping_test')
write(rel, test)


# ---------------------------------------------------------------------------
# 3) Permission context: request only the file decisions LeadProfile needs.
# ---------------------------------------------------------------------------
rel = 'client/src/contexts/PermissionContext.tsx'
ctx = read(rel)
ctx = replace_once(
    ctx,
    '''  "meetings.delete",\n  "contracts.view",\n  "campaigns.view",\n''',
    '''  "meetings.delete",\n  "contracts.view",\n  "files.view",\n  "files.upload",\n  "files.delete",\n  "campaigns.view",\n''',
    'permission_context_files_keys',
)
write(rel, ctx)


# ---------------------------------------------------------------------------
# 4) LeadProfile: query/card/upload/delete follow effective file permissions.
#    Existing canEdit role restriction remains additive for mutations.
# ---------------------------------------------------------------------------
rel = 'client/src/pages/LeadProfile.tsx'
page = read(rel)

page = replace_once(
    page,
    '''  const { can } = usePermissions();\n  const canViewDeal = can("deals.view");\n\n  const [editMode, setEditMode] = useState(false);\n''',
    '''  const { can } = usePermissions();\n  const canViewDeal = can("deals.view");\n  const canViewFiles = can("files.view");\n\n  const [editMode, setEditMode] = useState(false);\n''',
    'leadprofile_files_view_flag',
)

page = replace_once(
    page,
    '''  const { data: attachments, refetch: refetchAttachments } = trpc.attachments.byLead.useQuery({ leadId }, { enabled: Number.isFinite(leadId) && !!lead, retry: false });\n''',
    '''  const { data: attachments, refetch: refetchAttachments } = trpc.attachments.byLead.useQuery({ leadId }, { enabled: Number.isFinite(leadId) && !!lead && canViewFiles, retry: false });\n''',
    'leadprofile_attachments_query_view_gate',
)

page = replace_once(
    page,
    '''  const canCreateActivity = can("activities.create");\n  const canEditActivity = can("activities.edit");\n  const canDeleteActivity = can("activities.delete");\n  const isSalesRole = isSalesAgentRole(normalizedUserRole);\n''',
    '''  const canCreateActivity = can("activities.create");\n  const canEditActivity = can("activities.edit");\n  const canDeleteActivity = can("activities.delete");\n  const canUploadLeadAttachment = canEdit && can("files.upload");\n  const canDeleteLeadAttachment = canEdit && can("files.delete");\n  const isSalesRole = isSalesAgentRole(normalizedUserRole);\n''',
    'leadprofile_files_mutation_flags',
)

page = replace_once(
    page,
    '''              {/* ── Attachments ── */}\n              <Card className="rounded-2xl border-border/40 shadow-sm overflow-hidden">\n''',
    '''              {/* ── Attachments ── */}\n              {canViewFiles && (\n              <Card className="rounded-2xl border-border/40 shadow-sm overflow-hidden">\n''',
    'leadprofile_attachments_card_open_gate',
)

page = replace_once(
    page,
    '''              </Card>\n\n              {/* ── Transfer History ── */}\n''',
    '''              </Card>\n              )}\n\n              {/* ── Transfer History ── */}\n''',
    'leadprofile_attachments_card_close_gate',
)

page = replace_once(
    page,
    '''                  {canEdit && (\n                    <form onSubmit={attachmentHandleSubmit(onAddAttachment)} className="px-6 py-5 flex flex-col gap-4 rounded-lg border border-dashed border-border/50 p-2.5">\n''',
    '''                  {canUploadLeadAttachment && (\n                    <form onSubmit={attachmentHandleSubmit(onAddAttachment)} className="px-6 py-5 flex flex-col gap-4 rounded-lg border border-dashed border-border/50 p-2.5">\n''',
    'leadprofile_attachment_upload_form_gate',
)

page = replace_once(
    page,
    '''                        disabled={createAttachment.isPending || uploadLeadAttachment.isPending}\n''',
    '''                        disabled={!canUploadLeadAttachment || createAttachment.isPending || uploadLeadAttachment.isPending}\n''',
    'leadprofile_attachment_upload_submit_gate',
)

page = replace_once(
    page,
    '''                      onAction={() => {\n                        const target = document.getElementById("attachment-file-input");\n                        target?.focus();\n                      }}\n''',
    '''                      onAction={canUploadLeadAttachment ? () => {\n                        const target = document.getElementById("attachment-file-input");\n                        target?.focus();\n                      } : undefined}\n''',
    'leadprofile_attachment_empty_action_gate',
)

page = replace_once(
    page,
    '''                                {canEdit && (\n                                  <Button\n                                    variant="ghost"\n                                    size="icon"\n                                    className="h-6 w-6 rounded-md border border-red-200/60 bg-red-50/40 text-red-600 shadow-none transition-colors hover:border-red-300 hover:bg-red-100 hover:text-red-700 dark:border-red-900/50 dark:bg-red-950/20 dark:text-red-400 dark:hover:bg-red-950/40"\n''',
    '''                                {canDeleteLeadAttachment && (\n                                  <Button\n                                    variant="ghost"\n                                    size="icon"\n                                    className="h-6 w-6 rounded-md border border-red-200/60 bg-red-50/40 text-red-600 shadow-none transition-colors hover:border-red-300 hover:bg-red-100 hover:text-red-700 dark:border-red-900/50 dark:bg-red-950/20 dark:text-red-400 dark:hover:bg-red-950/40"\n''',
    'leadprofile_attachment_delete_gate',
)

write(rel, page)


# ---------------------------------------------------------------------------
# 5) Static post-checks. No router/CSS/DB/data changes.
# ---------------------------------------------------------------------------
checks = {
    'server/security/corePermissionPolicy.ts': [
        'TCRM_PERMISSIONS_LEADPROFILE_ATTACHMENTS_FILES_V1',
        'if (root === "attachments")',
        'if (operation === "create") return "files.upload"',
        'if (operation === "delete") return "files.delete"',
        'return "files.edit"',
    ],
    'server/security/corePermissionPolicy.test.ts': [
        'attachments.byLead',
        'attachments.create',
        'attachments.delete',
        'attachments.update',
    ],
    'client/src/contexts/PermissionContext.tsx': [
        '"files.view"',
        '"files.upload"',
        '"files.delete"',
    ],
    'client/src/pages/LeadProfile.tsx': [
        'const canViewFiles = can("files.view")',
        'const canUploadLeadAttachment = canEdit && can("files.upload")',
        'const canDeleteLeadAttachment = canEdit && can("files.delete")',
        '!!lead && canViewFiles',
        '{canViewFiles && (',
        '{canUploadLeadAttachment && (',
        'onAction={canUploadLeadAttachment ? () => {',
        '{canDeleteLeadAttachment && (',
    ],
}
for rel, needles in checks.items():
    data = read(rel)
    missing = [needle for needle in needles if needle not in data]
    if missing:
        raise SystemExit(f'POSTCHECK_FAILED={rel}:{missing}')

print(f'PATCH={PATCH}')
print(f'BASELINE={BASELINE}')
print('MODULES=files,attachments')
print('ATTACHMENTS_VIEW_SERVER_GATE=files.view')
print('ATTACHMENTS_CREATE_SERVER_GATE=files.upload')
print('ATTACHMENTS_DELETE_SERVER_GATE=files.delete')
print('ATTACHMENTS_FUTURE_MUTATION_FAIL_CLOSED=files.edit')
print('FILESTORAGE_EXISTING_GATE_PRESERVED=YES')
print('ATTACHMENTS_VIEW_UI_GATE=files.view')
print('ATTACHMENTS_UPLOAD_UI_GATE=files.upload+legacy_canEdit')
print('ATTACHMENTS_DELETE_UI_GATE=files.delete+legacy_canEdit')
print('EXISTING_TAM_SALES_ROW_GUARDS_PRESERVED=YES')
print('ROUTERS_CHANGED=NO')
print('CSS_CHANGED=NO')
print('DB_SCHEMA_CHANGED=NO')
print('DATA_CHANGED=NO')
print('FILES_CHANGED=server/security/corePermissionPolicy.ts,server/security/corePermissionPolicy.test.ts,client/src/contexts/PermissionContext.tsx,client/src/pages/LeadProfile.tsx')
