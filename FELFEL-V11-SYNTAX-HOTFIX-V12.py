#!/usr/bin/env python3
# FELFEL-V11-SYNTAX-HOTFIX-V12
# Fix only the malformed literal "\\n" inserted by V11 into runtime capture-bridge.js.
# Source logic is already correct; this creates a tiny derived image from V11.

from pathlib import Path

ROOT = Path("/var/www/TCRM-MAIN/ai-staff/felfel")
compose = ROOT / "deploy/compose"
compose.mkdir(parents=True, exist_ok=True)

fixjs = compose / "felfel-authfix-v12.js"
fixjs.write_text(r'''const fs = require("fs");

const p = "/app/core/meetings/services/bot/dist/capture-bridge.js";
let s = fs.readFileSync(p, "utf8");

const broken =
  'const joinArgs = getJoinBrowserArgs().filter((arg) => !inv.authenticated || arg !== "--incognito");\\n    const args = [...getAuthenticatedBrowserArgs(), ...joinArgs];';

const fixed =
  'const joinArgs = getJoinBrowserArgs().filter((arg) => !inv.authenticated || arg !== "--incognito");\n    const args = [...getAuthenticatedBrowserArgs(), ...joinArgs];';

if (s.includes(broken)) {
  s = s.replace(broken, fixed);
} else if (!s.includes(fixed)) {
  console.error("V12_RUNTIME_ANCHOR_MISSING");
  process.exit(42);
}

fs.writeFileSync(p, s);

if (!s.includes('!inv.authenticated || arg !== "--incognito"')) {
  console.error("V12_FILTER_MISSING");
  process.exit(43);
}

console.log("V12_RUNTIME_FIX=PASS");
''', encoding="utf-8")

dockerfile = compose / "Dockerfile.felfel-authfix-v12"
dockerfile.write_text(r'''ARG BASE_IMAGE=vexaai/vexa-bot:tcrm-authfix-v11
FROM ${BASE_IMAGE}

COPY deploy/compose/felfel-authfix-v12.js /tmp/felfel-authfix-v12.js
RUN node /tmp/felfel-authfix-v12.js \
 && node --check /app/core/meetings/services/bot/dist/capture-bridge.js \
 && rm -f /tmp/felfel-authfix-v12.js
''', encoding="utf-8")

print("PATCH=PASS")
print("V11_SYNTAX_HOTFIX=READY")
print("FULL_VEXA_BUILD_REQUIRED=NO")
