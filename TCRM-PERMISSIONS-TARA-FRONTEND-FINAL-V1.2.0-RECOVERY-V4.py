#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

WORKFLOW_SERIES = "TCRM-PERMISSIONS"
MODULE = "TARA"
PHASE = "FRONTEND-ACTIONS-FINAL-VERIFICATION-RECOVERY"
VERSION = "V1.2.0"
WORKFLOW_ID = "TCRM-PERMISSIONS-TARA-FRONTEND-FINAL-V1.2.0-RECOVERY-V4"
PREVIOUS_VERSION = "V1.0.1"
PREVIOUS_WORKFLOW_ID = "TCRM-PERMISSIONS-TARA-API-ENFORCEMENT-V1.0.1-RECOVERY"
RECOVERY_FROM_WORKFLOW_ID = "TCRM-PERMISSIONS-TARA-FRONTEND-FINAL-V1.2.0-RECOVERY-V3"
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


def dirty_paths() -> set[str]:
    tracked = set(filter(None, run("git", "diff", "--name-only").splitlines()))
    untracked = set(filter(None, run("git", "ls-files", "--others", "--exclude-standard").splitlines()))
    return tracked | untracked


def assert_count(text: str, marker: str, expected: int, label: str) -> None:
    count = text.count(marker)
    if count != expected:
        fail(f"STATE_MISMATCH:{label}:count={count}:expected={expected}")


def assert_once(text: str, marker: str, label: str) -> None:
    assert_count(text, marker, 1, label)


head = run("git", "rev-parse", "HEAD")
if head != BASELINE:
    fail(f"BASELINE_MISMATCH:{head}")

if run("git", "diff", "--cached", "--name-only"):
    fail("STAGED_CHANGES_PRESENT")

paths = dirty_paths()
if paths != EXPECTED:
    fail(f"FINAL_DIRTY_SET_MISMATCH:{sorted(paths)}")

run("git", "diff", "--check")

# -----------------------------------------------------------------------------
# PermissionContext
# -----------------------------------------------------------------------------
ctx = read("client/src/contexts/PermissionContext.tsx")
for marker in [
    '  "tara.view",',
    '  "tara.operate",',
    '  "tara.moderate",',
    '  "tara.manage",',
    '["/tara", "tara.view"]',
]:
    assert_once(ctx, marker, f"permission-context:{marker}")

# -----------------------------------------------------------------------------
# TaraAgentPage
# -----------------------------------------------------------------------------
page = read("client/src/pages/TaraAgentPage.tsx")
for marker in [
    'import { usePermissions } from "@/contexts/PermissionContext";',
    'const canOperate = can("tara.operate");',
    'const canModerate = can("tara.moderate");',
    'const canManage = can("tara.manage");',
    '<TaraModeratorWorkspace profile={profileQ.data} allowModerate={canModerate} allowOperate={canOperate}/>',
    'if (!canManage)',
    'function guardTaraMutation(',
]:
    assert_once(page, marker, f"tara-page:{marker}")

operations_mount = '<TaraModeratorOperations profile={profileQ.data} allowOperate={canOperate}/>'
assert_count(page, operations_mount, 2, "tara-page:operations-mount")

for name in [
    "saveCampaignM", "deleteCampaignM", "saveFieldM", "deleteFieldM",
    "saveKnowledgeM", "deleteKnowledgeM", "saveFollowupM", "deleteFollowupM",
    "testAgentM", "processQueueM",
]:
    assert_once(page, f"const {name}Raw = trpc.", f"tara-page-raw:{name}")
    assert_once(
        page,
        f'const {name} = guardTaraMutation({name}Raw, canOperate, "tara.operate");',
        f"tara-page-guard:{name}",
    )

# -----------------------------------------------------------------------------
# TaraModeratorOperations
# -----------------------------------------------------------------------------
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
    assert_once(
        ops,
        f'const {name} = guardTaraMutation({name}Raw, allowOperate, "tara.operate");',
        f"tara-operations-guard:{name}",
    )

# -----------------------------------------------------------------------------
# TaraModeratorWorkspace
# IMPORTANT: there are intentionally TWO `allowOperate = true` occurrences:
# 1) TaraModeratorWorkspace
# 2) nested EvolutionModeratorPanel
# Validate exact component signatures instead of generic substring uniqueness.
# -----------------------------------------------------------------------------
workspace = read("client/src/components/tara/TaraModeratorWorkspace.tsx")

assert_once(
    workspace,
    'export default function TaraModeratorWorkspace({ profile, allowModerate = true, allowOperate = true }: {',
    "workspace:main-component-signature",
)
assert_once(
    workspace,
    'function EvolutionModeratorPanel({ profile, allowOperate = true }: {',
    "workspace:evolution-component-signature",
)
assert_count(workspace, 'allowOperate = true', 2, "workspace:allowOperate-defaults")
assert_once(workspace, 'allowModerate = true', "workspace:allowModerate-default")
assert_once(workspace, 'data-tara-read-only="moderate"', "workspace:moderate-readonly-notice")
assert_once(
    workspace,
    '<EvolutionModeratorPanel profile={profile} allowOperate={allowOperate}/>',
    "workspace:evolution-prop-pass",
)

moderation_routes = {
    "generateM": "tara.moderation.generateReply",
    "sendM": "tara.moderation.sendReply",
    "retryM": "tara.moderation.retryReply",
    "updateM": "tara.moderation.updateConversation",
    "noteM": "tara.moderation.addNote",
}
for name, route in moderation_routes.items():
    assert_once(
        workspace,
        f"const {name}Raw = trpc.{route}.useMutation",
        f"workspace:moderate-raw:{name}",
    )
    assert_once(
        workspace,
        f'const {name} = guardTaraMutation({name}Raw, allowModerate, "tara.moderate");',
        f"workspace:moderate-guard:{name}",
    )

# Preserve WhatsApp Evolution send untouched while Tara status uses tara.operate.
assert_once(
    workspace,
    'const sendM = trpc.waGateway.sendText.useMutation',
    "workspace:whatsapp-send-preserved",
)
assert_once(
    workspace,
    'const statusMRaw = trpc.tara.setConversationStatus.useMutation',
    "workspace:status-raw",
)
assert_once(
    workspace,
    'const statusM = guardTaraMutation(statusMRaw, allowOperate, "tara.operate");',
    "workspace:status-guard",
)

# -----------------------------------------------------------------------------
# Final regression test file
# -----------------------------------------------------------------------------
final_test = read("server/security/taraFinalPermission.test.ts")
for marker in [
    'describe("Tara permissions final V1.2.0"',
    'resolveCorePermissionKey("tara.dashboard", "query")',
    'resolveCorePermissionKey("tara.testAgent", "mutation")',
    'resolveCorePermissionKey("tara.moderation.sendReply", "mutation")',
    'resolveCorePermissionKey("tara.saveProviderConfiguration", "mutation")',
    'resolveCorePermissionKey("tara.futureUnknownOperation", "query")',
    'resolveCorePermissionKey("tara.futureUnknownOperation", "mutation")',
    'data-tara-read-only="operate"',
    'data-tara-read-only="moderate"',
    'const sendM = trpc.waGateway.sendText.useMutation',
    'const statusM = guardTaraMutation(statusMRaw, allowOperate, "tara.operate")',
]:
    if marker not in final_test:
        fail(f"FINAL_TEST_MISSING_MARKER:{marker}")

run("git", "diff", "--check")

# This V4 intentionally writes NOTHING to the project. It verifies the five-file
# state produced before V3's overly-generic assertion stopped execution.
print(f"VERSION={VERSION}")
print(f"WORKFLOW_ID={WORKFLOW_ID}")
print(f"RECOVERY_FROM_WORKFLOW_ID={RECOVERY_FROM_WORKFLOW_ID}")
print("INPUT_STATE=FINAL_5_FROM_V2")
print("FINAL_STATE_VERIFIED=YES")
print("SOURCE_RECOVERY_WRITE=NO")
print("ROBUST_DIRTY_PATH_DETECTION=YES")
print("WORKSPACE_DUPLICATE_DEFAULT_HANDLED=YES")
print("FINAL_EXPECTED_FILES=5")
