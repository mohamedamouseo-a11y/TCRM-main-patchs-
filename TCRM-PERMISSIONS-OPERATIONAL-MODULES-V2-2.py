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


def update_file(rel: str, transform):
    path = ROOT / rel
    if not path.exists():
        raise SystemExit(f'MISSING_FILE={rel}')
    before = path.read_text(encoding='utf-8')
    after = transform(before)
    if after != before:
        path.write_text(after, encoding='utf-8')
        print(f'UPDATED={rel}:V2.2')
    else:
        print(f'SKIP={rel}:V2.2_no_change')


# ---------------------------------------------------------------------------
# 1) Re-run cumulative V2 with the anchor bug fixed in-memory.
#
# V2 intentionally performs two sequential replacements of the same legacy
# activities scope block (byLead + create). The original helper incorrectly
# required the block to be globally unique inside the Activities section, so
# the first replacement aborted when the valid count was 2. Scope the helper to
# replace exactly ONE matching occurrence per call while still failing closed
# when no anchor exists. All other V2 section edits remain unchanged.
# ---------------------------------------------------------------------------
source = urlopen(BASE_URL, timeout=30).read().decode('utf-8')
old_helper = '''def replace_in_section(text: str, start: str, end: str, old: str, new: str, label: str) -> str:\n    s = text.find(start)\n    if s < 0:\n        raise SystemExit(f'SECTION_START_MISSING={label}')\n    e = text.find(end, s + len(start))\n    if e < 0:\n        raise SystemExit(f'SECTION_END_MISSING={label}')\n    section = text[s:e]\n    section2 = replace_once(section, old, new, label)\n    return text[:s] + section2 + text[e:]\n'''
new_helper = '''def replace_in_section(text: str, start: str, end: str, old: str, new: str, label: str) -> str:\n    s = text.find(start)\n    if s < 0:\n        raise SystemExit(f'SECTION_START_MISSING={label}')\n    e = text.find(end, s + len(start))\n    if e < 0:\n        raise SystemExit(f'SECTION_END_MISSING={label}')\n    section = text[s:e]\n    count = section.count(old)\n    if count < 1:\n        raise SystemExit(f'ANCHOR_ERROR={label}:expected>=1:actual=0')\n    section2 = section.replace(old, new, 1)\n    return text[:s] + section2 + text[e:]\n'''
source = replace_once(source, old_helper, new_helper, 'v2_replace_in_section_helper')
exec(compile(source, BASE_URL, 'exec'), {'__name__': '__main__'})


# ---------------------------------------------------------------------------
# 2) V2.1 preservation fix: legacy after-sales task list semantics.
# ---------------------------------------------------------------------------
def patch_operational_scope(text: str) -> str:
    marker = 'decision.source === "legacy_role" && ["ServiceAdvisor", "PartsAgent", "CrmFollowUp"]'
    if marker in text:
        return text
    old = '''export async function assertTaskClientScopeForContext(ctx: any, clientId: number) {\n  return assertClientLinked(ctx, "tasks", clientId);\n}'''
    new = '''export async function assertTaskClientScopeForContext(ctx: any, clientId: number) {\n  const decision = requireDecision(ctx, "tasks");\n  const role = String(ctx?.user?.role || "");\n  if (decision.source === "legacy_role" && ["ServiceAdvisor", "PartsAgent", "CrmFollowUp"].includes(role)) {\n    return true;\n  }\n  return assertClientLinked(ctx, "tasks", clientId);\n}'''
    return replace_once(text, old, new, 'legacy_after_sales_task_scope')


update_file('server/security/operationalScopeEnforcement.ts', patch_operational_scope)


# ---------------------------------------------------------------------------
# 3) V2.1 calendar metadata correction for AM follow-up events.
# ---------------------------------------------------------------------------
def patch_followup_calendar(text: str) -> str:
    fixed = '''                  leadName: clientName,\n                  agentName: agentDisplayName,\n                  ownerUserId: ctx.user.id,'''
    if fixed in text:
        return text
    old = '''                await createCalendarEvent({\n                  summary,\n                  description: input.notes || "",\n                  startDateTime: startTime.toISOString(),\n                  endDateTime: endTime.toISOString(),\n                  attendees,\n                  leadId: input.clientId,\n                  leadName: clientName,\n                  agentName: agentDisplayName,\n                });'''
    new = '''                await createCalendarEvent({\n                  summary,\n                  description: input.notes || "",\n                  startDateTime: startTime.toISOString(),\n                  endDateTime: endTime.toISOString(),\n                  attendees,\n                  leadName: clientName,\n                  agentName: agentDisplayName,\n                  ownerUserId: ctx.user.id,\n                });'''
    return replace_once(text, old, new, 'followup_calendar_owner_metadata')


update_file('server/routers.ts', patch_followup_calendar)


# ---------------------------------------------------------------------------
# 4) V2.2 path correction: Client Tasks are nested under accountManagement.
#
# Real tRPC paths are accountManagement.clientTasks.*, not clientTasks.*.
# Without this alias the central permission middleware would never attach a
# tasks.* PermissionDecision, making the task scope helpers fail closed or the
# route remain on legacy-only authorization. Keep the direct alias too in case a
# future top-level clientTasks router is introduced.
# ---------------------------------------------------------------------------
def patch_core_policy(text: str) -> str:
    if 'operation.startsWith("clienttasks")' in text:
        return text
    old = '''    if (ACCOUNT_MANAGEMENT_CLIENT_OPERATIONS.has(operation)) return "clients";\n    if (ACCOUNT_MANAGEMENT_CONTRACT_OPERATIONS.has(operation)) return "contracts";\n  }\n\n  if (segments[0] === "clientTasks") return "tasks";'''
    new = '''    if (ACCOUNT_MANAGEMENT_CLIENT_OPERATIONS.has(operation)) return "clients";\n    if (ACCOUNT_MANAGEMENT_CONTRACT_OPERATIONS.has(operation)) return "contracts";\n    if (operation.startsWith("clienttasks")) return "tasks";\n  }\n\n  if (segments[0] === "clientTasks") return "tasks";'''
    return replace_once(text, old, new, 'nested_client_tasks_permission_alias')


update_file('server/security/corePermissionPolicy.ts', patch_core_policy)


def patch_core_policy_test(text: str) -> str:
    if 'accountManagement.clientTasks.list' in text:
        return text
    old = '''    expect(resolveCorePermissionKey("clientTasks.list", "query")).toBe("tasks.view");\n    expect(resolveCorePermissionKey("clientTasks.create", "mutation")).toBe("tasks.create");'''
    new = '''    expect(resolveCorePermissionKey("clientTasks.list", "query")).toBe("tasks.view");\n    expect(resolveCorePermissionKey("clientTasks.create", "mutation")).toBe("tasks.create");\n    expect(resolveCorePermissionKey("accountManagement.clientTasks.list", "query")).toBe("tasks.view");\n    expect(resolveCorePermissionKey("accountManagement.clientTasks.create", "mutation")).toBe("tasks.create");\n    expect(resolveCorePermissionKey("accountManagement.clientTasks.update", "mutation")).toBe("tasks.edit");\n    expect(resolveCorePermissionKey("accountManagement.clientTasks.delete", "mutation")).toBe("tasks.delete");'''
    return replace_once(text, old, new, 'nested_client_tasks_policy_tests')


update_file('server/security/corePermissionPolicy.test.ts', patch_core_policy_test)


# ---------------------------------------------------------------------------
# 5) Static post-apply assertions. These do not touch DB/data.
# ---------------------------------------------------------------------------
checks = {
    'server/routers.ts': [
        'TCRM_PERMISSIONS_OPERATIONAL_MODULES_V2',
        'await assertActivityLeadScopeForContext(ctx, input.leadId);',
        'await assertActivityScopeForContext(ctx, id);',
        'await assertTaskClientScopeForContext(ctx, input.clientId);',
        'await assertTaskScopeForContext(ctx, input.id);',
        'await assertMeetingCreateScopeForContext(ctx, { leadId: input.leadId });',
        'await assertCalendarEventScopeForContext(ctx, existingEvent);',
        'await assertContractClientScopeForContext(ctx, input.clientId);',
        'const existing = await assertContractScopeForContext(ctx, id);',
        'ownerUserId: ctx.user.id,',
    ],
    'server/security/corePermissionPolicy.ts': [
        '"activities"', '"tasks"', '"meetings"', '"contracts"',
        'operation.startsWith("clienttasks")',
    ],
    'server/security/operationalScopeEnforcement.ts': [
        'assertActivityScopeForContext',
        'assertTaskScopeForContext',
        'assertCalendarEventScopeForContext',
        'assertContractScopeForContext',
        'decision.source === "legacy_role"',
    ],
    'server/googleCalendar.ts': [
        'tcrmOwnerUserId',
        'extendedProperties',
    ],
    'server/_core/trpc.ts': [
        'TCRM_OPERATIONAL_TASK_LEGACY_FALLBACK_V2',
    ],
}
for rel, needles in checks.items():
    data = (ROOT / rel).read_text(encoding='utf-8')
    missing = [needle for needle in needles if needle not in data]
    if missing:
        raise SystemExit(f'POSTCHECK_FAILED={rel}:{missing}')

print('PATCH=TCRM-PERMISSIONS-OPERATIONAL-MODULES-V2-2')
print('BASELINE=61c66cf4ec8fe2695cf798dc10ab48084066a90d')
print('ANCHOR_DUPLICATE_FIX=YES')
print('CUMULATIVE_V2=YES')
print('V2_1_PRESERVATION_FIXES=YES')
print('NESTED_CLIENT_TASKS_PERMISSION_ALIAS=YES')
print('MODULES=activities,tasks,meetings,contracts')
print('DB_SCHEMA_CHANGED=NO')
print('DATA_CHANGED=NO')
