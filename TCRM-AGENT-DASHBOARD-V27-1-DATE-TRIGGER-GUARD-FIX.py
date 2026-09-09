#!/usr/bin/env python3
from pathlib import Path
import subprocess
import tempfile

ROOT = Path.cwd()
SOURCE = Path(__file__).resolve().parent / "TCRM-AGENT-DASHBOARD-V27-FINAL-PRECISION-POLISH.py"

if not SOURCE.exists():
    raise SystemExit("ERROR=V27_SOURCE_PATCH_MISSING")

text = SOURCE.read_text(encoding="utf-8")

# The live DateRangePicker version still renders button#date but does not carry
# the tcrm-date-range-trigger class. V27 must remain CSS-only, so remove only
# that invalid guard and make the trigger selectors target the stable #date id.
old_guard = 'for hook in ("tcrm-date-range-trigger", "tcrm-date-range-popover", "tcrm-date-range-calendar"):'
new_guard = 'for hook in ("tcrm-date-range-popover", "tcrm-date-range-calendar"):'
if old_guard not in text:
    raise SystemExit("ERROR=V27_GUARD_PATTERN_NOT_FOUND")
text = text.replace(old_guard, new_guard, 1)

# Replace only selectors inside the embedded V27 CSS so the live trigger is styled
# without touching DateRangePicker.tsx.
text = text.replace('#date.tcrm-date-range-trigger,\nbutton#date.tcrm-date-range-trigger {', '#date,\nbutton#date {')
text = text.replace('#date.tcrm-date-range-trigger:hover,\nbutton#date.tcrm-date-range-trigger:hover {', '#date:hover,\nbutton#date:hover {')
text = text.replace('#date.tcrm-date-range-trigger span,\n#date.tcrm-date-range-trigger svg {', '#date span,\n#date svg {')
text = text.replace('#date.tcrm-date-range-trigger > span.flex-1 {', '#date > span.flex-1 {')

# Defensive validation: old class-dependent trigger selectors must be gone.
if '#date.tcrm-date-range-trigger' in text:
    raise SystemExit("ERROR=TRIGGER_SELECTOR_REWRITE_INCOMPLETE")

with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as fh:
    fh.write(text)
    temp_path = Path(fh.name)

try:
    result = subprocess.run(["python3", str(temp_path)], cwd=str(ROOT))
    if result.returncode != 0:
        raise SystemExit(result.returncode)
finally:
    try:
        temp_path.unlink()
    except FileNotFoundError:
        pass

print("V27_1_DATE_TRIGGER_GUARD_FIX=YES")
print("INVALID_TRIGGER_GUARD_REMOVED=YES")
print("DATE_TRIGGER_SELECTOR_USES_STABLE_ID=YES")
