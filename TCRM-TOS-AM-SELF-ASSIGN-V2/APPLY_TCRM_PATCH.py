#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()


def replace_once(rel_path: str, old: str, new: str) -> None:
    path = ROOT / rel_path
    if not path.exists():
        raise SystemExit(f"Missing expected file: {path}")
    text = path.read_text(encoding="utf-8")
    if new in text:
        print(f"[skip] already patched: {rel_path}")
        return
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"Expected exactly one patch anchor in {rel_path}, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"[ok] patched: {rel_path}")


# 1) Ask TOS for Account Management only in the Handover directory flow.
replace_once(
    "server/services/tosIntegrationService.ts",
    '''export async function getTosProjectTeamDirectory(clientId?: number) {
  const { apiUrl, apiKey } = await requireTosIntegration();
  const directoryUrl = new URL(buildOperationalUrl(apiUrl, "team-directory"));
  if (Number.isInteger(clientId) && Number(clientId) > 0) {
    directoryUrl.searchParams.set("crmClientId", String(clientId));
  }
  const response = await fetch(directoryUrl.toString(), {''',
    '''export async function getTosProjectTeamDirectory(
  clientId?: number,
  options: { includeAccountManagement?: boolean } = {},
) {
  const { apiUrl, apiKey } = await requireTosIntegration();
  const directoryUrl = new URL(buildOperationalUrl(apiUrl, "team-directory"));
  if (Number.isInteger(clientId) && Number(clientId) > 0) {
    directoryUrl.searchParams.set("crmClientId", String(clientId));
  }
  if (options.includeAccountManagement) {
    directoryUrl.searchParams.set("includeAccountManagement", "1");
  }
  const response = await fetch(directoryUrl.toString(), {''',
)

# 2) Handover directory opts in; task-assignment directory calls keep the existing default.
replace_once(
    "server/routers.ts",
    '''        return getTosProjectTeamDirectory(input?.clientId);''',
    '''        return getTosProjectTeamDirectory(input?.clientId, { includeAccountManagement: true });''',
)

# 3) Backend guard: a regular AccountManager may only change their own pending TOS owner entry.
replace_once(
    "server/routers.ts",
    '''async function assertTosProjectTeamEditAccess(ctx: any, clientId: number) {
  await assertClientOperationAllowed({ id: Number(ctx.user.id), role: normalizeUserRole(ctx.user.role), teamId: ctx.user.teamId }, clientId, "project_team.manage");
  const client = await getClientById(clientId);
  if (!client || (client as any).deletedAt) throw new TRPCError({ code: "NOT_FOUND", message: "Client not found" });
  return client;
}''',
    '''async function assertTosProjectTeamEditAccess(ctx: any, clientId: number) {
  await assertClientOperationAllowed({ id: Number(ctx.user.id), role: normalizeUserRole(ctx.user.role), teamId: ctx.user.teamId }, clientId, "project_team.manage");
  const client = await getClientById(clientId);
  if (!client || (client as any).deletedAt) throw new TRPCError({ code: "NOT_FOUND", message: "Client not found" });
  return client;
}

function normalizeTosIdentityEmail(value: unknown) {
  return String(value ?? "").trim().toLowerCase();
}

function isAccountManagementDirectoryDepartment(department: any) {
  const raw = `${department?.key ?? ""} ${department?.name ?? ""}`
    .normalize("NFKC")
    .toLowerCase()
    .replace(/[\\s_\\-]+/g, "");
  return raw.includes("accountmanagement")
    || raw.includes("accountmanager")
    || raw.includes("ادارةالحساب")
    || raw.includes("إدارةالحساب");
}

async function sanitizeRegularAccountManagerTosOwners(ctx: any, clientId: number, requestedOwners: any[]) {
  const actor = await getUserById(Number(ctx.user.id));
  const actorEmails = new Set(
    [ctx.user?.email, (actor as any)?.email, (actor as any)?.centralEmail]
      .map(normalizeTosIdentityEmail)
      .filter(Boolean),
  );
  if (!actorEmails.size) {
    throw new TRPCError({ code: "PRECONDITION_FAILED", message: "Your TCRM account has no email identity that can be matched to TOS." });
  }

  const directory = await getTosProjectTeamDirectory(clientId, { includeAccountManagement: true });
  const accountManagementMembers = (Array.isArray((directory as any)?.departments) ? (directory as any).departments : [])
    .filter(isAccountManagementDirectoryDepartment)
    .flatMap((department: any) => (Array.isArray(department?.members) ? department.members : []).map((member: any) => ({
      ...member,
      departmentKey: member?.departmentKey || department?.key,
      departmentName: member?.departmentName || department?.name,
    })));

  const selfMember = accountManagementMembers.find((member: any) => actorEmails.has(normalizeTosIdentityEmail(member?.email)));
  if (!selfMember) {
    throw new TRPCError({
      code: "PRECONDITION_FAILED",
      message: "Your Account Management user is not mapped to a TOS employee by email. Ask an administrator to align the TCRM/TOS email identity.",
    });
  }

  const selfTosUserId = String(selfMember?.tosUserId || selfMember?.userId || selfMember?.id || "").trim();
  if (!selfTosUserId) {
    throw new TRPCError({ code: "PRECONDITION_FAILED", message: "The matched TOS employee has no usable user id." });
  }

  const currentBrief = await getHandoverBrief(clientId);
  const currentOwners = Array.isArray((currentBrief as any)?.tosProjectOwners)
    ? ((currentBrief as any).tosProjectOwners as any[])
    : [];
  const currentById = new Map(
    currentOwners
      .map((owner: any) => [String(owner?.tosUserId || "").trim(), owner] as const)
      .filter(([id]) => Boolean(id)),
  );
  const requestedById = new Map(
    (requestedOwners || [])
      .map((owner: any) => [String(owner?.tosUserId || "").trim(), owner] as const)
      .filter(([id]) => Boolean(id)),
  );

  for (const id of requestedById.keys()) {
    if (id !== selfTosUserId && !currentById.has(id)) {
      throw new TRPCError({ code: "FORBIDDEN", message: "Account Managers can only add themselves to the TOS project team." });
    }
  }
  for (const id of currentById.keys()) {
    if (id !== selfTosUserId && !requestedById.has(id)) {
      throw new TRPCError({ code: "FORBIDDEN", message: "Account Managers cannot remove another employee from the TOS project team draft." });
    }
  }

  const sanitized = currentOwners.filter((owner: any) => String(owner?.tosUserId || "").trim() !== selfTosUserId);
  if (requestedById.has(selfTosUserId)) {
    sanitized.push({
      tosUserId: selfTosUserId,
      name: String(selfMember?.name || "").trim(),
      email: String(selfMember?.email || "").trim() || undefined,
      departmentKey: String(selfMember?.departmentKey || "").trim() || undefined,
      departmentName: String(selfMember?.departmentName || "").trim() || undefined,
    });
  }
  return sanitized;
}''',
)

replace_once(
    "server/routers.ts",
    '''        await assertTosProjectTeamEditAccess(ctx, input.clientId);
        const id = await saveTosProjectOwners(
          input.clientId,
          input.tosProjectOwners,
          ctx.user.id,''',
    '''        await assertTosProjectTeamEditAccess(ctx, input.clientId);
        const ownersToSave = normalizeUserRole(ctx.user.role) === "AccountManager"
          ? await sanitizeRegularAccountManagerTosOwners(ctx, input.clientId, input.tosProjectOwners)
          : input.tosProjectOwners;
        const id = await saveTosProjectOwners(
          input.clientId,
          ownersToSave,
          ctx.user.id,''',
)

# 4) UI selector: regular AM can toggle only the directory identity matching their TCRM email.
replace_once(
    "client/src/components/TosProjectTeamSelector.tsx",
    '''  isRTL?: boolean;
  disabled?: boolean;
};''',
    '''  isRTL?: boolean;
  disabled?: boolean;
  selfOnly?: boolean;
  currentUserEmails?: string[];
};''',
)

replace_once(
    "client/src/components/TosProjectTeamSelector.tsx",
    '''function memberKey(member: any) {
  return String(member?.tosUserId || member?.userId || member?.id || "").trim();
}''',
    '''function memberKey(member: any) {
  return String(member?.tosUserId || member?.userId || member?.id || "").trim();
}

function normalizeEmail(value: unknown) {
  return String(value ?? "").trim().toLowerCase();
}''',
)

replace_once(
    "client/src/components/TosProjectTeamSelector.tsx",
    '''export function TosProjectTeamSelector({ clientId, value, onChange, isRTL = false, disabled = false }: Props) {''',
    '''export function TosProjectTeamSelector({
  clientId,
  value,
  onChange,
  isRTL = false,
  disabled = false,
  selfOnly = false,
  currentUserEmails = [],
}: Props) {''',
)

replace_once(
    "client/src/components/TosProjectTeamSelector.tsx",
    '''  const departments = Array.isArray(directoryQ.data?.departments) ? directoryQ.data.departments : [];

  const toggleMember = (member: any, department: any) => {
    const tosUserId = memberKey(member);
    if (!tosUserId || disabled || projectMemberById.has(tosUserId)) return;''',
    '''  const departments = Array.isArray(directoryQ.data?.departments) ? directoryQ.data.departments : [];
  const currentUserEmailSet = React.useMemo(
    () => new Set((currentUserEmails || []).map(normalizeEmail).filter(Boolean)),
    [currentUserEmails.join("|")],
  );
  const isSelfMember = React.useCallback(
    (member: any) => currentUserEmailSet.has(normalizeEmail(member?.email)),
    [currentUserEmailSet],
  );

  const toggleMember = (member: any, department: any) => {
    const tosUserId = memberKey(member);
    if (!tosUserId || disabled || projectMemberById.has(tosUserId) || (selfOnly && !isSelfMember(member))) return;''',
)

replace_once(
    "client/src/components/TosProjectTeamSelector.tsx",
    '''          {isRTL ? "لا يوجد موظفون متاحون بعد استبعاد قسم إدارة الحسابات." : "No eligible employees are available after excluding Account Management."}''',
    '''          {isRTL ? "لا يوجد موظفون متاحون في دليل فريق TOS." : "No employees are available in the TOS team directory."}''',
)

replace_once(
    "client/src/components/TosProjectTeamSelector.tsx",
    '''                  const checked = visibleSelectedIds.has(id);
                  const role = currentMembership?.projectRole || (locallySelectedIds.has(id) ? "OWNER" : "");
                  return (
                    <label
                      key={id}
                      className={`flex items-center gap-3 px-3 py-2.5 transition ${checked ? "bg-violet-50" : "hover:bg-zinc-50"} ${disabled || isCurrentTosMember ? "cursor-default" : "cursor-pointer"} ${disabled ? "opacity-60" : ""}`}
                      title={isCurrentTosMember ? (isRTL ? "هذه العضوية تُدار من داخل TOS" : "This membership is managed inside TOS") : undefined}
                    >
                      <input
                        type="checkbox"
                        className="h-4 w-4 rounded border-zinc-300 accent-violet-600"
                        checked={checked}
                        disabled={disabled || isCurrentTosMember}
                        onChange={() => toggleMember(member, department)}
                      />''',
    '''                  const checked = visibleSelectedIds.has(id);
                  const role = currentMembership?.projectRole || (locallySelectedIds.has(id) ? "OWNER" : "");
                  const selfSelectable = !selfOnly || isSelfMember(member);
                  const rowDisabled = disabled || isCurrentTosMember || !selfSelectable;
                  return (
                    <label
                      key={id}
                      className={`flex items-center gap-3 px-3 py-2.5 transition ${checked ? "bg-violet-50" : "hover:bg-zinc-50"} ${rowDisabled ? "cursor-default" : "cursor-pointer"} ${disabled || !selfSelectable ? "opacity-60" : ""}`}
                      title={
                        isCurrentTosMember
                          ? (isRTL ? "هذه العضوية تُدار من داخل TOS" : "This membership is managed inside TOS")
                          : selfOnly && !selfSelectable
                            ? (isRTL ? "مدير الحساب يمكنه اختيار نفسه فقط" : "Account Managers can only select themselves")
                            : undefined
                      }
                    >
                      <input
                        type="checkbox"
                        className="h-4 w-4 rounded border-zinc-300 accent-violet-600"
                        checked={checked}
                        disabled={rowDisabled}
                        onChange={() => toggleMember(member, department)}
                      />''',
)

replace_once(
    "client/src/components/TosProjectTeamSelector.tsx",
    '''        {isRTL
          ? "قسم إدارة الحسابات مستبعد تلقائيًا. العضويات الحالية وأدوارها تُقرأ من TOS وتظل إزالتها أو تغيير دورها من داخل TOS؛ الاختيارات الجديدة من TCRM تُضاف كـ Owner."
          : "Account Management is excluded automatically. Existing memberships and roles are read from TOS and remain managed there; new TCRM selections are added as Owners."}''',
    '''        {isRTL
          ? (selfOnly
              ? "قسم إدارة الحسابات ظاهر الآن. كمدير حساب يمكنك اختيار حسابك أنت فقط؛ العضويات الحالية تظل مُدارة من داخل TOS."
              : "قسم إدارة الحسابات ظاهر الآن. العضويات الحالية وأدوارها تُقرأ من TOS وتظل إزالتها أو تغيير دورها من داخل TOS؛ الاختيارات الجديدة من TCRM تُضاف كـ Owner.")
          : (selfOnly
              ? "Account Management is now visible. As an Account Manager you can select only your own account; existing memberships remain managed inside TOS."
              : "Account Management is now visible. Existing memberships and roles are read from TOS and remain managed there; new TCRM selections are added as Owners.")}''',
)

# 5) Client Profile wires the current TCRM identity to self-only mode for regular AMs.
replace_once(
    "client/src/pages/ClientProfile.tsx",
    '''                            {isRTL
                              ? "ملخص المبيعات يظل مملوكًا لفريق Sales، بينما يمكن لمسؤول الحساب المعيّن أو AM Lead أو المدير إدارة فريق مشروع TOS بشكل مستقل."
                              : "The Sales brief remains owned by Sales, while the assigned Account Manager, AM Lead, or managers can manage the TOS project team independently."}''',
    '''                            {isRTL
                              ? "ملخص المبيعات يظل مملوكًا لفريق Sales. مدير الحساب العادي يقدر يضيف نفسه فقط لفريق TOS، بينما AM Lead والمديرون يحتفظون بصلاحيات إدارة الفريق الحالية."
                              : "The Sales brief remains owned by Sales. A regular Account Manager can add only themselves to the TOS team, while AM Leads and managers keep their existing team-management permissions."}''',
)

replace_once(
    "client/src/pages/ClientProfile.tsx",
    '''                          <TosProjectTeamSelector
                            clientId={id}
                            value={tosProjectTeamDraft}
                            onChange={setTosProjectTeamDraft}
                            isRTL={isRTL}
                            disabled={!canEditTosProjectTeam || saveTosProjectTeamM.isPending}
                          />''',
    '''                          <TosProjectTeamSelector
                            clientId={id}
                            value={tosProjectTeamDraft}
                            onChange={setTosProjectTeamDraft}
                            isRTL={isRTL}
                            disabled={!canEditTosProjectTeam || saveTosProjectTeamM.isPending}
                            selfOnly={isAccountManagerUser}
                            currentUserEmails={[
                              String((user as any)?.email || ""),
                              String((user as any)?.centralEmail || ""),
                            ].filter(Boolean)}
                          />''',
)

print("\nTCRM patch applied successfully.")
print("NEXT: patch the live TOS team-directory endpoint using TOS_RUNTIME_PATCH_SPEC.md before building/restarting.")
