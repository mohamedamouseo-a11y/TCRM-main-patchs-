#!/usr/bin/env python3
# TCRM_SALES_MODULE_PREMIUM_V2_3_SCREENS_REFERENCE_MATCH
# Scope: Sales Funnel + Tasks/SLA + Calendar only.
# Leaves Team Dashboard, Leads, backend, routes, permissions and business logic untouched.

from pathlib import Path
from datetime import datetime
import re
import shutil
import sys

ROOT = Path.cwd()
FILES = {
    "sales": ROOT / "client/src/pages/SalesFunnelDashboard.tsx",
    "sla": ROOT / "client/src/pages/TaskSlaDashboard.tsx",
    "calendar": ROOT / "client/src/pages/CalendarPage.tsx",
}
CSS_PATH = ROOT / "client/src/sales-module-premium-v2-three-screen.css"
MARKER = "TCRM_SALES_MODULE_PREMIUM_V2_3_SCREENS_REFERENCE_MATCH"
IMPORT_LINE = 'import "../sales-module-premium-v2-three-screen.css";'

missing = [str(p) for p in FILES.values() if not p.exists()]
if missing:
    print("PATCH=NO")
    print("ERROR=MISSING_REQUIRED_FILES:" + ",".join(missing))
    sys.exit(1)

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup_dir = ROOT / f".patch-backups/sales-module-premium-v2-{stamp}"
backup_dir.mkdir(parents=True, exist_ok=True)

for path in [*FILES.values(), CSS_PATH]:
    if path.exists():
        dest = backup_dir / path.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)


def ensure_marker(text: str) -> str:
    if MARKER in text:
        return text
    lines = text.splitlines()
    insert_at = 0
    while insert_at < len(lines) and (lines[insert_at].startswith("//") or not lines[insert_at].strip()):
        insert_at += 1
    lines.insert(insert_at, f"// {MARKER}")
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def ensure_import_before(text: str, anchor: str) -> str:
    if IMPORT_LINE in text:
        return text
    idx = text.find(anchor)
    if idx < 0:
        raise RuntimeError(f"Import anchor not found: {anchor}")
    return text[:idx] + IMPORT_LINE + "\n\n" + text[idx:]


def add_main_root_classes(text: str, classes: list[str]) -> str:
    # Always patch the LAST CRMLayout block so auth/loading guard layouts are not touched.
    idx = text.rfind("<CRMLayout>")
    if idx < 0:
        raise RuntimeError("Main CRMLayout block not found")
    tail = text[idx:]
    pattern = re.compile(r'(<div\s+className=")([^"]+)("\s+dir=)')
    m = pattern.search(tail)
    if not m:
        raise RuntimeError("Main page root div with dir= not found")
    current = m.group(2).split()
    for cls in reversed(classes):
        if cls not in current:
            current.insert(0, cls)
    replacement = m.group(1) + " ".join(current) + m.group(3)
    tail = tail[:m.start()] + replacement + tail[m.end():]
    return text[:idx] + tail


configs = {
    "sales": ("const FUNNEL_COLORS", ["tcrm-sales-premium-v2", "tcrm-sales-funnel-premium-v2"]),
    "sla": ("const COLORS", ["tcrm-sales-premium-v2", "tcrm-sla-premium-v2"]),
    "calendar": ("interface EventForm", ["tcrm-sales-premium-v2", "tcrm-calendar-premium-v2"]),
}

changed = []
for key, path in FILES.items():
    original = path.read_text(encoding="utf-8")
    anchor, classes = configs[key]
    updated = ensure_marker(original)
    updated = ensure_import_before(updated, anchor)
    updated = add_main_root_classes(updated, classes)
    if updated != original:
        path.write_text(updated, encoding="utf-8")
        changed.append(str(path.relative_to(ROOT)))

CSS = r'''/* TCRM_SALES_MODULE_PREMIUM_V2_3_SCREENS_REFERENCE_MATCH
   Runtime-screen-inspired premium system for:
   1) Sales Funnel
   2) Tasks & SLA
   3) Calendar
   No global navigation/backend/logic changes. */

.tcrm-sales-premium-v2 {
  --sp-violet: #5f5cf1;
  --sp-violet-2: #7c67f5;
  --sp-indigo: #4654d8;
  --sp-blue: #3b82f6;
  --sp-cyan: #13b7cf;
  --sp-green: #16b97a;
  --sp-amber: #f59e0b;
  --sp-red: #ef5362;
  --sp-ink: #17233f;
  --sp-muted: #70809c;
  --sp-border: rgba(98, 111, 180, .16);
  --sp-panel: rgba(255, 255, 255, .92);
  --sp-panel-soft: rgba(250, 251, 255, .92);
  --sp-shadow: 0 18px 45px -34px rgba(47, 58, 133, .42), 0 2px 8px rgba(45, 56, 113, .055);
  position: relative;
  min-height: 100%;
  background:
    radial-gradient(circle at 8% 0%, rgba(105, 112, 255, .105), transparent 25%),
    radial-gradient(circle at 94% 8%, rgba(89, 189, 255, .08), transparent 22%),
    linear-gradient(180deg, #f8f9ff 0%, #f4f6fd 42%, #f8f9fc 100%);
}

.tcrm-sales-premium-v2::before {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  opacity: .35;
  background-image: radial-gradient(circle, rgba(82, 93, 165, .12) .7px, transparent .8px);
  background-size: 20px 20px;
  mask-image: linear-gradient(to bottom, #000 0, transparent 360px);
}

.tcrm-sales-premium-v2 > * { position: relative; z-index: 1; }

.tcrm-sales-premium-v2 [data-slot="card"] {
  border: 1px solid var(--sp-border) !important;
  border-radius: 16px !important;
  background: linear-gradient(180deg, rgba(255,255,255,.97), rgba(251,252,255,.94)) !important;
  box-shadow: var(--sp-shadow) !important;
  overflow: hidden;
  gap: 0 !important;
  padding-block: 0 !important;
}

.tcrm-sales-premium-v2 [data-slot="card-header"] {
  min-height: 52px;
  padding: 17px 18px 10px !important;
  border-bottom: 1px solid rgba(103, 113, 175, .09);
  background: linear-gradient(180deg, rgba(248,249,255,.86), rgba(255,255,255,0));
}

.tcrm-sales-premium-v2 [data-slot="card-title"] {
  color: var(--sp-ink);
  letter-spacing: -.01em;
}

.tcrm-sales-premium-v2 [data-slot="card-content"] {
  padding: 14px 18px 18px !important;
}

.tcrm-sales-premium-v2 table {
  border-collapse: separate;
  border-spacing: 0;
}

.tcrm-sales-premium-v2 table thead tr {
  background: linear-gradient(180deg, #f7f8fd 0%, #f3f5fb 100%) !important;
}

.tcrm-sales-premium-v2 table thead th {
  color: #6e7894 !important;
  font-size: 11px !important;
  font-weight: 700 !important;
  letter-spacing: .015em;
  border-bottom-color: rgba(101,113,175,.13) !important;
}

.tcrm-sales-premium-v2 table tbody tr {
  transition: background-color .18s ease, box-shadow .18s ease;
}

.tcrm-sales-premium-v2 table tbody tr:hover {
  background: rgba(93, 92, 241, .045) !important;
}

.tcrm-sales-premium-v2 table tbody td {
  border-bottom-color: rgba(105,116,170,.09) !important;
}

/* Shared premium PageBanner for Sales Funnel + SLA */
.tcrm-sales-funnel-premium-v2 > .relative.overflow-hidden.rounded-2xl,
.tcrm-sla-premium-v2 > .relative.overflow-hidden.rounded-2xl {
  border: 1px solid rgba(255,255,255,.38) !important;
  border-radius: 18px !important;
  padding: 18px 20px !important;
  background:
    radial-gradient(circle at 84% 0%, rgba(255,255,255,.24), transparent 25%),
    radial-gradient(circle at 54% 120%, rgba(149,129,255,.38), transparent 34%),
    linear-gradient(112deg, #6665da 0%, #7570e3 48%, #6559d7 100%) !important;
  box-shadow: 0 18px 38px -27px rgba(63,57,167,.7), inset 0 1px 0 rgba(255,255,255,.18) !important;
}

.tcrm-sales-funnel-premium-v2 > .relative.overflow-hidden.rounded-2xl::after,
.tcrm-sla-premium-v2 > .relative.overflow-hidden.rounded-2xl::after {
  content: "";
  position: absolute;
  width: 360px;
  height: 190px;
  inset-inline-end: -90px;
  top: -72px;
  border: 1px solid rgba(255,255,255,.12);
  border-radius: 50%;
  transform: rotate(-12deg);
  pointer-events: none;
}

/* KPI systems */
.tcrm-sales-funnel-premium-v2 > .grid.grid-cols-2.md\:grid-cols-5,
.tcrm-sla-premium-v2 > .grid.grid-cols-2.md\:grid-cols-4 {
  gap: 12px !important;
}

.tcrm-sales-funnel-premium-v2 > .grid.grid-cols-2.md\:grid-cols-5 > [data-slot="card"],
.tcrm-sla-premium-v2 > .grid.grid-cols-2.md\:grid-cols-4 > [data-slot="card"] {
  position: relative;
  min-height: 112px;
  background: linear-gradient(155deg, rgba(255,255,255,.98), rgba(247,249,255,.94)) !important;
  transition: transform .2s ease, box-shadow .2s ease, border-color .2s ease;
}

.tcrm-sales-funnel-premium-v2 > .grid.grid-cols-2.md\:grid-cols-5 > [data-slot="card"]::before,
.tcrm-sla-premium-v2 > .grid.grid-cols-2.md\:grid-cols-4 > [data-slot="card"]::before {
  content: "";
  position: absolute;
  inset: 0 0 auto 0;
  height: 3px;
  background: linear-gradient(90deg, var(--sp-violet), #8a7af8);
}

.tcrm-sales-funnel-premium-v2 > .grid.grid-cols-2.md\:grid-cols-5 > [data-slot="card"]:nth-child(2)::before,
.tcrm-sla-premium-v2 > .grid.grid-cols-2.md\:grid-cols-4 > [data-slot="card"]:nth-child(1)::before { background: linear-gradient(90deg,#13b978,#46d59c); }
.tcrm-sales-funnel-premium-v2 > .grid.grid-cols-2.md\:grid-cols-5 > [data-slot="card"]:nth-child(3)::before { background: linear-gradient(90deg,#685be7,#6aa6ff); }
.tcrm-sales-funnel-premium-v2 > .grid.grid-cols-2.md\:grid-cols-5 > [data-slot="card"]:nth-child(4)::before { background: linear-gradient(90deg,#7163f1,#4f8af5); }
.tcrm-sales-funnel-premium-v2 > .grid.grid-cols-2.md\:grid-cols-5 > [data-slot="card"]:nth-child(5)::before,
.tcrm-sla-premium-v2 > .grid.grid-cols-2.md\:grid-cols-4 > [data-slot="card"]:nth-child(3)::before { background: linear-gradient(90deg,#f1a018,#ffbf48); }
.tcrm-sla-premium-v2 > .grid.grid-cols-2.md\:grid-cols-4 > [data-slot="card"]:nth-child(2)::before { background: linear-gradient(90deg,#ed5362,#ff7e86); }
.tcrm-sla-premium-v2 > .grid.grid-cols-2.md\:grid-cols-4 > [data-slot="card"]:nth-child(4)::before { background: linear-gradient(90deg,#4b67e8,#60a0ff); }

.tcrm-sales-funnel-premium-v2 > .grid.grid-cols-2.md\:grid-cols-5 > [data-slot="card"]:hover,
.tcrm-sla-premium-v2 > .grid.grid-cols-2.md\:grid-cols-4 > [data-slot="card"]:hover {
  transform: translateY(-2px);
  border-color: rgba(92,92,225,.22) !important;
  box-shadow: 0 18px 35px -27px rgba(62,68,165,.55), 0 4px 12px rgba(54,62,134,.07) !important;
}

.tcrm-sales-funnel-premium-v2 > .grid.grid-cols-2.md\:grid-cols-5 [data-slot="card-content"],
.tcrm-sla-premium-v2 > .grid.grid-cols-2.md\:grid-cols-4 [data-slot="card-content"] {
  padding: 16px !important;
}

.tcrm-sales-premium-v2 .kpi-icon {
  border-radius: 10px !important;
  box-shadow: 0 8px 18px -10px currentColor, inset 0 1px 0 rgba(255,255,255,.28) !important;
}

/* Sales Funnel page */
.tcrm-sales-funnel-premium-v2 .chart-container {
  min-height: 0;
}

.tcrm-sales-funnel-premium-v2 .chart-container:hover {
  border-color: rgba(93,92,225,.20) !important;
}

.tcrm-sales-funnel-premium-v2 .recharts-cartesian-grid line {
  stroke: rgba(105,116,170,.12) !important;
}

.tcrm-sales-funnel-premium-v2 .recharts-text {
  fill: #7d879e;
}

.tcrm-sales-funnel-premium-v2 [data-slot="card"] .bg-muted\/30,
.tcrm-sales-funnel-premium-v2 [data-slot="card"] .bg-muted\/20 {
  border: 1px solid rgba(104,113,174,.10);
  background: linear-gradient(180deg, rgba(247,249,253,.95), rgba(250,251,255,.75)) !important;
}

.tcrm-sales-funnel-premium-v2 [data-slot="card"] .rounded-lg.border.border-border.bg-muted\/20 {
  border-radius: 12px !important;
}

.tcrm-sales-funnel-premium-v2 > [data-slot="card"]:has(table) {
  overflow: hidden;
}

.tcrm-sales-funnel-premium-v2 > [data-slot="card"]:last-child [data-slot="card-content"] > .flex.flex-wrap > div {
  min-width: 142px;
  border-radius: 12px !important;
  border-color: rgba(101,111,175,.13) !important;
  background: linear-gradient(180deg,#fff,#f8f9fd) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.9);
}

/* SLA / Tasks page */
.tcrm-sla-premium-v2 select {
  border-radius: 10px !important;
  border-color: rgba(255,255,255,.30) !important;
  background-color: rgba(30,36,104,.20) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.08);
}

.tcrm-sla-premium-v2 [data-slot="card"]:has(.recharts-wrapper) {
  min-height: 350px;
}

.tcrm-sla-premium-v2 a,
.tcrm-sla-premium-v2 button {
  transition: transform .16s ease, box-shadow .16s ease, background-color .16s ease, border-color .16s ease;
}

.tcrm-sla-premium-v2 table td .rounded-full,
.tcrm-sla-premium-v2 table td [data-slot="badge"] {
  font-weight: 700;
  letter-spacing: .01em;
}

.tcrm-sla-premium-v2 .recharts-cartesian-grid line {
  stroke: rgba(105,116,170,.12) !important;
}

/* Calendar: keep the real runtime IA; upgrade hierarchy/surfaces */
.tcrm-calendar-premium-v2 {
  gap: 18px !important;
}

.tcrm-calendar-premium-v2 > .flex.items-center.justify-between.flex-wrap.gap-3 {
  position: relative;
  overflow: hidden;
  padding: 17px 18px;
  border: 1px solid rgba(255,255,255,.42);
  border-radius: 18px;
  background:
    radial-gradient(circle at 84% 10%, rgba(255,255,255,.22), transparent 26%),
    linear-gradient(112deg, #6664df 0%, #766ee9 50%, #6558dc 100%);
  box-shadow: 0 18px 40px -28px rgba(58,53,165,.72), inset 0 1px 0 rgba(255,255,255,.15);
}

.tcrm-calendar-premium-v2 > .flex.items-center.justify-between.flex-wrap.gap-3::after {
  content: "";
  position: absolute;
  width: 300px;
  height: 140px;
  inset-inline-end: -65px;
  top: -62px;
  border: 1px solid rgba(255,255,255,.13);
  border-radius: 50%;
  transform: rotate(-14deg);
  pointer-events: none;
}

.tcrm-calendar-premium-v2 > .flex.items-center.justify-between.flex-wrap.gap-3 > * {
  position: relative;
  z-index: 1;
}

.tcrm-calendar-premium-v2 > .flex.items-center.justify-between.flex-wrap.gap-3 h1,
.tcrm-calendar-premium-v2 > .flex.items-center.justify-between.flex-wrap.gap-3 p {
  color: white !important;
}

.tcrm-calendar-premium-v2 > .flex.items-center.justify-between.flex-wrap.gap-3 p { opacity: .82; }

.tcrm-calendar-premium-v2 > .grid.grid-cols-1.xl\:grid-cols-4 {
  gap: 16px !important;
}

.tcrm-calendar-premium-v2 > .grid.grid-cols-1.xl\:grid-cols-4 > div {
  border-color: rgba(99,111,177,.16) !important;
  border-radius: 17px !important;
  background: linear-gradient(180deg,rgba(255,255,255,.98),rgba(250,251,255,.94)) !important;
  box-shadow: var(--sp-shadow) !important;
}

.tcrm-calendar-premium-v2 > .grid.grid-cols-1.xl\:grid-cols-4 > .xl\:col-span-3 > .flex.items-center.justify-between {
  min-height: 58px;
  background: linear-gradient(180deg,#fafbff 0%,#f5f7fd 100%);
  border-bottom-color: rgba(100,111,175,.11) !important;
}

.tcrm-calendar-premium-v2 > .grid.grid-cols-1.xl\:grid-cols-4 > .xl\:col-span-3 > .grid.grid-cols-7.border-b {
  background: #f8f9fd;
  border-bottom-color: rgba(100,111,175,.11) !important;
}

.tcrm-calendar-premium-v2 > .grid.grid-cols-1.xl\:grid-cols-4 > .xl\:col-span-3 > .grid.grid-cols-7.divide-x.divide-y {
  border-color: rgba(100,111,175,.10) !important;
}

.tcrm-calendar-premium-v2 > .grid.grid-cols-1.xl\:grid-cols-4 > .xl\:col-span-3 > .grid.grid-cols-7.divide-x.divide-y > div {
  min-height: 96px;
  border-color: rgba(100,111,175,.09) !important;
}

.tcrm-calendar-premium-v2 > .grid.grid-cols-1.xl\:grid-cols-4 > .xl\:col-span-3 > .grid.grid-cols-7.divide-x.divide-y > div:hover {
  background: linear-gradient(145deg,rgba(239,240,255,.68),rgba(247,249,255,.84)) !important;
}

.tcrm-calendar-premium-v2 .text-\[10px\].rounded-md {
  border-radius: 7px !important;
  padding-block: 3px !important;
  box-shadow: 0 4px 10px -8px rgba(52,62,126,.35);
}

.tcrm-calendar-premium-v2 > .grid.grid-cols-1.xl\:grid-cols-4 > div:last-child > .flex.items-center.gap-2\.5 {
  background: linear-gradient(180deg,#fafbff,#f6f7fc);
  border-bottom-color: rgba(100,111,175,.11) !important;
}

.tcrm-calendar-premium-v2 > .grid.grid-cols-1.xl\:grid-cols-4 > div:last-child .p-3.space-y-2 > .flex.items-start {
  border: 1px solid transparent !important;
}

.tcrm-calendar-premium-v2 > .grid.grid-cols-1.xl\:grid-cols-4 > div:last-child .p-3.space-y-2 > .flex.items-start:hover {
  background: linear-gradient(135deg,rgba(95,92,241,.055),rgba(76,142,255,.035)) !important;
  border-color: rgba(95,92,241,.11) !important;
}

/* DARK */
.dark .tcrm-sales-premium-v2 {
  --sp-ink: #edf2ff;
  --sp-muted: #91a0bd;
  --sp-border: rgba(103,126,205,.18);
  --sp-panel: rgba(11,24,45,.96);
  --sp-panel-soft: rgba(12,26,48,.94);
  --sp-shadow: 0 22px 46px -32px rgba(0,0,0,.72), inset 0 1px 0 rgba(255,255,255,.02);
  background:
    radial-gradient(circle at 8% 0%, rgba(68,88,220,.16), transparent 28%),
    radial-gradient(circle at 90% 6%, rgba(33,119,212,.10), transparent 24%),
    linear-gradient(180deg,#071321 0%,#091827 44%,#071522 100%);
}

.dark .tcrm-sales-premium-v2::before { opacity: .10; }

.dark .tcrm-sales-premium-v2 [data-slot="card"] {
  border-color: var(--sp-border) !important;
  background: linear-gradient(180deg,rgba(12,27,49,.97),rgba(9,22,40,.96)) !important;
  box-shadow: var(--sp-shadow) !important;
}

.dark .tcrm-sales-premium-v2 [data-slot="card-header"] {
  border-bottom-color: rgba(114,134,211,.12);
  background: linear-gradient(180deg,rgba(21,38,66,.55),rgba(12,27,49,0));
}

.dark .tcrm-sales-premium-v2 [data-slot="card-title"] { color: #eef3ff; }
.dark .tcrm-sales-premium-v2 .text-muted-foreground { color: #8f9ebb !important; }

.dark .tcrm-sales-funnel-premium-v2 > .relative.overflow-hidden.rounded-2xl,
.dark .tcrm-sla-premium-v2 > .relative.overflow-hidden.rounded-2xl {
  border-color: rgba(111,128,228,.27) !important;
  background:
    radial-gradient(circle at 82% 0%, rgba(94,101,255,.19), transparent 26%),
    linear-gradient(112deg,#1d2857 0%,#252e6c 45%,#30256e 100%) !important;
  box-shadow: 0 20px 45px -30px rgba(0,0,0,.85), inset 0 1px 0 rgba(255,255,255,.08) !important;
}

.dark .tcrm-sales-funnel-premium-v2 > .grid.grid-cols-2.md\:grid-cols-5 > [data-slot="card"],
.dark .tcrm-sla-premium-v2 > .grid.grid-cols-2.md\:grid-cols-4 > [data-slot="card"] {
  background:
    radial-gradient(circle at 88% 12%,rgba(83,101,244,.09),transparent 25%),
    linear-gradient(160deg,rgba(15,31,55,.98),rgba(9,24,43,.97)) !important;
}

.dark .tcrm-sales-premium-v2 table thead tr {
  background: linear-gradient(180deg,#122740,#102238) !important;
}
.dark .tcrm-sales-premium-v2 table thead th { color: #91a2c0 !important; }
.dark .tcrm-sales-premium-v2 table tbody tr:hover { background: rgba(89,103,231,.075) !important; }
.dark .tcrm-sales-premium-v2 table tbody td { border-bottom-color: rgba(107,128,204,.10) !important; }

.dark .tcrm-sales-funnel-premium-v2 .recharts-cartesian-grid line,
.dark .tcrm-sla-premium-v2 .recharts-cartesian-grid line { stroke: rgba(123,143,213,.11) !important; }
.dark .tcrm-sales-funnel-premium-v2 .recharts-text,
.dark .tcrm-sla-premium-v2 .recharts-text { fill: #899ab8 !important; }

.dark .tcrm-sales-funnel-premium-v2 [data-slot="card"] .bg-muted\/30,
.dark .tcrm-sales-funnel-premium-v2 [data-slot="card"] .bg-muted\/20 {
  border-color: rgba(108,129,204,.12);
  background: linear-gradient(180deg,rgba(15,32,55,.92),rgba(10,25,44,.88)) !important;
}

.dark .tcrm-sales-funnel-premium-v2 > [data-slot="card"]:last-child [data-slot="card-content"] > .flex.flex-wrap > div {
  border-color: rgba(107,127,205,.15) !important;
  background: linear-gradient(180deg,#102a45,#0d2239) !important;
}

.dark .tcrm-calendar-premium-v2 > .flex.items-center.justify-between.flex-wrap.gap-3 {
  border-color: rgba(112,128,230,.26);
  background:
    radial-gradient(circle at 84% 8%,rgba(98,111,255,.20),transparent 25%),
    linear-gradient(112deg,#1c2855 0%,#252f6b 48%,#30266f 100%);
  box-shadow: 0 20px 44px -29px rgba(0,0,0,.82), inset 0 1px 0 rgba(255,255,255,.07);
}

.dark .tcrm-calendar-premium-v2 > .grid.grid-cols-1.xl\:grid-cols-4 > div {
  border-color: rgba(108,130,205,.18) !important;
  background: linear-gradient(180deg,#0d2239,#0a1b2e) !important;
  box-shadow: var(--sp-shadow) !important;
}

.dark .tcrm-calendar-premium-v2 > .grid.grid-cols-1.xl\:grid-cols-4 > .xl\:col-span-3 > .flex.items-center.justify-between,
.dark .tcrm-calendar-premium-v2 > .grid.grid-cols-1.xl\:grid-cols-4 > .xl\:col-span-3 > .grid.grid-cols-7.border-b,
.dark .tcrm-calendar-premium-v2 > .grid.grid-cols-1.xl\:grid-cols-4 > div:last-child > .flex.items-center.gap-2\.5 {
  background: linear-gradient(180deg,#102741,#0d2137) !important;
  border-color: rgba(108,130,205,.12) !important;
}

.dark .tcrm-calendar-premium-v2 .text-slate-800,
.dark .tcrm-calendar-premium-v2 .text-slate-700,
.dark .tcrm-calendar-premium-v2 .text-slate-600 { color: #dce6fb !important; }
.dark .tcrm-calendar-premium-v2 .text-slate-500,
.dark .tcrm-calendar-premium-v2 .text-slate-400 { color: #8fa0bf !important; }
.dark .tcrm-calendar-premium-v2 .text-slate-300 { color: #627593 !important; }
.dark .tcrm-calendar-premium-v2 .border-slate-100,
.dark .tcrm-calendar-premium-v2 .border-slate-200\/80 { border-color: rgba(108,130,205,.12) !important; }
.dark .tcrm-calendar-premium-v2 .bg-white { background-color: #0c2138 !important; }
.dark .tcrm-calendar-premium-v2 .bg-slate-50\/50 { background-color: rgba(7,20,35,.56) !important; }
.dark .tcrm-calendar-premium-v2 .hover\:bg-violet-50\/30:hover { background-color: rgba(92,92,241,.08) !important; }
.dark .tcrm-calendar-premium-v2 .hover\:bg-slate-50:hover { background-color: rgba(91,103,218,.08) !important; }

.dark .tcrm-calendar-premium-v2 > .grid.grid-cols-1.xl\:grid-cols-4 > .xl\:col-span-3 > .grid.grid-cols-7.divide-x.divide-y > div {
  border-color: rgba(108,130,205,.10) !important;
}

/* RTL balance */
[dir="rtl"].tcrm-sales-premium-v2 table th,
[dir="rtl"].tcrm-sales-premium-v2 table td { text-align: right; }

@media (max-width: 1024px) {
  .tcrm-sales-premium-v2 { padding: 16px !important; }
  .tcrm-calendar-premium-v2 > .grid.grid-cols-1.xl\:grid-cols-4 > .xl\:col-span-3 > .grid.grid-cols-7.divide-x.divide-y > div { min-height: 86px; }
}

@media (prefers-reduced-motion: reduce) {
  .tcrm-sales-premium-v2 *, .tcrm-sales-premium-v2 *::before, .tcrm-sales-premium-v2 *::after {
    animation-duration: .01ms !important;
    transition-duration: .01ms !important;
  }
}
'''

old_css = CSS_PATH.read_text(encoding="utf-8") if CSS_PATH.exists() else None
if old_css != CSS:
    CSS_PATH.write_text(CSS, encoding="utf-8")
    changed.append(str(CSS_PATH.relative_to(ROOT)))

# Post-patch verification
verification = {}
for key, path in FILES.items():
    text = path.read_text(encoding="utf-8")
    verification[key] = (MARKER in text and IMPORT_LINE in text and "tcrm-sales-premium-v2" in text)

print("PATCH=YES")
print("TCRM_SALES_MODULE_PREMIUM_V2=YES")
print("REFERENCE_SCREEN_INSPIRED=YES")
print("SCREENS_INCLUDED=Sales Funnel,Tasks & SLA,Calendar")
print("TEAM_DASHBOARD_CHANGED=NO")
print("LEADS_CHANGED=NO")
print("LIGHT_MODE_PREMIUM=YES")
print("DARK_MODE_PREMIUM=YES")
print("RTL_PRESERVED=YES")
print("ROUTES_UNCHANGED=YES")
print("PERMISSIONS_UNCHANGED=YES")
print("BACKEND_UNCHANGED=YES")
print("BUSINESS_LOGIC_UNCHANGED=YES")
print("SALES_FUNNEL_PATCHED=" + ("YES" if verification["sales"] else "NO"))
print("SLA_PATCHED=" + ("YES" if verification["sla"] else "NO"))
print("CALENDAR_PATCHED=" + ("YES" if verification["calendar"] else "NO"))
print("BACKUP_DIR=" + str(backup_dir))
print("FILES_CHANGED=" + ",".join(changed))
