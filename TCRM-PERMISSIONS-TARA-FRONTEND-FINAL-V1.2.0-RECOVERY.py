#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

WORKFLOW_SERIES = "TCRM-PERMISSIONS"
MODULE = "TARA"
PHASE = "FRONTEND-ACTIONS-FINAL-VERIFICATION-RECOVERY"
VERSION = "V1.2.0"
WORKFLOW_ID = "TCRM-PERMISSIONS-TARA-FRONTEND-FINAL-V1.2.0-RECOVERY"
PREVIOUS_VERSION = "V1.0.1"
PREVIOUS_WORKFLOW_ID = "TCRM-PERMISSIONS-TARA-API-ENFORCEMENT-V1.0.1-RECOVERY"
BASELINE = "12507b2cdeb96ddcede8feddadbe321ba4a59dae"

ROOT = Path.cwd()
PARTIAL_EXPECTED = {
    "client/src/contexts/PermissionContext.tsx",
    "client/src/pages/TaraAgentPage.tsx",
    "client/src/components/tara/TaraModeratorOperations.tsx",
}
FINAL_EXPECTED = PARTIAL_EXPECTED | {
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


def rename_route_mutation(text: str, name: str, route: str, label: str) -> str:
    anchor = f"    const {name} = trpc.{route}.useMutation"
    count = text.count(anchor)
    if count != 1:
        fail(f"ANCHOR_DRIFT:{label}:{name}:{route}:count={count}")
    return text.replace(anchor, f"    const {name}Raw = trpc.{route}.useMutation", 1)


def insert_after_route_line(text: str, name: str, route: str, block: str, label: str) -> str:
    anchor = f"    const {name}Raw = trpc.{route}.useMutation"
    pos = text.find(anchor)
    if pos < 0 or text.find(anchor, pos + 1) >= 0:
        fail(f"ANCHOR_DRIFT:{label}:route-line")
    end = text.find("\n", pos)
    if end < 0:
        fail(f"ANCHOR_DRIFT:{label}:newline")
    return text[:end + 1] + block + text[end + 1:]


def assert_once(text: str, marker: str, label: str) -> None:
    count = text.count(marker)
    if count != 1:
        fail(f"PARTIAL_STATE_MISMATCH:{label}:count={count}")


head = run("git", "rev-parse", "HEAD")
if head != BASELINE:
    fail(f"BASELINE_MISMATCH:{head}")

if run("git", "diff", "--cached", "--name-only"):
    fail("PARTIAL_STATE_HAS_STAGED_CHANGES")

current_dirty = set(filter(None, run("git", "diff", "--name-only").splitlines()))
if current_dirty != PARTIAL_EXPECTED:
    fail(f"PARTIAL_DIRTY_SET_MISMATCH:{sorted(current_dirty)}")

if run("git", "diff", "--check"):
    fail("PARTIAL_DIFF_CHECK_FAILED")

# -----------------------------------------------------------------------------
# Verify the three dirty files are exactly in the expected patch-owned semantic
# state before continuing. Do not clean/reset them.
# -----------------------------------------------------------------------------
permission_context = read("client/src/contexts/PermissionContext.tsx")
for marker in [
    '  "tara.view",',
    '  "tara.operate",',
    '  "tara.moderate",',
    '  "tara.manage",',
    '["/tara", "tara.view"]',
]:
    assert_once(permission_context, marker, f"permission-context:{marker}")

page = read("client/src/pages/TaraAgentPage.tsx")
for marker in [
    'import { usePermissions } from "@/contexts/PermissionContext";',
    'const canOperate = can("tara.operate");',
    'const canModerate = can("tara.moderate");',
    'const canManage = can("tara.manage");',
    '<TaraModeratorWorkspace profile={profileQ.data} allowModerate={canModerate} allowOperate={canOperate}/>',
    '<TaraModeratorOperations profile={profileQ.data} allowOperate={canOperate}/>',
    'if (!canManage)',
    'function guardTaraMutation(',
]:
    assert_once(page, marker, f"tara-page:{marker}")
for name in [
    "saveCampaignM", "deleteCampaignM", "saveFieldM", "deleteFieldM",
    "saveKnowledgeM", "deleteKnowledgeM", "saveFollowupM", "deleteFollowupM",
    "testAgentM", "processQueueM",
]:
    assert_once(page, f"const {name}Raw = trpc.", f"tara-page-raw:{name}")
    assert_once(page, f"const {name} = guardTaraMutation({name}Raw, canOperate, \"tara.operate\");", f"tara-page-guard:{name}")

ops = read("client/src/components/tara/TaraModeratorOperations.tsx")
for marker in [
    'allowOperate = true',
    'allowOperate?: boolean;',
    'data-tara-read-only="operate"',
    'function guardTaraMutation(',
]:
    assert_once(ops, marker, f"tara-operations:{marker}")
for name in [
    "saveSettings", "saveCampaign", "deleteCampaign", "saveField", "deleteField",
    "saveKnowledge", "deleteKnowledge", "saveFollowup", "deleteFollowup",
    "testAgent", "processQueue",
]:
    assert_once(ops, f"const {name}Raw = trpc.", f"tara-operations-raw:{name}")
    assert_once(ops, f"const {name} = guardTaraMutation({name}Raw, allowOperate, \"tara.operate\");", f"tara-operations-guard:{name}")

# -----------------------------------------------------------------------------
# Complete TaraModeratorWorkspace using route-qualified mutation anchors so the
# two different sendM declarations (Tara moderation + WhatsApp Evolution) cannot
# collide again.
# -----------------------------------------------------------------------------
rel = "client/src/components/tara/TaraModeratorWorkspace.tsx"
s = read(rel)

# Workspace must still be pristine relative to HEAD because the failed patch never
# wrote this file.
if run("git", "diff", "--name-only", "--", rel):
    fail("WORKSPACE_UNEXPECTEDLY_DIRTY")

helper = '''\nfunction guardTaraMutation(mutation: any, allowed: boolean, permission: string) {\n    return {\n        ...mutation,\n        mutate: (...args: any[]) => {\n            if (!allowed) {\n                toast.error(`Permission required: ${permission}`);\n                return;\n            }\n            return mutation.mutate(...args);\n        },\n        mutateAsync: async (...args: any[]) => {\n            if (!allowed)\n                throw new Error(`Permission required: ${permission}`);\n            return mutation.mutateAsync(...args);\n        },\n    };\n}\n'''

s = replace_once(
    s,
    'import { taraDirection, taraText, taraToast as toast, useTaraI18n } from "@/components/tara/taraI18n";\n',
    'import { taraDirection, taraText, taraToast as toast, useTaraI18n } from "@/components/tara/taraI18n";\n' + helper,
    "tara-workspace-guard-helper",
)
s = replace_once(
    s,
    'export default function TaraModeratorWorkspace({ profile }: {\n    profile: any;\n}) {',
    'export default function TaraModeratorWorkspace({ profile, allowModerate = true, allowOperate = true }: {\n    profile: any;\n    allowModerate?: boolean;\n    allowOperate?: boolean;\n}) {',
    "tara-workspace-props",
)

routes = {
    "generateM": "tara.moderation.generateReply",
    "sendM": "tara.moderation.sendReply",
    "retryM": "tara.moderation.retryReply",
    "updateM": "tara.moderation.updateConversation",
    "noteM": "tara.moderation.addNote",
}
for name, route in routes.items():
    s = rename_route_mutation(s, name, route, "tara-workspace-moderate-mutation")

mod_wrappers = ''.join(
    f'    const {name} = guardTaraMutation({name}Raw, allowModerate, "tara.moderate");\n'
    for name in ["generateM", "sendM", "retryM", "updateM", "noteM"]
)
s = insert_after_route_line(
    s,
    "noteM",
    "tara.moderation.addNote",
    mod_wrappers,
    "tara-workspace-moderate-wrappers",
)
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
s = rename_route_mutation(s, "statusM", "tara.setConversationStatus", "tara-workspace-evolution-status")
s = insert_after_route_line(
    s,
    "statusM",
    "tara.setConversationStatus",
    '    const statusM = guardTaraMutation(statusMRaw, allowOperate, "tara.operate");\n',
    "tara-workspace-evolution-status-wrapper",
)
write(rel, s)

# -----------------------------------------------------------------------------
# Persist final combined regression coverage.
# -----------------------------------------------------------------------------
final_test_rel = "server/security/taraFinalPermission.test.ts"
if (ROOT / final_test_rel).exists():
    fail("FINAL_TEST_ALREADY_EXISTS")

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
const moderatorAccess = read("shared/moderatorOperationalAccess.ts");

describe("Tara permissions final V1.2.0", () => {
  it("preserves the four-level backend contract and fail-closed management", () => {
    expect(resolveCorePermissionKey("tara.dashboard", "query")).toBe("tara.view");
    expect(resolveCorePermissionKey("tara.testAgent", "mutation")).toBe("tara.operate");
    expect(resolveCorePermissionKey("tara.moderation.sendReply", "mutation")).toBe("tara.moderate");
    expect(resolveCorePermissionKey("tara.saveProviderConfiguration", "mutation")).toBe("tara.manage");
    expect(resolveCorePermissionKey("tara.futureUnknownOperation", "query")).toBe("tara.manage");
    expect(resolveCorePermissionKey("tara.futureUnknownOperation", "mutation")).toBe("tara.manage");
  });

  it("keeps Moderator-safe operational mutations aligned with tara.operate", () => {
    const routes = [
      "tara.moderation.saveOperationalSettings",
      "tara.saveCampaign",
      "tara.deleteCampaign",
      "tara.saveQualificationField",
      "tara.deleteQualificationField",
      "tara.saveKnowledge",
      "tara.deleteKnowledge",
      "tara.saveFollowupRule",
      "tara.deleteFollowupRule",
    ];
    for (const route of routes) expect(resolveCorePermissionKey(route, "mutation"), route).toBe("tara.operate");
    for (const name of [
      "tara.saveCampaign", "tara.deleteCampaign", "tara.saveQualificationField", "tara.deleteQualificationField",
      "tara.saveKnowledge", "tara.deleteKnowledge", "tara.saveFollowupRule", "tara.deleteFollowupRule",
    ]) expect(moderatorAccess).toContain(`"${name}"`);
  });

  it("exposes all Tara frontend permissions while keeping /tara on tara.view", () => {
    for (const permission of ["tara.view", "tara.operate", "tara.moderate", "tara.manage"]) {
      expect(permissionContext).toContain(`"${permission}"`);
    }
    expect(permissionContext).toContain('["/tara", "tara.view"]');
  });

  it("uses effective permissions to select Tara frontend surfaces", () => {
    expect(taraPage).toContain('const canOperate = can("tara.operate")');
    expect(taraPage).toContain('const canModerate = can("tara.moderate")');
    expect(taraPage).toContain('const canManage = can("tara.manage")');
    expect(taraPage).toContain('allowModerate={canModerate} allowOperate={canOperate}');
    expect(taraPage).toContain('if (!canManage)');
    expect(taraPage).toContain('<TaraModeratorOperations profile={profileQ.data} allowOperate={canOperate}/>');
  });

  it("defensively guards Admin operational mutations with tara.operate", () => {
    for (const name of [
      "saveCampaignM", "deleteCampaignM", "saveFieldM", "deleteFieldM", "saveKnowledgeM",
      "deleteKnowledgeM", "saveFollowupM", "deleteFollowupM", "testAgentM", "processQueueM",
    ]) {
      expect(taraPage).toContain(`const ${name}Raw = trpc.`);
      expect(taraPage).toContain(`const ${name} = guardTaraMutation(${name}Raw, canOperate, "tara.operate")`);
    }
  });

  it("keeps Tara Operations readable while guarding all operational writes", () => {
    expect(operations).toContain('data-tara-read-only="operate"');
    expect(operations).toContain("dashboardQ = trpc.tara.dashboard.useQuery");
    expect(operations).toContain("campaignsQ = trpc.tara.listCampaigns.useQuery");
    expect(operations).toContain("logsQ = trpc.tara.logs.useQuery");
    for (const name of [
      "saveSettings", "saveCampaign", "deleteCampaign", "saveField", "deleteField", "saveKnowledge",
      "deleteKnowledge", "saveFollowup", "deleteFollowup", "testAgent", "processQueue",
    ]) {
      expect(operations).toContain(`const ${name}Raw = trpc.`);
      expect(operations).toContain(`const ${name} = guardTaraMutation(${name}Raw, allowOperate, "tara.operate")`);
    }
  });

  it("guards native moderation actions with tara.moderate", () => {
    expect(workspace).toContain('allowModerate = true');
    expect(workspace).toContain('data-tara-read-only="moderate"');
    for (const name of ["generateM", "sendM", "retryM", "updateM", "noteM"]) {
      expect(workspace).toContain(`const ${name}Raw = trpc.tara.moderation.`);
      expect(workspace).toContain(`const ${name} = guardTaraMutation(${name}Raw, allowModerate, "tara.moderate")`);
    }
  });

  it("keeps Evolution Tara status under tara.operate without hijacking WhatsApp send", () => {
    expect(workspace).toContain('<EvolutionModeratorPanel profile={profile} allowOperate={allowOperate}/>');
    expect(workspace).toContain('const statusMRaw = trpc.tara.setConversationStatus.useMutation');
    expect(workspace).toContain('const statusM = guardTaraMutation(statusMRaw, allowOperate, "tara.operate")');
    expect(workspace).toContain('const sendM = trpc.waGateway.sendText.useMutation');
  });

  it("does not expose technical configuration to the non-manage branch", () => {
    const boundary = taraPage.indexOf("if (!canManage)");
    const adminMount = taraPage.indexOf("return <TaraAdminAgentPage", boundary);
    expect(boundary).toBeGreaterThan(-1);
    expect(adminMount).toBeGreaterThan(boundary);
    expect(taraPage).toContain("TaraProviderSettingsPanel");
    expect(taraPage).toContain("TaraVoiceSettingsPanel");
    expect(taraPage).toContain("TaraSocialChannelsPanel");
  });
});
'''
write(final_test_rel, final_test)

# -----------------------------------------------------------------------------
# Final fail-closed dirty-set and semantic checks.
# -----------------------------------------------------------------------------
final_dirty = set(filter(None, run("git", "status", "--short", "--untracked-files=all").splitlines()))
final_paths = set()
for line in final_dirty:
    path = line[3:] if len(line) >= 4 else ""
    if path:
        final_paths.add(path)
if final_paths != FINAL_EXPECTED:
    fail(f"FINAL_DIRTY_SET_MISMATCH:{sorted(final_paths)}")

# The two files completed by this recovery must contain their exact guards.
workspace = read("client/src/components/tara/TaraModeratorWorkspace.tsx")
for marker in [
    'allowModerate = true',
    'allowOperate = true',
    'data-tara-read-only="moderate"',
    'const sendMRaw = trpc.tara.moderation.sendReply.useMutation',
    'const sendM = guardTaraMutation(sendMRaw, allowModerate, "tara.moderate")',
    'const sendM = trpc.waGateway.sendText.useMutation',
    'const statusMRaw = trpc.tara.setConversationStatus.useMutation',
    'const statusM = guardTaraMutation(statusMRaw, allowOperate, "tara.operate")',
]:
    assert_once(workspace, marker, f"workspace-final:{marker}")

if run("git", "diff", "--check"):
    fail("FINAL_DIFF_CHECK_FAILED")

print(f"VERSION={VERSION}")
print(f"WORKFLOW_ID={WORKFLOW_ID}")
print("RECOVERY_APPLIED=YES")
print("PARTIAL_STATE_VERIFIED=YES")
print("FINAL_EXPECTED_FILES=5")
