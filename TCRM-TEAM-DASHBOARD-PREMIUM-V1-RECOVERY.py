#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path.cwd()
TSX = ROOT / "client/src/pages/TeamDashboard.tsx"
CSS = ROOT / "client/src/team-dashboard-premium-v1.css"
PATCH = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/tcrm-patches/TCRM-TEAM-DASHBOARD-PREMIUM-V1.patch")

if not TSX.exists():
    raise SystemExit("ERROR=TeamDashboard.tsx not found; run from live TCRM repo root")
if not PATCH.exists():
    raise SystemExit(f"ERROR=Patch source not found: {PATCH}")

patch_text = PATCH.read_text(encoding="utf-8")
marker = "diff --git a/client/src/team-dashboard-premium-v1.css b/client/src/team-dashboard-premium-v1.css"
pos = patch_text.find(marker)
if pos < 0:
    raise SystemExit("ERROR=CSS payload not found in V1 patch")
css_section = patch_text[pos:]
next_diff = css_section.find("\ndiff --git ", 1)
if next_diff >= 0:
    css_section = css_section[:next_diff]
lines = css_section.splitlines()
css_lines = []
in_hunk = False
for line in lines:
    if line.startswith("@@"):
        in_hunk = True
        continue
    if in_hunk and line.startswith("+") and not line.startswith("+++"):
        css_lines.append(line[1:])
if not css_lines:
    raise SystemExit("ERROR=Could not extract CSS payload from V1 patch")
css_payload = "\n".join(css_lines).rstrip() + "\n"
CSS.write_text(css_payload, encoding="utf-8")

text = TSX.read_text(encoding="utf-8")
original = text

# 1) Import premium CSS exactly once.
import_line = 'import "../team-dashboard-premium-v1.css";'
if import_line not in text:
    anchor = 'import { useCurrentMonthDateRange } from "@/hooks/useCurrentMonthDateRange";'
    if anchor in text:
        text = text.replace(anchor, anchor + "\n" + import_line, 1)
    else:
        m = re.search(r'(^import .*?;\s*$)(?![\s\S]*^import )', text, flags=re.M)
        if not m:
            raise SystemExit("ERROR=Could not locate import insertion point")
        text = text[:m.end()] + "\n" + import_line + text[m.end():]

# 2) Add root dashboard class without depending on line numbers.
if "tcrm-team-dashboard-premium" not in text:
    exact = 'className="p-6 space-y-6 fade-in"'
    if exact in text:
        text = text.replace(exact, 'className="p-6 space-y-6 fade-in tcrm-team-dashboard-premium"', 1)
    else:
        def add_root(m):
            classes = m.group(1)
            if "p-6" in classes and "space-y-6" in classes and "fade-in" in classes:
                return f'className="{classes} tcrm-team-dashboard-premium"'
            return m.group(0)
        text, n = re.subn(r'className="([^"]+)"', add_root, text, count=1)
        if n == 0 or "tcrm-team-dashboard-premium" not in text:
            raise SystemExit("ERROR=Could not add dashboard root class")

# 3) Wrap the PageBanner in the premium hero shell if needed.
if 'className="tcrm-team-hero"' not in text:
    banner_re = re.compile(
        r'(\s*\{\/\* Page Banner \*\/\}\s*\n)(\s*)(<PageBanner\b[\s\S]*?</PageBanner>)',
        re.M,
    )
    m = banner_re.search(text)
    if not m:
        raise SystemExit("ERROR=Could not locate PageBanner block")
    prefix, indent, banner = m.groups()
    wrapped = prefix + indent + '<div className="tcrm-team-hero">\n' + indent + '  ' + banner.replace('\n' + indent, '\n' + indent + '  ') + '\n' + indent + '</div>'
    text = text[:m.start()] + wrapped + text[m.end():]

# 4) Add KPI grid hook.
kpi_grid = 'grid grid-cols-2 md:grid-cols-4 gap-4 stagger-children'
if 'tcrm-team-kpi-grid' not in text:
    if kpi_grid not in text:
        raise SystemExit("ERROR=Could not locate KPI grid")
    text = text.replace(kpi_grid, kpi_grid + ' tcrm-team-kpi-grid', 1)

# 5) Add KPI card hooks.
if 'tcrm-team-kpi-card' not in text:
    old = 'className={`cursor-pointer group ${kpiGradients[i]}`}'
    new = 'className={`cursor-pointer group ${kpiGradients[i]} tcrm-team-kpi-card tcrm-team-kpi-${i}`}'
    if old in text:
        text = text.replace(old, new, 1)
    else:
        text, n = re.subn(
            r'className=\{`([^`]*\$\{kpiGradients\[i\]\}[^`]*)`\}',
            lambda m: 'className={`' + m.group(1) + ' tcrm-team-kpi-card tcrm-team-kpi-${i}`}',
            text,
            count=1,
        )
        if n == 0:
            raise SystemExit("ERROR=Could not locate KPI Card className")

# 6) Add analytics chart-grid hook.
chart_grid = 'grid grid-cols-1 lg:grid-cols-2 gap-6'
if 'tcrm-team-chart-grid' not in text:
    if chart_grid not in text:
        raise SystemExit("ERROR=Could not locate chart grid")
    text = text.replace(chart_grid, chart_grid + ' tcrm-team-chart-grid', 1)

# 7) Add Agent Performance card hook.
if 'tcrm-team-performance-card' not in text:
    old = 'className="slide-up" style={{ animationDelay: \'0.3s\' }}'
    if old in text:
        text = text.replace(old, 'className="slide-up tcrm-team-performance-card" style={{ animationDelay: \'0.3s\' }}', 1)
    else:
        text, n = re.subn(
            r'className="slide-up"(?=\s+style=\{\{\s*animationDelay:)',
            'className="slide-up tcrm-team-performance-card"',
            text,
            count=1,
        )
        if n == 0:
            raise SystemExit("ERROR=Could not locate Agent Performance card")

required = [
    import_line,
    "tcrm-team-dashboard-premium",
    "tcrm-team-hero",
    "tcrm-team-kpi-grid",
    "tcrm-team-kpi-card",
    "tcrm-team-chart-grid",
    "tcrm-team-performance-card",
]
missing = [item for item in required if item not in text]
if missing:
    raise SystemExit("ERROR=Missing required hooks after apply: " + ",".join(missing))

TSX.write_text(text, encoding="utf-8")

print("RECOVERY_APPLY=YES")
print(f"TSX_CHANGED={'YES' if text != original else 'NO'}")
print("CSS_WRITTEN=YES")
print("CSS_IMPORTED=YES")
print("PREMIUM_HOOKS=YES")
