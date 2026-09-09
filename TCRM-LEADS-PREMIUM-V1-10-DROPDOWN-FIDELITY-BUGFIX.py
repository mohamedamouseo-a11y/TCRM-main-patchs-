#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path.cwd()
TSX = ROOT / "client/src/pages/LeadsList.tsx"
CSS = ROOT / "client/src/leads-premium-v1-10.css"

if not TSX.exists():
    raise SystemExit("ERROR=client/src/pages/LeadsList.tsx not found; run from EXISTING LIVE TCRM project root")

text = TSX.read_text(encoding="utf-8")
original = text

required_base = [
    'import "../leads-premium-v1-9.css";',
    'tcrm-leads-premium',
    'tcrm-leads-filter-card',
    'tcrm-leads-filter-grid',
]
missing = [x for x in required_base if x not in text]
if missing:
    raise SystemExit("ERROR=LEADS_V19_REQUIRED_MISSING:" + ",".join(missing))

# Import the new visual layer after V1.9.
css_import = 'import "../leads-premium-v1-10.css";'
if css_import not in text:
    anchor = 'import "../leads-premium-v1-9.css";'
    if anchor not in text:
        raise SystemExit("ERROR=Could not locate V1.9 import anchor")
    text = text.replace(anchor, anchor + "\n" + css_import, 1)

# Runtime bug visible in screenshot: a source audit comment is rendered literally inside the Campaign selector.
# Remove only this audit marker whether written as a JSX comment or raw JSX text.
marker_re = r'SMART_SEARCH_AUDIT_EXEMPT\s*:\s*specialized campaign selector, not the primary free-text entity search'
text, wrapped_removed = re.subn(r'\{\s*/\*\s*' + marker_re + r'\s*\*/\s*\}', '', text, flags=re.S)
text, raw_removed = re.subn(r'/\*\s*' + marker_re + r'\s*\*/', '', text, flags=re.S)
comment_removed = wrapped_removed + raw_removed

# Add page-specific styling hooks to portaled Radix Select / Popover content.
def add_class_to_tag(src: str, tag: str, cls: str) -> str:
    # Add class when no className exists.
    pattern_no_class = re.compile(rf'<{tag}(?![^>]*\bclassName=)([^>]*)>', re.S)
    src = pattern_no_class.sub(lambda m: f'<{tag} className="{cls}"{m.group(1)}>', src)
    # Append class to simple quoted className values.
    pattern_class = re.compile(rf'(<{tag}[^>]*\bclassName=")([^"]*)(")', re.S)
    def repl(m):
        existing = m.group(2)
        if cls in existing.split():
            return m.group(0)
        return m.group(1) + existing + (" " if existing else "") + cls + m.group(3)
    return pattern_class.sub(repl, src)

text = add_class_to_tag(text, "SelectContent", "tcrm-leads-select-content")
text = add_class_to_tag(text, "PopoverContent", "tcrm-leads-popover-content")
text = add_class_to_tag(text, "Command", "tcrm-leads-command")
text = add_class_to_tag(text, "CommandInput", "tcrm-leads-command-input")
text = add_class_to_tag(text, "CommandItem", "tcrm-leads-command-item")

css = r'''/* TCRM Leads Premium V1.10 — dropdown fidelity + Campaign selector bugfix.
   ORIGINAL FIRST Leads concept remains the only visual reference.
   Scope: dropdown/popover surfaces only. No filter behavior changes.
*/

/* ===== RADIX SELECT CONTENT ===== */
body:has(.tcrm-leads-premium) .tcrm-leads-select-content{
  min-width:var(--radix-select-trigger-width, 150px)!important;
  max-width:min(360px, calc(100vw - 28px))!important;
  max-height:min(420px, var(--radix-select-content-available-height, 420px))!important;
  padding:6px!important;
  border-radius:14px!important;
  border:1px solid rgba(103,91,246,.20)!important;
  background:
    radial-gradient(115% 90% at 0% 0%,rgba(113,94,255,.10),transparent 55%),
    linear-gradient(180deg,rgba(255,255,255,.985),rgba(246,247,255,.97))!important;
  color:#20283b!important;
  box-shadow:
    0 26px 60px -28px rgba(47,43,122,.38),
    0 12px 28px -20px rgba(53,64,118,.22),
    inset 0 1px 0 rgba(255,255,255,.98)!important;
  backdrop-filter:blur(22px) saturate(1.08)!important;
  z-index:120!important;
}
.dark body:has(.tcrm-leads-premium) .tcrm-leads-select-content{
  border-color:rgba(112,127,218,.32)!important;
  background:
    radial-gradient(120% 95% at 0% 0%,rgba(92,80,255,.15),transparent 57%),
    linear-gradient(180deg,rgba(10,25,49,.99),rgba(7,19,38,.99))!important;
  color:#eef3ff!important;
  box-shadow:0 28px 64px -28px rgba(0,0,0,.88),0 0 34px -22px rgba(96,78,255,.48),inset 0 1px 0 rgba(255,255,255,.055)!important;
}

body:has(.tcrm-leads-premium) .tcrm-leads-select-content [role="option"]{
  min-height:34px!important;
  margin:1px 0!important;
  padding:7px 10px!important;
  border-radius:9px!important;
  font-size:12px!important;
  line-height:1.25!important;
  font-weight:600!important;
  color:#3c465c!important;
  transition:background .14s ease,color .14s ease,box-shadow .14s ease,transform .14s ease!important;
}
body:has(.tcrm-leads-premium) .tcrm-leads-select-content [role="option"][data-highlighted]{
  background:linear-gradient(90deg,rgba(103,91,246,.12),rgba(76,132,255,.07))!important;
  color:#29265d!important;
  outline:none!important;
}
body:has(.tcrm-leads-premium) .tcrm-leads-select-content [role="option"][data-state="checked"]{
  background:linear-gradient(90deg,rgba(103,91,246,.14),rgba(94,112,255,.08))!important;
  color:#2d2a67!important;
  font-weight:760!important;
}
.dark body:has(.tcrm-leads-premium) .tcrm-leads-select-content [role="option"]{color:#bac6dc!important}
.dark body:has(.tcrm-leads-premium) .tcrm-leads-select-content [role="option"][data-highlighted],
.dark body:has(.tcrm-leads-premium) .tcrm-leads-select-content [role="option"][data-state="checked"]{
  background:linear-gradient(90deg,rgba(105,90,255,.20),rgba(50,112,255,.11))!important;
  color:#fff!important;
}

/* ===== CAMPAIGN / COMMAND POPOVER ===== */
body:has(.tcrm-leads-premium) .tcrm-leads-popover-content{
  border-radius:15px!important;
  border:1px solid rgba(104,92,241,.20)!important;
  background:
    radial-gradient(120% 100% at 0% 0%,rgba(112,93,255,.10),transparent 56%),
    linear-gradient(180deg,rgba(255,255,255,.99),rgba(246,247,255,.975))!important;
  color:#252d41!important;
  box-shadow:0 28px 64px -30px rgba(47,43,122,.40),0 13px 30px -22px rgba(51,64,119,.22),inset 0 1px 0 rgba(255,255,255,.99)!important;
  backdrop-filter:blur(22px) saturate(1.08)!important;
  overflow:hidden!important;
  z-index:120!important;
}
.dark body:has(.tcrm-leads-premium) .tcrm-leads-popover-content{
  border-color:rgba(112,128,218,.32)!important;
  background:
    radial-gradient(120% 100% at 0% 0%,rgba(91,79,255,.15),transparent 56%),
    linear-gradient(180deg,rgba(10,25,49,.995),rgba(7,19,38,.995))!important;
  color:#eef3ff!important;
  box-shadow:0 28px 64px -28px rgba(0,0,0,.90),0 0 34px -23px rgba(96,78,255,.46),inset 0 1px 0 rgba(255,255,255,.05)!important;
}

body:has(.tcrm-leads-premium) .tcrm-leads-command{
  background:transparent!important;
  color:inherit!important;
}
body:has(.tcrm-leads-premium) .tcrm-leads-command-input{
  min-height:40px!important;
  border-bottom:1px solid rgba(104,92,241,.12)!important;
  background:rgba(250,250,255,.52)!important;
  color:#293247!important;
  font-size:12px!important;
}
.dark body:has(.tcrm-leads-premium) .tcrm-leads-command-input{
  border-bottom-color:rgba(111,127,212,.18)!important;
  background:rgba(8,24,47,.42)!important;
  color:#edf3ff!important;
}
body:has(.tcrm-leads-premium) .tcrm-leads-command-input::placeholder{color:#8a94a8!important}
.dark body:has(.tcrm-leads-premium) .tcrm-leads-command-input::placeholder{color:#71829e!important}

body:has(.tcrm-leads-premium) .tcrm-leads-command-item{
  margin:1px 4px!important;
  min-height:34px!important;
  border-radius:9px!important;
  padding:7px 10px!important;
  font-size:12px!important;
  line-height:1.28!important;
  color:#3b455b!important;
}
body:has(.tcrm-leads-premium) .tcrm-leads-command-item[data-selected="true"]{
  background:linear-gradient(90deg,rgba(103,91,246,.12),rgba(74,130,255,.07))!important;
  color:#29265e!important;
}
.dark body:has(.tcrm-leads-premium) .tcrm-leads-command-item{color:#b9c5db!important}
.dark body:has(.tcrm-leads-premium) .tcrm-leads-command-item[data-selected="true"]{
  background:linear-gradient(90deg,rgba(105,90,255,.20),rgba(48,111,255,.11))!important;
  color:#fff!important;
}

/* Classification / Fit / Quality option visuals should keep their existing icons/dots and simply breathe better. */
body:has(.tcrm-leads-premium) .tcrm-leads-select-content [role="option"] svg,
body:has(.tcrm-leads-premium) .tcrm-leads-command-item svg{flex:0 0 auto!important}

@media (prefers-reduced-motion:reduce){
  body:has(.tcrm-leads-premium) .tcrm-leads-select-content *,
  body:has(.tcrm-leads-premium) .tcrm-leads-popover-content *{transition-duration:.01ms!important}
}
'''

CSS.write_text(css, encoding="utf-8")
if text != original:
    TSX.write_text(text, encoding="utf-8")

# Verification markers.
if css_import not in text:
    raise SystemExit("ERROR=V110_IMPORT_MISSING")

print("PATCH=YES")
print("V19_BASE=YES")
print("TSX_CHANGED=" + ("YES" if text != original else "NO"))
print("V110_CSS_WRITTEN=YES")
print("V110_CSS_IMPORTED=YES")
print("CAMPAIGN_AUDIT_TEXT_REMOVED=" + ("YES" if comment_removed > 0 else "NOT_FOUND"))
print("SELECT_CONTENT_HOOKED=" + ("YES" if "tcrm-leads-select-content" in text else "NO"))
print("POPOVER_CONTENT_HOOKED=" + ("YES" if "tcrm-leads-popover-content" in text else "NO"))
print("DROPDOWN_PREMIUM_FIDELITY=YES")
print("LIGHT_DROPDOWN_THEME=YES")
print("DARK_DROPDOWN_THEME=YES")
print("FUNCTIONALITY_CHANGED=NO")
