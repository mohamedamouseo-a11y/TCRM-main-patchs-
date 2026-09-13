#!/usr/bin/env python3
from pathlib import Path
import shutil
import time

ROOT = Path.cwd()
LAYOUT = ROOT / "client/src/components/CRMLayout.tsx"
CSS = ROOT / "client/src/crm-sidebar-premium-v1.css"
BACKUP_DIR = ROOT / ".tcrm-recovery-backups"
MARKER = "TCRM_CRM_SIDEBAR_PREMIUM_V1_REFERENCE_MATCH"
IMPORT = 'import "../crm-sidebar-premium-v1.css";'

if not LAYOUT.exists():
    raise SystemExit("ERROR: client/src/components/CRMLayout.tsx not found. Run from the live TCRM project root.")

src = LAYOUT.read_text(encoding="utf-8")
required = [
    'const SidebarContent = () => (',
    'className="flex flex-col h-full"',
    'className="flex items-center gap-3 px-4 py-5 border-b border-sidebar-border/50"',
    'className="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto scrollbar-thin"',
    'crm-sidebar-collapse-toggle',
    'className="border-t border-sidebar-border/50 p-3"',
]
for token in required:
    if token not in src:
        raise SystemExit(f"ERROR: required CRMLayout anchor missing: {token}")

if MARKER in src and CSS.exists():
    print("PATCH=ALREADY_APPLIED")
    print("CRM_SIDEBAR_PREMIUM_V1=YES")
    raise SystemExit(0)

BACKUP_DIR.mkdir(exist_ok=True)
stamp = time.strftime("%Y%m%d-%H%M%S")
backup = BACKUP_DIR / f"CRMLayout.tsx.{stamp}.sidebar-premium-v1.bak"
shutil.copy2(LAYOUT, backup)

# Import the visual-only sidebar layer.
if IMPORT not in src:
    src = src.replace("import BDNotificationBell from './BDNotificationBell';", "import BDNotificationBell from './BDNotificationBell';\n" + IMPORT, 1)

# Marker for safe/idempotent verification.
if MARKER not in src:
    src = src.replace("interface NavItem {", f"// {MARKER}\ninterface NavItem {{", 1)

# Scoped styling hooks only. No routes, permissions, data, labels, groups or behavior changed.
src = src.replace('className="flex flex-col h-full"', 'className="crm-sidebar-content-premium flex flex-col h-full"', 1)
src = src.replace('className="flex items-center gap-3 px-4 py-5 border-b border-sidebar-border/50"', 'className="crm-sidebar-brand-premium flex items-center gap-3 px-4 py-5 border-b border-sidebar-border/50"', 1)
src = src.replace('className="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto scrollbar-thin"', 'className="crm-sidebar-nav-premium flex-1 px-2 py-3 space-y-0.5 overflow-y-auto scrollbar-thin"', 1)
src = src.replace('className="border-t border-sidebar-border/50 p-3"', 'className="crm-sidebar-user-premium border-t border-sidebar-border/50 p-3"', 1)

# All top-level navigation/group rows share one visual contract.
old_row = '"group relative flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium cursor-pointer transition-all duration-200'
new_row = '"crm-sidebar-row group relative flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium cursor-pointer transition-all duration-200'
if old_row not in src:
    raise SystemExit("ERROR: top-level sidebar row anchor missing")
src = src.replace(old_row, new_row)

# All expanded group bodies use the reference tree-line treatment.
old_submenu = 'className="mt-0.5 space-y-0.5 overflow-hidden" style={{ animation: "slideDown 0.18s ease-out" }}'
new_submenu = 'className="crm-sidebar-submenu mt-0.5 space-y-0.5 overflow-hidden" style={{ animation: "slideDown 0.18s ease-out" }}'
if old_submenu not in src:
    raise SystemExit("ERROR: submenu anchor missing")
src = src.replace(old_submenu, new_submenu)

# Expanded group items.
old_subitem = '"flex items-center gap-2.5 pl-9 pr-3 py-2 rounded-xl text-sm cursor-pointer transition-all duration-150"'
new_subitem = '"crm-sidebar-subitem flex items-center gap-2.5 pl-9 pr-3 py-2 rounded-xl text-sm cursor-pointer transition-all duration-150"'
if old_subitem not in src:
    raise SystemExit("ERROR: subitem anchor missing")
src = src.replace(old_subitem, new_subitem)

# Scope both desktop and mobile sidebars.
old_desktop = '"hidden md:flex flex-col bg-sidebar transition-all duration-300 shrink-0 relative",'
new_desktop = '"crm-sidebar-premium-v1 hidden md:flex flex-col bg-sidebar transition-all duration-300 shrink-0 relative",'
if old_desktop not in src:
    raise SystemExit("ERROR: desktop aside anchor missing")
src = src.replace(old_desktop, new_desktop, 1)

old_mobile = '"absolute top-0 h-full w-64 bg-sidebar flex flex-col shadow-2xl",'
new_mobile = '"crm-sidebar-premium-v1 crm-sidebar-mobile absolute top-0 h-full w-64 bg-sidebar flex flex-col shadow-2xl",'
if old_mobile not in src:
    raise SystemExit("ERROR: mobile aside anchor missing")
src = src.replace(old_mobile, new_mobile, 1)

LAYOUT.write_text(src, encoding="utf-8")

css = r'''/*
TCRM CRM Sidebar Premium V1 — Reference Match
VISUAL BASIS: supplied light-mode sidebar reference screenshot.
SCOPE: navigation shell only.
NO route / permission / data / backend / business-logic changes.
*/

.crm-sidebar-premium-v1{
  --sb-accent:#5965e8;
  --sb-accent-2:#7564f4;
  --sb-ink:#263654;
  --sb-muted:#71809c;
  --sb-line:rgba(96,108,184,.14);
  --sb-soft:rgba(96,99,230,.065);
  --sb-card:rgba(255,255,255,.68);
  isolation:isolate;
  overflow:visible;
  background:
    radial-gradient(circle at 14% 3%,rgba(104,113,255,.12),transparent 24%),
    radial-gradient(circle at 82% 100%,rgba(130,99,255,.08),transparent 30%),
    linear-gradient(180deg,#fbfcff 0%,#f8f8ff 54%,#f7f8ff 100%)!important;
  border-inline-end:1px solid rgba(104,112,194,.16);
  box-shadow:14px 0 42px -38px rgba(54,63,137,.55),inset -1px 0 0 rgba(255,255,255,.72);
}
.crm-sidebar-premium-v1::before{
  content:"";
  position:absolute;
  inset:0;
  z-index:-1;
  pointer-events:none;
  opacity:.34;
  background-image:radial-gradient(circle,rgba(99,102,241,.18) .7px,transparent .8px);
  background-size:22px 22px;
  mask-image:linear-gradient(to bottom,#000,transparent 32%);
}

/* Brand / logo block */
.crm-sidebar-premium-v1 .crm-sidebar-brand-premium{
  min-height:74px;
  padding:14px 14px 12px!important;
  gap:10px!important;
  position:relative;
  background:linear-gradient(180deg,rgba(255,255,255,.58),rgba(255,255,255,.18));
  border-bottom:1px solid var(--sb-line)!important;
}
.crm-sidebar-premium-v1 .crm-sidebar-brand-premium img{
  max-width:36px;
  max-height:36px;
  object-fit:contain;
  filter:drop-shadow(0 5px 10px rgba(70,76,154,.12));
}
.crm-sidebar-premium-v1 .crm-sidebar-brand-premium .font-bold{
  color:#3144be!important;
  font-size:13px!important;
  font-weight:850!important;
  letter-spacing:-.018em;
}
.crm-sidebar-premium-v1 .crm-sidebar-brand-premium .text-slate-500{
  color:#8290ad!important;
  font-size:9px!important;
  line-height:1.2!important;
}

/* Collapse control sits inside the header like the reference. */
.crm-sidebar-premium-v1 .crm-sidebar-collapse-toggle{
  top:14px!important;
  right:10px!important;
  left:auto!important;
  width:24px!important;
  height:24px!important;
  border:0!important;
  background:rgba(91,101,232,.08)!important;
  color:#6874d9!important;
  box-shadow:none!important;
}
[dir="rtl"] .crm-sidebar-premium-v1 .crm-sidebar-collapse-toggle{
  right:auto!important;
  left:10px!important;
}

/* Navigation rhythm */
.crm-sidebar-premium-v1 .crm-sidebar-nav-premium{
  padding:9px 10px 8px!important;
  scrollbar-width:thin;
  scrollbar-color:rgba(99,102,241,.20) transparent;
}
.crm-sidebar-premium-v1 .crm-sidebar-row{
  min-height:36px;
  margin:1px 0;
  padding:7px 9px!important;
  gap:10px!important;
  border:1px solid transparent;
  border-radius:10px!important;
  color:var(--sb-ink)!important;
  font-size:12px!important;
  font-weight:570!important;
  line-height:1.15;
  box-shadow:none!important;
}
.crm-sidebar-premium-v1 .crm-sidebar-row>span:first-of-type svg{
  width:17px;
  height:17px;
  stroke-width:1.8;
}
.crm-sidebar-premium-v1 .crm-sidebar-row:hover{
  color:#394cc4!important;
  border-color:rgba(92,101,225,.10)!important;
  background:linear-gradient(90deg,rgba(92,101,225,.075),rgba(120,105,242,.025))!important;
  transform:translateX(1px);
}
[dir="rtl"] .crm-sidebar-premium-v1 .crm-sidebar-row:hover{transform:translateX(-1px);}

/* An expanded group becomes a soft capsule, even when the current route is elsewhere. */
.crm-sidebar-premium-v1 .crm-sidebar-row:has(+ .crm-sidebar-submenu){
  color:#3448bd!important;
  font-weight:760!important;
  border-color:rgba(88,99,225,.11)!important;
  background:linear-gradient(90deg,rgba(88,99,225,.075),rgba(118,101,242,.035))!important;
}
.crm-sidebar-premium-v1 .crm-sidebar-row:has(+ .crm-sidebar-submenu) svg{color:#5965e8!important;}

/* Active primary route — luminous violet-blue capsule from the reference. */
.crm-sidebar-premium-v1 .crm-sidebar-row.text-white,
.crm-sidebar-premium-v1 a[aria-current="page"] .crm-sidebar-row{
  color:white!important;
  border-color:rgba(255,255,255,.24)!important;
  background:linear-gradient(135deg,#5364df 0%,#655fe8 58%,#7561ef 100%)!important;
  box-shadow:0 8px 18px -10px rgba(72,76,211,.78),inset 0 1px 0 rgba(255,255,255,.22)!important;
}
.crm-sidebar-premium-v1 .crm-sidebar-row.text-white svg{color:white!important;filter:drop-shadow(0 1px 2px rgba(25,31,110,.22));}

/* Badges */
.crm-sidebar-premium-v1 .crm-sidebar-row [data-slot="badge"]{
  min-width:29px;
  height:18px!important;
  padding-inline:6px!important;
  border:0!important;
  border-radius:999px!important;
  font-size:9px!important;
  font-weight:850!important;
  box-shadow:0 3px 8px rgba(217,43,74,.18)!important;
}

/* Sales / other submenus — slim tree line + dense child rows. */
.crm-sidebar-premium-v1 .crm-sidebar-submenu{
  position:relative;
  margin:2px 0 5px 21px!important;
  padding:1px 0 1px 15px!important;
  border-left:1px solid rgba(102,113,201,.20);
  overflow:visible!important;
}
.crm-sidebar-premium-v1 .crm-sidebar-subitem{
  position:relative;
  min-height:30px;
  padding:5px 8px!important;
  gap:8px!important;
  border-radius:8px!important;
  color:#586986!important;
  font-size:11px!important;
  line-height:1.15;
  box-shadow:none!important;
}
.crm-sidebar-premium-v1 .crm-sidebar-subitem::before{
  content:"";
  position:absolute;
  left:-17px;
  top:50%;
  width:6px;
  height:6px;
  transform:translateY(-50%);
  border-radius:999px;
  border:1.5px solid rgba(96,107,205,.38);
  background:#f9faff;
}
.crm-sidebar-premium-v1 .crm-sidebar-subitem:hover{
  color:#3f50c7!important;
  background:rgba(90,99,226,.055)!important;
}
.crm-sidebar-premium-v1 .crm-sidebar-subitem.font-semibold,
.crm-sidebar-premium-v1 .crm-sidebar-subitem.text-white{
  color:#3f50c7!important;
  background:linear-gradient(90deg,rgba(85,98,225,.10),rgba(124,105,242,.045))!important;
  box-shadow:inset 0 0 0 1px rgba(91,102,225,.10)!important;
}
.crm-sidebar-premium-v1 .crm-sidebar-subitem.font-semibold svg,
.crm-sidebar-premium-v1 .crm-sidebar-subitem.text-white svg{color:#5364df!important;}
.crm-sidebar-premium-v1 .crm-sidebar-subitem.font-semibold::before,
.crm-sidebar-premium-v1 .crm-sidebar-subitem.text-white::before{
  background:#5965e8;
  border-color:#5965e8;
  box-shadow:0 0 0 3px rgba(89,101,232,.09);
}
[dir="rtl"] .crm-sidebar-premium-v1 .crm-sidebar-submenu{
  margin:2px 21px 5px 0!important;
  padding:1px 15px 1px 0!important;
  border-left:0;
  border-right:1px solid rgba(102,113,201,.20);
}
[dir="rtl"] .crm-sidebar-premium-v1 .crm-sidebar-subitem::before{
  left:auto;
  right:-17px;
}

/* Bottom user card */
.crm-sidebar-premium-v1 .crm-sidebar-user-premium{
  margin:0 10px 10px;
  padding:8px!important;
  border:1px solid rgba(102,113,201,.13)!important;
  border-radius:14px;
  background:linear-gradient(145deg,rgba(255,255,255,.80),rgba(248,249,255,.64));
  box-shadow:0 10px 24px -20px rgba(63,70,150,.40),inset 0 1px 0 rgba(255,255,255,.9);
}
.crm-sidebar-premium-v1 .crm-sidebar-user-premium>.flex{
  flex-wrap:wrap;
  row-gap:7px;
}
.crm-sidebar-premium-v1 .crm-sidebar-user-premium .w-9.h-9{
  width:34px!important;
  height:34px!important;
  border-radius:999px!important;
  box-shadow:0 5px 12px rgba(78,84,200,.20)!important;
}
.crm-sidebar-premium-v1 .crm-sidebar-user-premium p:first-child{
  color:#293a5a!important;
  font-size:11px!important;
  font-weight:780!important;
}
.crm-sidebar-premium-v1 .crm-sidebar-user-premium p:last-child{
  color:#8a95ad!important;
  font-size:9px!important;
}
.crm-sidebar-premium-v1 .crm-sidebar-user-premium .crm-signout-btn{
  order:3;
  flex:0 0 100%;
  width:100%!important;
  min-height:29px!important;
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
  gap:6px!important;
  border:1px solid rgba(239,68,68,.20)!important;
  border-radius:9px!important;
  color:#dc3f52!important;
  background:rgba(255,239,242,.74)!important;
  box-shadow:none!important;
  font-size:10px!important;
}
.crm-sidebar-premium-v1 .crm-sidebar-user-premium .crm-signout-btn:hover{
  background:rgba(255,229,234,.96)!important;
  border-color:rgba(239,68,68,.30)!important;
}

/* Collapsed desktop state stays usable. */
.crm-sidebar-premium-v1.w-16 .crm-sidebar-brand-premium{padding-inline:12px!important;justify-content:center;}
.crm-sidebar-premium-v1.w-16 .crm-sidebar-nav-premium{padding-inline:7px!important;}
.crm-sidebar-premium-v1.w-16 .crm-sidebar-row{justify-content:center!important;padding-inline:7px!important;}
.crm-sidebar-premium-v1.w-16 .crm-sidebar-user-premium{margin-inline:6px;padding:6px!important;}
.crm-sidebar-premium-v1.w-16 .crm-sidebar-user-premium>.flex{justify-content:center!important;}
.crm-sidebar-premium-v1.w-16 .crm-sidebar-user-premium .crm-signout-btn{flex:0 0 34px;width:34px!important;height:32px!important;padding:0!important;}
.crm-sidebar-premium-v1.w-16 .crm-sidebar-collapse-toggle{right:-9px!important;left:auto!important;}
[dir="rtl"] .crm-sidebar-premium-v1.w-16 .crm-sidebar-collapse-toggle{left:-9px!important;right:auto!important;}

/* Dark mode counterpart — same structure, Team Dashboard navy language. */
.dark .crm-sidebar-premium-v1{
  --sb-ink:#e8efff;
  --sb-muted:#8fa0c0;
  --sb-line:rgba(111,130,220,.18);
  background:
    radial-gradient(circle at 10% 2%,rgba(65,94,255,.18),transparent 25%),
    radial-gradient(circle at 86% 100%,rgba(116,72,255,.16),transparent 28%),
    linear-gradient(180deg,#09182f 0%,#0a1b34 55%,#08172c 100%)!important;
  border-inline-end-color:rgba(98,121,222,.24);
  box-shadow:14px 0 46px -35px rgba(0,0,0,.85),inset -1px 0 0 rgba(143,164,255,.04);
}
.dark .crm-sidebar-premium-v1::before{opacity:.18;background-image:radial-gradient(circle,rgba(96,126,255,.24) .7px,transparent .8px);}
.dark .crm-sidebar-premium-v1 .crm-sidebar-brand-premium{background:linear-gradient(180deg,rgba(11,31,61,.76),rgba(10,28,53,.34));}
.dark .crm-sidebar-premium-v1 .crm-sidebar-brand-premium .font-bold{color:#dbe5ff!important;}
.dark .crm-sidebar-premium-v1 .crm-sidebar-brand-premium .text-slate-500{color:#8193b7!important;}
.dark .crm-sidebar-premium-v1 .crm-sidebar-row{color:#c5d1ea!important;}
.dark .crm-sidebar-premium-v1 .crm-sidebar-row:hover,
.dark .crm-sidebar-premium-v1 .crm-sidebar-row:has(+ .crm-sidebar-submenu){color:#eef3ff!important;background:linear-gradient(90deg,rgba(83,100,225,.16),rgba(118,91,241,.08))!important;border-color:rgba(103,121,233,.18)!important;}
.dark .crm-sidebar-premium-v1 .crm-sidebar-submenu{border-left-color:rgba(111,132,230,.24);}
.dark [dir="rtl"] .crm-sidebar-premium-v1 .crm-sidebar-submenu{border-right-color:rgba(111,132,230,.24);}
.dark .crm-sidebar-premium-v1 .crm-sidebar-subitem{color:#93a5c6!important;}
.dark .crm-sidebar-premium-v1 .crm-sidebar-subitem::before{background:#0a1b34;border-color:rgba(116,137,236,.42);}
.dark .crm-sidebar-premium-v1 .crm-sidebar-subitem:hover,
.dark .crm-sidebar-premium-v1 .crm-sidebar-subitem.font-semibold,
.dark .crm-sidebar-premium-v1 .crm-sidebar-subitem.text-white{color:#dce6ff!important;background:rgba(83,101,225,.13)!important;}
.dark .crm-sidebar-premium-v1 .crm-sidebar-user-premium{background:linear-gradient(145deg,rgba(14,35,67,.90),rgba(9,26,50,.82));border-color:rgba(109,130,228,.20)!important;box-shadow:0 12px 28px -20px rgba(0,0,0,.85),inset 0 1px 0 rgba(255,255,255,.035);}
.dark .crm-sidebar-premium-v1 .crm-sidebar-user-premium p:first-child{color:#eef3ff!important;}
.dark .crm-sidebar-premium-v1 .crm-sidebar-user-premium p:last-child{color:#8295ba!important;}
.dark .crm-sidebar-premium-v1 .crm-sidebar-user-premium .crm-signout-btn{background:rgba(109,33,55,.18)!important;border-color:rgba(244,91,117,.22)!important;color:#ff9aae!important;}

/* Mobile keeps the same premium material without changing navigation behavior. */
.crm-sidebar-mobile{width:256px!important;}

@media (max-height:760px){
  .crm-sidebar-premium-v1 .crm-sidebar-brand-premium{min-height:64px;padding-top:10px!important;padding-bottom:9px!important;}
  .crm-sidebar-premium-v1 .crm-sidebar-nav-premium{padding-top:6px!important;}
  .crm-sidebar-premium-v1 .crm-sidebar-row{min-height:33px;padding-top:6px!important;padding-bottom:6px!important;}
  .crm-sidebar-premium-v1 .crm-sidebar-subitem{min-height:27px;padding-top:4px!important;padding-bottom:4px!important;}
}
'''
CSS.write_text(css, encoding="utf-8")

print("PATCH=YES")
print("CRM_SIDEBAR_PREMIUM_V1=YES")
print("REFERENCE_MATCH_SCOPE=SIDEBAR_ONLY")
print("LIGHT_MODE_REFERENCE_MATCH=YES")
print("DARK_MODE_COUNTERPART=YES")
print("ROUTES_UNCHANGED=YES")
print("PERMISSIONS_UNCHANGED=YES")
print("BACKEND_UNCHANGED=YES")
print("BUSINESS_LOGIC_UNCHANGED=YES")
print("FILES_CHANGED=client/src/components/CRMLayout.tsx,client/src/crm-sidebar-premium-v1.css")
print(f"BACKUP={backup}")
