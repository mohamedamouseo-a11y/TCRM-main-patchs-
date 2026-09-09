#!/usr/bin/env python3
from pathlib import Path
import datetime
import shutil
import sys

ROOT = Path.cwd()
TARGET = ROOT / "client/src/components/InnoCallWebCallWidget.tsx"
BACKUP_ROOT = ROOT / ".tcrm-recovery-backups"
OLD_MARKER = "TCRM_INNOCALL_V1R7_2_STABLE_CONTROLS_DRAG"
MARKER = "TCRM_INNOCALL_V1R7_3_ROBUST_DRAG_ENGINE"


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
    print("INNOCALL_V1R7_3=YES")
    print(f"FILES_CHANGED={TARGET.relative_to(ROOT)}")
    print("ERROR=NONE")
    sys.exit(0)

required = [
    OLD_MARKER,
    'function createWidgetControls(',
    'const cleanupDrag = bindPointerDrag(',
    'move,\n    movable,',
    'savePosition(position: Position)',
    'const MINIMIZE_BUTTON_ATTR = "data-tcrm-innocall-minimize-button";',
]
for token in required:
    if token not in text:
        fail(f"GUARD_MISSING:{token}")

text = text.replace(
    f"// {OLD_MARKER}\n",
    f"// {MARKER}\n// {OLD_MARKER}\n",
    1,
)

# Make the whole compact control bar an explicit drag surface. This is much easier
# to grab than the tiny glyph and stays outside the cross-origin provider iframe.
bar_style_old = '''    zIndex: "10002",\n  });\n\n  const move = document.createElement("button");'''
bar_style_new = '''    zIndex: "10002",\n    cursor: "grab",\n    touchAction: "none",\n    userSelect: "none",\n  });\n\n  const move = document.createElement("button");'''
if bar_style_old not in text:
    fail("CONTROL_BAR_STYLE_ANCHOR_NOT_FOUND")
text = text.replace(bar_style_old, bar_style_new, 1)

old_drag = '''  const cleanupDrag = bindPointerDrag(\n    move,\n    movable,\n    getPosition,\n    (next) => {\n      applyPosition(next);\n      sync();\n    },\n    "grip",\n  );\n'''

new_drag = '''  // V1R7.3 robust external drag engine.\n  // The previous generic drag binding was technically present but could fail to\n  // move the provider in the real browser runtime. Keep dragging completely in\n  // the parent document, capture the pointer on our own control bar, and apply\n  // right/bottom coordinates synchronously on every pointermove.\n  type ControlDragState = {\n    pointerId: number;\n    startX: number;\n    startY: number;\n    startPosition: Position;\n    moved: boolean;\n  };\n\n  let controlDrag: ControlDragState | null = null;\n\n  const controlDragDown = (event: PointerEvent) => {\n    if (event.button !== 0 || minimized) return;\n    const target = event.target instanceof Element ? event.target : null;\n    if (target?.closest(`[${MINIMIZE_BUTTON_ATTR}="true"]`)) return;\n\n    event.preventDefault();\n    event.stopPropagation();\n\n    controlDrag = {\n      pointerId: event.pointerId,\n      startX: event.clientX,\n      startY: event.clientY,\n      startPosition: getPosition(),\n      moved: false,\n    };\n\n    try {\n      bar.setPointerCapture(event.pointerId);\n    } catch {\n      // Window-level listeners below still keep drag operational.\n    }\n\n    bar.style.cursor = "grabbing";\n    move.style.cursor = "grabbing";\n    document.documentElement.setAttribute("data-innocall-drag-active", "true");\n  };\n\n  const controlDragMove = (event: PointerEvent) => {\n    if (!controlDrag || event.pointerId !== controlDrag.pointerId) return;\n\n    const dx = event.clientX - controlDrag.startX;\n    const dy = event.clientY - controlDrag.startY;\n    if (!controlDrag.moved && Math.hypot(dx, dy) < 2) return;\n    controlDrag.moved = true;\n\n    event.preventDefault();\n    event.stopPropagation();\n\n    const rect = movable.getBoundingClientRect();\n    const next = clamp({\n      right: controlDrag.startPosition.right - dx,\n      bottom: controlDrag.startPosition.bottom - dy,\n    }, rect.width, rect.height);\n\n    // No provider DOM interaction is needed; only move its outer fixed container.\n    applyPosition(next);\n    sync();\n    document.documentElement.setAttribute("data-innocall-drag-last-right", String(Math.round(next.right)));\n    document.documentElement.setAttribute("data-innocall-drag-last-bottom", String(Math.round(next.bottom)));\n  };\n\n  const controlDragEnd = (event: PointerEvent) => {\n    if (!controlDrag || event.pointerId !== controlDrag.pointerId) return;\n\n    const didMove = controlDrag.moved;\n    event.preventDefault();\n    event.stopPropagation();\n\n    try {\n      if (bar.hasPointerCapture(event.pointerId)) bar.releasePointerCapture(event.pointerId);\n    } catch {\n      // Ignore unavailable pointer capture.\n    }\n\n    bar.style.cursor = "grab";\n    move.style.cursor = "grab";\n    controlDrag = null;\n    document.documentElement.removeAttribute("data-innocall-drag-active");\n\n    if (didMove) {\n      const finalPosition = getPosition();\n      savePosition(finalPosition);\n      applyPosition(finalPosition);\n      sync();\n      window.dispatchEvent(new CustomEvent("tcrm:innocall-position-change", {\n        detail: finalPosition,\n      }));\n    }\n  };\n\n  bar.addEventListener("pointerdown", controlDragDown, true);\n  window.addEventListener("pointermove", controlDragMove, { capture: true, passive: false });\n  window.addEventListener("pointerup", controlDragEnd, { capture: true, passive: false });\n  window.addEventListener("pointercancel", controlDragEnd, { capture: true, passive: false });\n\n  const cleanupDrag = () => {\n    bar.removeEventListener("pointerdown", controlDragDown, true);\n    window.removeEventListener("pointermove", controlDragMove, true);\n    window.removeEventListener("pointerup", controlDragEnd, true);\n    window.removeEventListener("pointercancel", controlDragEnd, true);\n    controlDrag = null;\n    document.documentElement.removeAttribute("data-innocall-drag-active");\n  };\n'''

if old_drag not in text:
    fail("GENERIC_CONTROL_DRAG_BLOCK_NOT_FOUND")
text = text.replace(old_drag, new_drag, 1)

checks = [
    MARKER,
    'type ControlDragState = {',
    'bar.setPointerCapture(event.pointerId);',
    'window.addEventListener("pointermove", controlDragMove',
    'applyPosition(next);',
    'savePosition(finalPosition);',
    'data-innocall-drag-active',
    'cursor: "grab"',
]
for token in checks:
    if token not in text:
        fail(f"POST_PATCH_VALIDATION_FAILED:{token}")

if text == original:
    fail("NO_CHANGE")

BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
backup = BACKUP_ROOT / f"InnoCallWebCallWidget.tsx.{stamp}.v1r7-3.bak"
shutil.copy2(TARGET, backup)
TARGET.write_text(text, encoding="utf-8")

print("PATCH=YES")
print("INNOCALL_V1R7_3=YES")
print("ROBUST_PARENT_DOCUMENT_DRAG_ENGINE=YES")
print("WHOLE_CONTROL_BAR_DRAG_SURFACE=YES")
print("POINTER_CAPTURE=YES")
print("WINDOW_POINTERMOVE_FALLBACK=YES")
print("SYNCHRONOUS_POSITION_UPDATE=YES")
print("POSITION_PERSISTENCE_PRESERVED=YES")
print("MINIMIZE_RESTORE_PRESERVED=YES")
print("PROVIDER_CONFIG_UNCHANGED=YES")
print("BACKEND_UNCHANGED=YES")
print(f"BACKUP_CREATED={backup.relative_to(ROOT)}")
print(f"FILES_CHANGED={TARGET.relative_to(ROOT)}")
print("ERROR=NONE")
