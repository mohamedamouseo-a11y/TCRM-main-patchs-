#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()


def read(rel):
    path = ROOT / rel
    if not path.exists():
        raise SystemExit(f"Missing expected file: {path}")
    return path, path.read_text(encoding="utf-8")


def write(path, text):
    path.write_text(text, encoding="utf-8")


def replace_once(rel, old, new, required=True):
    path, text = read(rel)
    if new in text:
        print(f"[skip] already patched: {rel}")
        return
    count = text.count(old)
    if count == 0 and not required:
        print(f"[skip] optional anchor not found: {rel}")
        return
    if count != 1:
        raise SystemExit(f"Expected exactly one patch anchor in {rel}, found {count}")
    write(path, text.replace(old, new, 1))
    print(f"[ok] patched: {rel}")


def replace_ts_function(rel, function_name, new_function):
    path, text = read(rel)
    marker = f"async function {function_name}"
    start = text.find(marker)
    if start < 0:
        if new_function.split("(", 1)[0].strip() in text:
            print(f"[skip] replacement function already exists: {rel}")
            return
        raise SystemExit(f"Could not find function {function_name} in {rel}")
    brace = text.find("{", start)
    if brace < 0:
        raise SystemExit(f"Could not find opening brace for {function_name}")
    depth = 0
    end = None
    for i in range(brace, len(text)):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end is None:
        raise SystemExit(f"Could not find closing brace for {function_name}")
    updated = text[:start] + new_function.rstrip() + text[end:]
    write(path, updated)
    print(f"[ok] replaced function {function_name}: {rel}")


# ---------------------------------------------------------------------------
# 1) Backend: V4 removes the V3 self-only rule, but keeps backend validation.
#    Any requested Owner from a regular AccountManager must exist in the trusted
#    TOS directory. Metadata is canonicalized from TOS instead of trusting UI.
# ---------------------------------------------------------------------------

NEW_SANITIZER = r'''async function sanitizeAccountManagerTosOwners(ctx: any, clientId: number, requestedOwners: any[]) {
  const directory = await getTosProjectTeamDirectory(clientId, { includeAccountManagement: true });
  const departments = Array.isArray((directory as any)?.departments) ? (directory as any).departments : [];
  const trustedById = new Map<string, any>();

  for (const department of departments) {
    for (const member of Array.isArray(department?.members) ? department.members : []) {
      const tosUserId = String(member?.tosUserId || member?.userId || member?.id || "").trim();
      if (!tosUserId) continue;
      trustedById.set(tosUserId, {
        tosUserId,
        name: String(member?.name || "").trim(),
        email: String(member?.email || "").trim() || undefined,
        departmentKey: String(member?.departmentKey || department?.key || "").trim() || undefined,
        departmentName: String(member?.departmentName || department?.name || "").trim() || undefined,
      });
    }
  }

  const sanitized: any[] = [];
  const seen = new Set<string>();
  for (const requested of requestedOwners || []) {
    const tosUserId = String(requested?.tosUserId || "").trim();
    if (!tosUserId || seen.has(tosUserId)) continue;
    const trusted = trustedById.get(tosUserId);
    if (!trusted) {
      throw new TRPCError({
        code: "FORBIDDEN",
        message: "The selected employee is not an active member of the trusted TOS team directory.",
      });
    }
    seen.add(tosUserId);
    sanitized.push(trusted);
  }

  return sanitized;
}'''

routers_path, routers_text = read("server/routers.ts")
if "async function sanitizeRegularAccountManagerTosOwners" in routers_text:
    replace_ts_function("server/routers.ts", "sanitizeRegularAccountManagerTosOwners", NEW_SANITIZER)
elif "async function sanitizeAccountManagerTosOwners" in routers_text:
    print("[skip] V4 backend sanitizer already present")
else:
    raise SystemExit(
        "Could not find the V3 AccountManager sanitizer. Inspect server/routers.ts and port the V4 behavior manually."
    )

# Point mutation to V4 sanitizer.
path, text = read("server/routers.ts")
if "sanitizeRegularAccountManagerTosOwners" in text:
    text = text.replace("sanitizeRegularAccountManagerTosOwners", "sanitizeAccountManagerTosOwners")
    write(path, text)
    print("[ok] saveTosProjectTeam now uses V4 directory sanitizer")

# ---------------------------------------------------------------------------
# 2) Frontend: enable every non-current-project employee row for a permitted
#    AccountManager. Existing actual TOS memberships stay disabled/read-only.
# ---------------------------------------------------------------------------

replace_once(
    "client/src/components/TosProjectTeamSelector.tsx",
    '''    if (isRegularAccountManager && !isSelfMember(member)) return;''',
    '''    // V4: permitted Account Managers may select any active employee returned by TOS.''',
    required=False,
)

replace_once(
    "client/src/components/TosProjectTeamSelector.tsx",
    '''                  const selfSelectable = !isRegularAccountManager || isSelfMember(member);
                  const rowDisabled = disabled || isCurrentTosMember || !selfSelectable;''',
    '''                  const rowDisabled = disabled || isCurrentTosMember;''',
    required=False,
)

replace_once(
    "client/src/components/TosProjectTeamSelector.tsx",
    '''                      className={`flex items-center gap-3 px-3 py-2.5 transition ${checked ? "bg-violet-50" : "hover:bg-zinc-50"} ${rowDisabled ? "cursor-default" : "cursor-pointer"} ${disabled || !selfSelectable ? "opacity-60" : ""}`}''',
    '''                      className={`flex items-center gap-3 px-3 py-2.5 transition ${checked ? "bg-violet-50" : "hover:bg-zinc-50"} ${rowDisabled ? "cursor-default" : "cursor-pointer"} ${disabled ? "opacity-60" : ""}`}''',
    required=False,
)

replace_once(
    "client/src/components/TosProjectTeamSelector.tsx",
    '''                      title={
                        isCurrentTosMember
                          ? (isRTL ? "هذه العضوية تُدار من داخل TOS" : "This membership is managed inside TOS")
                          : isRegularAccountManager && !selfSelectable
                            ? (isRTL ? "مدير الحساب يمكنه اختيار نفسه فقط" : "Account Managers can only select themselves")
                            : undefined
                      }''',
    '''                      title={isCurrentTosMember ? (isRTL ? "هذه العضوية تُدار من داخل TOS" : "This membership is managed inside TOS") : undefined}''',
    required=False,
)

# Update footer/help text from self-only to full directory selection.
path, text = read("client/src/components/TosProjectTeamSelector.tsx")
text = text.replace(
    '"Account Management is visible. You can assign only yourself; existing memberships remain managed inside TOS."',
    '"All active TOS employees can be selected across departments, including Account Management. Existing memberships remain managed inside TOS."',
)
text = text.replace(
    '"قسم إدارة الحسابات ظاهر الآن. يمكنك تعيين نفسك فقط؛ العضويات الحالية تظل مُدارة من داخل TOS."',
    '"يمكنك اختيار أي موظف نشط من جميع أقسام TOS، بما فيها إدارة الحسابات؛ العضويات الحالية تظل مُدارة من داخل TOS."',
)
text = text.replace(
    '"You can only assign yourself. You cannot assign any other employee."',
    '"You can assign any active employee shown in the TOS directory."',
)
text = text.replace(
    '"يمكنك تعيين نفسك فقط. لا يمكنك تعيين أي موظف آخر."',
    '"يمكنك تعيين أي موظف نشط ظاهر في دليل فريق TOS."',
)
write(path, text)
print("[ok] updated selector helper text")

print("\nV4 TCRM patch applied.")
print("IMPORTANT: now follow TOS_RUNTIME_SPEC.md. The selector cannot show names that the live TOS directory does not return.")
print("Then run git diff --check, npm run check/build as appropriate, and functional QA before deploy.")
