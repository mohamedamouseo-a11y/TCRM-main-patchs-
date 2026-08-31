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


# 1) Handover directory may explicitly request Account Management from TOS.
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

# Only the Handover selector opts in. Other consumers keep the current default.
replace_once(
    "server/routers.ts",
    '''        return getTosProjectTeamDirectory(input?.clientId);''',
    '''        return getTosProjectTeamDirectory(input?.clientId, { includeAccountManagement: true });''',
)

# 2) Backend identity mapping and self-only sanitization for regular AccountManager.
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
    throw new TRPCError({
      code: "PRECONDITION_FAILED",
      message: "Your TCRM account has no email identity that can be matched to TOS.",
    });
  }

  const directory = await getTosProjectTeamDirectory(clientId, { includeAccountManagement: true });
  const accountManagementMembers = (Array.isArray((directory as any)?.departments) ? (directory as any).departments : [])
    .filter(isAccountManagementDirectoryDepartment)
    .flatMap((department: any) => (Array.isArray(department?.members) ? department.members : []).map((member: any) => ({
      ...member,
      departmentKey: member?.departmentKey || department?.key,
      departmentName: member?.departmentName || department?.name,
    })));

  const selfMember = accountManagementMembers.find((member: any) =>
    actorEmails.has(normalizeTosIdentityEmail(member?.email)),
  );
  if (!selfMember) {
    throw new TRPCError({
      code: "PRECONDITION_FAILED",
      message: "Your Account Management user is not mapped to a TOS employee by email. Align the TCRM and TOS email identity first.",
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

  const currentIds = new Set(
    currentOwners
      .map((owner: any) => String(owner?.tosUserId || "").trim())
      .filter(Boolean),
  );
  const requestedIds = new Set(
    (requestedOwners || [])
      .map((owner: any) => String(owner?.tosUserId || "").trim())
      .filter(Boolean),
  );

  for (const requestedId of requestedIds) {
    if (requestedId !== selfTosUserId && !currentIds.has(requestedId)) {
      throw new TRPCError({
        code: "FORBIDDEN",
        message: "Account Managers can only add themselves to the TOS project team.",
      });
    }
  }

  // Preserve every non-self pending owner exactly as it already exists.
  // A regular AM can only add/remove their own pending Owner entry.
  const sanitized = currentOwners.filter(
    (owner: any) => String(owner?.tosUserId || "").trim() !== selfTosUserId,
  );

  if (requestedIds.has(selfTosUserId)) {
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
    '''      .mutation(async ({ input, ctx }) => {
        await assertTosProjectTeamEditAccess(ctx, input.clientId);
        const id = await saveTosProjectOwners(
          input.clientId,
          input.tosProjectOwners,
          ctx.user.id,
          ctx.user.name ?? "Unknown",
          ctx.user.role,
        );''',
    '''      .mutation(async ({ input, ctx }) => {
        await assertTosProjectTeamEditAccess(ctx, input.clientId);
        const ownersToSave = normalizeUserRole(ctx.user.role) === "AccountManager"
          ? await sanitizeRegularAccountManagerTosOwners(ctx, input.clientId, input.tosProjectOwners)
          : input.tosProjectOwners;
        const id = await saveTosProjectOwners(
          input.clientId,
          ownersToSave,
          ctx.user.id,
          ctx.user.name ?? "Unknown",
          ctx.user.role,
        );''',
)

# 3) Frontend selector: regular AccountManager can choose only their own TOS identity.
replace_once(
    "client/src/components/TosProjectTeamSelector.tsx",
    '''import { Loader2, RefreshCw, ShieldCheck, UsersRound } from "lucide-react";''',
    '''import { Loader2, RefreshCw, ShieldCheck, UserCheck, UsersRound } from "lucide-react";''',
)

replace_once(
    "client/src/components/TosProjectTeamSelector.tsx",
    '''  isRTL?: boolean;
  disabled?: boolean;
};''',
    '''  isRTL?: boolean;
  disabled?: boolean;
  currentUserRole?: string;
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
}

function isAccountManagementDepartment(department: any) {
  const raw = `${department?.key ?? ""} ${department?.name ?? ""}`
    .normalize("NFKC")
    .toLowerCase()
    .replace(/[\\s_\\-]+/g, "");
  return raw.includes("accountmanagement")
    || raw.includes("accountmanager")
    || raw.includes("ادارةالحساب")
    || raw.includes("إدارةالحساب");
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
  currentUserRole = "",
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
  const isRegularAccountManager = String(currentUserRole || "").trim() === "AccountManager";
  const currentUserEmailSet = React.useMemo(
    () => new Set((currentUserEmails || []).map(normalizeEmail).filter(Boolean)),
    [currentUserEmails],
  );
  const isSelfMember = React.useCallback(
    (member: any) => currentUserEmailSet.has(normalizeEmail(member?.email)),
    [currentUserEmailSet],
  );
  const selfEntry = React.useMemo(() => {
    if (!isRegularAccountManager) return null;
    for (const department of departments) {
      if (!isAccountManagementDepartment(department)) continue;
      const member = (Array.isArray(department?.members) ? department.members : []).find(isSelfMember);
      if (member) return { member, department };
    }
    return null;
  }, [departments, isRegularAccountManager, isSelfMember]);

  const toggleMember = (member: any, department: any) => {
    const tosUserId = memberKey(member);
    if (!tosUserId || disabled || projectMemberById.has(tosUserId)) return;
    if (isRegularAccountManager && !isSelfMember(member)) return;''',
)

replace_once(
    "client/src/components/TosProjectTeamSelector.tsx",
    '''  };

  return (
    <div className="rounded-xl border border-violet-200 bg-violet-50/40 p-4 space-y-4"''',
    '''  };

  const selfAlreadyLinked = Boolean(selfEntry && visibleSelectedIds.has(memberKey(selfEntry.member)));
  const assignMyself = () => {
    if (!selfEntry || selfAlreadyLinked || disabled) return;
    toggleMember(selfEntry.member, selfEntry.department);
  };

  return (
    <div className="rounded-xl border border-violet-200 bg-violet-50/40 p-4 space-y-4"''',
)

replace_once(
    "client/src/components/TosProjectTeamSelector.tsx",
    '''          <Button
            type="button"
            size="sm"
            variant="outline"
            className="h-8 rounded-lg bg-white"
            disabled={directoryQ.isFetching}
            onClick={() => directoryQ.refetch()}
          >''',
    '''          {isRegularAccountManager && selfEntry && (
            <Button
              type="button"
              size="sm"
              className="h-8 rounded-lg bg-emerald-600 text-white hover:bg-emerald-700"
              disabled={disabled || selfAlreadyLinked}
              onClick={assignMyself}
            >
              <UserCheck size={14} className="me-1" />
              {selfAlreadyLinked
                ? (isRTL ? "تم تعييني" : "Assigned")
                : (isRTL ? "تعيين نفسي" : "Assign myself")}
            </Button>
          )}
          <Button
            type="button"
            size="sm"
            variant="outline"
            className="h-8 rounded-lg bg-white"
            disabled={directoryQ.isFetching}
            onClick={() => directoryQ.refetch()}
          >''',
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
                  const selfSelectable = !isRegularAccountManager || isSelfMember(member);
                  const rowDisabled = disabled || isCurrentTosMember || !selfSelectable;
                  return (
                    <label
                      key={id}
                      className={`flex items-center gap-3 px-3 py-2.5 transition ${checked ? "bg-violet-50" : "hover:bg-zinc-50"} ${rowDisabled ? "cursor-default" : "cursor-pointer"} ${disabled || !selfSelectable ? "opacity-60" : ""}`}
                      title={
                        isCurrentTosMember
                          ? (isRTL ? "هذه العضوية تُدار من داخل TOS" : "This membership is managed inside TOS")
                          : isRegularAccountManager && !selfSelectable
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
    '''                        <span className="block truncate text-xs font-semibold text-zinc-900">{member.name}</span>''',
    '''                        <span className="flex min-w-0 items-center gap-1.5">
                          <span className="truncate text-xs font-semibold text-zinc-900">{member.name}</span>
                          {isAccountManagementDepartment(department) && (
                            <span className="shrink-0 rounded-full border border-emerald-200 bg-emerald-50 px-1.5 py-0.5 text-[9px] font-bold text-emerald-700">AM</span>
                          )}
                        </span>''',
)

replace_once(
    "client/src/components/TosProjectTeamSelector.tsx",
    '''        {isRTL
          ? "قسم إدارة الحسابات مستبعد تلقائيًا. العضويات الحالية وأدوارها تُقرأ من TOS وتظل إزالتها أو تغيير دورها من داخل TOS؛ الاختيارات الجديدة من TCRM تُضاف كـ Owner."
          : "Account Management is excluded automatically. Existing memberships and roles are read from TOS and remain managed there; new TCRM selections are added as Owners."}''',
    '''        {isRTL
          ? (isRegularAccountManager
              ? "قسم إدارة الحسابات ظاهر الآن. يمكنك تعيين نفسك فقط؛ العضويات الحالية تظل مُدارة من داخل TOS."
              : "قسم إدارة الحسابات ظاهر في خطوة التسليم. العضويات الحالية وأدوارها تُقرأ من TOS؛ الاختيارات الجديدة من TCRM تُضاف كـ Owner.")
          : (isRegularAccountManager
              ? "Account Management is visible. You can assign only yourself; existing memberships remain managed inside TOS."
              : "Account Management is visible in Handover. Existing memberships and roles are read from TOS; new TCRM selections are added as Owners.")}''',
)

# 4) Pass current TCRM identity to the selector. Email is the identity bridge, not numeric id.
replace_once(
    "client/src/pages/ClientProfile.tsx",
    '''                          onChange={setTosProjectTeamDraft}
                          isRTL={isRTL}
                          disabled={!canEditTosProjectTeam || saveTosProjectTeamM.isPending}''',
    '''                          onChange={setTosProjectTeamDraft}
                          isRTL={isRTL}
                          currentUserRole={normalizeUserRole((user as any)?.role)}
                          currentUserEmails={[(user as any)?.email, (user as any)?.centralEmail].filter(Boolean)}
                          disabled={!canEditTosProjectTeam || saveTosProjectTeamM.isPending}''',
)

print("\nPatch applied successfully.")
print("Review git diff, then run the project typecheck/build before deployment.")
