#!/usr/bin/env python3
from pathlib import Path
from urllib.request import urlopen

ROOT = Path('/var/www/TCRM-MAIN')
BASE_URL = 'https://raw.githubusercontent.com/mohamedamouseo-a11y/TCRM-main-patchs-/main/TCRM-PERMISSIONS-OPERATIONAL-MODULES-V2.py'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'ANCHOR_ERROR={label}:expected=1:actual={count}')
    return text.replace(old, new, 1)


# Apply cumulative V2 first.
source = urlopen(BASE_URL, timeout=30).read().decode('utf-8')
exec(compile(source, BASE_URL, 'exec'), {'__name__': '__main__'})

# V2.1: preserve existing after-sales task list semantics.
# The central gate synthesizes tasks.view/tasks.edit with assigned scope only when
# the permission engine has no explicit decision for these legacy roles. Their
# existing list route already filters rows by assignedTo=current user, so do not
# additionally require client.accountManagerId to match them.
scope_path = ROOT / 'server/security/operationalScopeEnforcement.ts'
scope = scope_path.read_text(encoding='utf-8')
old_scope = '''export async function assertTaskClientScopeForContext(ctx: any, clientId: number) {\n  return assertClientLinked(ctx, "tasks", clientId);\n}'''
new_scope = '''export async function assertTaskClientScopeForContext(ctx: any, clientId: number) {\n  const decision = requireDecision(ctx, "tasks");\n  const role = String(ctx?.user?.role || "");\n  if (decision.source === "legacy_role" && ["ServiceAdvisor", "PartsAgent", "CrmFollowUp"].includes(role)) {\n    return true;\n  }\n  return assertClientLinked(ctx, "tasks", clientId);\n}'''
if old_scope in scope:
    scope = replace_once(scope, old_scope, new_scope, 'legacy_after_sales_task_scope')
    scope_path.write_text(scope, encoding='utf-8')
    print('UPDATED=server/security/operationalScopeEnforcement.ts:V2.1')
elif 'decision.source === "legacy_role" && ["ServiceAdvisor", "PartsAgent", "CrmFollowUp"]' in scope:
    print('SKIP=server/security/operationalScopeEnforcement.ts:V2.1_already_applied')
else:
    raise SystemExit('ANCHOR_ERROR=legacy_after_sales_task_scope:missing')

# V2.1: an Account Management follow-up calendar event previously reused
# clientId in the descriptive leadId field. Once V2 makes leadId a security
# metadata field, that value must not be treated as a real lead id. Persist the
# actual creator instead so own/team meeting scope remains correct.
routers_path = ROOT / 'server/routers.ts'
routers = routers_path.read_text(encoding='utf-8')
old_followup = '''                await createCalendarEvent({\n                  summary,\n                  description: input.notes || "",\n                  startDateTime: startTime.toISOString(),\n                  endDateTime: endTime.toISOString(),\n                  attendees,\n                  leadId: input.clientId,\n                  leadName: clientName,\n                  agentName: agentDisplayName,\n                });'''
new_followup = '''                await createCalendarEvent({\n                  summary,\n                  description: input.notes || "",\n                  startDateTime: startTime.toISOString(),\n                  endDateTime: endTime.toISOString(),\n                  attendees,\n                  leadName: clientName,\n                  agentName: agentDisplayName,\n                  ownerUserId: ctx.user.id,\n                });'''
if old_followup in routers:
    routers = replace_once(routers, old_followup, new_followup, 'followup_calendar_owner_metadata')
    routers_path.write_text(routers, encoding='utf-8')
    print('UPDATED=server/routers.ts:V2.1')
elif 'leadName: clientName,\n                  agentName: agentDisplayName,\n                  ownerUserId: ctx.user.id,' in routers:
    print('SKIP=server/routers.ts:V2.1_already_applied')
else:
    raise SystemExit('ANCHOR_ERROR=followup_calendar_owner_metadata:missing')

print('PATCH=TCRM-PERMISSIONS-OPERATIONAL-MODULES-V2-1')
print('CUMULATIVE_V2=YES')
print('LEGACY_AFTER_SALES_TASKS_PRESERVED=YES')
print('FOLLOWUP_CALENDAR_SECURITY_METADATA_FIXED=YES')
print('DB_SCHEMA_CHANGED=NO')
print('DATA_CHANGED=NO')
