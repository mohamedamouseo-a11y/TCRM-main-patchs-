#!/usr/bin/env python3
from pathlib import Path
import datetime
import shutil
import sys

ROOT = Path.cwd()
TARGET = ROOT / "client/src/components/InnoCallWebCallWidget.tsx"
BACKUP_ROOT = ROOT / ".tcrm-recovery-backups"
OLD_MARKER = "TCRM_INNOCALL_FREE_DRAG_MINIMIZE_V1R7"
MARKER = "TCRM_INNOCALL_FREE_DRAG_MINIMIZE_V1R7_1_RESTORE_HOTFIX"


def fail(msg: str):
    print(f"ERROR={msg}")
    sys.exit(1)


if not TARGET.exists():
    fail(f"TARGET_MISSING:{TARGET}")

text = TARGET.read_text(encoding="utf-8")
original = text

if MARKER in text:
    print("PATCH=YES")
    print("ALREADY_APPLIED=YES")
    print("INNOCALL_V1R7_1_RESTORE_HOTFIX=YES")
    print(f"FILES_CHANGED={TARGET.relative_to(ROOT)}")
    print("ERROR=NONE")
    sys.exit(0)

required = [
    OLD_MARKER,
    'let minimized = readMinimized();',
    'function createWidgetControls(',
    'publishDragMode("controls", candidate);',
    'const bindProviderDom = () => {',
]
for token in required:
    if token not in text:
        fail(f"GUARD_MISSING:{token}")

# Add hotfix marker above V1R7.
text = text.replace(
    f"// {OLD_MARKER}\n",
    f"// {MARKER}\n// {OLD_MARKER}\n",
    1,
)

# Root cause fix:
# V1R7 hides the provider movable with visibility:hidden when minimized.
# The discovery poll then rejects it as non-visible, calls cleanupDragBinding(),
# and removes the restore control as well. Result: the whole InnoCall appears gone.
# While minimized and the already-bound provider node is still connected,
# keep that binding alive and only sync the external restore control.
needle = '''    const bindProviderDom = () => {\n      cleanupLegacyArtifacts();\n      const provider = classifyProviderDom();\n'''
replacement = '''    const bindProviderDom = () => {\n      cleanupLegacyArtifacts();\n\n      // V1R7.1: when minimized, the provider node is intentionally hidden.\n      // Do not rediscover/cleanup it on the polling cycle, otherwise the\n      // restore button is removed together with the drag controls and the\n      // widget becomes impossible to restore.\n      if (minimized && currentCandidate?.movable.isConnected && dragCleanup) {\n        syncGrip?.();\n        publishDragMode("controls", currentCandidate);\n        return 1;\n      }\n\n      const provider = classifyProviderDom();\n'''
if needle not in text:
    fail("BIND_PROVIDER_ANCHOR_NOT_FOUND")
text = text.replace(needle, replacement, 1)

# Add a defensive runtime marker/state attribute so QA can verify the hotfix path.
needle2 = '''      if (minimized && currentCandidate?.movable.isConnected && dragCleanup) {\n        syncGrip?.();\n        publishDragMode("controls", currentCandidate);\n        return 1;\n      }\n'''
replacement2 = '''      if (minimized && currentCandidate?.movable.isConnected && dragCleanup) {\n        document.documentElement.setAttribute("data-innocall-minimize-restore-hotfix", "V1R7.1");\n        syncGrip?.();\n        publishDragMode("controls", currentCandidate);\n        return 1;\n      }\n'''
if needle2 not in text:
    fail("MINIMIZED_KEEPALIVE_BLOCK_NOT_FOUND")
text = text.replace(needle2, replacement2, 1)

checks = [
    MARKER,
    'data-innocall-minimize-restore-hotfix',
    'if (minimized && currentCandidate?.movable.isConnected && dragCleanup)',
    'syncGrip?.();',
    'publishDragMode("controls", currentCandidate);',
]
for token in checks:
    if token not in text:
        fail(f"POST_PATCH_VALIDATION_FAILED:{token}")

if text == original:
    fail("NO_CHANGE")

BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
backup = BACKUP_ROOT / f"InnoCallWebCallWidget.tsx.{stamp}.v1r7-1.bak"
shutil.copy2(TARGET, backup)
TARGET.write_text(text, encoding="utf-8")

print("PATCH=YES")
print("INNOCALL_V1R7_1_RESTORE_HOTFIX=YES")
print("ROOT_CAUSE_FIXED=MINIMIZED_PROVIDER_WAS_REJECTED_BY_VISIBILITY_DISCOVERY_AND_CLEANUP_REMOVED_RESTORE_BUTTON")
print("MINIMIZED_BINDING_KEEPALIVE=YES")
print("RESTORE_CONTROL_PRESERVED_DURING_POLLING=YES")
print("FREE_DRAG_LOGIC_PRESERVED=YES")
print("PROVIDER_CONFIG_UNCHANGED=YES")
print("BACKEND_UNCHANGED=YES")
print(f"BACKUP_CREATED={backup.relative_to(ROOT)}")
print(f"FILES_CHANGED={TARGET.relative_to(ROOT)}")
print("ERROR=NONE")
