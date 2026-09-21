#!/usr/bin/env python3
# FELFEL-AUTH-INCOGNITO-RUNTIME-FIX-V11
# Root cause:
# capture-bridge merges getAuthenticatedBrowserArgs() with getJoinBrowserArgs(),
# and JOIN_BROWSER_ARGS contains --incognito. Chromium incognito ignores the
# restored persistent Google session, so validation succeeds in isolation but
# the real Meet bot lands in the guest lobby and throws auth_session_missing.
#
# Fix source for future builds and add a tiny derived-image Dockerfile so the
# live published bot image can be patched without a full 3.6GB Vexa rebuild.

from pathlib import Path

ROOT = Path("/var/www/TCRM-MAIN/ai-staff/felfel")

src = ROOT / "core/meetings/services/bot/src/capture-bridge.ts"
if not src.exists():
    raise SystemExit("PATCH_FAIL=CAPTURE_BRIDGE_SOURCE_MISSING")

s = src.read_text(encoding="utf-8")
old = '''  const args = [...getAuthenticatedBrowserArgs(), ...getJoinBrowserArgs()];'''
new = '''  // Authenticated persistent profiles must never launch with --incognito:
  // incognito hides the restored Google cookies and makes Meet render the guest lobby.
  const joinArgs = getJoinBrowserArgs().filter((arg) => !inv.authenticated || arg !== "--incognito");
  const args = [...getAuthenticatedBrowserArgs(), ...joinArgs];'''

if new not in s:
    if old not in s:
        raise SystemExit("PATCH_FAIL=SOURCE_ANCHOR_MISSING")
    s = s.replace(old, new, 1)
    src.write_text(s, encoding="utf-8")

dockerfile = ROOT / "deploy/compose/Dockerfile.felfel-authfix-v11"
dockerfile.write_text(r'''ARG BASE_IMAGE=vexaai/vexa-bot:v012
FROM ${BASE_IMAGE}

RUN node -e 'const fs=require("fs");const p="/app/core/meetings/services/bot/dist/capture-bridge.js";let s=fs.readFileSync(p,"utf8");const old="const args = [...getAuthenticatedBrowserArgs(), ...getJoinBrowserArgs()];";const neu="const joinArgs = getJoinBrowserArgs().filter((arg) => !inv.authenticated || arg !== \"--incognito\");\\n    const args = [...getAuthenticatedBrowserArgs(), ...joinArgs];";if(!s.includes(old)){ console.error("RUNTIME_ANCHOR_MISSING"); process.exit(42); }fs.writeFileSync(p,s.replace(old,neu));'

RUN node -e 'const fs=require("fs");const s=fs.readFileSync("/app/core/meetings/services/bot/dist/capture-bridge.js","utf8");if(!s.includes("!inv.authenticated || arg !== \"--incognito\"")) process.exit(43);console.log("AUTH_INCOGNITO_FILTER=PASS");'
''', encoding="utf-8")

print("PATCH=PASS")
print("SOURCE_AUTH_INCOGNITO_FILTER=FIXED")
print("DERIVED_DOCKERFILE=deploy/compose/Dockerfile.felfel-authfix-v11")
print("FULL_VEXA_BUILD_REQUIRED=NO")
