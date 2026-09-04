#!/usr/bin/env python3
from pathlib import Path
import shutil, sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
cat = root / "server/security/permissionCatalog.ts"
trpc = root / "server/_core/trpc.ts"
verifier_src = Path(__file__).with_name("verify-advanced-permissions-phase3b-tara.ts")
verifier_dst = root / "scripts/verify-advanced-permissions-phase3b-tara.ts"

for p in (cat, trpc):
    if not p.exists():
        raise SystemExit(f"missing required file: {p}")

for p in (cat, trpc):
    bak = p.with_suffix(p.suffix + ".pre-tara-v1.bak")
    if not bak.exists(): shutil.copy2(p, bak)

text = cat.read_text()
keys = '  "tara.view", "tara.operate", "tara.moderate", "tara.manage",\n'
if '"tara.view"' not in text:
    anchor = '  "messenger.view", "messenger.send", "messenger.manage",\n'
    if anchor not in text:
        raise SystemExit("permission catalog anchor not found")
    text = text.replace(anchor, anchor + keys, 1)
    cat.write_text(text)

text = trpc.read_text()
block = '''\n// ADVANCED_PERMISSIONS_PHASE3B_TARA_V1\nexport const taraViewScope = phase3Scope("tara.view");\nexport const taraOperateScope = phase3Scope("tara.operate");\nexport const taraModerateScope = phase3Scope("tara.moderate");\nexport const taraManageScope = phase3Scope("tara.manage");\n'''
if 'ADVANCED_PERMISSIONS_PHASE3B_TARA_V1' not in text:
    anchor = 'export const messengerManageScope = phase3Scope("messenger.manage");\n'
    if anchor not in text:
        raise SystemExit("trpc messenger scope anchor not found")
    text = text.replace(anchor, anchor + block, 1)
    trpc.write_text(text)

if verifier_src.exists():
    shutil.copy2(verifier_src, verifier_dst)
else:
    raise SystemExit(f"missing verifier beside patch: {verifier_src}")

print("Tara V1 deterministic patch applied. Next: inventory and wire only server/routers.ts Tara routes.")
