#!/usr/bin/env python3
from pathlib import Path
import subprocess

ROOT = Path('/var/www/TCRM-MAIN')
BASELINE = '90b5af4766cf4115bca861a2a5fcb02396c7d726'
VERSION = 'V1.1.0'
WORKFLOW_ID = 'TCRM-PERMISSIONS-WHATSAPP-MEDIA-ENDPOINT-V1.1.0'


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.exists():
        raise SystemExit(f'MISSING_FILE={rel}')
    return path.read_text(encoding='utf-8')


def write(rel: str, content: str):
    path = ROOT / rel
    before = path.read_text(encoding='utf-8') if path.exists() else None
    if before == content:
        print(f'SKIP={rel}:already_current')
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    print(f'UPDATED={rel}')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'ANCHOR_ERROR={label}:expected=1:actual={count}')
    return text.replace(old, new, 1)


def git(*args: str) -> str:
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


head = git('rev-parse', 'HEAD')
if head != BASELINE:
    raise SystemExit(f'BASELINE_MISMATCH=expected:{BASELINE}:actual:{head}')

print(f'VERSION={VERSION}')
print(f'WORKFLOW_ID={WORKFLOW_ID}')
print(f'BASELINE={BASELINE}')

# 1) Raw HTTP WhatsApp media-send endpoint: require whatsapp.send before upload allocation/body handling.
rel = 'server/_core/index.ts'
data = read(rel)
data = replace_once(
    data,
    'import { configureTrustProxy } from "../services/trustProxy";\n',
    'import { configureTrustProxy } from "../services/trustProxy";\nimport { evaluatePermission } from "../security/permissionEngine";\n',
    'wa_media_permission_engine_import',
)
data = replace_once(
    data,
    '      const user = await authenticateRequest(req);\n      if (!user) return res.status(401).json({ success: false, error: "Authentication required" });\n      const userId = Number(user.id || 0);\n',
    '      const user = await authenticateRequest(req);\n      if (!user) return res.status(401).json({ success: false, error: "Authentication required" });\n      // TCRM_PERMISSIONS_WHATSAPP_MEDIA_ENDPOINT_V1_1_0\n      // This raw Express mutation bypasses the tRPC protectedProcedure permission middleware,\n      // so enforce the same whatsapp.send decision explicitly before reserving upload capacity\n      // or reading/processing the attachment body. Existing account/chat scope checks remain additive.\n      const mediaSendPermission = await evaluatePermission(user, "whatsapp.send");\n      if (!mediaSendPermission.allowed) {\n        return res.status(403).json({ success: false, error: "Permission denied: whatsapp.send" });\n      }\n      const userId = Number(user.id || 0);\n',
    'wa_media_send_permission_gate',
)
write(rel, data)

# 2) Focused regression test for the raw HTTP wiring and ordering.
test_rel = 'server/security/waGatewayMediaHttpPermission.test.ts'
test_content = '''import { describe, expect, it } from "vitest";\nimport { readFileSync } from "node:fs";\nimport { fileURLToPath } from "node:url";\nimport path from "node:path";\n\nconst here = path.dirname(fileURLToPath(import.meta.url));\nconst indexSource = readFileSync(path.resolve(here, "../_core/index.ts"), "utf8");\n\ndescribe("WhatsApp raw media HTTP permission gate V1.1.0", () => {\n  it("requires whatsapp.send before reserving upload capacity", () => {\n    expect(indexSource).toContain('import { evaluatePermission } from "../security/permissionEngine";');\n\n    const gateStart = indexSource.indexOf("const waMediaUploadGate = async");\n    const routeStart = indexSource.indexOf('app.post("/api/wa-gateway/media/send", waMediaUploadGate', gateStart);\n    expect(gateStart).toBeGreaterThanOrEqual(0);\n    expect(routeStart).toBeGreaterThan(gateStart);\n\n    const gateSource = indexSource.slice(gateStart, routeStart);\n    const authAt = gateSource.indexOf("await authenticateRequest(req)");\n    const permissionAt = gateSource.indexOf('await evaluatePermission(user, "whatsapp.send")');\n    const reserveAt = gateSource.indexOf("waMediaUploadsInFlight += 1");\n\n    expect(authAt).toBeGreaterThanOrEqual(0);\n    expect(permissionAt).toBeGreaterThan(authAt);\n    expect(reserveAt).toBeGreaterThan(permissionAt);\n    expect(gateSource).toContain('res.status(403).json({ success: false, error: "Permission denied: whatsapp.send" })');\n  });\n\n  it("preserves the existing account/chat media access check", () => {\n    const routeStart = indexSource.indexOf('app.post("/api/wa-gateway/media/send", waMediaUploadGate');\n    expect(routeStart).toBeGreaterThanOrEqual(0);\n    const routeSource = indexSource.slice(routeStart, routeStart + 5000);\n    expect(routeSource).toContain("await assertWAGatewayMediaUploadAccess({");\n    expect(routeSource).toContain("actor: user");\n  });\n});\n'''
path = ROOT / test_rel
if path.exists() and path.read_text(encoding='utf-8') != test_content:
    raise SystemExit(f'UNEXPECTED_EXISTING_FILE={test_rel}')
write(test_rel, test_content)

# Fail-closed postchecks.
index_after = read('server/_core/index.ts')
required = [
    'import { evaluatePermission } from "../security/permissionEngine";',
    '// TCRM_PERMISSIONS_WHATSAPP_MEDIA_ENDPOINT_V1_1_0',
    'await evaluatePermission(user, "whatsapp.send")',
    'Permission denied: whatsapp.send',
    'app.post("/api/wa-gateway/media/send", waMediaUploadGate',
    'await assertWAGatewayMediaUploadAccess({',
]
missing = [marker for marker in required if marker not in index_after]
if missing:
    raise SystemExit(f'POSTCHECK_FAILED=server/_core/index.ts:{missing}')

if index_after.count('await evaluatePermission(user, "whatsapp.send")') != 1:
    raise SystemExit('POSTCHECK_FAILED=whatsapp_send_permission_gate_count')

expected_dirty = {
    'server/_core/index.ts',
    'server/security/waGatewayMediaHttpPermission.test.ts',
}
dirty = set(filter(None, git('diff', '--name-only').splitlines()))
unexpected = sorted(dirty - expected_dirty)
missing_dirty = sorted(expected_dirty - dirty)
if unexpected or missing_dirty:
    raise SystemExit(f'POSTCHECK_DIRTY_MISMATCH=unexpected:{unexpected}:missing:{missing_dirty}')

print('PATCH_APPLIED=YES')
print('MODULES=whatsapp_media_http')
print('WHATSAPP_MEDIA_SEND_PERMISSION=whatsapp.send')
print('EXISTING_MEDIA_SCOPE_GUARD_PRESERVED=YES')
print('FILES_CHANGED=' + ','.join(sorted(expected_dirty)))
print('READY_FOR_TESTS=YES')
