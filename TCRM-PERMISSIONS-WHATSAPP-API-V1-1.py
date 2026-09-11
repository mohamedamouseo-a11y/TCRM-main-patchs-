#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('/var/www/TCRM-MAIN')
BASELINE = 'ad90e63377b5e6e7f5d3a2e023bccc11007d61ba'
PATCH = 'TCRM-PERMISSIONS-WHATSAPP-API-V1-1'


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.exists():
        raise SystemExit(f'MISSING_FILE={rel}')
    return path.read_text(encoding='utf-8')


def write(rel: str, content: str):
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


# Recovery-safe/idempotent application. V1 may already have written both files
# before its static postcheck failed. Do not revert those valid changes.
rel = 'server/security/corePermissionPolicy.ts'
policy = read(rel)
policy = replace_once(
    policy,
    '''function hasAny(value: string, words: readonly string[]) {\n''',
    '''const WA_GATEWAY_VIEW_OPERATIONS = new Set([\n  "getstatus",\n  "listchats",\n  "listchatspage",\n  "getinboxcounts",\n  "getchat",\n  "listgroupparticipants",\n  "listmessages",\n  "listmessagespage",\n  "forwardmessagestatus",\n]);\n\nconst WA_GATEWAY_SEND_OPERATIONS = new Set([\n  "markread",\n  "setchatstate",\n  "setchatpinned",\n  "updatechatrouting",\n  "bulkupdatechats",\n  "sendtext",\n  "forwardmessage",\n  "allowforwardmessageretry",\n  "refreshprofilepicture",\n]);\n\nfunction hasAny(value: string, words: readonly string[]) {\n''',
    'wa_gateway_operation_sets',
)
policy = replace_once(
    policy,
    '''  const module = moduleFromPath(path);\n''',
    '''  // TCRM_PERMISSIONS_WHATSAPP_API_V1\n  // WA Gateway has three distinct permission levels:\n  // - whatsapp.view: passive reads\n  // - whatsapp.send: normal inbox/operator actions and outbound sends\n  // - whatsapp.manage: account/config/admin operations\n  // Unknown future WA Gateway operations fail closed behind manage.\n  if (root === "waGateway") {\n    if (WA_GATEWAY_VIEW_OPERATIONS.has(operation)) return "whatsapp.view";\n    if (WA_GATEWAY_SEND_OPERATIONS.has(operation)) return "whatsapp.send";\n    return "whatsapp.manage";\n  }\n\n  const module = moduleFromPath(path);\n''',
    'wa_gateway_permission_mapping',
)
write(rel, policy)

rel = 'server/security/corePermissionPolicy.test.ts'
test = read(rel)
anchor = '''  it("does not hijack sales contract handover", () => {\n'''
new_test = '''  it("maps WA Gateway reads, operator actions, and management fail-closed", () => {\n    const viewOperations = [\n      "getStatus",\n      "listChats",\n      "listChatsPage",\n      "getInboxCounts",\n      "getChat",\n      "listGroupParticipants",\n      "listMessages",\n      "listMessagesPage",\n      "forwardMessageStatus",\n    ];\n    for (const operation of viewOperations) {\n      expect(resolveCorePermissionKey(`waGateway.${operation}`, "query")).toBe("whatsapp.view");\n    }\n\n    const operatorOperations = [\n      "markRead",\n      "setChatState",\n      "setChatPinned",\n      "updateChatRouting",\n      "bulkUpdateChats",\n      "sendText",\n      "forwardMessage",\n      "allowForwardMessageRetry",\n      "refreshProfilePicture",\n    ];\n    for (const operation of operatorOperations) {\n      expect(resolveCorePermissionKey(`waGateway.${operation}`, "mutation")).toBe("whatsapp.send");\n    }\n\n    expect(resolveCorePermissionKey("waGateway.getSettings", "query")).toBe("whatsapp.manage");\n    expect(resolveCorePermissionKey("waGateway.createAccount", "mutation")).toBe("whatsapp.manage");\n    expect(resolveCorePermissionKey("waGateway.manageCredentials", "mutation")).toBe("whatsapp.manage");\n    expect(resolveCorePermissionKey("waGateway.futureRead", "query")).toBe("whatsapp.manage");\n    expect(resolveCorePermissionKey("waGateway.futureMutation", "mutation")).toBe("whatsapp.manage");\n  });\n\n'''
if 'maps WA Gateway reads, operator actions, and management fail-closed' not in test:
    test = replace_once(test, anchor, new_test + anchor, 'wa_gateway_mapping_test')
write(rel, test)

# Corrected V1.1 postchecks: loop-based tests intentionally contain operation
# names separately rather than literal strings such as waGateway.getStatus.
checks = {
    'server/security/corePermissionPolicy.ts': [
        'TCRM_PERMISSIONS_WHATSAPP_API_V1',
        'const WA_GATEWAY_VIEW_OPERATIONS = new Set([',
        'const WA_GATEWAY_SEND_OPERATIONS = new Set([',
        'if (root === "waGateway")',
        'if (WA_GATEWAY_VIEW_OPERATIONS.has(operation)) return "whatsapp.view";',
        'if (WA_GATEWAY_SEND_OPERATIONS.has(operation)) return "whatsapp.send";',
        'return "whatsapp.manage";',
    ],
    'server/security/corePermissionPolicy.test.ts': [
        'maps WA Gateway reads, operator actions, and management fail-closed',
        '"getStatus"',
        '"sendText"',
        '`waGateway.${operation}`',
        'waGateway.getSettings',
        'waGateway.futureRead',
        'waGateway.futureMutation',
    ],
}
for rel, needles in checks.items():
    data = read(rel)
    missing = [needle for needle in needles if needle not in data]
    if missing:
        raise SystemExit(f'POSTCHECK_FAILED={rel}:{missing}')

print(f'PATCH={PATCH}')
print(f'BASELINE={BASELINE}')
print('RECOVERY_FROM_V1_POSTCHECK_FAILURE=YES')
print('MODULES=whatsapp')
print('WHATSAPP_VIEW_GATE=whatsapp.view')
print('WHATSAPP_SEND_GATE=whatsapp.send')
print('WHATSAPP_OPERATOR_STATE_GATE=whatsapp.send')
print('WHATSAPP_ADMIN_MANAGE_GATE=whatsapp.manage')
print('WHATSAPP_UNKNOWN_OPERATION_FAIL_CLOSED=whatsapp.manage')
print('VIEWER_READ_ONLY_ENFORCED_AT_API=YES')
print('NON_ADMIN_MANAGE_REQUIRED_FOR_OPERATIONAL_ACTIONS=NO')
print('EXISTING_WA_SCOPE_GUARDS_PRESERVED=YES')
print('EXISTING_ADMIN_SUPERADMIN_GUARDS_PRESERVED=YES')
print('ROUTERS_CHANGED=NO')
print('CLIENT_CHANGED=NO')
print('CSS_CHANGED=NO')
print('SERVER_RUNTIME_POLICY_CHANGED=YES')
print('DB_SCHEMA_CHANGED=NO')
print('DATA_CHANGED=NO')
print('FILES_CHANGED=server/security/corePermissionPolicy.ts,server/security/corePermissionPolicy.test.ts')
