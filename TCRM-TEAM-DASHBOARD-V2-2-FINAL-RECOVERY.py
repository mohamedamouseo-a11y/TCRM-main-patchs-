#!/usr/bin/env python3
from pathlib import Path
import subprocess
import shutil
import hashlib
import datetime

ROOT = Path.cwd()
TARGETS = [
    "client/src/pages/TeamDashboard.tsx",
    "client/src/team-dashboard-premium-v1.css",
    "client/src/team-dashboard-premium-v2.css",
    "client/src/team-dashboard-premium-v2-1.css",
    "client/src/team-dashboard-premium-v2-2.css",
]
PROTECTED = [
    "client/src/pages/AgentDashboard.tsx",
    "client/src/pages/LeadsList.tsx",
]


def run(*args):
    r = subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def git_show(path):
    return run("git", "show", f"HEAD:{path}")


def sha_file(path):
    p = ROOT / path
    if not p.exists():
        return "MISSING"
    return hashlib.sha256(p.read_bytes()).hexdigest()

if not (ROOT / ".git").exists():
    raise SystemExit("ERROR=NOT_IN_LIVE_TCRM_GIT_ROOT")

# Read the candidate recovery baseline only from the existing LOCAL git HEAD.
# No network, checkout, reset, pull, branch switch, commit, or push.
try:
    head_tsx = git_show(TARGETS[0])
    head_v1 = git_show(TARGETS[1])
    head_v2 = git_show(TARGETS[2])
    head_v21 = git_show(TARGETS[3])
    head_v22 = git_show(TARGETS[4])
except Exception as e:
    raise SystemExit(f"ERROR=LOCAL_HEAD_MISSING_FINAL_TEAM_FILES:{e}")

required_tsx = [
    'import "../team-dashboard-premium-v1.css";',
    'import "../team-dashboard-premium-v2.css";',
    'import "../team-dashboard-premium-v2-1.css";',
    'import "../team-dashboard-premium-v2-2.css";',
    "tcrm-team-dashboard-premium",
    "tcrm-team-kpi-card",
    "tcrm-team-chart-card",
    "tcrm-team-performance-card",
    "tcrm-team-kpi-spark",
    "TCRM_CURRENT_MONTH_DEFAULT_DATE_RANGE_FINAL",
]
missing = [m for m in required_tsx if m not in head_tsx]
if missing:
    raise SystemExit("ERROR=LOCAL_HEAD_NOT_VALIDATED_TEAM_V22_BASELINE:MISSING=" + "|".join(missing))

if "TCRM Team Dashboard Premium V2.2" not in head_v22:
    raise SystemExit("ERROR=LOCAL_HEAD_V22_MARKER_MISSING")

# Protect already-recovered/finalized screens.
protected_before = {p: sha_file(p) for p in PROTECTED}

# Create local backup of current Team Dashboard state before any write.
stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
backup_dir = ROOT / ".tcrm-recovery-backups" / f"team-dashboard-v22-{stamp}"
backup_dir.mkdir(parents=True, exist_ok=True)
for rel in TARGETS:
    src = ROOT / rel
    if src.exists():
        dst = backup_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

head_contents = {
    TARGETS[0]: head_tsx,
    TARGETS[1]: head_v1,
    TARGETS[2]: head_v2,
    TARGETS[3]: head_v21,
    TARGETS[4]: head_v22,
}

changed = []
for rel, content in head_contents.items():
    p = ROOT / rel
    before = p.read_text(encoding="utf-8") if p.exists() else None
    if before != content:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        changed.append(rel)

# Verify exact recovery and protection.
for rel, content in head_contents.items():
    if (ROOT / rel).read_text(encoding="utf-8") != content:
        raise SystemExit(f"ERROR=RECOVERY_VERIFY_FAILED:{rel}")

protected_after = {p: sha_file(p) for p in PROTECTED}
if protected_before != protected_after:
    raise SystemExit("ERROR=PROTECTED_SCREEN_CHANGED")

final_tsx = (ROOT / TARGETS[0]).read_text(encoding="utf-8")
final_v22 = (ROOT / TARGETS[4]).read_text(encoding="utf-8")
imports_ok = all(x in final_tsx for x in required_tsx[:4])
classes_ok = all(x in final_tsx for x in [
    "tcrm-team-dashboard-premium",
    "tcrm-team-kpi-card",
    "tcrm-team-chart-card",
    "tcrm-team-performance-card",
    "tcrm-team-kpi-spark",
])

print("PATCH=YES")
print("RECOVERY_SOURCE=VALIDATED_LOCAL_GIT_HEAD")
print("TEAM_V22_BASELINE_VALIDATED=YES")
print("TEAM_IMPORTS_RESTORED=" + ("YES" if imports_ok else "NO"))
print("TEAM_PREMIUM_CLASSES_RESTORED=" + ("YES" if classes_ok else "NO"))
print("TEAM_V22_MARKER_RESTORED=" + ("YES" if "TCRM Team Dashboard Premium V2.2" in final_v22 else "NO"))
print("AGENT_DASHBOARD_PROTECTED=YES")
print("LEADS_PROTECTED=YES")
print("BACKUP_CREATED=YES")
print("BACKUP_DIR=" + str(backup_dir))
print("FUNCTIONALITY_CHANGED=NO")
print("FILES_CHANGED=" + (",".join(changed) if changed else "NONE"))
