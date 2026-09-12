#!/usr/bin/env python3
from pathlib import Path
import subprocess

ROOT = Path('/var/www/TCRM-MAIN')
BASELINE = '376aecc4284c83d8c7bc6c1ab720af872db792fc'
VERSION = 'V1.1.1'
WORKFLOW_ID = 'TCRM-PERMISSIONS-MESSENGER-FRONTEND-ACTIONS-V1.1.1-RECOVERY'
PREVIOUS_VERSION = 'V1.1.0'
PREVIOUS_WORKFLOW_ID = 'TCRM-PERMISSIONS-MESSENGER-FRONTEND-ACTIONS-V1.1.0'


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
    if new in text and old not in text:
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
print(f'PREVIOUS_VERSION={PREVIOUS_VERSION}')
print(f'PREVIOUS_WORKFLOW_ID={PREVIOUS_WORKFLOW_ID}')
print(f'BASELINE={BASELINE}')

chat_rel = 'client/src/tos-chat/components/ChatPanel.tsx'
chat = read(chat_rel)

# V1.1.0 made canManageChat additive to messenger.manage, but the direct-mode
# moderation loader retained a legacy System Admin bypass. That caused a
# view/send-only System Admin to auto-call the manage-only endpoint and receive
# a 403. The canonical canManageChat decision already includes both the TCRM
# permission and the existing Central Chat manager/admin authorization.
chat = replace_once(
    chat,
    '    if (!canManageChat && !(isDirectMode && isSystemAdmin(user))) return;\n',
    '    if (!canManageChat) return;\n',
    'moderation_manage_bypass',
)

# Read-only Messenger access must not advertise a file-delete mutation action.
# Keep the existing ownership/admin/project-manager authorization additive.
chat = replace_once(
    chat,
    '    return isSystemAdmin(user) || message.userId === user?.id || file.uploadedById === user?.id || (!isDirectMode && canManageChat);\n',
    '    return Boolean(allowMessengerSend) && (isSystemAdmin(user) || message.userId === user?.id || file.uploadedById === user?.id || (!isDirectMode && canManageChat));\n',
    'file_delete_send_gate',
)

# The compact/mobile direct-conversation starter is a second UI surface. Its
# handler was already fail-safe, but the controls must visibly honor read-only
# Messenger access just like the desktop/sidebar surface.
chat = replace_once(
    chat,
    '                <select value={selectedDirectUserId} onChange={(event) => setSelectedDirectUserId(event.target.value)} className="min-w-0 flex-1 rounded-2xl border border-zinc-100 bg-white px-3 py-2 text-xs outline-none">\n',
    '                <select value={selectedDirectUserId} onChange={(event) => setSelectedDirectUserId(event.target.value)} disabled={!allowMessengerSend} className="min-w-0 flex-1 rounded-2xl border border-zinc-100 bg-white px-3 py-2 text-xs outline-none disabled:cursor-not-allowed disabled:opacity-50">\n',
    'mobile_direct_select_send_gate',
)
chat = replace_once(
    chat,
    '                <button type="submit" disabled={!selectedDirectUserId || directStartLoading} className="rounded-2xl bg-zinc-950 px-3 py-2 text-xs font-black text-white disabled:opacity-50">{directStartLoading ? (lang === "en" ? "Opening..." : "جاري") : (lang === "en" ? "Start" : "بدء")}</button>\n',
    '                <button type="submit" disabled={!allowMessengerSend || !selectedDirectUserId || directStartLoading} className="rounded-2xl bg-zinc-950 px-3 py-2 text-xs font-black text-white disabled:cursor-not-allowed disabled:opacity-50">{directStartLoading ? (lang === "en" ? "Opening..." : "جاري") : (lang === "en" ? "Start" : "بدء")}</button>\n',
    'mobile_direct_submit_send_gate',
)
write(chat_rel, chat)

test_rel = 'server/security/messengerFrontendPermission.test.ts'
test = read(test_rel)
marker = 'describe("Messenger frontend permission recovery V1.1.1"'
if marker not in test:
    recovery_tests = r'''

describe("Messenger frontend permission recovery V1.1.1", () => {
  it("removes the direct-mode System Admin bypass from messenger.manage moderation", () => {
    const start = chatPanel.indexOf('async function loadModerationDashboard()');
    expect(start).toBeGreaterThanOrEqual(0);
    const block = chatPanel.slice(start, start + 520);
    expect(block).toContain('if (!canManageChat) return;');
    expect(block).not.toContain('isDirectMode && isSystemAdmin(user)');
    expect(block).toContain('api.chat.moderation(filters)');
    expect(chatPanel).toContain('const canManageChat = Boolean(allowMessengerManage) && (isSystemAdmin(user)');
  });

  it("keeps chat-file delete UI additive to messenger.send and existing ownership authorization", () => {
    expect(chatPanel).toContain('return Boolean(allowMessengerSend) && (isSystemAdmin(user) || message.userId === user?.id || file.uploadedById === user?.id || (!isDirectMode && canManageChat));');
    expect(useChat).toContain('async function deleteChatFile(fileId) {\n    requireMutationPermission();');
  });

  it("disables the compact direct-conversation creator for read-only Messenger access", () => {
    expect(chatPanel).toContain('disabled={!allowMessengerSend} className="min-w-0 flex-1 rounded-2xl border border-zinc-100 bg-white px-3 py-2 text-xs outline-none disabled:cursor-not-allowed disabled:opacity-50"');
    expect(chatPanel).toContain('disabled={!allowMessengerSend || !selectedDirectUserId || directStartLoading} className="rounded-2xl bg-zinc-950 px-3 py-2 text-xs font-black text-white disabled:cursor-not-allowed disabled:opacity-50"');
    expect(chatPanel).toContain('async function openDirectConversationFor(targetUserId) {\n    if (!allowMessengerSend) {');
  });
});
'''
    test = test.rstrip() + recovery_tests + '\n'
write(test_rel, test)

# Fail-closed postchecks.
chat_after = read(chat_rel)
test_after = read(test_rel)
required = [
    'const canManageChat = Boolean(allowMessengerManage) && (isSystemAdmin(user)',
    'async function loadModerationDashboard() {\n    if (!canManageChat) return;',
    'return Boolean(allowMessengerSend) && (isSystemAdmin(user) || message.userId === user?.id || file.uploadedById === user?.id || (!isDirectMode && canManageChat));',
    'disabled={!allowMessengerSend} className="min-w-0 flex-1 rounded-2xl border border-zinc-100 bg-white px-3 py-2 text-xs outline-none disabled:cursor-not-allowed disabled:opacity-50"',
    'disabled={!allowMessengerSend || !selectedDirectUserId || directStartLoading}',
]
missing = [value for value in required if value not in chat_after]
if missing:
    raise SystemExit(f'POSTCHECK_FAILED={chat_rel}:{missing}')
if 'if (!canManageChat && !(isDirectMode && isSystemAdmin(user))) return;' in chat_after:
    raise SystemExit('POSTCHECK_FAILED=legacy_manage_bypass_still_present')
if marker not in test_after:
    raise SystemExit('POSTCHECK_FAILED=recovery_tests_missing')

expected_dirty = {
    'client/src/tos-chat/components/ChatPanel.tsx',
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
print('MODULES=messenger_frontend_recovery')
print('MODERATION_MANAGE_BYPASS_FIXED=YES')
print('FILE_DELETE_SEND_UI_GATE=YES')
print('MOBILE_DIRECT_CREATOR_SEND_GATE=YES')
print('BACKEND_POLICY_CHANGED=NO')
print('FILES_CHANGED=' + ','.join(sorted(expected_dirty)))
print('READY_FOR_TESTS=YES')
