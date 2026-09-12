#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

WORKFLOW_SERIES = "TCRM-PERMISSIONS"
MODULE = "TARA"
PHASE = "FRONTEND-ACTIONS-FINAL-VERIFICATION"
VERSION = "V1.2.0"
WORKFLOW_ID = "TCRM-PERMISSIONS-TARA-FRONTEND-FINAL-V1.2.0"
PREVIOUS_VERSION = "V1.0.1"
PREVIOUS_WORKFLOW_ID = "TCRM-PERMISSIONS-TARA-API-ENFORCEMENT-V1.0.1-RECOVERY"
BASELINE = "12507b2cdeb96ddcede8feddadbe321ba4a59dae"

ROOT = Path.cwd()
EXPECTED = {
    "client/src/contexts/PermissionContext.tsx",
    "client/src/pages/TaraAgentPage.tsx",
    "client/src/components/tara/TaraModeratorOperations.tsx",
    "client/src/components/tara/TaraModeratorWorkspace.tsx",
    "server/security/taraFinalPermission.test.ts",
}


def fail(message: str) -> None:
    print(f"ERROR={message}", file=sys.stderr)
    raise SystemExit(1)


def run(*args: str) -> str:
    p = subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        fail(f"COMMAND_FAILED:{' '.join(args)}:{p.stderr.strip()}")
    return p.stdout.strip()


def read(rel: str) -> str:
    p = ROOT / rel
    if not p.exists():
        fail(f"MISSING_FILE:{rel}")
    return p.read_text(encoding="utf-8")


def write(rel: str, text: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        fail(f"ANCHOR_DRIFT:{label}:count={count}")
    return text.replace(old, new, 1)


def rename_mutation(text: str, name: str, label: str) -> str:
    anchor = f"    const {name} = trpc."
    if text.count(anchor) != 1:
        fail(f"ANCHOR_DRIFT:{label}:{name}:count={text.count(anchor)}")
    return text.replace(anchor, f"    const {name}Raw = trpc.", 1)


def insert_after_line(text: str, starts_with: str, block: str, label: str) -> str:
    pattern = re.compile(rf"^({re.escape(starts_with)}.*\n)", re.MULTILINE)
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        fail(f"ANCHOR_DRIFT:{label}:count={len(matches)}")
    m = matches[0]
    return text[:m.end()] + block + text[m.end():]


head = run("git", "rev-parse", "HEAD")
if head != BASELINE:
    fail(f"BASELINE_MISMATCH:{head}")

tracked = run("git", "status", "--short", "--untracked-files=no")
if tracked:
    fail("TRACKED_WORKTREE_NOT_CLEAN")

# -----------------------------------------------------------------------------
# PermissionContext: expose all four Tara permissions to frontend decisions.
# -----------------------------------------------------------------------------
rel = "client/src/contexts/PermissionContext.tsx"
s = read(rel)
s = replace_once(
    s,
    '  "tara.view",\n  "settings.view",',
    '  "tara.view",\n  "tara.operate",\n  "tara.moderate",\n  "tara.manage",\n  "settings.view",',
    "permission-context-tara-keys",
)
write(rel, s)

# Shared frontend mutation guard. It keeps backend enforcement authoritative while
# preventing denied buttons/callbacks from firing mutation requests.
guard_helper = '''\nfunction guardTaraMutation(mutation: any, allowed: boolean, permission: string) {\n    return {\n        ...mutation,\n        mutate: (...args: any[]) => {\n            if (!allowed) {\n                toast.error(`Permission required: ${permission}`);\n                return;\n            }\n            return mutation.mutate(...args);\n        },\n        mutateAsync: async (...args: any[]) => {\n            if (!allowed)\n                throw new Error(`Permission required: ${permission}`);\n            return mutation.mutateAsync(...args);\n        },\n    };\n}\n'''

# -----------------------------------------------------------------------------
# TaraAgentPage: permission-driven branch selection + guarded operational actions.
# Technical/admin page is mounted only with tara.manage. A non-manage Admin/Developer
# receives the existing non-secret Tara Operations workspace instead.
# -----------------------------------------------------------------------------
rel = "client/src/pages/TaraAgentPage.tsx"
s = read(rel)
s = replace_once(
    s,
    'import { useLanguage } from "@/contexts/LanguageContext";\n',
    'import { useLanguage } from "@/contexts/LanguageContext";\nimport { usePermissions } from "@/contexts/PermissionContext";\n',
    "tara-page-permissions-import",
)
s = replace_once(
    s,
    'function ScopeSelect({ value, onChange, campaigns, label }: any) {\n    return <div className="space-y-2"><Label>{label}</Label><Select value={value ? String(value) : "global"} onValueChange={(v) => onChange(v === "global" ? null : Number(v))}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="global">{taraText("\\u0625\\u0639\\u062F\\u0627\\u062F \\u0639\\u0627\\u0645 \\u0644\\u0644\\u0634\\u0631\\u0643\\u0629")}</SelectItem>{campaigns.map((item: any) => <SelectItem key={item.id} value={String(item.id)}>{item.name}</SelectItem>)}</SelectContent></Select></div>;\n}\n',
    'function ScopeSelect({ value, onChange, campaigns, label }: any) {\n    return <div className="space-y-2"><Label>{label}</Label><Select value={value ? String(value) : "global"} onValueChange={(v) => onChange(v === "global" ? null : Number(v))}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="global">{taraText("\\u0625\\u0639\\u062F\\u0627\\u062F \\u0639\\u0627\\u0645 \\u0644\\u0644\\u0634\\u0631\\u0643\\u0629")}</SelectItem>{campaigns.map((item: any) => <SelectItem key={item.id} value={String(item.id)}>{item.name}</SelectItem>)}</SelectContent></Select></div>;\n}\n' + guard_helper,
    "tara-page-guard-helper",
)
s = replace_once(
    s,
    'export default function TaraAgentPage() {\n    useTaraI18n();\n    const profileQ =',
    'export default function TaraAgentPage() {\n    useTaraI18n();\n    const { can } = usePermissions();\n    const canOperate = can("tara.operate");\n    const canModerate = can("tara.moderate");\n    const canManage = can("tara.manage");\n    const profileQ =',
    "tara-page-effective-permissions",
)
s = replace_once(
    s,
    '? <TaraModeratorWorkspace profile={profileQ.data}/>\n            : <TaraModeratorOperations profile={profileQ.data}/>;',
    '? <TaraModeratorWorkspace profile={profileQ.data} allowModerate={canModerate} allowOperate={canOperate}/>\n            : <TaraModeratorOperations profile={profileQ.data} allowOperate={canOperate}/>;',
    "tara-page-moderator-props",
)
s = replace_once(
    s,
    '    return <TaraAdminAgentPage canManageModerators={Boolean(profileQ.data.canManageModerators)}/>;\n}\nfunction TaraAdminAgentPage({ canManageModerators }: {\n    canManageModerators: boolean;\n}) {',
    '    if (!canManage)\n        return <TaraModeratorOperations profile={profileQ.data} allowOperate={canOperate}/>;\n    return <TaraAdminAgentPage canManageModerators={Boolean(profileQ.data.canManageModerators)} canOperate={canOperate}/>;\n}\nfunction TaraAdminAgentPage({ canManageModerators, canOperate }: {\n    canManageModerators: boolean;\n    canOperate: boolean;\n}) {',
    "tara-page-admin-manage-boundary",
)
admin_operate = [
    "saveCampaignM", "deleteCampaignM", "saveFieldM", "deleteFieldM",
    "saveKnowledgeM", "deleteKnowledgeM", "saveFollowupM", "deleteFollowupM",
    "testAgentM", "processQueueM",
]
for name in admin_operate:
    s = rename_mutation(s, name, "tara-page-operate-mutation")
wrapper_block = ''.join(
    f'    const {name} = guardTaraMutation({name}Raw, canOperate, "tara.operate");\n'
    for name in admin_operate
)
s = insert_after_line(s, "    const processQueueMRaw =", wrapper_block, "tara-page-operate-wrappers")
write(rel, s)

# -----------------------------------------------------------------------------
# Moderator Operations: all non-secret Tara operational mutations are guarded by
# tara.operate. Reads remain untouched.
# -----------------------------------------------------------------------------
rel = "client/src/components/tara/TaraModeratorOperations.tsx"
s = read(rel)
s = replace_once(
    s,
    'import { taraDirection, taraText, taraToast as toast, useTaraI18n } from "@/components/tara/taraI18n";\n',
    'import { taraDirection, taraText, taraToast as toast, useTaraI18n } from "@/components/tara/taraI18n";\n' + guard_helper,
    "tara-operations-guard-helper",
)
s = replace_once(
    s,
    'export default function TaraModeratorOperations({ profile }: {\n    profile: any;\n}) {',
    'export default function TaraModeratorOperations({ profile, allowOperate = true }: {\n    profile: any;\n    allowOperate?: boolean;\n}) {',
    "tara-operations-prop",
)
ops_names = [
    "saveSettings", "saveCampaign", "deleteCampaign", "saveField", "deleteField",
    "saveKnowledge", "deleteKnowledge", "saveFollowup", "deleteFollowup",
    "testAgent", "processQueue",
]
for name in ops_names:
    s = rename_mutation(s, name, "tara-operations-mutation")
ops_wrappers = ''.join(
    f'    const {name} = guardTaraMutation({name}Raw, allowOperate, "tara.operate");\n'
    for name in ops_names
)
s = insert_after_line(s, "    const processQueueRaw =", ops_wrappers, "tara-operations-wrappers")
s = replace_once(
    s,
    '    return <CRMLayout>\n    <div className="mx-auto max-w-7xl space-y-5 p-4 md:p-6" dir={isRTL ? "rtl" : "ltr"}>',
    '    return <CRMLayout>\n    <div className="mx-auto max-w-7xl space-y-5 p-4 md:p-6" dir={isRTL ? "rtl" : "ltr"}>\n      {!allowOperate && <div data-tara-read-only="operate" className="rounded-2xl border bg-muted/30 p-3 text-sm text-muted-foreground">{isRTL ? "صلاحية تارا للعرض فقط: إجراءات التشغيل معطلة." : "Read-only Tara access: operational actions are disabled."}</div>}',
    "tara-operations-readonly-notice",
)
write(rel, s)

# -----------------------------------------------------------------------------
# Moderator Workspace: native moderation actions require tara.moderate; Evolution
# Tara status changes require tara.operate. WhatsApp send permission remains its
# own independent backend/frontend concern and is not remapped here.
# -----------------------------------------------------------------------------
rel = "client/src/components/tara/TaraModeratorWorkspace.tsx"
s = read(rel)
s = replace_once(
    s,
    'import { taraDirection, taraText, taraToast as toast, useTaraI18n } from "@/components/tara/taraI18n";\n',
    'import { taraDirection, taraText, taraToast as toast, useTaraI18n } from "@/components/tara/taraI18n";\n' + guard_helper,
    "tara-workspace-guard-helper",
)
s = replace_once(
    s,
    'export default function TaraModeratorWorkspace({ profile }: {\n    profile: any;\n}) {',
    'export default function TaraModeratorWorkspace({ profile, allowModerate = true, allowOperate = true }: {\n    profile: any;\n    allowModerate?: boolean;\n    allowOperate?: boolean;\n}) {',
    "tara-workspace-props",
)
moderate_names = ["generateM", "sendM", "retryM", "updateM", "noteM"]
for name in moderate_names:
    s = rename_mutation(s, name, "tara-workspace-moderate-mutation")
mod_wrappers = ''.join(
    f'    const {name} = guardTaraMutation({name}Raw, allowModerate, "tara.moderate");\n'
    for name in moderate_names
)
s = insert_after_line(s, "    const noteMRaw =", mod_wrappers, "tara-workspace-moderate-wrappers")
s = replace_once(
    s,
    '    return <CRMLayout>\n    <div className="mx-auto max-w-7xl space-y-5 p-4 md:p-6" dir={taraDirection()}>',
    '    return <CRMLayout>\n    <div className="mx-auto max-w-7xl space-y-5 p-4 md:p-6" dir={taraDirection()}>\n      {!allowModerate && <div data-tara-read-only="moderate" className="rounded-2xl border bg-muted/30 p-3 text-sm text-muted-foreground">{taraText("صلاحية المراجعة غير متاحة؛ المحادثات للعرض فقط.")}</div>}',
    "tara-workspace-readonly-notice",
)
s = replace_once(
    s,
    '<EvolutionModeratorPanel profile={profile}/>',
    '<EvolutionModeratorPanel profile={profile} allowOperate={allowOperate}/>',
    "tara-workspace-evolution-prop-pass",
)
s = replace_once(
    s,
    'function EvolutionModeratorPanel({ profile }: {\n    profile: any;\n}) {',
    'function EvolutionModeratorPanel({ profile, allowOperate = true }: {\n    profile: any;\n    allowOperate?: boolean;\n}) {',
    "tara-workspace-evolution-prop",
)
s = rename_mutation(s, "statusM", "tara-workspace-evolution-status")
s = insert_after_line(
    s,
    "    const statusMRaw =",
    '    const statusM = guardTaraMutation(statusMRaw, allowOperate, "tara.operate");\n',
    "tara-workspace-evolution-status-wrapper",
)
write(rel, s)

# -----------------------------------------------------------------------------
# Final regression suite: verifies backend + route + frontend action decisions in
# one persisted test so this single patch closes Tara after one manual push.
# -----------------------------------------------------------------------------
final_test = r'''import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { resolveCorePermissionKey } from "./corePermissionPolicy";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "../..");
const read = (relative: string) => readFileSync(path.join(root, relative), "utf8");

const permissionContext = read("client/src/contexts/PermissionContext.tsx");
const taraPage = read("client/src/pages/TaraAgentPage.tsx");
const operations = read("client/src/components/tara/TaraModeratorOperations.tsx");
const workspace = read("client/src/components/tara/TaraModeratorWorkspace.tsx");
const moderatorPolicy = read("shared/moderatorOperationalAccess.ts");

const expectContainsAll = (source: string, values: string[]) => {
  for (const value of values) expect(source, value).toContain(value);
};

describe("Tara permissions final verification V1.2.0", () => {
  it("exposes Tara view/operate/moderate/manage and keeps /tara on tara.view", () => {
    expectContainsAll(permissionContext, [
      '"tara.view"',
      '"tara.operate"',
      '"tara.moderate"',
      '"tara.manage"',
      '["/tara", "tara.view"]',
    ]);
  });

  it("keeps backend Tara mapping explicit and fail-closed", () => {
    expect(resolveCorePermissionKey("tara.dashboard", "query")).toBe("tara.view");
    expect(resolveCorePermissionKey("tara.saveCampaign", "mutation")).toBe("tara.operate");
    expect(resolveCorePermissionKey("tara.moderation.sendReply", "mutation")).toBe("tara.moderate");
    expect(resolveCorePermissionKey("tara.saveProviderConfiguration", "mutation")).toBe("tara.manage");
    expect(resolveCorePermissionKey("tara.futureUnknownControl", "query")).toBe("tara.manage");
    expect(resolveCorePermissionKey("tara.futureUnknownControl", "mutation")).toBe("tara.manage");
  });

  it("uses effective permissions to select Tara frontend capabilities", () => {
    expectContainsAll(taraPage, [
      'usePermissions',
      'can("tara.operate")',
      'can("tara.moderate")',
      'can("tara.manage")',
      'allowModerate={canModerate}',
      'allowOperate={canOperate}',
      'if (!canManage)',
      'guardTaraMutation(saveCampaignMRaw, canOperate, "tara.operate")',
      'guardTaraMutation(processQueueMRaw, canOperate, "tara.operate")',
    ]);
  });

  it("guards Moderator operational and moderation mutation surfaces while preserving reads", () => {
    expectContainsAll(operations, [
      'allowOperate = true',
      'data-tara-read-only="operate"',
      'guardTaraMutation(saveSettingsRaw, allowOperate, "tara.operate")',
      'guardTaraMutation(saveCampaignRaw, allowOperate, "tara.operate")',
      'guardTaraMutation(testAgentRaw, allowOperate, "tara.operate")',
      'guardTaraMutation(processQueueRaw, allowOperate, "tara.operate")',
      'trpc.tara.dashboard.useQuery',
      'trpc.tara.logs.useQuery',
    ]);
    expectContainsAll(workspace, [
      'allowModerate = true',
      'allowOperate = true',
      'data-tara-read-only="moderate"',
      'guardTaraMutation(generateMRaw, allowModerate, "tara.moderate")',
      'guardTaraMutation(sendMRaw, allowModerate, "tara.moderate")',
      'guardTaraMutation(updateMRaw, allowModerate, "tara.moderate")',
      'guardTaraMutation(noteMRaw, allowModerate, "tara.moderate")',
      'guardTaraMutation(statusMRaw, allowOperate, "tara.operate")',
      'trpc.tara.moderation.overview.useQuery',
      'trpc.tara.getConversationContext.useQuery',
    ]);
  });

  it("preserves the existing Moderator scope/secret boundary as an additive layer", () => {
    expectContainsAll(moderatorPolicy, [
      'isModeratorNativeScopedApiPath',
      'isModeratorBlockedApiPath',
      'tara.moderation.',
      'tara.getConversationContext',
      'tara.setConversationStatus',
    ]);
    expect(taraPage).toContain('profileQ.data.role === "Moderator"');
    expect(taraPage).not.toContain('normalizeUserRole(');
  });
});
'''
write("server/security/taraFinalPermission.test.ts", final_test)

# Exact dirty-set guard.
status = run("git", "status", "--short", "--untracked-files=all")
dirty = set()
for line in status.splitlines():
    if not line.strip():
        continue
    path = line[3:].strip()
    if " -> " in path:
        path = path.split(" -> ", 1)[1]
    dirty.add(path)
if dirty != EXPECTED:
    fail(f"DIRTY_SET_MISMATCH:expected={sorted(EXPECTED)}:actual={sorted(dirty)}")

print(f"WORKFLOW_SERIES={WORKFLOW_SERIES}")
print(f"MODULE={MODULE}")
print(f"PHASE={PHASE}")
print(f"VERSION={VERSION}")
print(f"WORKFLOW_ID={WORKFLOW_ID}")
print(f"PREVIOUS_VERSION={PREVIOUS_VERSION}")
print(f"PREVIOUS_WORKFLOW_ID={PREVIOUS_WORKFLOW_ID}")
print(f"BASELINE={BASELINE}")
print("PATCH_APPLIED=YES")
print("FILES_CHANGED=" + ",".join(sorted(EXPECTED)))
