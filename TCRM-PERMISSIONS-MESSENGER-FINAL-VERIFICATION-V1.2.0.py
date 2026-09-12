#!/usr/bin/env python3
from pathlib import Path
import subprocess

ROOT = Path('/var/www/TCRM-MAIN')
BASELINE = 'b98bba55c4faf8736e72bb55271fecb22b39e9c6'
VERSION = 'V1.2.0'
WORKFLOW_ID = 'TCRM-PERMISSIONS-MESSENGER-FINAL-VERIFICATION-V1.2.0'


def git(*args: str) -> str:
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def write_new(rel: str, content: str):
    path = ROOT / rel
    if path.exists():
        existing = path.read_text(encoding='utf-8')
        if existing == content:
            print(f'SKIP={rel}:already_current')
            return
        raise SystemExit(f'UNEXPECTED_EXISTING_FILE={rel}')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    print(f'CREATED={rel}')


head = git('rev-parse', 'HEAD')
if head != BASELINE:
    raise SystemExit(f'BASELINE_MISMATCH=expected:{BASELINE}:actual:{head}')

tracked_diff = git('diff', '--name-only')
if tracked_diff:
    raise SystemExit(f'PREEXISTING_TRACKED_DIFF={tracked_diff.replace(chr(10), ",")}')

print(f'VERSION={VERSION}')
print(f'WORKFLOW_ID={WORKFLOW_ID}')
print(f'BASELINE={BASELINE}')

rel = 'server/security/messengerFinalVerification.test.ts'
test_content = r'''import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { resolveMessengerHttpPermission } from "../routes/central-chat-native";

const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, "../..");
const read = (relativePath: string) => readFileSync(path.join(repo, relativePath), "utf8");

const permissionContext = read("client/src/contexts/PermissionContext.tsx");
const chatPage = read("client/src/pages/TosChatPage.tsx");
const chatPanel = read("client/src/tos-chat/components/ChatPanel.tsx");
const useChat = read("client/src/tos-chat/hooks/useChat.ts");
const httpRouter = read("server/routes/central-chat-native.ts");

function functionWindow(source: string, signature: string, size = 420) {
  const start = source.indexOf(signature);
  expect(start, signature).toBeGreaterThanOrEqual(0);
  return source.slice(start, start + size);
}

describe("Messenger final permission verification V1.2.0", () => {
  it("keeps the raw HTTP permission contract split view/send/manage with fail-closed unknowns", () => {
    const reads = [
      ["GET", "/api/central-chat/me"],
      ["GET", "/api/central-chat/conversations"],
      ["GET", "/api/chat/conversations"],
      ["GET", "/api/chat/conversations/c1/messages?limit=50"],
      ["GET", "/api/chat/search?q=x"],
      ["GET", "/api/files/f1/download"],
    ];
    const sends = [
      ["POST", "/api/central-chat/conversations/direct"],
      ["POST", "/api/chat/conversations/group"],
      ["POST", "/api/chat/messages"],
      ["PATCH", "/api/chat/messages/m1"],
      ["DELETE", "/api/chat/messages/m1"],
      ["POST", "/api/chat/messages/m1/reactions"],
      ["POST", "/api/files/upload"],
      ["DELETE", "/api/files/f1"],
    ];

    for (const [method, route] of reads) {
      expect(resolveMessengerHttpPermission(method, route), `${method} ${route}`).toBe("messenger.view");
    }
    for (const [method, route] of sends) {
      expect(resolveMessengerHttpPermission(method, route), `${method} ${route}`).toBe("messenger.send");
    }

    expect(resolveMessengerHttpPermission("GET", "/api/chat/moderation")).toBe("messenger.manage");
    expect(resolveMessengerHttpPermission("POST", "/api/chat/future-route")).toBe("messenger.manage");
    expect(resolveMessengerHttpPermission("DELETE", "/api/central-chat/future-config")).toBe("messenger.manage");
  });

  it("keeps raw HTTP permission middleware scoped and additive before Central Chat routes", () => {
    expect(httpRouter).toContain('import { evaluatePermission } from "../security/permissionEngine";');
    expect(httpRouter).toContain('await evaluatePermission(user, permission, req)');
    expect(httpRouter).toContain('router.use("/central-chat", requireMessengerPermission);');
    expect(httpRouter).toContain('router.use("/chat", requireMessengerPermission);');
    expect(httpRouter).toContain('router.use("/files", requireMessengerPermission);');
    expect(httpRouter).not.toContain('router.use(requireMessengerPermission);');

    const gate = httpRouter.indexOf('async function requireMessengerPermission');
    const mounts = httpRouter.indexOf('router.use("/central-chat", requireMessengerPermission);');
    const firstRoute = httpRouter.indexOf('router.get("/central-chat/me"');
    expect(gate).toBeGreaterThanOrEqual(0);
    expect(mounts).toBeGreaterThan(gate);
    expect(firstRoute).toBeGreaterThan(mounts);
  });

  it("keeps /chat route visibility and page decisions permission-driven", () => {
    expect(permissionContext).toContain('"messenger.view"');
    expect(permissionContext).toContain('"messenger.send"');
    expect(permissionContext).toContain('"messenger.manage"');
    expect(permissionContext).toContain('["/chat", "messenger.view"]');
    expect(chatPage).toContain('const canSendMessenger = can("messenger.send")');
    expect(chatPage).toContain('const canManageMessenger = can("messenger.manage")');
    expect(chatPage).toContain('allowMessengerSend={canSendMessenger}');
    expect(chatPage).toContain('allowMessengerManage={canManageMessenger}');
    expect(chatPage).not.toContain('user?.role ===');
  });

  it("keeps messenger.send additive across desktop/mobile mutation surfaces while preserving read-only access", () => {
    expect(chatPanel).toContain('allowMessengerSend = true');
    expect(chatPanel).toContain('const canSend = Boolean(allowMessengerSend) && (isDirectMode ?');
    expect(chatPanel).toContain('showNewGroup && allowMessengerSend');
    expect(chatPanel).toContain('disabled={!allowMessengerSend || !selectedDirectUserId || directStartLoading}');
    expect(chatPanel).toContain('return Boolean(allowMessengerSend) && (isSystemAdmin(user) || message.userId === user?.id || file.uploadedById === user?.id || (!isDirectMode && canManageChat));');
    expect(chatPanel).toContain('Read-only Messenger access: you can view conversations, but sending and chat mutations are disabled.');
    expect(chatPanel).toContain('صلاحية الماسنجر للقراءة فقط: يمكنك عرض المحادثات، بينما الإرسال وتعديلات الشات معطلة.');
  });

  it("keeps messenger.manage additive and removes the legacy direct-mode moderation bypass", () => {
    expect(chatPanel).toContain('const canManageChat = Boolean(allowMessengerManage) && (isSystemAdmin(user)');
    const moderation = functionWindow(chatPanel, 'async function loadModerationDashboard()', 540);
    expect(moderation).toContain('if (!canManageChat) return;');
    expect(moderation).toContain('api.chat.moderation(filters)');
    expect(moderation).not.toContain('isDirectMode && isSystemAdmin(user)');
  });

  it("keeps automatic Messenger mutations silent when messenger.send is absent", () => {
    expect(useChat).toContain('allowMutations = true');
    expect(functionWindow(useChat, 'async function acknowledgeDelivered', 220)).toContain('if (!allowMutations) return;');
    expect(functionWindow(useChat, 'async function markNotificationsRead', 220)).toContain('if (!allowMutations) return;');
    expect(functionWindow(useChat, 'async function markRead()', 220)).toContain('if (!allowMutations) return;');
    expect(functionWindow(useChat, 'function startTyping()', 220)).toContain('if (!allowMutations) return;');
  });

  it("keeps explicit Messenger mutation helpers fail-closed behind the defensive mutation guard", () => {
    expect(useChat).toContain('throw new Error("Messenger send permission required")');
    for (const fn of [
      'sendMessage',
      'addReaction',
      'markDecision',
      'pinMessage',
      'convertToTask',
      'editMessage',
      'deleteMessage',
      'uploadChatFile',
      'deleteChatFile',
      'createChannel',
      'startMeeting',
    ]) {
      const block = functionWindow(useChat, `async function ${fn}`, 240);
      expect(block, fn).toContain('requireMutationPermission();');
    }
  });

  it("preserves passive read paths without adding the mutation guard", () => {
    for (const fn of ['loadNotifications', 'loadMessages', 'refreshMessagesSilently', 'loadOlderMessages']) {
      const block = functionWindow(useChat, `async function ${fn}`, 650);
      expect(block, fn).not.toContain('requireMutationPermission();');
    }
  });
});
'''

write_new(rel, test_content)

expected_dirty = {rel}
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
missing = sorted(expected_dirty - dirty)
if unexpected or missing:
    raise SystemExit(f'POSTCHECK_DIRTY_MISMATCH=unexpected:{unexpected}:missing:{missing}')

print('PATCH_APPLIED=YES')
print('MODULES=messenger_final_verification')
print('RUNTIME_SOURCE_CHANGED=NO')
print('TEST_REGRESSION_ONLY=YES')
print('FILES_CHANGED=' + rel)
print('READY_FOR_TESTS=YES')
