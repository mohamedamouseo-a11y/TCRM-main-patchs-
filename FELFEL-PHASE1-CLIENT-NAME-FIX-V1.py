#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys

ROOT = Path("/var/www/TCRM-MAIN")
EXPECTED_HEAD = "b47b0b07d1dd9d0f1233caa44b9dbac0bd44a78f"
TARGET = ROOT / "server/services/felfel/felfelCrmMeetingService.ts"
MARKER = "FELFEL_PHASE1_CLIENT_NAME_FIX_V1"

def fail(msg):
    print("PATCH=FAIL")
    print("ERROR=" + msg)
    sys.exit(1)

head = subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"], text=True).strip()
if head != EXPECTED_HEAD:
    fail(f"unexpected HEAD {head}; expected {EXPECTED_HEAD}")

text = TARGET.read_text()

old = '''  } else if (input.clientId) {
    const client = (await db.select({ name: clients.name }).from(clients)
      .where(and(eq(clients.id, input.clientId), isNull(clients.deletedAt))).limit(1))[0];
    if (client?.name) contextName = client.name;
'''
new = '''  } else if (input.clientId) {
    // FELFEL_PHASE1_CLIENT_NAME_FIX_V1
    const client = (await db.select({ name: clients.leadName }).from(clients)
      .where(and(eq(clients.id, input.clientId), isNull(clients.deletedAt))).limit(1))[0];
    if (client?.name) contextName = client.name;
'''

if MARKER not in text:
    if text.count(old) != 1:
        fail(f"anchor mismatch; found {text.count(old)}")
    text = text.replace(old, new, 1)
    TARGET.write_text(text)

check = subprocess.run(["git","-C",str(ROOT),"diff","--check"], text=True, capture_output=True)
if check.returncode != 0:
    fail((check.stdout + check.stderr).strip())

print("PATCH=PASS")
print("CLIENT_COLUMN_FIX=clients.name->clients.leadName")
print("GIT_DIFF_CHECK=PASS")
print("CHANGED_FILE=server/services/felfel/felfelCrmMeetingService.ts")
print("ERROR=NONE")
