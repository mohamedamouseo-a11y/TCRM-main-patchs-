#!/usr/bin/env python3
# TCRM-FELFEL-AM-MEETING-SCOPE-V15
# Fix AccountManager Felfel meeting scope when a meeting is linked to BOTH
# clientId + leadId. AM ownership is defined by client.accountManagerId, while
# Sales ownership is lead-based. The old generic check preferred leadId first,
# incorrectly rejecting valid AM client ownership.

from pathlib import Path

target = Path("/var/www/TCRM-MAIN/server/security/operationalScopeEnforcement.ts")
if not target.exists():
    raise SystemExit("PATCH_FAIL=FILE_MISSING")

s = target.read_text(encoding="utf-8")

old_create = '''export async function assertMeetingCreateScopeForContext(ctx: any, resource?: { leadId?: number | null; clientId?: number | null }) {
  const decision = requireDecision(ctx, "meetings");
  if (resource?.leadId) return assertLeadLinked(ctx, "meetings", Number(resource.leadId));
  if (resource?.clientId) return assertClientLinked(ctx, "meetings", Number(resource.clientId));
  if (["all", "own", "assigned", "team"].includes(decision.scope)) return true;
  deny("meetings");
}'''

new_create = '''export async function assertMeetingCreateScopeForContext(ctx: any, resource?: { leadId?: number | null; clientId?: number | null }) {
  const decision = requireDecision(ctx, "meetings");
  const role = String(ctx?.user?.role || "").trim();
  const isAccountManager = ["AccountManager", "AccountManagerLead"].includes(role);

  // Account-management meetings are scoped by canonical client ownership
  // (clients.accountManagerId). A client commonly also carries leadId, so
  // checking leadId first incorrectly applies Sales ownership to AM users.
  if (isAccountManager && resource?.clientId) {
    return assertClientLinked(ctx, "meetings", Number(resource.clientId));
  }

  if (resource?.leadId) return assertLeadLinked(ctx, "meetings", Number(resource.leadId));
  if (resource?.clientId) return assertClientLinked(ctx, "meetings", Number(resource.clientId));
  if (["all", "own", "assigned", "team"].includes(decision.scope)) return true;
  deny("meetings");
}'''

if new_create not in s:
    if old_create not in s:
        raise SystemExit("PATCH_FAIL=CREATE_SCOPE_ANCHOR_MISSING")
    s = s.replace(old_create, new_create, 1)

old_scope = '''export async function assertFelfelMeetingScopeForContext(ctx: any, meeting: any) {
  const decision = requireDecision(ctx, "meetings");
  if (decision.scope === "all") return meeting;
  if (Number(meeting?.leadId ?? 0) > 0) {
    await assertLeadLinked(ctx, "meetings", Number(meeting.leadId));
    return meeting;
  }
  if (Number(meeting?.clientId ?? 0) > 0) {
    await assertClientLinked(ctx, "meetings", Number(meeting.clientId));
    return meeting;
  }
  await assertCalendarEventScopeForContext(ctx, { ownerUserId: Number(meeting?.ownerUserId ?? meeting?.createdByUserId ?? 0) });
  return meeting;
}'''

new_scope = '''export async function assertFelfelMeetingScopeForContext(ctx: any, meeting: any) {
  const decision = requireDecision(ctx, "meetings");
  if (decision.scope === "all") return meeting;

  const role = String(ctx?.user?.role || "").trim();
  const isAccountManager = ["AccountManager", "AccountManagerLead"].includes(role);

  // For AM users, a client-linked meeting follows client.accountManagerId scope
  // even when the same meeting also has a leadId.
  if (isAccountManager && Number(meeting?.clientId ?? 0) > 0) {
    await assertClientLinked(ctx, "meetings", Number(meeting.clientId));
    return meeting;
  }

  if (Number(meeting?.leadId ?? 0) > 0) {
    await assertLeadLinked(ctx, "meetings", Number(meeting.leadId));
    return meeting;
  }
  if (Number(meeting?.clientId ?? 0) > 0) {
    await assertClientLinked(ctx, "meetings", Number(meeting.clientId));
    return meeting;
  }
  await assertCalendarEventScopeForContext(ctx, { ownerUserId: Number(meeting?.ownerUserId ?? meeting?.createdByUserId ?? 0) });
  return meeting;
}'''

if new_scope not in s:
    if old_scope not in s:
        raise SystemExit("PATCH_FAIL=FELFEL_SCOPE_ANCHOR_MISSING")
    s = s.replace(old_scope, new_scope, 1)

target.write_text(s, encoding="utf-8")

print("PATCH=PASS")
print("FILES=server/security/operationalScopeEnforcement.ts")
print("AM_SCOPE=CLIENT_FIRST")
print("SALES_SCOPE=LEAD_FIRST")
print("CLIENT_OWNERSHIP=accountManagerId")
