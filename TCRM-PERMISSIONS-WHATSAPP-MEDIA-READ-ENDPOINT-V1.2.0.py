#!/usr/bin/env python3
from pathlib import Path
import subprocess

ROOT = Path('/var/www/TCRM-MAIN')
BASELINE = '3a5434a4049c8c5582bfdded91504905f599999a'
VERSION = 'V1.2.0'
WORKFLOW_ID = 'TCRM-PERMISSIONS-WHATSAPP-MEDIA-READ-ENDPOINT-V1.2.0'


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


def git(*args: str) -> str:
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


head = git('rev-parse', 'HEAD')
if head != BASELINE:
    raise SystemExit(f'BASELINE_MISMATCH=expected:{BASELINE}:actual:{head}')

if git('diff', '--name-only'):
    raise SystemExit('WORKTREE_NOT_CLEAN=tracked_diff_present')

print(f'VERSION={VERSION}')
print(f'WORKFLOW_ID={WORKFLOW_ID}')
print(f'BASELINE={BASELINE}')

# The V1.1.0 media-send phase already introduced the shared permission engine import.
rel = 'server/_core/index.ts'
data = read(rel)
if 'import { evaluatePermission } from "../security/permissionEngine";' not in data:
    raise SystemExit('ANCHOR_ERROR=permission_engine_import_missing')

route_start_marker = '  app.get("/api/wa-gateway/media/:messageId", async (req: any, res: any) => {'
route_end_marker = '\n\n  app.post("/api/wa-gateway/webhook"'
route_start = data.find(route_start_marker)
if route_start < 0:
    raise SystemExit('ANCHOR_ERROR=media_read_route_missing')
route_end = data.find(route_end_marker, route_start)
if route_end < 0:
    raise SystemExit('ANCHOR_ERROR=media_read_route_end_missing')

route = data[route_start:route_end]
marker = '// TCRM_PERMISSIONS_WHATSAPP_MEDIA_READ_ENDPOINT_V1_2_0'
old = '''      const user = await authenticateRequest(req);\n      if (!user) return res.status(401).json({ success: false, error: "Authentication required" });\n      if (isDeveloperRole(user.role)) {\n'''
new = '''      const user = await authenticateRequest(req);\n      if (!user) return res.status(401).json({ success: false, error: "Authentication required" });\n      // TCRM_PERMISSIONS_WHATSAPP_MEDIA_READ_ENDPOINT_V1_2_0\n      // Raw Express media reads bypass tRPC protectedProcedure, so enforce whatsapp.view\n      // before message lookup or Drive streaming. Existing Developer privacy and actor scope\n      // checks remain additive and unchanged.\n      const mediaViewPermission = await evaluatePermission(user, "whatsapp.view", req);\n      if (!mediaViewPermission.allowed) {\n        return res.status(403).json({ success: false, error: "Permission denied: whatsapp.view" });\n      }\n      if (isDeveloperRole(user.role)) {\n'''

if marker not in route:
    count = route.count(old)
    if count != 1:
        raise SystemExit(f'ANCHOR_ERROR=media_read_permission_gate:expected=1:actual={count}')
    route = route.replace(old, new, 1)
    data = data[:route_start] + route + data[route_end:]

write(rel, data)

# Focused regression test for raw HTTP media-read permission wiring.
test_rel = 'server/security/waGatewayMediaReadHttpPermission.test.ts'
test_content = '''import { describe, expect, it } from "vitest";\nimport { readFileSync } from "node:fs";\nimport { fileURLToPath } from "node:url";\nimport path from "node:path";\n\nconst here = path.dirname(fileURLToPath(import.meta.url));\nconst indexSource = readFileSync(path.resolve(here, "../_core/index.ts"), "utf8");\n\ndescribe("WhatsApp raw media read HTTP permission gate V1.2.0", () => {\n  it("requires whatsapp.view before media lookup or Drive streaming", () => {\n    const routeStart = indexSource.indexOf('app.get("/api/wa-gateway/media/:messageId"');\n    const routeEnd = indexSource.indexOf('app.post("/api/wa-gateway/webhook"', routeStart);\n    expect(routeStart).toBeGreaterThanOrEqual(0);\n    expect(routeEnd).toBeGreaterThan(routeStart);\n\n    const routeSource = indexSource.slice(routeStart, routeEnd);\n    const authAt = routeSource.indexOf("await authenticateRequest(req)");\n    const permissionAt = routeSource.indexOf('await evaluatePermission(user, "whatsapp.view", req)');\n    const lookupAt = routeSource.indexOf("await getWAGatewayMessageMedia({");\n    const streamAt = routeSource.indexOf("await prepareWAGatewayDriveMedia({");\n\n    expect(authAt).toBeGreaterThanOrEqual(0);\n    expect(permissionAt).toBeGreaterThan(authAt);\n    expect(lookupAt).toBeGreaterThan(permissionAt);\n    expect(streamAt).toBeGreaterThan(lookupAt);\n    expect(routeSource).toContain('res.status(403).json({ success: false, error: "Permission denied: whatsapp.view" })');\n  });\n\n  it("preserves Developer privacy and actor-scoped media authorization", () => {\n    const routeStart = indexSource.indexOf('app.get("/api/wa-gateway/media/:messageId"');\n    const routeEnd = indexSource.indexOf('app.post("/api/wa-gateway/webhook"', routeStart);\n    const routeSource = indexSource.slice(routeStart, routeEnd);\n\n    expect(routeSource).toContain("if (isDeveloperRole(user.role))");\n    expect(routeSource).toContain("WhatsApp customer media is hidden in Developer mode");\n    expect(routeSource).toContain("await getWAGatewayMessageMedia({ messageId: Number(req.params.messageId || 0), actor: user })");\n  });\n});\n'''

test_path = ROOT / test_rel
if test_path.exists() and test_path.read_text(encoding='utf-8') != test_content:
    raise SystemExit(f'UNEXPECTED_EXISTING_FILE={test_rel}')
write(test_rel, test_content)

# Fail-closed postchecks.
index_after = read('server/_core/index.ts')
read_start = index_after.find(route_start_marker)
read_end = index_after.find(route_end_marker, read_start)
if read_start < 0 or read_end < 0:
    raise SystemExit('POSTCHECK_FAILED=media_read_route_bounds')
read_route = index_after[read_start:read_end]
required = [
    '// TCRM_PERMISSIONS_WHATSAPP_MEDIA_READ_ENDPOINT_V1_2_0',
    'await evaluatePermission(user, "whatsapp.view", req)',
    'Permission denied: whatsapp.view',
    'if (isDeveloperRole(user.role))',
    'await getWAGatewayMessageMedia({ messageId: Number(req.params.messageId || 0), actor: user })',
    'await prepareWAGatewayDriveMedia({',
]
missing = [item for item in required if item not in read_route]
if missing:
    raise SystemExit(f'POSTCHECK_FAILED=media_read_route:{missing}')

if read_route.count('await evaluatePermission(user, "whatsapp.view", req)') != 1:
    raise SystemExit('POSTCHECK_FAILED=whatsapp_view_permission_gate_count')

expected_dirty = {
    'server/_core/index.ts',
    'server/security/waGatewayMediaReadHttpPermission.test.ts',
}
dirty = set(filter(None, git('diff', '--name-only').splitlines()))
unexpected = sorted(dirty - expected_dirty)
missing_dirty = sorted(expected_dirty - dirty)
if unexpected or missing_dirty:
    raise SystemExit(f'POSTCHECK_DIRTY_MISMATCH=unexpected:{unexpected}:missing:{missing_dirty}')

print('PATCH_APPLIED=YES')
print('MODULES=whatsapp_media_read_http')
print('WHATSAPP_MEDIA_VIEW_PERMISSION=whatsapp.view')
print('EXISTING_MEDIA_ACTOR_SCOPE_PRESERVED=YES')
print('DEVELOPER_MEDIA_PRIVACY_PRESERVED=YES')
print('FILES_CHANGED=' + ','.join(sorted(expected_dirty)))
print('READY_FOR_TESTS=YES')
