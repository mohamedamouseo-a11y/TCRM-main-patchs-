#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('/var/www/TCRM-MAIN')
BASELINE = 'c0e9f76e53323bc5ea8511fccfc53b525c3952f0'
PATCH = 'TCRM-PERMISSIONS-LEADPROFILE-ACTIVITIES-ACTIONS-V1'


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
# 1) Permission context: request the remaining activity action decisions.
# ---------------------------------------------------------------------------
rel = 'client/src/contexts/PermissionContext.tsx'
ctx = read(rel)
ctx = replace_once(
    ctx,
    '''  "clients.export",\n  "activities.create",\n  "tasks.view",\n''',
    '''  "clients.export",\n  "activities.create",\n  "activities.edit",\n  "activities.delete",\n  "tasks.view",\n''',
    'permission_context_activity_keys',
)
write(rel, ctx)


# ---------------------------------------------------------------------------
# 2) LeadProfile: activity create/edit/delete UI uses effective permissions.
#    Internal notes, deals, files and all existing business logic stay untouched.
# ---------------------------------------------------------------------------
rel = 'client/src/pages/LeadProfile.tsx'
page = read(rel)

page = replace_once(
    page,
    '''  const canAssignLead = can("leads.assign");\n  const canReassignLead = can("leads.reassign");\n  const isSalesRole = isSalesAgentRole(normalizedUserRole);\n''',
    '''  const canAssignLead = can("leads.assign");\n  const canReassignLead = can("leads.reassign");\n  const canCreateActivity = can("activities.create");\n  const canEditActivity = can("activities.edit");\n  const canDeleteActivity = can("activities.delete");\n  const isSalesRole = isSalesAgentRole(normalizedUserRole);\n''',
    'leadprofile_activity_flags',
)

page = replace_once(
    page,
    '''                          <Button variant="outline" size="sm" className="gap-1.5 rounded-lg h-7 text-xs" onClick={() => setShowActivity(true)}>\n                            <Plus size={12} />\n                            {t("newActivity")}\n                          </Button>\n''',
    '''                          {canCreateActivity && (\n                            <Button variant="outline" size="sm" className="gap-1.5 rounded-lg h-7 text-xs" onClick={() => setShowActivity(true)}>\n                              <Plus size={12} />\n                              {t("newActivity")}\n                            </Button>\n                          )}\n''',
    'leadprofile_new_activity_button',
)

page = replace_once(
    page,
    '''                      onAction={composerMode === "note" ? undefined : () => setShowActivity(true)}\n''',
    '''                      onAction={composerMode === "note" ? undefined : (canCreateActivity ? () => setShowActivity(true) : undefined)}\n''',
    'leadprofile_empty_activity_action',
)

page = replace_once(
    page,
    '''                            onEditActivity={(activity) => setEditingActivity(activity)}\n                            canEdit={canEdit}\n                            userId={user?.id}\n''',
    '''                            onEditActivity={(activity) => setEditingActivity(activity)}\n                            canEditActivity={canEditActivity}\n                            canDeleteActivity={canDeleteActivity}\n                            userId={user?.id}\n''',
    'leadprofile_feed_permissions',
)

page = replace_once(
    page,
    '''      <Dialog open={showActivity} onOpenChange={(o) => { setShowActivity(o); if (!o) { setActTypeValue("Call"); setActOutcomeValue(undefined); actReset(); } }}>\n''',
    '''      <Dialog open={showActivity && canCreateActivity} onOpenChange={(o) => { setShowActivity(o && canCreateActivity); if (!o) { setActTypeValue("Call"); setActOutcomeValue(undefined); actReset(); } }}>\n''',
    'leadprofile_activity_dialog_gate',
)

page = replace_once(
    page,
    '''              <Button type="submit" style={{ background: tokens.primaryColor }} className="text-white rounded-xl text-sm h-9 min-w-[80px]" disabled={createActivity.isPending}>\n''',
    '''              <Button type="submit" style={{ background: tokens.primaryColor }} className="text-white rounded-xl text-sm h-9 min-w-[80px]" disabled={!canCreateActivity || createActivity.isPending}>\n''',
    'leadprofile_activity_submit_gate',
)

page = replace_once(
    page,
    '''      <Dialog open={!!editingActivity} onOpenChange={(open) => { if (!open) setEditingActivity(null); }}>\n''',
    '''      <Dialog open={!!editingActivity && canEditActivity} onOpenChange={(open) => { if (!open || !canEditActivity) setEditingActivity(null); }}>\n''',
    'leadprofile_activity_edit_dialog_gate',
)

page = replace_once(
    page,
    '''                  disabled={updateActivityMutation.isPending}\n                  onClick={() => {\n''',
    '''                  disabled={!canEditActivity || updateActivityMutation.isPending}\n                  onClick={() => {\n''',
    'leadprofile_activity_edit_submit_gate',
)

page = replace_once(
    page,
    '''  onEditActivity,\n  canEdit,\n  userId,\n''',
    '''  onEditActivity,\n  canEditActivity,\n  canDeleteActivity,\n  userId,\n''',
    'feeditem_destructure_permissions',
)

page = replace_once(
    page,
    '''  onEditActivity: (activity: { id: number; type: string; outcome?: string; notes?: string; activityTime?: string }) => void;\n  canEdit: boolean;\n  userId?: number;\n''',
    '''  onEditActivity: (activity: { id: number; type: string; outcome?: string; notes?: string; activityTime?: string }) => void;\n  canEditActivity: boolean;\n  canDeleteActivity: boolean;\n  userId?: number;\n''',
    'feeditem_type_permissions',
)

page = replace_once(
    page,
    '''  const canDeleteCurrentNote = isNote ? (item.data.userId === userId || userRole === "Admin" || userRole === "admin") : false;\n  const canDeleteThis = isNote ? canDeleteCurrentNote : canEdit;\n''',
    '''  const canDeleteCurrentNote = isNote ? (item.data.userId === userId || userRole === "Admin" || userRole === "admin") : false;\n  const canDeleteThis = isNote ? canDeleteCurrentNote : canDeleteActivity;\n''',
    'feeditem_delete_permission',
)

page = replace_once(
    page,
    '''              {!isNote && canEdit && (\n''',
    '''              {!isNote && canEditActivity && (\n''',
    'feeditem_edit_permission',
)

write(rel, page)


# ---------------------------------------------------------------------------
# 3) Static post-checks. No server/router/CSS/data changes in this phase.
# ---------------------------------------------------------------------------
checks = {
    'client/src/contexts/PermissionContext.tsx': [
        '"activities.create"',
        '"activities.edit"',
        '"activities.delete"',
    ],
    'client/src/pages/LeadProfile.tsx': [
        'const canCreateActivity = can("activities.create")',
        'const canEditActivity = can("activities.edit")',
        'const canDeleteActivity = can("activities.delete")',
        'showActivity && canCreateActivity',
        '!!editingActivity && canEditActivity',
        'canEditActivity={canEditActivity}',
        'canDeleteActivity={canDeleteActivity}',
        'canDeleteThis = isNote ? canDeleteCurrentNote : canDeleteActivity',
        '!isNote && canEditActivity',
    ],
}
for rel, needles in checks.items():
    data = read(rel)
    missing = [needle for needle in needles if needle not in data]
    if missing:
        raise SystemExit(f'POSTCHECK_FAILED={rel}:{missing}')

print(f'PATCH={PATCH}')
print(f'BASELINE={BASELINE}')
print('MODULES=activities')
print('ACTIVITY_CREATE_UI_GATE=activities.create')
print('ACTIVITY_EDIT_UI_GATE=activities.edit')
print('ACTIVITY_DELETE_UI_GATE=activities.delete')
print('EXISTING_ACTIVITY_SERVER_GATE_PRESERVED=YES')
print('INTERNAL_NOTES_GATING_CHANGED=NO')
print('DEALS_FILES_LEAD_GATING_CHANGED=NO')
print('ROUTERS_CHANGED=NO')
print('CSS_CHANGED=NO')
print('DB_SCHEMA_CHANGED=NO')
print('DATA_CHANGED=NO')
print('FILES_CHANGED=client/src/contexts/PermissionContext.tsx,client/src/pages/LeadProfile.tsx')
