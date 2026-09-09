#!/usr/bin/env python3
from pathlib import Path
import datetime
import shutil
import sys

ROOT = Path.cwd()
TARGET = ROOT / "client/src/components/InnoCallWebCallWidget.tsx"
BACKUP_ROOT = ROOT / ".tcrm-recovery-backups"
OLD_MARKER = "TCRM_INNOCALL_FREE_DRAG_MINIMIZE_V1R7_1_RESTORE_HOTFIX"
MARKER = "TCRM_INNOCALL_V1R7_2_STABLE_CONTROLS_DRAG"


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
    print("INNOCALL_V1R7_2=YES")
    print(f"FILES_CHANGED={TARGET.relative_to(ROOT)}")
    print("ERROR=NONE")
    sys.exit(0)

required = [
    OLD_MARKER,
    'function createWidgetControls(',
    'let minimized = initialMinimized;',
    'const sync = () => {',
    'const bindProviderDom = () => {',
    'publishDragMode("controls", candidate);',
]
for token in required:
    if token not in text:
        fail(f"GUARD_MISSING:{token}")

# 1) Version marker.
text = text.replace(
    f"// {OLD_MARKER}\n",
    f"// {MARKER}\n// {OLD_MARKER}\n",
    1,
)

# 2) Make the controls self-healing, but never resurrect them after cleanup.
needle = '''  let minimized = initialMinimized;\n\n  const sync = () => {\n    if (!movable.isConnected) {\n      bar.remove();\n      restore.remove();\n      return;\n    }\n\n    if (minimized) {\n      bar.style.display = "none";\n      restore.style.display = "grid";\n'''
replacement = '''  let minimized = initialMinimized;\n  let disposed = false;\n\n  const sync = () => {\n    if (disposed) return;\n    if (!movable.isConnected) {\n      bar.remove();\n      restore.remove();\n      return;\n    }\n\n    if (minimized) {\n      if (!restore.isConnected) document.body.appendChild(restore);\n      bar.style.display = "none";\n      restore.style.display = "grid";\n'''
if needle not in text:
    fail("CONTROLS_SYNC_ANCHOR_NOT_FOUND")
text = text.replace(needle, replacement, 1)

needle2 = '''    restore.style.display = "none";\n    bar.style.display = "flex";\n    const rect = movable.getBoundingClientRect();\n'''
replacement2 = '''    if (!bar.isConnected) document.body.appendChild(bar);\n    restore.style.display = "none";\n    bar.style.display = "flex";\n    const rect = movable.getBoundingClientRect();\n'''
if needle2 not in text:
    fail("CONTROL_BAR_SELF_HEAL_ANCHOR_NOT_FOUND")
text = text.replace(needle2, replacement2, 1)

needle3 = '''    cleanup: () => {\n      cleanupDrag();\n      bar.remove();\n      restore.remove();\n    },\n'''
replacement3 = '''    cleanup: () => {\n      disposed = true;\n      cleanupDrag();\n      bar.remove();\n      restore.remove();\n    },\n'''
if needle3 not in text:
    fail("CONTROLS_CLEANUP_ANCHOR_NOT_FOUND")
text = text.replace(needle3, replacement3, 1)

# 3) Core V1R7.2 fix:
# Once a provider node has been successfully bound, polling must NOT tear down and
# rediscover it every time the provider mutates its internal DOM/classes. That churn
# was removing the external control bar even though the visible Call Us launcher
# remained on screen. Keep the current binding while its movable node is connected.
old_bind = '''    const bindProviderDom = () => {\n      cleanupLegacyArtifacts();\n\n      // V1R7.1: when minimized, the provider node is intentionally hidden.\n      // Do not rediscover/cleanup it on the polling cycle, otherwise the\n      // restore button is removed together with the drag controls and the\n      // widget becomes impossible to restore.\n      if (minimized && currentCandidate?.movable.isConnected && dragCleanup) {\n        document.documentElement.setAttribute("data-innocall-minimize-restore-hotfix", "V1R7.1");\n        syncGrip?.();\n        publishDragMode("controls", currentCandidate);\n        return 1;\n      }\n\n      const provider = classifyProviderDom();\n'''
new_bind = '''    const bindProviderDom = () => {\n      // V1R7.2: keep a successfully-bound provider node stable for BOTH open and\n      // minimized states. InnoCall mutates its own DOM/classes after render; the\n      // old polling path interpreted those mutations as a new candidate and called\n      // cleanupDragBinding(), which removed the external drag/minimize bar.\n      // As long as the actual movable node is still connected, preserve the same\n      // binding and only re-apply position + sync controls.\n      if (currentCandidate?.movable.isConnected && dragCleanup) {\n        document.documentElement.setAttribute("data-innocall-stable-controls", "V1R7.2");\n        if (minimized) {\n          document.documentElement.setAttribute("data-innocall-minimize-restore-hotfix", "V1R7.1");\n        }\n        position = positionLauncher(currentCandidate.movable, position);\n        syncGrip?.();\n        publishDragMode("controls", currentCandidate);\n        return 1;\n      }\n\n      cleanupLegacyArtifacts();\n      const provider = classifyProviderDom();\n'''
if old_bind not in text:
    fail("V1R7_1_BIND_BLOCK_NOT_FOUND")
text = text.replace(old_bind, new_bind, 1)

# 4) Add a lightweight motion hint to the movable node. Positioning still uses the
# existing requestAnimationFrame path, so call behavior/provider internals remain untouched.
needle4 = '''  launcher.style.setProperty("transition", "none", "important");\n\n  return safe;\n}\n'''
replacement4 = '''  launcher.style.setProperty("transition", "none", "important");\n  launcher.style.setProperty("will-change", "right, bottom", "important");\n\n  return safe;\n}\n'''
if needle4 not in text:
    fail("POSITION_LAUNCHER_ANCHOR_NOT_FOUND")
text = text.replace(needle4, replacement4, 1)

checks = [
    MARKER,
    'data-innocall-stable-controls',
    'if (currentCandidate?.movable.isConnected && dragCleanup)',
    'if (!restore.isConnected) document.body.appendChild(restore);',
    'if (!bar.isConnected) document.body.appendChild(bar);',
    'let disposed = false;',
    'will-change", "right, bottom"',
]
for token in checks:
    if token not in text:
        fail(f"POST_PATCH_VALIDATION_FAILED:{token}")

if text == original:
    fail("NO_CHANGE")

BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
backup = BACKUP_ROOT / f"InnoCallWebCallWidget.tsx.{stamp}.v1r7-2.bak"
shutil.copy2(TARGET, backup)
TARGET.write_text(text, encoding="utf-8")

print("PATCH=YES")
print("INNOCALL_V1R7_2=YES")
print("STABLE_CONTROL_BINDING=YES")
print("CONTROL_BAR_SELF_HEAL=YES")
print("RESTORE_SELF_HEAL=YES")
print("POLLING_REBIND_CHURN_FIXED=YES")
print("FREE_DRAG_PRESERVED=YES")
print("MINIMIZE_RESTORE_PRESERVED=YES")
print("PROVIDER_CONFIG_UNCHANGED=YES")
print("BACKEND_UNCHANGED=YES")
print(f"BACKUP_CREATED={backup.relative_to(ROOT)}")
print(f"FILES_CHANGED={TARGET.relative_to(ROOT)}")
print("ERROR=NONE")
