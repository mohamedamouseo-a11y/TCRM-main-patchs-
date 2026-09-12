#!/usr/bin/env python3
from pathlib import Path
import shutil, time, sys

ROOT = Path.cwd()
TSX = ROOT / "client/src/pages/LeadProfile.tsx"
CSS = ROOT / "client/src/lead-profile-premium-v1.css"
BACKUP_DIR = ROOT / ".tcrm-recovery-backups"
MARKER = "TCRM_LEAD_PROFILE_PREMIUM_V1_TEAM_DASHBOARD_COMMAND_CENTER"

if not TSX.exists():
    raise SystemExit("ERROR: client/src/pages/LeadProfile.tsx not found. Run from the live TCRM project root.")

src = TSX.read_text(encoding="utf-8")
required = [
    "TCRM_SALES_REVENUE_PAYMENT_WON_ALIGNMENT_FINAL_REVIEWED",
    "export default function LeadProfile()",
    '<div className="min-h-screen p-4 md:p-6" dir={isRTL ? "rtl" : "ltr"}>',
    '<div className="lead-profile-grid grid gap-4">',
]
for token in required:
    if token not in src:
        raise SystemExit(f"ERROR: required LeadProfile anchor missing: {token}")

if MARKER in src and CSS.exists():
    print("PATCH=ALREADY_APPLIED")
    print("LEAD_PROFILE_PREMIUM_V1=YES")
    sys.exit(0)

BACKUP_DIR.mkdir(exist_ok=True)
stamp = time.strftime("%Y%m%d-%H%M%S")
backup = BACKUP_DIR / f"LeadProfile.tsx.{stamp}.lead-profile-v1.bak"
shutil.copy2(TSX, backup)

# 1) Dedicated CSS import and marker. No business logic changes.
import_anchor = 'import { InnoCallHistoryDialog } from "@/components/InnoCallHistoryDialog";'
if 'import "../lead-profile-premium-v1.css";' not in src:
    if import_anchor not in src:
        raise SystemExit("ERROR: import anchor missing")
    src = src.replace(import_anchor, import_anchor + '\nimport "../lead-profile-premium-v1.css";', 1)

marker_anchor = "// TCRM_INNOCALL_CALL_BUTTON_VISIBILITY_V1R2"
if MARKER not in src:
    src = src.replace(marker_anchor, marker_anchor + f"\n// {MARKER}", 1)

# 2) Scope the whole page so this patch cannot bleed into other screens.
root_old = '<div className="min-h-screen p-4 md:p-6" dir={isRTL ? "rtl" : "ltr"}>'
root_new = '<div className="tcrm-lead-profile-premium-v1 min-h-screen p-4 md:p-6" dir={isRTL ? "rtl" : "ltr"}>'
src = src.replace(root_old, root_new, 1)

# 3) Add safe visual hooks only. Do not alter handlers, queries, permissions, routes, data or forms.
visual_replacements = [
    (
        '<div className="sticky top-0 z-30 rounded-2xl border border-border/70 bg-background/90 shadow-sm backdrop-blur supports-[backdrop-filter]:bg-background/75">',
        '<div className="tcrm-lp-hero sticky top-0 z-30 rounded-2xl border border-border/70 bg-background/90 shadow-sm backdrop-blur supports-[backdrop-filter]:bg-background/75">'
    ),
    (
        '<div className="min-w-[220px] rounded-2xl border border-border/60 bg-muted/20 p-3">',
        '<div className="tcrm-lp-sla min-w-[220px] rounded-2xl border border-border/60 bg-muted/20 p-3">'
    ),
    (
        '<div className="rounded-2xl overflow-hidden shadow-sm mb-4" style={{background:"linear-gradient(135deg,#0f2040 0%,#1e3a5f 60%,#244875 100%)"}}>',
        '<div className="tcrm-lp-tabs rounded-2xl overflow-hidden shadow-sm mb-4" style={{background:"linear-gradient(135deg,#0f2040 0%,#1e3a5f 60%,#244875 100%)"}}>'
    ),
    (
        '<div className="space-y-3 lg:sticky lg:top-28 lg:self-start lg:max-h-[calc(100vh-8rem)] lg:overflow-y-auto lg:scrollbar-thin overflow-hidden">',
        '<div className="tcrm-lp-rail space-y-3 lg:sticky lg:top-28 lg:self-start lg:max-h-[calc(100vh-8rem)] lg:overflow-y-auto lg:scrollbar-thin overflow-hidden">'
    ),
]
for old, new in visual_replacements:
    if old not in src:
        raise SystemExit(f"ERROR: visual anchor missing: {old[:90]}")
    src = src.replace(old, new, 1)

# Section headers are repeated intentionally; add a common visual hook to all of them.
section_old = '<div className="relative px-4 py-3 overflow-hidden" style={{background:"linear-gradient(135deg,#1e3a5f 0%,#2d5a9e 100%)"}}>'
section_new = '<div className="tcrm-lp-section-head relative px-4 py-3 overflow-hidden" style={{background:"linear-gradient(135deg,#1e3a5f 0%,#2d5a9e 100%)"}}>'
section_count = src.count(section_old)
if section_count < 2:
    raise SystemExit(f"ERROR: expected repeated premium section headers, found {section_count}")
src = src.replace(section_old, section_new)

TSX.write_text(src, encoding="utf-8")

css = r'''/*
TCRM Lead Profile Premium V1
PRIMARY UX/UI REFERENCE: Team Dashboard Sales
- Light: pearl / soft-lilac depth, executive hierarchy, restrained luminous accents
- Dark: deep navy layered surfaces, electric blue / indigo / violet edges
- Scope: .tcrm-lead-profile-premium-v1 only
- No business logic, route, permission, query, mutation or data changes
*/

.tcrm-lead-profile-premium-v1 {
  --lp-ink: #14213d;
  --lp-muted: #73809a;
  --lp-line: rgba(117, 129, 190, .18);
  --lp-blue: #4f67ff;
  --lp-violet: #7457ff;
  --lp-cyan: #47b7ff;
  --lp-pearl: #f8f9ff;
  --lp-card: rgba(255,255,255,.82);
  --lp-card-strong: rgba(255,255,255,.94);
  --lp-shadow: 0 18px 54px rgba(73, 84, 165, .10), 0 2px 12px rgba(40, 54, 122, .05);
  position: relative;
  background:
    radial-gradient(circle at 12% 2%, rgba(111, 126, 255, .14), transparent 27%),
    radial-gradient(circle at 78% 0%, rgba(73, 181, 255, .11), transparent 30%),
    linear-gradient(180deg, #fafbff 0%, #f5f7ff 48%, #f8f9ff 100%);
  color: var(--lp-ink);
}

.tcrm-lead-profile-premium-v1::before {
  content: "";
  pointer-events: none;
  position: absolute;
  inset: 0;
  opacity: .34;
  background-image: radial-gradient(circle, rgba(99,102,241,.16) 1px, transparent 1px);
  background-size: 26px 26px;
  -webkit-mask-image: linear-gradient(to bottom, #000, transparent 52%);
  mask-image: linear-gradient(to bottom, #000, transparent 52%);
}

.tcrm-lead-profile-premium-v1 > .mx-auto { position: relative; z-index: 1; }

/* Breadcrumb: quieter executive navigation */
.tcrm-lead-profile-premium-v1 nav[aria-label="breadcrumb"],
.tcrm-lead-profile-premium-v1 [data-slot="breadcrumb"] {
  opacity: .82;
  margin-bottom: 2px;
}

/* ===== Command Center Hero ===== */
.tcrm-lead-profile-premium-v1 .tcrm-lp-hero {
  position: relative;
  overflow: hidden;
  border-radius: 26px !important;
  border: 1px solid rgba(120, 126, 225, .22) !important;
  background:
    radial-gradient(circle at 88% 6%, rgba(110, 110, 255, .20), transparent 27%),
    radial-gradient(circle at 11% 90%, rgba(86, 186, 255, .14), transparent 30%),
    linear-gradient(125deg, rgba(255,255,255,.98), rgba(246,248,255,.96) 52%, rgba(241,244,255,.94)) !important;
  box-shadow: 0 24px 72px rgba(77, 83, 173, .13), inset 0 1px 0 rgba(255,255,255,.95) !important;
  backdrop-filter: blur(20px) saturate(135%);
  top: 10px !important;
}

.tcrm-lead-profile-premium-v1 .tcrm-lp-hero::after {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  opacity: .65;
  background:
    linear-gradient(110deg, transparent 0 58%, rgba(102,92,255,.07) 58% 59%, transparent 59% 100%),
    radial-gradient(circle at 86% 24%, rgba(255,255,255,.92) 0 1px, transparent 1.5px);
  background-size: auto, 22px 22px;
}

.tcrm-lead-profile-premium-v1 .tcrm-lp-hero > .h-1 {
  height: 3px !important;
  background: linear-gradient(90deg, #44c9ff, #4f67ff 38%, #7a55ff 72%, #b36cff) !important;
  box-shadow: 0 0 18px rgba(92, 91, 255, .55);
}

.tcrm-lead-profile-premium-v1 .tcrm-lp-hero > .p-3,
.tcrm-lead-profile-premium-v1 .tcrm-lp-hero > .md\:p-4 { position: relative; z-index: 1; }

.tcrm-lead-profile-premium-v1 .tcrm-lp-hero h1,
.tcrm-lead-profile-premium-v1 .tcrm-lp-hero h2 {
  letter-spacing: -.025em;
  color: #14213d;
}

.tcrm-lead-profile-premium-v1 .tcrm-lp-hero button {
  min-height: 38px;
  border-radius: 12px;
  border-color: rgba(94, 108, 197, .19);
  background: rgba(255,255,255,.76);
  box-shadow: 0 5px 16px rgba(73, 86, 160, .06);
  transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
}
.tcrm-lead-profile-premium-v1 .tcrm-lp-hero button:hover {
  transform: translateY(-1px);
  border-color: rgba(86, 92, 255, .34);
  box-shadow: 0 10px 24px rgba(76, 85, 190, .12);
}

/* score / SLA become executive signal tiles */
.tcrm-lead-profile-premium-v1 .tcrm-lp-sla,
.tcrm-lead-profile-premium-v1 .tcrm-lp-hero .rounded-full:has(svg) {
  border-color: rgba(104, 116, 209, .17) !important;
}
.tcrm-lead-profile-premium-v1 .tcrm-lp-sla {
  min-width: 250px !important;
  border-radius: 18px !important;
  background: linear-gradient(145deg, rgba(255,255,255,.82), rgba(245,248,255,.88)) !important;
  box-shadow: 0 12px 28px rgba(70, 83, 165, .08), inset 0 1px 0 #fff;
}

/* ===== Premium navigation strip ===== */
.tcrm-lead-profile-premium-v1 .tcrm-lp-tabs {
  border: 1px solid rgba(89, 103, 199, .22);
  border-radius: 18px !important;
  background:
    radial-gradient(circle at 8% -40%, rgba(104, 111, 255, .28), transparent 40%),
    linear-gradient(115deg, #14294d 0%, #183968 58%, #244d82 100%) !important;
  box-shadow: 0 16px 36px rgba(20, 44, 94, .18), inset 0 1px 0 rgba(255,255,255,.08) !important;
}
.tcrm-lead-profile-premium-v1 .tcrm-lp-tabs button {
  min-height: 34px;
  border-radius: 10px !important;
  color: rgba(235,243,255,.72);
  border: 1px solid transparent;
  transition: .18s ease;
}
.tcrm-lead-profile-premium-v1 .tcrm-lp-tabs button:hover {
  color: #fff;
  background: rgba(255,255,255,.08);
}
.tcrm-lead-profile-premium-v1 .tcrm-lp-tabs button.bg-orange-500,
.tcrm-lead-profile-premium-v1 .tcrm-lp-tabs button[class*="bg-orange"] {
  background: linear-gradient(135deg,#6556ff,#4f72ff) !important;
  color: #fff !important;
  border-color: rgba(255,255,255,.20) !important;
  box-shadow: 0 7px 18px rgba(83,89,255,.28);
}

/* ===== Core command-center layout ===== */
.tcrm-lead-profile-premium-v1 .lead-profile-grid {
  grid-template-columns: minmax(0, 1fr) 330px !important;
  align-items: start;
  gap: 18px !important;
}
[dir="rtl"] .tcrm-lead-profile-premium-v1 .lead-profile-grid {
  grid-template-columns: 330px minmax(0, 1fr) !important;
}

.tcrm-lead-profile-premium-v1 [data-slot="card"],
.tcrm-lead-profile-premium-v1 .tcrm-lp-rail > div,
.tcrm-lead-profile-premium-v1 .tcrm-lp-rail > [data-slot="card"] {
  border: 1px solid rgba(113, 124, 198, .16) !important;
  background: linear-gradient(145deg, rgba(255,255,255,.90), rgba(249,250,255,.82)) !important;
  box-shadow: var(--lp-shadow) !important;
}

.tcrm-lead-profile-premium-v1 [data-slot="card"] {
  border-radius: 20px !important;
}

.tcrm-lead-profile-premium-v1 [data-slot="card"]:hover {
  border-color: rgba(99, 102, 241, .24) !important;
}

/* Existing section titles, upgraded to Team Dashboard identity */
.tcrm-lead-profile-premium-v1 .tcrm-lp-section-head {
  padding: 14px 18px !important;
  background:
    radial-gradient(circle at 80% 0%, rgba(126,92,255,.30), transparent 34%),
    linear-gradient(115deg,#17325d 0%,#24528c 58%,#3c68b6 100%) !important;
  border-bottom: 1px solid rgba(255,255,255,.10);
}
.tcrm-lead-profile-premium-v1 .tcrm-lp-section-head::after {
  content: "";
  position: absolute;
  inset: auto 0 0;
  height: 1px;
  background: linear-gradient(90deg,transparent,rgba(110,142,255,.9),rgba(131,92,255,.7),transparent);
}

/* Information density: remove the huge empty feeling */
.tcrm-lead-profile-premium-v1 [data-slot="card-content"] {
  padding-top: 18px;
  padding-bottom: 20px;
}
.tcrm-lead-profile-premium-v1 [data-slot="card-content"] .grid {
  row-gap: 12px;
}

/* Buttons / fields stay functional, but become executive controls */
.tcrm-lead-profile-premium-v1 button:not(.tcrm-lp-tabs button),
.tcrm-lead-profile-premium-v1 input,
.tcrm-lead-profile-premium-v1 textarea,
.tcrm-lead-profile-premium-v1 [role="combobox"] {
  border-radius: 12px;
}
.tcrm-lead-profile-premium-v1 input,
.tcrm-lead-profile-premium-v1 textarea,
.tcrm-lead-profile-premium-v1 [role="combobox"] {
  border-color: rgba(112,125,194,.22);
  background: rgba(255,255,255,.74);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.95);
}
.tcrm-lead-profile-premium-v1 input:focus,
.tcrm-lead-profile-premium-v1 textarea:focus,
.tcrm-lead-profile-premium-v1 [role="combobox"]:focus {
  border-color: rgba(79,103,255,.64) !important;
  box-shadow: 0 0 0 3px rgba(79,103,255,.10) !important;
}

/* Rail: deal / ownership / smart notes feels integrated instead of detached */
.tcrm-lead-profile-premium-v1 .tcrm-lp-rail {
  padding-right: 2px;
  scrollbar-width: thin;
  scrollbar-color: rgba(102,111,255,.35) transparent;
}
.tcrm-lead-profile-premium-v1 .tcrm-lp-rail [data-slot="card"] {
  border-radius: 18px !important;
  box-shadow: 0 14px 34px rgba(59,72,150,.08) !important;
}
.tcrm-lead-profile-premium-v1 .tcrm-lp-rail [data-slot="card-title"] {
  color: #273657;
  letter-spacing: .04em;
}

/* semantic badges retain their business colors but get a better material */
.tcrm-lead-profile-premium-v1 [data-slot="badge"] {
  border-radius: 999px;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.55);
}

/* ===== DARK — Team Dashboard deep navy luminous system ===== */
.dark .tcrm-lead-profile-premium-v1 {
  --lp-ink: #eef4ff;
  --lp-muted: #8fa3c7;
  --lp-card: rgba(11, 29, 55, .88);
  --lp-card-strong: rgba(12, 31, 59, .96);
  --lp-shadow: 0 20px 58px rgba(0, 8, 28, .34), inset 0 1px 0 rgba(142,173,255,.05);
  background:
    radial-gradient(circle at 12% 0%, rgba(58,101,255,.18), transparent 30%),
    radial-gradient(circle at 84% 4%, rgba(116,76,255,.20), transparent 32%),
    linear-gradient(180deg,#07152a 0%,#081a31 44%,#071426 100%);
  color: #eef4ff;
}
.dark .tcrm-lead-profile-premium-v1::before {
  opacity: .24;
  background-image: radial-gradient(circle, rgba(89,129,255,.24) 1px, transparent 1px);
}

.dark .tcrm-lead-profile-premium-v1 .tcrm-lp-hero {
  border-color: rgba(74,126,255,.44) !important;
  background:
    radial-gradient(circle at 84% -15%, rgba(132,79,255,.42), transparent 36%),
    radial-gradient(circle at 12% 115%, rgba(28,152,255,.27), transparent 38%),
    linear-gradient(120deg, rgba(9,31,67,.98), rgba(10,39,85,.98) 52%, rgba(27,32,92,.98)) !important;
  box-shadow: 0 24px 70px rgba(0,6,26,.45), 0 0 0 1px rgba(69,121,255,.12), inset 0 1px 0 rgba(150,183,255,.08) !important;
}
.dark .tcrm-lead-profile-premium-v1 .tcrm-lp-hero h1,
.dark .tcrm-lead-profile-premium-v1 .tcrm-lp-hero h2,
.dark .tcrm-lead-profile-premium-v1 .tcrm-lp-hero .text-foreground { color: #f6f9ff !important; }
.dark .tcrm-lead-profile-premium-v1 .tcrm-lp-hero .text-muted-foreground { color: #9eb0d2 !important; }
.dark .tcrm-lead-profile-premium-v1 .tcrm-lp-hero button {
  background: rgba(13,37,73,.72);
  border-color: rgba(83,128,225,.30);
  color: #edf4ff;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.04), 0 8px 24px rgba(0,8,30,.18);
}
.dark .tcrm-lead-profile-premium-v1 .tcrm-lp-hero button:hover {
  border-color: rgba(91,118,255,.72);
  background: rgba(19,48,94,.88);
  box-shadow: 0 0 0 1px rgba(85,106,255,.16), 0 12px 34px rgba(42,67,182,.18);
}

.dark .tcrm-lead-profile-premium-v1 .tcrm-lp-sla {
  background: linear-gradient(145deg, rgba(12,38,73,.92), rgba(9,29,58,.90)) !important;
  border-color: rgba(78,124,220,.30) !important;
}

.dark .tcrm-lead-profile-premium-v1 .tcrm-lp-tabs {
  background:
    radial-gradient(circle at 12% -20%, rgba(71,120,255,.28), transparent 35%),
    linear-gradient(115deg,#091b37 0%,#102c56 54%,#1c2f68 100%) !important;
  border-color: rgba(68,116,221,.38);
  box-shadow: 0 18px 40px rgba(0,8,28,.34), inset 0 1px 0 rgba(255,255,255,.05) !important;
}

.dark .tcrm-lead-profile-premium-v1 [data-slot="card"],
.dark .tcrm-lead-profile-premium-v1 .tcrm-lp-rail > div,
.dark .tcrm-lead-profile-premium-v1 .tcrm-lp-rail > [data-slot="card"] {
  color: #eaf1ff;
  border-color: rgba(64,111,204,.32) !important;
  background:
    radial-gradient(circle at 100% 0%, rgba(55,79,158,.16), transparent 38%),
    linear-gradient(145deg, rgba(12,31,59,.96), rgba(8,25,49,.96)) !important;
  box-shadow: var(--lp-shadow) !important;
}
.dark .tcrm-lead-profile-premium-v1 [data-slot="card-title"],
.dark .tcrm-lead-profile-premium-v1 .tcrm-lp-rail [data-slot="card-title"] { color: #f0f5ff !important; }
.dark .tcrm-lead-profile-premium-v1 .text-muted-foreground { color: #8fa3c7 !important; }
.dark .tcrm-lead-profile-premium-v1 .border-border,
.dark .tcrm-lead-profile-premium-v1 .border-border\/40,
.dark .tcrm-lead-profile-premium-v1 .border-border\/60 { border-color: rgba(71,112,197,.28) !important; }

.dark .tcrm-lead-profile-premium-v1 input,
.dark .tcrm-lead-profile-premium-v1 textarea,
.dark .tcrm-lead-profile-premium-v1 [role="combobox"] {
  color: #edf4ff;
  border-color: rgba(72,113,199,.34);
  background: rgba(7,24,48,.74);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.025);
}
.dark .tcrm-lead-profile-premium-v1 input::placeholder,
.dark .tcrm-lead-profile-premium-v1 textarea::placeholder { color: #7185ab; }

.dark .tcrm-lead-profile-premium-v1 .tcrm-lp-section-head {
  background:
    radial-gradient(circle at 82% -15%, rgba(116,79,255,.34), transparent 38%),
    linear-gradient(115deg,#0d2850 0%,#17447d 58%,#254f98 100%) !important;
}

/* Responsive safety — preserve all real controls and content */
@media (max-width: 1180px) {
  .tcrm-lead-profile-premium-v1 .lead-profile-grid,
  [dir="rtl"] .tcrm-lead-profile-premium-v1 .lead-profile-grid {
    grid-template-columns: minmax(0,1fr) 300px !important;
  }
}
@media (max-width: 980px) {
  .tcrm-lead-profile-premium-v1 .lead-profile-grid,
  [dir="rtl"] .tcrm-lead-profile-premium-v1 .lead-profile-grid {
    grid-template-columns: 1fr !important;
  }
  .tcrm-lead-profile-premium-v1 .tcrm-lp-rail {
    position: static !important;
    max-height: none !important;
    overflow: visible !important;
  }
}
@media (max-width: 640px) {
  .tcrm-lead-profile-premium-v1 { padding: 12px !important; }
  .tcrm-lead-profile-premium-v1 .tcrm-lp-hero { border-radius: 20px !important; }
  .tcrm-lead-profile-premium-v1 .tcrm-lp-sla { min-width: 100% !important; }
  .tcrm-lead-profile-premium-v1 .tcrm-lp-tabs { border-radius: 15px !important; }
}
'''

CSS.write_text(css, encoding="utf-8")

# Final invariant checks: only visual additions to LeadProfile + dedicated CSS.
final = TSX.read_text(encoding="utf-8")
checks = {
    "marker": MARKER in final,
    "css_import": 'import "../lead-profile-premium-v1.css";' in final,
    "scope": "tcrm-lead-profile-premium-v1" in final,
    "hero_hook": "tcrm-lp-hero" in final,
    "tabs_hook": "tcrm-lp-tabs" in final,
    "rail_hook": "tcrm-lp-rail" in final,
    "section_hook": "tcrm-lp-section-head" in final,
    "css_exists": CSS.exists(),
}
if not all(checks.values()):
    raise SystemExit("ERROR: post-patch verification failed: " + repr(checks))

print("PATCH=YES")
print("LEAD_PROFILE_PREMIUM_V1=YES")
print("TEAM_DASHBOARD_PRIMARY_REFERENCE=YES")
print("EXECUTIVE_COMMAND_CENTER=YES")
print("LIGHT_PEARL_SYSTEM=YES")
print("DARK_DEEP_NAVY_LUMINOUS_SYSTEM=YES")
print("HERO_UPGRADED=YES")
print("NAVIGATION_STRIP_UPGRADED=YES")
print("INFORMATION_CARDS_UPGRADED=YES")
print("DEAL_TEAM_SMART_NOTES_RAIL_INTEGRATED=YES")
print("FORM_LOGIC_UNCHANGED=YES")
print("BACKEND_UNCHANGED=YES")
print("PERMISSIONS_UNCHANGED=YES")
print("FILES_CHANGED=client/src/pages/LeadProfile.tsx,client/src/lead-profile-premium-v1.css")
print(f"BACKUP={backup}")
