#!/usr/bin/env python3
from pathlib import Path
import subprocess
import shutil
import hashlib
import datetime

ROOT = Path.cwd()
GOOD_COMMIT = "b016f9ada07e334b47bf95a19a59e667b7351b1b"
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


def git_show(commit, path):
    return run("git", "show", f"{commit}:{path}")


def sha_file(rel):
    p = ROOT / rel
    if not p.exists():
        return "MISSING"
    return hashlib.sha256(p.read_bytes()).hexdigest()

if not (ROOT / ".git").exists():
    raise SystemExit("ERROR=NOT_IN_LIVE_TCRM_GIT_ROOT")

# Validate historical commit is already available locally. No network, fetch, checkout or reset.
try:
    run("git", "cat-file", "-e", f"{GOOD_COMMIT}^{{commit}}")
except Exception as e:
    raise SystemExit(f"ERROR=LAST_GOOD_COMMIT_NOT_LOCAL:{e}")

historical = {}
for rel in TARGETS:
    try:
        historical[rel] = git_show(GOOD_COMMIT, rel)
    except Exception as e:
        raise SystemExit(f"ERROR=HISTORICAL_FILE_MISSING:{rel}:{e}")

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
]

hist_tsx = historical[TARGETS[0]]
missing = [m for m in required_tsx if m not in hist_tsx]
if missing:
    raise SystemExit("ERROR=HISTORICAL_TEAM_V22_BASELINE_INVALID:MISSING=" + "|".join(missing))

if "TCRM Team Dashboard Premium V2.2" not in historical[TARGETS[4]]:
    raise SystemExit("ERROR=HISTORICAL_V22_MARKER_MISSING")

# Protect already finalized screens.
protected_before = {rel: sha_file(rel) for rel in PROTECTED}

# Backup current Team Dashboard state.
stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
backup_dir = ROOT / ".tcrm-recovery-backups" / f"team-dashboard-v22-historical-{stamp}"
backup_dir.mkdir(parents=True, exist_ok=True)
for rel in TARGETS:
    src = ROOT / rel
    if src.exists():
        dst = backup_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

changed = []
for rel, content in historical.items():
    p = ROOT / rel
    before = p.read_text(encoding="utf-8") if p.exists() else None
    if before != content:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        changed.append(rel)

# Exact verification against the historical commit.
for rel, expected in historical.items():
    actual = (ROOT / rel).read_text(encoding="utf-8")
    if actual != expected:
        raise SystemExit(f"ERROR=EXACT_HISTORICAL_VERIFY_FAILED:{rel}")

protected_after = {rel: sha_file(rel) for rel in PROTECTED}
if protected_before != protected_after:
    raise SystemExit("ERROR=PROTECTED_SCREEN_CHANGED")

final_tsx = (ROOT / TARGETS[0]).read_text(encoding="utf-8")
final_v22 = (ROOT / TARGETS[4]).read_text(encoding="utf-8")
imports_ok = all(x in final_tsx for x in required_tsx[:4])
classes_ok = all(x in final_tsx for x in required_tsx[4:])

print("PATCH=YES")
print("RECOVERY_SOURCE=HISTORICAL_COMMIT_" + GOOD_COMMIT)
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
