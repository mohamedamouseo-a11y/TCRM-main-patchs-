#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys
from datetime import datetime, timezone

PATCH_ID = "TCRM-TOS-TEAM-DIRECTORY-SUCCESS-RETURN-FIX-V1"
REL = Path("server/services/tosIntegrationService.ts")

OLD = """  if (!body) {\n    return {\n      departments: [],\n      projectMembers: [],\n      project: null,\n      excludedDepartment: \"Account Manager\",\n      generatedAt: null,\n    };\n  }\n}"""

NEW = """  if (!body) {\n    return {\n      departments: [],\n      projectMembers: [],\n      project: null,\n      excludedDepartment: \"Account Manager\",\n      generatedAt: null,\n    };\n  }\n  return {\n    departments: Array.isArray(body?.departments) ? body.departments : [],\n    projectMembers: Array.isArray(body?.projectMembers) ? body.projectMembers : [],\n    project: body?.project && typeof body.project === \"object\" ? body.project : null,\n    excludedDepartment: body?.excludedDepartment || \"Account Manager\",\n    generatedAt: body?.generatedAt || null,\n  };\n}"""

def sha(p):
    h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()

root=Path(sys.argv[1]).resolve()
target=root/REL
if not target.exists():
    raise SystemExit("[ABORT] file missing")
s=target.read_text()
if NEW in s:
    print("[OK] already fixed")
    raise SystemExit(0)
if OLD not in s:
    raise SystemExit("[ABORT] expected missing success return pattern not found")

backup=root/".patch-backups"/PATCH_ID/datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")/REL
backup.parent.mkdir(parents=True)
shutil.copy2(target, backup)
before=sha(target)
target.write_text(s.replace(OLD,NEW,1))
print("[APPLIED]", PATCH_ID)
print("[BACKUP]", backup)
print("[SHA256 BEFORE]", before)
print("[SHA256 AFTER]", sha(target))
print("[CHANGE] restored success-path return only")
