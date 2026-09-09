#!/usr/bin/env python3
from pathlib import Path
import shutil
import datetime
import hashlib

ROOT = Path.cwd()
PATCH_DIR = Path(__file__).resolve().parent
SOURCE_PATCH = PATCH_DIR / "TCRM-AGENT-DASHBOARD-V27-FINAL-PRECISION-POLISH.py"
CSS = ROOT / "client/src/dashboard-premium-luminous-v16.css"
AGENT = ROOT / "client/src/pages/AgentDashboard.tsx"
TEAM = ROOT / "client/src/pages/TeamDashboard.tsx"
LEADS = ROOT / "client/src/pages/LeadsList.tsx"
REMINDERS = ROOT / "client/src/components/ReminderCalendar.tsx"
DATE_PICKER = ROOT / "client/src/components/DateRangePicker.tsx"

V26_MARKER = "/* TCRM Dashboard V26 Premium Control Polish */"
V27_MARKER = "/* TCRM Dashboard V27 Final Precision Polish */"

for p in (SOURCE_PATCH, CSS, AGENT, TEAM, LEADS, REMINDERS, DATE_PICKER):
    if not p.exists():
        raise SystemExit(f"ERROR=TARGET_MISSING:{p}")

css_before = CSS.read_text(encoding="utf-8")
if V26_MARKER not in css_before:
    raise SystemExit("ERROR=V26_BASELINE_NOT_FOUND")

if V27_MARKER in css_before:
    print("PATCH=NO")
    print("ALREADY_APPLIED=YES")
    print("V27_2_STANDALONE_DIRECT_APPLY=YES")
    print("FILES_CHANGED=NONE")
    raise SystemExit(0)

# Protect all non-CSS source files. V27.2 is intentionally CSS-only.
protected = {
    p: hashlib.sha256(p.read_bytes()).hexdigest()
    for p in (AGENT, TEAM, LEADS, REMINDERS, DATE_PICKER)
}

# Extract ONLY the embedded V27 CSS body from the original V27 patch.
# Do not execute or rewrite the original Python patch itself.
source = SOURCE_PATCH.read_text(encoding="utf-8")
start_token = "V27 = r'''"
start = source.find(start_token)
if start < 0:
    raise SystemExit("ERROR=V27_CSS_BODY_START_NOT_FOUND")
start += len(start_token)
end = source.find("'''", start)
if end < 0:
    raise SystemExit("ERROR=V27_CSS_BODY_END_NOT_FOUND")

v27_css = source[start:end]
if V27_MARKER not in v27_css:
    raise SystemExit("ERROR=V27_MARKER_NOT_IN_EXTRACTED_CSS")

# Live DateRangePicker has stable button#date but may not carry the
# tcrm-date-range-trigger class. Rewrite ONLY the extracted CSS body.
old_selector = "#date.tcrm-date-range-trigger"
selector_count = v27_css.count(old_selector)
if selector_count == 0:
    raise SystemExit("ERROR=V27_TRIGGER_SELECTOR_NOT_FOUND_IN_CSS_BODY")

v27_css = v27_css.replace(old_selector, "#date")

# Validate the final CSS body rather than the Python source text.
if old_selector in v27_css:
    raise SystemExit("ERROR=V27_TRIGGER_SELECTOR_REWRITE_INCOMPLETE")
if "#date," not in v27_css or "#date:hover" not in v27_css or "#date span" not in v27_css:
    raise SystemExit("ERROR=V27_STABLE_ID_SELECTORS_NOT_CREATED")

stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
backup_dir = ROOT / ".tcrm-recovery-backups" / f"agent-dashboard-v27-2-{stamp}"
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(CSS, backup_dir / CSS.name)

# Append V27 exactly once on top of the already-applied V25/V26 baseline.
CSS.write_text(css_before.rstrip() + "\n" + v27_css.strip() + "\n", encoding="utf-8")

# Hard safety verification: no protected source file changed.
for p, before_hash in protected.items():
    after_hash = hashlib.sha256(p.read_bytes()).hexdigest()
    if after_hash != before_hash:
        raise SystemExit(f"ERROR=PROTECTED_FILE_CHANGED:{p}")

css_after = CSS.read_text(encoding="utf-8")
if V27_MARKER not in css_after:
    raise SystemExit("ERROR=V27_MARKER_NOT_WRITTEN")
if old_selector in css_after[css_after.rfind(V27_MARKER):]:
    raise SystemExit("ERROR=OLD_TRIGGER_SELECTOR_PRESENT_IN_V27_BLOCK")

print("PATCH=YES")
print("V27_2_STANDALONE_DIRECT_APPLY=YES")
print("ORIGINAL_V27_PYTHON_NOT_EXECUTED=YES")
print("INVALID_DATE_TRIGGER_GUARD_BYPASSED=YES")
print("DATE_TRIGGER_SELECTOR_USES_STABLE_ID=YES")
print(f"TRIGGER_SELECTORS_REWRITTEN={selector_count}")
print("CSS_ONLY=YES")
print("PROTECTED_FILES_UNCHANGED=YES")
print(f"BACKUP_DIR={backup_dir}")
print("FILES_CHANGED=client/src/dashboard-premium-luminous-v16.css")
print("ERROR=NONE")
