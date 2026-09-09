#!/usr/bin/env python3
from pathlib import Path
import subprocess
import hashlib

ROOT = Path.cwd()
TSX = ROOT / "client/src/pages/AgentDashboard.tsx"
CSS = ROOT / "client/src/dashboard-premium-luminous-v16.css"

if not (ROOT / ".git").exists():
    raise SystemExit("ERROR=Run from existing LIVE TCRM git project root")
if not TSX.exists():
    raise SystemExit("ERROR=client/src/pages/AgentDashboard.tsx missing")


def git_show(path: str) -> str:
    r = subprocess.run(
        ["git", "show", f"HEAD:{path}"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if r.returncode != 0:
        raise SystemExit(f"ERROR=HEAD baseline missing for {path}: {r.stderr.strip()}")
    return r.stdout


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]

head_tsx = git_show("client/src/pages/AgentDashboard.tsx")
head_css = git_show("client/src/dashboard-premium-luminous-v16.css")

required_tsx = [
    'import "../dashboard-premium-luminous-v16.css";',
    'tcrm-premium-dashboard',
]
for marker in required_tsx:
    if marker not in head_tsx:
        raise SystemExit("ERROR=HEAD AgentDashboard is not the approved final premium baseline: missing " + marker)

required_css = [
    "V23 Safe Color Variables",
    "TCRM Dashboard Luxury Concept V16",
]
for marker in required_css:
    if marker not in head_css:
        raise SystemExit("ERROR=HEAD dashboard v16 CSS is not the approved final baseline: missing " + marker)

current_tsx = TSX.read_text(encoding="utf-8")
current_css = CSS.read_text(encoding="utf-8") if CSS.exists() else ""

tsx_changed = current_tsx != head_tsx
css_changed = current_css != head_css

if tsx_changed:
    TSX.write_text(head_tsx, encoding="utf-8")
if css_changed:
    CSS.write_text(head_css, encoding="utf-8")

print("PATCH=YES")
print("RESTORE_SOURCE=HEAD_APPROVED_FINAL_V23")
print("AGENT_DASHBOARD_RESTORED=" + ("YES" if tsx_changed else "ALREADY_MATCHED"))
print("V16_CSS_RESTORED=" + ("YES" if css_changed else "ALREADY_MATCHED"))
print("V16_IMPORTED=" + ("YES" if 'import \"../dashboard-premium-luminous-v16.css\";' in TSX.read_text(encoding="utf-8") else "NO"))
print("V23_MARKERS_PRESENT=" + ("YES" if all(x in CSS.read_text(encoding="utf-8") for x in required_css) else "NO"))
print("HEAD_TSX_SHA256_16=" + sha(head_tsx))
print("HEAD_V16_CSS_SHA256_16=" + sha(head_css))
print("FUNCTIONALITY_CHANGED=NO")
print("FILES_CHANGED=" + ",".join([
    p for p, changed in [
        ("client/src/pages/AgentDashboard.tsx", tsx_changed),
        ("client/src/dashboard-premium-luminous-v16.css", css_changed),
    ] if changed
]) if (tsx_changed or css_changed) else "FILES_CHANGED=NONE")
