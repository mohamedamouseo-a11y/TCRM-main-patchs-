#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import re, shutil, sys

HOSTS = {"sales.tamiyouzplaform.com", "sales.tamiyouzplatform.com"}
ROOTS = [Path("/etc/nginx/sites-enabled"), Path("/etc/nginx/conf.d"), Path("/etc/nginx/sites-available")]
stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup_root = Path("/etc/nginx/.tcrm-backups") / f"sales-upstream-ipv4-{stamp}"

server_re = re.compile(r"server\s*\{", re.M)
proxy_pat = re.compile(r"proxy_pass\s+http://localhost:3001\s*;", re.I)

def find_server_blocks(text):
    blocks = []
    for m in server_re.finditer(text):
        depth = 0
        start = m.start()
        i = text.find("{", m.start())
        if i < 0:
            continue
        j = i
        while j < len(text):
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    blocks.append((start, j + 1, text[start:j+1]))
                    break
            j += 1
    return blocks

seen = set()
files = []
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
            txt = rp.read_text(encoding="utf-8")
        except Exception:
            continue
        if any(h in txt for h in HOSTS) and "proxy_pass" in txt:
            files.append((rp, txt))

if not files:
    print("PATCH=FAIL")
    print("ERROR=NO_SALES_NGINX_CONFIG_FOUND")
    sys.exit(2)

changed = []
replaced = 0

for path, text in files:
    blocks = find_server_blocks(text)
    new = text
    offset = 0
    touched = False

    for start, end, block in blocks:
        if not any(h in block for h in HOSTS):
            continue
        if not proxy_pat.search(block):
            continue
        patched = proxy_pat.sub("proxy_pass http://127.0.0.1:3001;", block)
        count = len(proxy_pat.findall(block))
        if count:
            s = start + offset
            e = end + offset
            new = new[:s] + patched + new[e:]
            offset += len(patched) - len(block)
            replaced += count
            touched = True

    if touched and new != text:
        backup_root.mkdir(parents=True, exist_ok=True)
        backup_name = str(path).lstrip("/").replace("/", "__")
        shutil.copy2(path, backup_root / backup_name)
        path.write_text(new, encoding="utf-8")
        changed.append(str(path))

if replaced == 0:
    print("PATCH=FAIL")
    print("ERROR=NO_MATCHING_LOCALHOST_3001_PROXY_FOUND")
    sys.exit(3)

# Post-verify: sales blocks must not retain localhost:3001
bad = []
for path, _ in files:
    try:
        txt = path.read_text(encoding="utf-8")
    except Exception:
        continue
    for _, _, block in find_server_blocks(txt):
        if any(h in block for h in HOSTS) and "proxy_pass http://localhost:3001" in block:
            bad.append(str(path))

if bad:
    print("PATCH=FAIL")
    print("ERROR=VERIFY_LOCALHOST_REMAINS:" + ",".join(sorted(set(bad))))
    sys.exit(4)

print("PATCH=PASS")
print(f"PROXY_REPLACED={replaced}")
print("UPSTREAM=http://127.0.0.1:3001")
print("FILES_CHANGED=" + ",".join(changed))
print("BACKUP_DIR=" + str(backup_root))
print("ERROR=NONE")
