#!/usr/bin/env python3
from pathlib import Path

PATCH_DIR = Path(__file__).resolve().parent
BASE = PATCH_DIR / "TCRM-AGENT-DASHBOARD-V25-ORIGINAL-CONCEPT-STRUCTURAL-FIDELITY.py"

if not BASE.exists():
    raise SystemExit(f"ERROR=BASE_V25_PATCH_MISSING:{BASE}")

source = BASE.read_text(encoding="utf-8")
needle = '    "luxury-activity-icon",\n'
count = source.count(needle)
if count != 1:
    raise SystemExit(f"ERROR=GUARD_FIX_TARGET_COUNT:{count}")

# The live audit proved this class is not a valid AgentDashboard source guard.
# It may exist only as a CSS hook in some revisions. Remove ONLY this guard item;
# do not alter V25 patch behavior, reminder logic, CSS payload, or target files.
fixed = source.replace(needle, "", 1)

print("V25_1_GUARD_FIX=YES")
print("REMOVED_INVALID_AGENT_GUARD=luxury-activity-icon")
print("BASE_PATCH=" + str(BASE))

exec(compile(fixed, str(BASE), "exec"), {"__name__": "__main__", "__file__": str(BASE)})
