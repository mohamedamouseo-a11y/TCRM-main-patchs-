#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import os, re, shutil, sys

LEGACY = "sales.tamiyouzplaform.com"
CORRECT = "sales.tamiyouzplatform.com"
ROOTS = [
    Path("/etc/nginx/sites-enabled"),
    Path("/etc/nginx/conf.d"),
    Path("/etc/nginx/sites-available"),
]

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup_root = Path("/etc/nginx/.tcrm-backups") / f"sales-hostname-fix-{stamp}"
seen = set()
candidates = []

for root in ROOTS:
    if not root.exists():
        continue
    for p in root.rglob("*"):
        if not (p.is_file() or p.is_symlink()):
            continue
        try:
            rp = p.resolve()
        except Exception:
            continue
        if rp in seen or not rp.is_file():
            continue
        seen.add(rp)
        try:
            text = rp.read_text(encoding="utf-8")
        except Exception:
            continue
        if LEGACY in text:
            candidates.append((rp, text))

if not candidates:
    print("PATCH=FAIL")
    print("ERROR=LEGACY_HOSTNAME_NOT_FOUND")
    sys.exit(2)

server_name_re = re.compile(r"(server_name\s+)([^;]*?)(;)", re.I)
changed_files = []
matched_directives = 0

for path, text in candidates:
    original = text

    def repl(m):
        global matched_directives
        names = m.group(2).split()
        if LEGACY not in names:
            return m.group(0)
        matched_directives += 1
        if CORRECT not in names:
            idx = names.index(LEGACY) + 1
            names.insert(idx, CORRECT)
        return m.group(1) + " ".join(names) + m.group(3)

    updated = server_name_re.sub(repl, text)

    if updated != original:
        rel = str(path).lstrip("/").replace("/", "__")
        backup_root.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup_root / rel)
        path.write_text(updated, encoding="utf-8")
        changed_files.append(str(path))

# Verify every legacy server_name directive now contains the correct hostname.
verify_fail = []
verified = 0
for path, _ in candidates:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        continue
    for m in server_name_re.finditer(text):
        names = m.group(2).split()
        if LEGACY in names:
            if CORRECT not in names:
                verify_fail.append(str(path))
            else:
                verified += 1

if verify_fail:
    print("PATCH=FAIL")
    print("ERROR=VERIFY_FAILED:" + ",".join(sorted(set(verify_fail))))
    sys.exit(3)

print("PATCH=PASS")
print("LEGACY_HOST_PRESERVED=YES")
print("CORRECT_HOST_ADDED=YES")
print(f"DIRECTIVES_VERIFIED={verified}")
print("FILES_CHANGED=" + (",".join(changed_files) if changed_files else "NONE_ALREADY_FIXED"))
print("BACKUP_DIR=" + (str(backup_root) if changed_files else "NONE"))
print("ERROR=NONE")
