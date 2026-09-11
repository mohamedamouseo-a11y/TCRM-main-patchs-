#!/usr/bin/env python3
from pathlib import Path
import subprocess

ROOT = Path('/var/www/TCRM-MAIN')
BASELINE = '006e9fe98af570caf7925de9a9f204dc03987f36'
VERSION = 'V1.1.0'
WORKFLOW_ID = 'TCRM-PERMISSIONS-MESSENGER-FRONTEND-ACTIONS-V1.1.0'


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

# ---------------------------------------------------------------------------
# 1) PermissionContext: expose Messenger permissions and route-gate /chat.
# ---------------------------------------------------------------------------
rel = 'client/src/contexts/PermissionContext.tsx'
data = read(rel)
data = replace_once(
    data,
    '  "whatsapp.manage",\n  "tara.view",\n',
    '  "whatsapp.manage",\n  "messenger.view",\n  "messenger.send",\n  "messenger.manage",\n  "tara.view",\n',
    'permission_context_messenger_keys',
)
data = replace_once(
    data,
    '    ["/wa-gateway", "whatsapp.view"],\n    ["/tara", "tara.view"],\n',
    '    ["/wa-gateway", "whatsapp.view"],\n    ["/chat", "messenger.view"],\n    ["/tara", "tara.view"],\n',
    'permission_context_chat_route',
)
write(rel, data)

# ---------------------------------------------------------------------------
# 2) TCRM chat page: resolve effective Messenger permissions once and pass them
#    into the cloned ChatPanel without hardcoding any roles.
# ---------------------------------------------------------------------------
rel = 'client/src/pages/TosChatPage.tsx'
data = read(rel)
data = replace_once(
    data,
    'import { useAuth } from "@/_core/hooks/useAuth";\n',
    'import { useAuth } from "@/_core/hooks/useAuth";\nimport { usePermissions } from "@/contexts/PermissionContext";\n',
    'tos_chat_permission_import',
)
data = replace_once(
    data,
    '  const { user } = useAuth();\n\n  return (\n',
    '  const { user } = useAuth();\n  const { can } = usePermissions();\n  const canSendMessenger = can("messenger.send");\n  const canManageMessenger = can("messenger.manage");\n\n  return (\n',
    'tos_chat_permission_decisions',
)
data = replace_once(
    data,
    '            allowExternalFileUpload={false}\n          />\n',
    '            allowExternalFileUpload={false}\n            allowMessengerSend={canSendMessenger}\n            allowMessengerManage={canManageMessenger}\n          />\n',
    'tos_chat_permission_props',
)
write(rel, data)

# ---------------------------------------------------------------------------
# 3) ChatPanel: make the central permission layer additive to the existing
#    Central Chat/project authorization. Defaults preserve non-TCRM callers.
# ---------------------------------------------------------------------------
rel = 'client/src/tos-chat/components/ChatPanel.tsx'
data = read(rel)
data = replace_once(
    data,
    'export function ChatPanel({ user, project, projectId, projectName, externalDirectOnly = false, allowExternalFileUpload = false, allowHuddle = true, allowAvatarUpload = true, crmNative = false }) {\n',
    'export function ChatPanel({ user, project, projectId, projectName, externalDirectOnly = false, allowExternalFileUpload = false, allowHuddle = true, allowAvatarUpload = true, crmNative = false, allowMessengerSend = true, allowMessengerManage = true }) {\n',
    'chat_panel_permission_props',
)
data = replace_once(
    data,
    '    currentUserId: user?.id || "",\n    onNotify: (message) => setLocalSuccess(message),\n  });\n',
    '    currentUserId: user?.id || "",\n    onNotify: (message) => setLocalSuccess(message),\n    allowMutations: Boolean(allowMessengerSend),\n  });\n',
    'chat_panel_use_chat_mutation_gate',
)
data = replace_once(
    data,
    '  const canManageChat = isSystemAdmin(user) || (!isDirectMode && ["OWNER", "MANAGER", "owner", "manager"].includes(projectRole || ""));\n',
    '  const canManageChat = Boolean(allowMessengerManage) && (isSystemAdmin(user) || (!isDirectMode && ["OWNER", "MANAGER", "owner", "manager"].includes(projectRole || "")));\n',
    'chat_panel_manage_gate',
)
data = replace_once(
    data,
    '  const canSend = isDirectMode ? canDirectChat && Boolean(activeConversationId) : canProjectInteract && (!activeChannelLocked || canManageChat) && (!activeChannelMemberSendDisabled || canManageChat) && roleCanSend;\n',
    '  const canSend = Boolean(allowMessengerSend) && (isDirectMode ? canDirectChat && Boolean(activeConversationId) : canProjectInteract && (!activeChannelLocked || canManageChat) && (!activeChannelMemberSendDisabled || canManageChat) && roleCanSend);\n',
    'chat_panel_send_gate',
)
data = replace_once(
    data,
    '  async function submitGroupConversation(event) {\n    event.preventDefault();\n    if (!canDirectChat || groupMemberIds.length < 2) {\n',
    '  async function submitGroupConversation(event) {\n    event.preventDefault();\n    if (!allowMessengerSend) {\n      setLocalError(lang === "en" ? "Your Messenger access is read-only." : "صلاحية الماسنجر الحالية للقراءة فقط.");\n      return;\n    }\n    if (!canDirectChat || groupMemberIds.length < 2) {\n',
    'chat_panel_group_create_guard',
)
data = replace_once(
    data,
    '  async function openDirectConversationFor(targetUserId) {\n    if (!canDirectChat) {\n',
    '  async function openDirectConversationFor(targetUserId) {\n    if (!allowMessengerSend) {\n      setLocalError(lang === "en" ? "Your Messenger access is read-only." : "صلاحية الماسنجر الحالية للقراءة فقط.");\n      return false;\n    }\n    if (!canDirectChat) {\n',
    'chat_panel_direct_create_guard',
)
data = replace_once(
    data,
    '        onOpenDirectChat={isDirectMode && canDirectChat && selectedProfile?.id && selectedProfile.id !== (displayUser?.id || user?.id)\n',
    '        onOpenDirectChat={allowMessengerSend && isDirectMode && canDirectChat && selectedProfile?.id && selectedProfile.id !== (displayUser?.id || user?.id)\n',
    'chat_panel_profile_direct_gate',
)
data = replace_once(
    data,
    '                  <button type="button" onClick={() => setShowNewGroup((value) => !value)} className="rounded-lg bg-white/10 px-2 py-1 text-zinc-300">{ui.group}</button>\n',
    '                  <button type="button" onClick={() => setShowNewGroup((value) => !value)} disabled={!allowMessengerSend} className="rounded-lg bg-white/10 px-2 py-1 text-zinc-300 disabled:cursor-not-allowed disabled:opacity-40">{ui.group}</button>\n',
    'chat_panel_group_button_gate',
)
data = replace_once(
    data,
    '                <select value={selectedDirectUserId} onChange={(event) => setSelectedDirectUserId(event.target.value)} className="w-full rounded-xl border border-white/10 bg-zinc-900 px-3 py-2 text-sm text-white outline-none">\n',
    '                <select value={selectedDirectUserId} onChange={(event) => setSelectedDirectUserId(event.target.value)} disabled={!allowMessengerSend} className="w-full rounded-xl border border-white/10 bg-zinc-900 px-3 py-2 text-sm text-white outline-none disabled:cursor-not-allowed disabled:opacity-50">\n',
    'chat_panel_direct_select_gate',
)
data = replace_once(
    data,
    '                <button type="submit" disabled={!selectedDirectUserId || directStartLoading} className="mt-2 w-full rounded-xl bg-amber-400 px-3 py-2 text-xs font-black text-zinc-950 disabled:opacity-50">{directStartLoading ? (lang === "en" ? "Opening..." : "جاري الفتح...") : ui.startConversation}</button>\n',
    '                <button type="submit" disabled={!allowMessengerSend || !selectedDirectUserId || directStartLoading} className="mt-2 w-full rounded-xl bg-amber-400 px-3 py-2 text-xs font-black text-zinc-950 disabled:cursor-not-allowed disabled:opacity-50">{directStartLoading ? (lang === "en" ? "Opening..." : "جاري الفتح...") : ui.startConversation}</button>\n',
    'chat_panel_direct_submit_gate',
)
data = replace_once(
    data,
    '              {showNewGroup && (\n',
    '              {showNewGroup && allowMessengerSend && (\n',
    'chat_panel_group_form_gate',
)
data = replace_once(
    data,
    '      {isDirectMode && canDirectChat && !activeConversationId && !externalDirectOnly && <Notice type="info" className="m-4">اختر محادثة خاصة أو ابدأ محادثة مع أحد أعضاء الفريق.</Notice>}\n',
    '      {isDirectMode && canDirectChat && !activeConversationId && !externalDirectOnly && <Notice type="info" className="m-4">اختر محادثة خاصة أو ابدأ محادثة مع أحد أعضاء الفريق.</Notice>}\n      {isDirectMode && canDirectChat && !allowMessengerSend && <Notice type="info" className="m-4">{lang === "en" ? "Read-only Messenger access: you can view conversations, but sending and chat mutations are disabled." : "صلاحية الماسنجر للقراءة فقط: يمكنك عرض المحادثات، بينما الإرسال وتعديلات الشات معطلة."}</Notice>}\n',
    'chat_panel_read_only_notice',
)
write(rel, data)

# ---------------------------------------------------------------------------
# 4) useChat: defensive gating for mutations, including automatic read/delivery
#    acknowledgements and typing socket events. Reads remain untouched.
# ---------------------------------------------------------------------------
rel = 'client/src/tos-chat/hooks/useChat.ts'
data = read(rel)
data = replace_once(
    data,
    'export function useChat({ projectId, channelId = "", conversationId = "", currentUserId = "", onNotify = null }) {\n',
    'export function useChat({ projectId, channelId = "", conversationId = "", currentUserId = "", onNotify = null, allowMutations = true }) {\n',
    'use_chat_allow_mutations_param',
)
data = replace_once(
    data,
    '  function clearError() {\n    setError("");\n  }\n\n',
    '  function clearError() {\n    setError("");\n  }\n\n  function requireMutationPermission() {\n    if (allowMutations) return;\n    throw new Error("Messenger send permission required");\n  }\n\n',
    'use_chat_mutation_guard_helper',
)
# Silent automatic mutations.
for signature, label in [
    ('  async function acknowledgeDelivered(messageId, socket = null) {\n', 'ack_delivered'),
    ('  async function markNotificationsRead(notificationIds = []) {\n', 'mark_notifications_read'),
    ('  async function markRead() {\n', 'mark_read'),
    ('  function startTyping() {\n', 'typing'),
]:
    data = replace_once(
        data,
        signature,
        signature + '    if (!allowMutations) return;\n',
        f'use_chat_{label}_guard',
    )

# Explicit user-triggered mutations fail defensively if invoked despite hidden UI.
for signature, label in [
    ('  async function sendMessage(body, parentMessageId = null) {\n', 'send_message'),
    ('  async function addReaction(messageId, emoji) {\n', 'reaction'),
    ('  async function markDecision(messageId, payload = {}) {\n', 'decision'),
    ('  async function pinMessage(messageId, isPinned = true) {\n', 'pin'),
    ('  async function convertToTask(messageId, title = "") {\n', 'to_task'),
    ('  async function editMessage(messageId, body) {\n', 'edit'),
    ('  async function deleteMessage(messageId) {\n', 'delete'),
    ('  async function uploadChatFile(messageId, file) {\n', 'upload_file'),
    ('  async function deleteChatFile(fileId) {\n', 'delete_file'),
    ('  async function createChannel(payload) {\n', 'create_channel'),
    ('  async function startMeeting(meetUrl) {\n', 'start_meeting'),
]:
    data = replace_once(
        data,
        signature,
        signature + '    requireMutationPermission();\n',
        f'use_chat_{label}_guard',
    )
write(rel, data)

# ---------------------------------------------------------------------------
# 5) Regression test: static source-contract test avoids rendering the huge
#    ChatPanel while verifying all permission wiring and additive gates.
# ---------------------------------------------------------------------------
test_rel = 'server/security/messengerFrontendPermission.test.ts'
test_content = '''import { describe, expect, it } from "vitest";\nimport { readFileSync } from "node:fs";\nimport { fileURLToPath } from "node:url";\nimport path from "node:path";\n\nconst here = path.dirname(fileURLToPath(import.meta.url));\nconst repo = path.resolve(here, "../..");\nconst permissionContext = readFileSync(path.join(repo, "client/src/contexts/PermissionContext.tsx"), "utf8");\nconst chatPage = readFileSync(path.join(repo, "client/src/pages/TosChatPage.tsx"), "utf8");\nconst chatPanel = readFileSync(path.join(repo, "client/src/tos-chat/components/ChatPanel.tsx"), "utf8");\nconst useChat = readFileSync(path.join(repo, "client/src/tos-chat/hooks/useChat.ts"), "utf8");\n\ndescribe("Messenger frontend permissions V1.1.0", () => {\n  it("exposes Messenger decisions and route-gates /chat with messenger.view", () => {\n    expect(permissionContext).toContain('"messenger.view"');\n    expect(permissionContext).toContain('"messenger.send"');\n    expect(permissionContext).toContain('"messenger.manage"');\n    expect(permissionContext).toContain('["/chat", "messenger.view"]');\n  });\n\n  it("passes effective send/manage permissions into the TCRM ChatPanel", () => {\n    expect(chatPage).toContain('const canSendMessenger = can("messenger.send")');\n    expect(chatPage).toContain('const canManageMessenger = can("messenger.manage")');\n    expect(chatPage).toContain('allowMessengerSend={canSendMessenger}');\n    expect(chatPage).toContain('allowMessengerManage={canManageMessenger}');\n  });\n\n  it("keeps Messenger permissions additive to existing ChatPanel authorization", () => {\n    expect(chatPanel).toContain('allowMessengerSend = true');\n    expect(chatPanel).toContain('allowMessengerManage = true');\n    expect(chatPanel).toContain('allowMutations: Boolean(allowMessengerSend)');\n    expect(chatPanel).toContain('const canManageChat = Boolean(allowMessengerManage) && (isSystemAdmin(user)');\n    expect(chatPanel).toContain('const canSend = Boolean(allowMessengerSend) && (isDirectMode ?');\n    expect(chatPanel).toContain('if (!allowMessengerSend) {');\n    expect(chatPanel).toContain('disabled={!allowMessengerSend || !selectedDirectUserId || directStartLoading}');\n    expect(chatPanel).toContain('showNewGroup && allowMessengerSend');\n    expect(chatPanel).toContain('Read-only Messenger access');\n  });\n\n  it("blocks automatic and explicit chat mutations when messenger.send is absent", () => {\n    expect(useChat).toContain('allowMutations = true');\n    expect(useChat).toContain('throw new Error("Messenger send permission required")');\n    expect(useChat).toContain('async function acknowledgeDelivered(messageId, socket = null) {\\n    if (!allowMutations) return;');\n    expect(useChat).toContain('async function markRead() {\\n    if (!allowMutations) return;');\n    expect(useChat).toContain('function startTyping() {\\n    if (!allowMutations) return;');\n    for (const fn of [\n      'sendMessage',\n      'addReaction',\n      'markDecision',\n      'pinMessage',\n      'convertToTask',\n      'editMessage',\n      'deleteMessage',\n      'uploadChatFile',\n      'deleteChatFile',\n      'createChannel',\n      'startMeeting',\n    ]) {\n      const start = useChat.indexOf(`async function ${fn}`);\n      expect(start, fn).toBeGreaterThanOrEqual(0);\n      expect(useChat.slice(start, start + 180), fn).toContain('requireMutationPermission();');\n    }\n  });\n});\n'''
path = ROOT / test_rel
if path.exists() and path.read_text(encoding='utf-8') != test_content:
    raise SystemExit(f'UNEXPECTED_EXISTING_FILE={test_rel}')
write(test_rel, test_content)

# Fail-closed postchecks.
postchecks = {
    'client/src/contexts/PermissionContext.tsx': [
        '"messenger.view"', '"messenger.send"', '"messenger.manage"', '["/chat", "messenger.view"]',
    ],
    'client/src/pages/TosChatPage.tsx': [
        'can("messenger.send")', 'can("messenger.manage")', 'allowMessengerSend={canSendMessenger}', 'allowMessengerManage={canManageMessenger}',
    ],
    'client/src/tos-chat/components/ChatPanel.tsx': [
        'allowMutations: Boolean(allowMessengerSend)',
        'const canManageChat = Boolean(allowMessengerManage)',
        'const canSend = Boolean(allowMessengerSend)',
        'Read-only Messenger access',
    ],
    'client/src/tos-chat/hooks/useChat.ts': [
        'allowMutations = true', 'Messenger send permission required', 'if (!allowMutations) return;', 'requireMutationPermission();',
    ],
}
for file_rel, markers in postchecks.items():
    source = read(file_rel)
    missing = [marker for marker in markers if marker not in source]
    if missing:
        raise SystemExit(f'POSTCHECK_FAILED={file_rel}:{missing}')

expected_dirty = {
    'client/src/contexts/PermissionContext.tsx',
    'client/src/pages/TosChatPage.tsx',
    'client/src/tos-chat/components/ChatPanel.tsx',
    'client/src/tos-chat/hooks/useChat.ts',
    'server/security/messengerFrontendPermission.test.ts',
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
print('MODULES=messenger_frontend_route_actions')
print('MESSENGER_VIEW_ROUTE_GATE=YES')
print('MESSENGER_SEND_ACTION_GATE=YES')
print('MESSENGER_MANAGE_ACTION_GATE=YES')
print('AUTO_MUTATIONS_GATED=YES')
print('ROLE_HARDCODING_ADDED=NO')
print('FILES_CHANGED=' + ','.join(sorted(expected_dirty)))
print('READY_FOR_TESTS=YES')
