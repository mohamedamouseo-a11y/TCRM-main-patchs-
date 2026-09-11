#!/usr/bin/env python3
from pathlib import Path
import subprocess

ROOT = Path('/var/www/TCRM-MAIN')
BASELINE = '8c7b95135e6efd5236373849184ae353226317a6'
VERSION = 'V1.3.0'
WORKFLOW_ID = 'TCRM-PERMISSIONS-WHATSAPP-FINAL-VERIFICATION-V1.3.0'
TARGET = 'server/security/waGatewayMediaReadHttpPermission.test.ts'


def git(*args: str) -> str:
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.exists():
        raise SystemExit(f'MISSING_FILE={rel}')
    return path.read_text(encoding='utf-8')


def write(rel: str, content: str) -> None:
    path = ROOT / rel
    before = path.read_text(encoding='utf-8')
    if before == content:
        print(f'SKIP={rel}:already_current')
        return
    path.write_text(content, encoding='utf-8')
    print(f'UPDATED={rel}')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'ANCHOR_ERROR={label}:expected=1:actual={count}')
    return text.replace(old, new, 1)


head = git('rev-parse', 'HEAD')
if head != BASELINE:
    raise SystemExit(f'BASELINE_MISMATCH=expected:{BASELINE}:actual:{head}')

tracked_diff = git('diff', '--name-only')
if tracked_diff:
    raise SystemExit(f'WORKTREE_NOT_CLEAN={tracked_diff}')

print(f'VERSION={VERSION}')
print(f'WORKFLOW_ID={WORKFLOW_ID}')
print(f'BASELINE={BASELINE}')

data = read(TARGET)

data = replace_once(
    data,
    'import path from "node:path";\n',
    'import path from "node:path";\nimport { resolveCorePermissionKey } from "./corePermissionPolicy";\n',
    'final_verification_import',
)

data = replace_once(
    data,
    'const here = path.dirname(fileURLToPath(import.meta.url));\nconst indexSource = readFileSync(path.resolve(here, "../_core/index.ts"), "utf8");\n',
    '''const here = path.dirname(fileURLToPath(import.meta.url));\nconst projectRoot = path.resolve(here, "../..");\nconst readProjectSource = (relativePath: string) => readFileSync(path.resolve(projectRoot, relativePath), "utf8");\nconst indexSource = readProjectSource("server/_core/index.ts");\nconst permissionContextSource = readProjectSource("client/src/contexts/PermissionContext.tsx");\nconst inboxSource = readProjectSource("client/src/pages/wa/WAGatewayInbox.tsx");\nconst conversationListSource = readProjectSource("client/src/components/wa/ConversationList.tsx");\nconst conversationHeaderSource = readProjectSource("client/src/components/wa/ConversationHeader.tsx");\nconst customerContextSource = readProjectSource("client/src/components/wa/CustomerContextPanel.tsx");\nconst messageTimelineSource = readProjectSource("client/src/components/wa/MessageTimeline.tsx");\n''',
    'final_verification_source_loaders',
)

final_block = r'''

describe("WhatsApp permissions final verification V1.3.0", () => {
  it("keeps tRPC WA Gateway operations split into view, send, and fail-closed manage", () => {
    const viewOperations = [
      "getStatus",
      "listChats",
      "listChatsPage",
      "getInboxCounts",
      "getChat",
      "listGroupParticipants",
      "listMessages",
      "listMessagesPage",
      "forwardMessageStatus",
    ];
    for (const operation of viewOperations) {
      expect(resolveCorePermissionKey(`waGateway.${operation}`, "query")).toBe("whatsapp.view");
    }

    const sendOperations = [
      "markRead",
      "setChatState",
      "setChatPinned",
      "updateChatRouting",
      "bulkUpdateChats",
      "sendText",
      "forwardMessage",
      "allowForwardMessageRetry",
      "refreshProfilePicture",
    ];
    for (const operation of sendOperations) {
      expect(resolveCorePermissionKey(`waGateway.${operation}`, "mutation")).toBe("whatsapp.send");
    }

    expect(resolveCorePermissionKey("waGateway.listAccounts", "query")).toBe("whatsapp.manage");
    expect(resolveCorePermissionKey("waGateway.futureUnknownMutation", "mutation")).toBe("whatsapp.manage");
  });

  it("exposes view/send/manage to the UI and keeps route access split correctly", () => {
    expect(permissionContextSource).toContain('"whatsapp.view"');
    expect(permissionContextSource).toContain('"whatsapp.send"');
    expect(permissionContextSource).toContain('"whatsapp.manage"');
    expect(permissionContextSource).toContain('["/wa-gateway", "whatsapp.view"]');
    expect(permissionContextSource).toContain('["/wa-gateway/accounts", "whatsapp.manage"]');
    expect(permissionContextSource).toContain('["/wa-gateway/settings", "whatsapp.manage"]');
  });

  it("keeps inbox mutations behind whatsapp.send and account management behind whatsapp.manage", () => {
    expect(inboxSource).toContain('const canSendWhatsApp = can("whatsapp.send");');
    expect(inboxSource).toContain('const canManageWhatsApp = can("whatsapp.manage");');
    expect(inboxSource).toContain('onManageAccounts={canManageWhatsApp ? () => navigate("/wa-gateway/accounts") : undefined}');
    expect(inboxSource).toContain('if (!canSendWhatsApp || !selected || !currentDraft.trim()');
    expect(inboxSource).toContain('if (!canSendWhatsApp || !Number.isInteger(chatId) || chatId <= 0) return Promise.resolve(false);');
    expect(inboxSource).toContain('if (!canSendWhatsApp) return;');
    expect(inboxSource).toContain('canOperate={canSendWhatsApp}');
    expect(inboxSource).toContain('canSendActions={canSendWhatsApp}');
    expect(inboxSource).toContain('disabled={!canSendWhatsApp || !selectedAccountRecord?.connected');
    expect(inboxSource).toContain('open={canSendWhatsApp && Boolean(forwardSource)}');
  });

  it("preserves Viewer-style read-only controls while keeping normal read/copy actions available", () => {
    expect(conversationListSource).toContain('canOperate && selectedChatIds.length > 0');
    expect(conversationListSource).toContain('disabled={!canOperate}');
    expect(conversationListSource).toContain('onChange={() => canOperate && onToggleSelection(chat.id)}');

    expect(conversationHeaderSource).toContain('{canOperate && <DropdownMenuItem disabled={pinUpdating} onClick={onTogglePin}>');
    expect(conversationHeaderSource).toContain('{canOperate && chat.conversationState !== "Open"');
    expect(conversationHeaderSource).toContain('<DropdownMenuItem onClick={onCopyPhone}><Copy');

    expect(customerContextSource).toContain('const canEditRouting = canOperate && Boolean(account?.canManage);');
    expect(customerContextSource).toContain('select disabled={!canEditRouting}');
    expect(customerContextSource).toContain('disabled={routingUpdating || !canEditRouting}');

    expect(messageTimelineSource).toContain('canSendActions &&');
    expect(messageTimelineSource).toContain('{canSendActions && <button type="button" onClick={() => onReply(message)}');
    expect(messageTimelineSource).toContain('<button type="button" onClick={() => copyMessage(message)}');
  });

  it("keeps raw media send/read endpoints protected before any sensitive work", () => {
    const sendGateStart = indexSource.indexOf("const waMediaUploadGate = async");
    const sendRouteStart = indexSource.indexOf('app.post("/api/wa-gateway/media/send", waMediaUploadGate', sendGateStart);
    expect(sendGateStart).toBeGreaterThanOrEqual(0);
    expect(sendRouteStart).toBeGreaterThan(sendGateStart);
    const sendGateSource = indexSource.slice(sendGateStart, sendRouteStart);
    const sendAuthAt = sendGateSource.indexOf("await authenticateRequest(req)");
    const sendPermissionAt = sendGateSource.indexOf('await evaluatePermission(user, "whatsapp.send")');
    const reserveAt = sendGateSource.indexOf("waMediaUploadsInFlight += 1");
    expect(sendAuthAt).toBeGreaterThanOrEqual(0);
    expect(sendPermissionAt).toBeGreaterThan(sendAuthAt);
    expect(reserveAt).toBeGreaterThan(sendPermissionAt);
    expect(sendGateSource).toContain('Permission denied: whatsapp.send');

    const readRouteStart = indexSource.indexOf('app.get("/api/wa-gateway/media/:messageId"');
    const readRouteEnd = indexSource.indexOf('app.post("/api/wa-gateway/webhook"', readRouteStart);
    expect(readRouteStart).toBeGreaterThanOrEqual(0);
    expect(readRouteEnd).toBeGreaterThan(readRouteStart);
    const readRouteSource = indexSource.slice(readRouteStart, readRouteEnd);
    const readAuthAt = readRouteSource.indexOf("await authenticateRequest(req)");
    const readPermissionAt = readRouteSource.indexOf('await evaluatePermission(user, "whatsapp.view", req)');
    const developerPrivacyAt = readRouteSource.indexOf("if (isDeveloperRole(user.role))");
    const lookupAt = readRouteSource.indexOf("await getWAGatewayMessageMedia({");
    const driveAt = readRouteSource.indexOf("await prepareWAGatewayDriveMedia({");
    expect(readAuthAt).toBeGreaterThanOrEqual(0);
    expect(readPermissionAt).toBeGreaterThan(readAuthAt);
    expect(developerPrivacyAt).toBeGreaterThan(readPermissionAt);
    expect(lookupAt).toBeGreaterThan(developerPrivacyAt);
    expect(driveAt).toBeGreaterThan(lookupAt);
    expect(readRouteSource).toContain('Permission denied: whatsapp.view');
    expect(readRouteSource).toContain('actor: user');
  });

  it("keeps Tara controls independent from whatsapp.send gating", () => {
    expect(conversationHeaderSource).toContain('{chat.chatType === "Direct" && taraContext && onSetTaraStatus && <>');
    expect(conversationHeaderSource).not.toContain('{canOperate && chat.chatType === "Direct" && taraContext && onSetTaraStatus');
    expect(inboxSource).toContain('onSetTaraStatus={(status) => { const reason =');
    expect(inboxSource).not.toContain('if (canSendWhatsApp) setTaraStatus.mutate');
  });
});
'''

if 'describe("WhatsApp permissions final verification V1.3.0"' not in data:
    data = data.rstrip() + final_block + '\n'

write(TARGET, data)

post = read(TARGET)
required_markers = [
    'import { resolveCorePermissionKey } from "./corePermissionPolicy";',
    'describe("WhatsApp permissions final verification V1.3.0"',
    'waGateway.futureUnknownMutation',
    'const canSendWhatsApp = can("whatsapp.send");',
    'const canManageWhatsApp = can("whatsapp.manage");',
    'await evaluatePermission(user, "whatsapp.send")',
    'await evaluatePermission(user, "whatsapp.view", req)',
]
missing = [marker for marker in required_markers if marker not in post]
if missing:
    raise SystemExit(f'POSTCHECK_FAILED={missing}')

tracked_after = set(filter(None, git('diff', '--name-only').splitlines()))
expected = {TARGET}
if tracked_after != expected:
    raise SystemExit(f'POSTCHECK_DIRTY_MISMATCH=expected:{sorted(expected)}:actual:{sorted(tracked_after)}')

print('PATCH_APPLIED=YES')
print('MODULES=whatsapp_final_verification')
print('RUNTIME_SOURCE_CHANGED=NO')
print('TEST_REGRESSION_ONLY=YES')
print(f'FILES_CHANGED={TARGET}')
print('READY_FOR_TESTS=YES')
