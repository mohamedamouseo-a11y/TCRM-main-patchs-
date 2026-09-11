#!/usr/bin/env python3
from pathlib import Path
import subprocess

ROOT = Path('/var/www/TCRM-MAIN')
BASELINE = '4d95fcde8c2d765070649f89f3dbc6dd83855fad'
VERSION = 'V1.0.0'
WORKFLOW_ID = 'TCRM-PERMISSIONS-MESSENGER-API-ENFORCEMENT-V1.0.0'


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

tracked_diff = git('diff', '--name-only')
if tracked_diff:
    raise SystemExit(f'PREEXISTING_TRACKED_DIFF={tracked_diff.replace(chr(10), ",")}')

print(f'VERSION={VERSION}')
print(f'WORKFLOW_ID={WORKFLOW_ID}')
print(f'BASELINE={BASELINE}')

rel = 'server/routes/central-chat-native.ts'
data = read(rel)

data = replace_once(
    data,
    'import { Router, type Request, type Response } from "express";\n',
    'import { Router, type NextFunction, type Request, type Response } from "express";\n',
    'express_next_function_import',
)

data = replace_once(
    data,
    'import { authenticateRequest } from "../auth";\n',
    'import { authenticateRequest } from "../auth";\nimport { evaluatePermission } from "../security/permissionEngine";\nimport type { PermissionKey } from "../security/permissionCatalog";\n',
    'messenger_permission_engine_import',
)

anchor = '''// Backward-compatible aliases and TOS-compatible chat API for cloned ChatPanel/useChat.\n'''
insert = r'''// TCRM_PERMISSIONS_MESSENGER_API_ENFORCEMENT_V1_0_0
// The Central Chat bridge is mounted as raw Express routes under /api, so it
// bypasses tRPC's protectedProcedure permission boundary. Keep the central
// service's own room/member/ownership authorization additive, and enforce the
// TCRM Messenger permission catalog before proxying any chat/file operation.
type MessengerPermissionKey = Extract<PermissionKey, "messenger.view" | "messenger.send" | "messenger.manage">;

type MessengerHttpRouteRule = {
  method: "GET" | "POST" | "PATCH" | "DELETE";
  pattern: RegExp;
};

const MESSENGER_VIEW_HTTP_ROUTES: MessengerHttpRouteRule[] = [
  { method: "GET", pattern: /^\/central-chat\/me$/ },
  { method: "GET", pattern: /^\/central-chat\/users$/ },
  { method: "GET", pattern: /^\/central-chat\/conversations$/ },
  { method: "GET", pattern: /^\/central-chat\/conversations\/[^/]+\/messages$/ },
  { method: "GET", pattern: /^\/central-chat\/users\/[^/]+\/profile-summary$/ },
  { method: "GET", pattern: /^\/chat\/conversations\/users$/ },
  { method: "GET", pattern: /^\/chat\/conversations$/ },
  { method: "GET", pattern: /^\/chat\/conversations\/[^/]+\/messages$/ },
  { method: "GET", pattern: /^\/chat\/conversations\/[^/]+\/pins$/ },
  { method: "GET", pattern: /^\/chat\/messages\/[^/]+\/thread$/ },
  { method: "GET", pattern: /^\/chat\/notifications$/ },
  { method: "GET", pattern: /^\/chat\/search$/ },
  { method: "GET", pattern: /^\/chat\/insights$/ },
  { method: "GET", pattern: /^\/chat\/decisions$/ },
  { method: "GET", pattern: /^\/files$/ },
  { method: "GET", pattern: /^\/files\/[^/]+\/download$/ },
  { method: "GET", pattern: /^\/files\/[^/]+\/preview$/ },
];

const MESSENGER_SEND_HTTP_ROUTES: MessengerHttpRouteRule[] = [
  { method: "POST", pattern: /^\/central-chat\/conversations\/direct$/ },
  { method: "POST", pattern: /^\/central-chat\/messages$/ },
  { method: "POST", pattern: /^\/central-chat\/messages\/read$/ },
  { method: "POST", pattern: /^\/chat\/conversations\/direct$/ },
  { method: "POST", pattern: /^\/chat\/conversations\/group$/ },
  { method: "POST", pattern: /^\/chat\/messages$/ },
  { method: "POST", pattern: /^\/chat\/messages\/read$/ },
  { method: "PATCH", pattern: /^\/chat\/messages\/[^/]+$/ },
  { method: "DELETE", pattern: /^\/chat\/messages\/[^/]+$/ },
  { method: "PATCH", pattern: /^\/chat\/messages\/[^/]+\/pin$/ },
  { method: "PATCH", pattern: /^\/chat\/messages\/[^/]+\/decision$/ },
  { method: "POST", pattern: /^\/chat\/messages\/[^/]+\/delivered$/ },
  { method: "POST", pattern: /^\/chat\/messages\/[^/]+\/to-task$/ },
  { method: "POST", pattern: /^\/chat\/messages\/[^/]+\/reactions$/ },
  { method: "PATCH", pattern: /^\/chat\/notifications\/read$/ },
  { method: "POST", pattern: /^\/files\/upload$/ },
  { method: "DELETE", pattern: /^\/files\/[^/]+$/ },
];

function normalizedMessengerHttpPath(value: unknown) {
  const raw = String(value || "/").split("?", 1)[0] || "/";
  return raw.replace(/^\/api(?=\/)/, "") || "/";
}

function matchesMessengerHttpRoute(rules: MessengerHttpRouteRule[], method: string, path: string) {
  return rules.some((rule) => rule.method === method && rule.pattern.test(path));
}

export function resolveMessengerHttpPermission(methodValue: unknown, pathValue: unknown): MessengerPermissionKey {
  const method = String(methodValue || "").trim().toUpperCase();
  const path = normalizedMessengerHttpPath(pathValue);

  if (matchesMessengerHttpRoute(MESSENGER_VIEW_HTTP_ROUTES, method, path)) return "messenger.view";
  if (matchesMessengerHttpRoute(MESSENGER_SEND_HTTP_ROUTES, method, path)) return "messenger.send";

  // Administrative/moderation routes and any future route that has not been
  // deliberately classified fail closed behind messenger.manage.
  return "messenger.manage";
}

async function requireMessengerPermission(req: Request, res: Response, next: NextFunction) {
  try {
    const user = await authenticateRequest(req);
    if (!user) return res.status(401).json({ message: "Unauthorized" });

    const permission = resolveMessengerHttpPermission(req.method, req.originalUrl || req.url);
    const decision = await evaluatePermission(user, permission, req);
    if (!decision.allowed) {
      return res.status(403).json({ message: `Permission denied: ${permission}` });
    }
    return next();
  } catch (error) {
    return next(error);
  }
}

// Only these Central Chat bridge prefixes are intercepted. The router itself is
// mounted at /api, so never install an unscoped router.use() that could affect
// unrelated TCRM API endpoints.
router.use("/central-chat", requireMessengerPermission);
router.use("/chat", requireMessengerPermission);
router.use("/files", requireMessengerPermission);

'''
data = replace_once(data, anchor, insert + anchor, 'messenger_http_permission_gate')
write(rel, data)

# Focused permission mapping + wiring regression.
test_rel = 'server/security/messengerHttpPermission.test.ts'
test_content = '''import { describe, expect, it } from "vitest";\nimport { readFileSync } from "node:fs";\nimport { fileURLToPath } from "node:url";\nimport path from "node:path";\nimport { resolveMessengerHttpPermission } from "../routes/central-chat-native";\n\nconst here = path.dirname(fileURLToPath(import.meta.url));\nconst source = readFileSync(path.resolve(here, "../routes/central-chat-native.ts"), "utf8");\n\ndescribe("Messenger raw HTTP permission enforcement V1.0.0", () => {\n  it("maps passive Central Chat reads to messenger.view", () => {\n    const reads = [\n      ["GET", "/api/central-chat/me"],\n      ["GET", "/api/central-chat/users"],\n      ["GET", "/api/central-chat/conversations"],\n      ["GET", "/api/central-chat/conversations/c1/messages?limit=50"],\n      ["GET", "/api/central-chat/users/tcrm%3A7/profile-summary"],\n      ["GET", "/api/chat/conversations/users"],\n      ["GET", "/api/chat/conversations"],\n      ["GET", "/api/chat/conversations/c1/messages?search=x"],\n      ["GET", "/api/chat/conversations/c1/pins"],\n      ["GET", "/api/chat/messages/m1/thread"],\n      ["GET", "/api/chat/notifications"],\n      ["GET", "/api/chat/search?q=test"],\n      ["GET", "/api/chat/insights"],\n      ["GET", "/api/chat/decisions"],\n      ["GET", "/api/files"],\n      ["GET", "/api/files/f1/download"],\n      ["GET", "/api/files/f1/preview"],\n    ];\n    for (const [method, route] of reads) {\n      expect(resolveMessengerHttpPermission(method, route), `${method} ${route}`).toBe("messenger.view");\n    }\n  });\n\n  it("maps normal operator mutations to messenger.send", () => {\n    const sends = [\n      ["POST", "/api/central-chat/conversations/direct"],\n      ["POST", "/api/central-chat/messages"],\n      ["POST", "/api/central-chat/messages/read"],\n      ["POST", "/api/chat/conversations/direct"],\n      ["POST", "/api/chat/conversations/group"],\n      ["POST", "/api/chat/messages"],\n      ["POST", "/api/chat/messages/read"],\n      ["PATCH", "/api/chat/messages/m1"],\n      ["DELETE", "/api/chat/messages/m1"],\n      ["PATCH", "/api/chat/messages/m1/pin"],\n      ["PATCH", "/api/chat/messages/m1/decision"],\n      ["POST", "/api/chat/messages/m1/delivered"],\n      ["POST", "/api/chat/messages/m1/to-task"],\n      ["POST", "/api/chat/messages/m1/reactions"],\n      ["PATCH", "/api/chat/notifications/read"],\n      ["POST", "/api/files/upload"],\n      ["DELETE", "/api/files/f1"],\n    ];\n    for (const [method, route] of sends) {\n      expect(resolveMessengerHttpPermission(method, route), `${method} ${route}`).toBe("messenger.send");\n    }\n  });\n\n  it("fails administrative, moderation, and future unknown bridge routes closed behind messenger.manage", () => {\n    expect(resolveMessengerHttpPermission("GET", "/api/chat/moderation")).toBe("messenger.manage");\n    expect(resolveMessengerHttpPermission("POST", "/api/chat/future-admin-action")).toBe("messenger.manage");\n    expect(resolveMessengerHttpPermission("DELETE", "/api/central-chat/future-config")).toBe("messenger.manage");\n  });\n\n  it("wires the permission engine before every scoped Central Chat bridge route family", () => {\n    const gateAt = source.indexOf('async function requireMessengerPermission');\n    const centralMountAt = source.indexOf('router.use("/central-chat", requireMessengerPermission);');\n    const chatMountAt = source.indexOf('router.use("/chat", requireMessengerPermission);');\n    const filesMountAt = source.indexOf('router.use("/files", requireMessengerPermission);');\n    const firstRouteAt = source.indexOf('router.get("/central-chat/me"');\n\n    expect(source).toContain('import { evaluatePermission } from "../security/permissionEngine";');\n    expect(source).toContain('await evaluatePermission(user, permission, req)');\n    expect(source).toContain('Permission denied: ${permission}');\n    expect(gateAt).toBeGreaterThanOrEqual(0);\n    expect(centralMountAt).toBeGreaterThan(gateAt);\n    expect(chatMountAt).toBeGreaterThan(centralMountAt);\n    expect(filesMountAt).toBeGreaterThan(chatMountAt);\n    expect(firstRouteAt).toBeGreaterThan(filesMountAt);\n  });\n});\n'''
path = ROOT / test_rel
if path.exists() and path.read_text(encoding='utf-8') != test_content:
    raise SystemExit(f'UNEXPECTED_EXISTING_FILE={test_rel}')
write(test_rel, test_content)

# Fail-closed postchecks.
source_after = read(rel)
required = [
    '// TCRM_PERMISSIONS_MESSENGER_API_ENFORCEMENT_V1_0_0',
    'import { evaluatePermission } from "../security/permissionEngine";',
    'return "messenger.view";',
    'return "messenger.send";',
    'return "messenger.manage";',
    'await evaluatePermission(user, permission, req)',
    'router.use("/central-chat", requireMessengerPermission);',
    'router.use("/chat", requireMessengerPermission);',
    'router.use("/files", requireMessengerPermission);',
    'router.get("/chat/moderation"',
]
missing = [marker for marker in required if marker not in source_after]
if missing:
    raise SystemExit(f'POSTCHECK_FAILED={rel}:{missing}')

expected_dirty = {
    'server/routes/central-chat-native.ts',
    'server/security/messengerHttpPermission.test.ts',
}
status_lines = git('status', '--porcelain=v1', '--untracked-files=all').splitlines()
dirty = set()
for line in status_lines:
    if not line:
        continue
    candidate = line[3:]
    if ' -> ' in candidate:
        candidate = candidate.split(' -> ', 1)[1]
    dirty.add(candidate)
unexpected = sorted(dirty - expected_dirty)
missing_dirty = sorted(expected_dirty - dirty)
if unexpected or missing_dirty:
    raise SystemExit(f'POSTCHECK_DIRTY_MISMATCH=unexpected:{unexpected}:missing:{missing_dirty}')

print('PATCH_APPLIED=YES')
print('MODULES=messenger_central_chat_http')
print('MESSENGER_VIEW_HTTP_GATE=YES')
print('MESSENGER_SEND_HTTP_GATE=YES')
print('MESSENGER_MANAGE_FAIL_CLOSED=YES')
print('EXISTING_CENTRAL_CHAT_AUTHORIZATION_PRESERVED=YES')
print('FILES_CHANGED=' + ','.join(sorted(expected_dirty)))
print('READY_FOR_TESTS=YES')
