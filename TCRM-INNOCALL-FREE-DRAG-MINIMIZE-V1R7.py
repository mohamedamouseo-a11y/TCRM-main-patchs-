#!/usr/bin/env python3
from pathlib import Path
import datetime
import re
import shutil
import sys

ROOT = Path.cwd()
TARGET = ROOT / "client/src/components/InnoCallWebCallWidget.tsx"
BACKUP_ROOT = ROOT / ".tcrm-recovery-backups"
MARKER = "TCRM_INNOCALL_FREE_DRAG_MINIMIZE_V1R7"
OLD_MARKER = "TCRM_INNOCALL_STABLE_DRAG_CLEANUP_V1R6R5"


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
    print(f"FILES_CHANGED={TARGET.relative_to(ROOT)}")
    print("ERROR=NONE")
    sys.exit(0)

required = [
    OLD_MARKER,
    'const DRAG_GRIP_ATTR = "data-tcrm-innocall-drag-grip";',
    'const POSITION_KEY = "tcrm:innocall-widget-position:v3";',
    'type DragMode = "direct" | "iframe-grip" | "not-found";',
    'function launcherLike(element: HTMLElement) {',
    'function createIframeGrip(',
    'const { isAuthenticated } = useAuth();',
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

# 2) Runtime attributes and persisted minimize state.
text = text.replace(
    'const DRAG_GRIP_ATTR = "data-tcrm-innocall-drag-grip";\n',
    'const DRAG_GRIP_ATTR = "data-tcrm-innocall-drag-grip";\n'
    'const CONTROL_BAR_ATTR = "data-tcrm-innocall-control-bar";\n'
    'const RESTORE_BUTTON_ATTR = "data-tcrm-innocall-restore-button";\n'
    'const MINIMIZE_BUTTON_ATTR = "data-tcrm-innocall-minimize-button";\n',
    1,
)
text = text.replace(
    'const POSITION_KEY = "tcrm:innocall-widget-position:v3";\n',
    'const POSITION_KEY = "tcrm:innocall-widget-position:v3";\n'
    'const MINIMIZED_KEY = "tcrm:innocall-widget-minimized:v1";\n',
    1,
)
text = text.replace(
    'type DragMode = "direct" | "iframe-grip" | "not-found";',
    'type DragMode = "direct" | "iframe-grip" | "controls" | "not-found";',
    1,
)

# 3) Add minimized-state helpers without touching provider config/business logic.
save_pos = '''function savePosition(position: Position) {
  try {
    localStorage.setItem(POSITION_KEY, JSON.stringify(position));
  } catch {
    // Ignore unavailable storage.
  }
}
'''
if save_pos not in text:
    fail("SAVE_POSITION_BLOCK_NOT_FOUND")
text = text.replace(
    save_pos,
    save_pos + '''
function readMinimized() {
  try {
    return localStorage.getItem(MINIMIZED_KEY) === "1";
  } catch {
    return false;
  }
}

function saveMinimized(value: boolean) {
  try {
    localStorage.setItem(MINIMIZED_KEY, value ? "1" : "0");
  } catch {
    // Ignore unavailable storage.
  }
}
''',
    1,
)

# 4) IMPORTANT FIX: a centered provider launcher must still be discoverable/draggable.
#    V1R6R5 rejected launchers unless they were already near a viewport edge.
launcher_pattern = re.compile(
    r'''function launcherLike\(element: HTMLElement\) \{.*?\n\}''',
    re.S,
)
launcher_replacement = '''function launcherLike(element: HTMLElement) {
  const { rect, visible } = visibleRect(element);
  if (!visible) return false;

  const compactArea = rect.width * rect.height <= 180_000;
  const compactSide = Math.min(rect.width, rect.height) <= 220;
  const bounded = rect.width <= 560 && rect.height <= 560;
  const position = getComputedStyle(element).position;
  const floating = position === "fixed" || position === "absolute" || position === "sticky";

  // Do NOT require the launcher to already be near an edge. The broken runtime
  // can leave InnoCall in the middle of the screen; it must still be discovered
  // so the user can drag it anywhere inside the viewport.
  return compactArea && compactSide && bounded && floating;
}'''
text, count = launcher_pattern.subn(launcher_replacement, text, count=1)
if count != 1:
    fail("LAUNCHER_CLASSIFIER_REPLACE_FAILED")

# 5) Cleanup must also remove our new controls.
remove_grip_pattern = re.compile(
    r'''function removeGrip\(\) \{.*?\n\}''',
    re.S,
)
remove_grip_replacement = '''function removeGrip() {
  document.querySelectorAll<HTMLElement>(
    `[${DRAG_GRIP_ATTR}="true"],`
      + `[${CONTROL_BAR_ATTR}="true"],`
      + `[${RESTORE_BUTTON_ATTR}="true"]`,
  ).forEach((item) => item.remove());
}'''
text, count = remove_grip_pattern.subn(remove_grip_replacement, text, count=1)
if count != 1:
    fail("REMOVE_GRIP_REPLACE_FAILED")

# 6) Replace iframe-only grip with universal external controls.
#    The provider remains fully clickable; dragging is done from our small handle.
controls_pattern = re.compile(
    r'''function createIframeGrip\(.*?\n\}\n\nfunction removeKnownWidgetDom\(\)''',
    re.S,
)
controls_replacement = '''function createWidgetControls(
  movable: HTMLElement,
  getPosition: () => Position,
  applyPosition: (next: Position) => void,
  initialMinimized: boolean,
  onMinimizedChange: (next: boolean) => void,
) {
  removeGrip();

  const bar = document.createElement("div");
  bar.setAttribute(CONTROL_BAR_ATTR, "true");
  Object.assign(bar.style, {
    position: "fixed",
    height: "30px",
    display: "flex",
    alignItems: "center",
    gap: "3px",
    padding: "3px",
    borderRadius: "999px",
    border: "1px solid rgba(139,92,246,.34)",
    background: "rgba(15,23,42,.86)",
    backdropFilter: "blur(14px)",
    WebkitBackdropFilter: "blur(14px)",
    boxShadow: "0 8px 24px rgba(15,23,42,.28), inset 0 1px 0 rgba(255,255,255,.12)",
    zIndex: "10002",
  });

  const move = document.createElement("button");
  move.type = "button";
  move.setAttribute(DRAG_GRIP_ATTR, "true");
  move.setAttribute("aria-label", "Move InnoCall");
  move.title = "اسحب لتحريك InnoCall";
  move.textContent = "⠿";
  Object.assign(move.style, {
    width: "26px",
    height: "24px",
    border: "0",
    borderRadius: "999px",
    background: "transparent",
    color: "rgba(255,255,255,.92)",
    display: "grid",
    placeItems: "center",
    padding: "0",
    fontSize: "16px",
    lineHeight: "1",
    cursor: "grab",
    touchAction: "none",
    userSelect: "none",
  });

  const minimize = document.createElement("button");
  minimize.type = "button";
  minimize.setAttribute(MINIMIZE_BUTTON_ATTR, "true");
  minimize.setAttribute("aria-label", "Minimize InnoCall");
  minimize.title = "تصغير InnoCall";
  minimize.textContent = "−";
  Object.assign(minimize.style, {
    width: "26px",
    height: "24px",
    border: "0",
    borderRadius: "999px",
    background: "rgba(139,92,246,.22)",
    color: "#fff",
    display: "grid",
    placeItems: "center",
    padding: "0",
    fontSize: "18px",
    fontWeight: "700",
    lineHeight: "1",
    cursor: "pointer",
  });

  const restore = document.createElement("button");
  restore.type = "button";
  restore.setAttribute(RESTORE_BUTTON_ATTR, "true");
  restore.setAttribute("aria-label", "Restore InnoCall");
  restore.title = "فتح InnoCall";
  restore.textContent = "☎";
  Object.assign(restore.style, {
    position: "fixed",
    width: "42px",
    height: "42px",
    border: "1px solid rgba(255,255,255,.34)",
    borderRadius: "999px",
    background: "linear-gradient(145deg, #7c3aed 0%, #4f46e5 58%, #2563eb 100%)",
    color: "#fff",
    boxShadow: "0 10px 28px rgba(79,70,229,.34), inset 0 1px 0 rgba(255,255,255,.26)",
    display: "none",
    placeItems: "center",
    padding: "0",
    fontSize: "18px",
    lineHeight: "1",
    cursor: "pointer",
    zIndex: "10002",
  });

  bar.append(move, minimize);
  document.body.append(bar, restore);

  const savedInline = {
    opacity: movable.style.opacity,
    visibility: movable.style.visibility,
    pointerEvents: movable.style.pointerEvents,
  };

  let minimized = initialMinimized;

  const sync = () => {
    if (!movable.isConnected) {
      bar.remove();
      restore.remove();
      return;
    }

    if (minimized) {
      bar.style.display = "none";
      restore.style.display = "grid";
      const safe = clamp(getPosition(), 42, 42);
      restore.style.right = `${safe.right}px`;
      restore.style.bottom = `${safe.bottom}px`;
      restore.style.left = "auto";
      restore.style.top = "auto";
      return;
    }

    restore.style.display = "none";
    bar.style.display = "flex";
    const rect = movable.getBoundingClientRect();
    const barWidth = 61;
    const left = Math.max(GAP, Math.min(
      rect.right - barWidth,
      window.innerWidth - barWidth - GAP,
    ));
    const top = Math.max(GAP, Math.min(
      rect.top - 18,
      window.innerHeight - 30 - GAP,
    ));
    bar.style.left = `${left}px`;
    bar.style.top = `${top}px`;
    bar.style.right = "auto";
    bar.style.bottom = "auto";
  };

  const setMinimized = (next: boolean) => {
    minimized = next;
    saveMinimized(next);
    onMinimizedChange(next);

    if (next) {
      movable.style.setProperty("opacity", "0", "important");
      movable.style.setProperty("visibility", "hidden", "important");
      movable.style.setProperty("pointer-events", "none", "important");
    } else {
      if (savedInline.opacity) movable.style.setProperty("opacity", savedInline.opacity);
      else movable.style.removeProperty("opacity");
      if (savedInline.visibility) movable.style.setProperty("visibility", savedInline.visibility);
      else movable.style.removeProperty("visibility");
      if (savedInline.pointerEvents) movable.style.setProperty("pointer-events", savedInline.pointerEvents);
      else movable.style.removeProperty("pointer-events");
      applyPosition(getPosition());
    }

    sync();

    window.dispatchEvent(new CustomEvent("tcrm:innocall-minimized-change", {
      detail: { minimized: next },
    }));
  };

  const cleanupDrag = bindPointerDrag(
    move,
    movable,
    getPosition,
    (next) => {
      applyPosition(next);
      sync();
    },
    "grip",
  );

  minimize.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    setMinimized(true);
  });

  restore.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    setMinimized(false);
  });

  if (initialMinimized) {
    setMinimized(true);
  } else {
    sync();
  }

  return {
    sync,
    cleanup: () => {
      cleanupDrag();
      bar.remove();
      restore.remove();
    },
  };
}

function removeKnownWidgetDom()'''
text, count = controls_pattern.subn(controls_replacement, text, count=1)
if count != 1:
    fail("CONTROLS_BLOCK_REPLACE_FAILED")

# 7) Persist minimized state inside the existing effect.
text = text.replace(
    '    let position = clamp(readPosition());\n    let currentCandidate: Candidate | null = null;\n',
    '    let position = clamp(readPosition());\n'
    '    let minimized = readMinimized();\n'
    '    let currentCandidate: Candidate | null = null;\n',
    1,
)

# 8) Use the external controls for EVERY discovered launcher (iframe or not).
#    This avoids provider click/iframe quirks and restores reliable free movement.
bind_pattern = re.compile(
    r'''      if \(candidate\.iframeDominant\) \{.*?      \}\n\n      guardCleanup = createPositionGuard\(''',
    re.S,
)
bind_replacement = '''      const controls = createWidgetControls(
        candidate.movable,
        () => position,
        applyEverywhere,
        minimized,
        (next) => {
          minimized = next;
        },
      );
      syncGrip = controls.sync;
      dragCleanup = controls.cleanup;
      publishDragMode("controls", candidate);

      guardCleanup = createPositionGuard('''
text, count = bind_pattern.subn(bind_replacement, text, count=1)
if count != 1:
    fail("BIND_PROVIDER_BLOCK_REPLACE_FAILED")

# 9) Final validation before writing.
checks = [
    MARKER,
    'const MINIMIZED_KEY = "tcrm:innocall-widget-minimized:v1";',
    'return compactArea && compactSide && bounded && floating;',
    'function createWidgetControls(',
    'publishDragMode("controls", candidate);',
    'restore.textContent = "☎";',
    'minimize.textContent = "−";',
]
for token in checks:
    if token not in text:
        fail(f"POST_PATCH_VALIDATION_FAILED:{token}")

if text == original:
    fail("NO_CHANGE")

BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
backup = BACKUP_ROOT / f"InnoCallWebCallWidget.tsx.{stamp}.bak"
shutil.copy2(TARGET, backup)
TARGET.write_text(text, encoding="utf-8")

print("PATCH=YES")
print("INNOCALL_FREE_DRAG=YES")
print("CENTERED_WIDGET_DISCOVERY_FIX=YES")
print("EXTERNAL_DRAG_HANDLE=YES")
print("MINIMIZE_BUTTON=YES")
print("RESTORE_BUTTON=YES")
print("MINIMIZED_STATE_PERSISTED=YES")
print("PROVIDER_CONFIG_UNCHANGED=YES")
print("BACKEND_UNCHANGED=YES")
print(f"BACKUP_CREATED={backup.relative_to(ROOT)}")
print(f"FILES_CHANGED={TARGET.relative_to(ROOT)}")
print("ERROR=NONE")
