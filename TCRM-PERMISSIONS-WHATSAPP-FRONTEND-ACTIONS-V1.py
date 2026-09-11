#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('/var/www/TCRM-MAIN')
BASELINE = '96e1eb58a2498986a7e0d9b0c80ec5e1ccb9bcef'
PATCH = 'TCRM-PERMISSIONS-WHATSAPP-FRONTEND-ACTIONS-V1'


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


# 1) Expose whatsapp.send to frontend permission consumers.
rel = 'client/src/contexts/PermissionContext.tsx'
data = read(rel)
data = replace_once(
    data,
    '  "whatsapp.view",\n  "whatsapp.manage",\n',
    '  "whatsapp.view",\n  "whatsapp.send",\n  "whatsapp.manage",\n',
    'permission_context_whatsapp_send',
)
write(rel, data)


# 2) Conversation list: keep layout, disable selection for read-only users and hide bulk toolbar.
rel = 'client/src/components/wa/ConversationList.tsx'
data = read(rel)
data = replace_once(
    data,
    '  selectedChatIds: number[];\n  bulkUpdating?: boolean;\n',
    '  selectedChatIds: number[];\n  canOperate?: boolean;\n  bulkUpdating?: boolean;\n',
    'conversation_list_prop',
)
data = replace_once(
    data,
    'export function ConversationList({ chats, selectedChatId, search, filter, loading, loadingMore, hasMore, error, showAccountName, locale, copy, selectedChatIds, bulkUpdating, onSearch, onFilterChange, onSelect, onToggleSelection, onClearSelection, onBulkAction, onLoadMore, onRetry, onRefreshPicture }: Props) {',
    'export function ConversationList({ chats, selectedChatId, search, filter, loading, loadingMore, hasMore, error, showAccountName, locale, copy, selectedChatIds, canOperate = true, bulkUpdating, onSearch, onFilterChange, onSelect, onToggleSelection, onClearSelection, onBulkAction, onLoadMore, onRetry, onRefreshPicture }: Props) {',
    'conversation_list_destructure',
)
data = replace_once(
    data,
    '        {selectedChatIds.length > 0 && (\n',
    '        {canOperate && selectedChatIds.length > 0 && (\n',
    'conversation_list_bulk_toolbar',
)
data = replace_once(
    data,
    '                  <input type="checkbox" checked={selectedForBulk} onChange={() => onToggleSelection(chat.id)} onClick={(event) => event.stopPropagation()} className="absolute start-2 top-1/2 z-20 h-4 w-4 -translate-y-1/2 accent-emerald-600" aria-label={`${copy.selected}: ${label}`} />',
    '                  <input type="checkbox" checked={selectedForBulk} disabled={!canOperate} onChange={() => canOperate && onToggleSelection(chat.id)} onClick={(event) => event.stopPropagation()} className="absolute start-2 top-1/2 z-20 h-4 w-4 -translate-y-1/2 accent-emerald-600 disabled:cursor-not-allowed disabled:opacity-40" aria-label={`${copy.selected}: ${label}`} />',
    'conversation_list_checkbox',
)
write(rel, data)


# 3) Header: gate WhatsApp pin/state actions only; copy + Tara controls remain unchanged.
rel = 'client/src/components/wa/ConversationHeader.tsx'
data = read(rel)
data = replace_once(
    data,
    '  copy: WhatsAppInboxCopy;\n  onBack?: () => void;\n',
    '  copy: WhatsAppInboxCopy;\n  canOperate?: boolean;\n  onBack?: () => void;\n',
    'conversation_header_prop',
)
data = replace_once(
    data,
    'export function ConversationHeader({ chat, account, isRTL, contextVisible, copy, onBack, onToggleContext, onCopyPhone, onSetState, onTogglePin, stateUpdating, pinUpdating, taraContext, taraUpdating, onSetTaraStatus }: Props) {',
    'export function ConversationHeader({ chat, account, isRTL, contextVisible, copy, canOperate = true, onBack, onToggleContext, onCopyPhone, onSetState, onTogglePin, stateUpdating, pinUpdating, taraContext, taraUpdating, onSetTaraStatus }: Props) {',
    'conversation_header_destructure',
)
data = replace_once(
    data,
    '            <DropdownMenuItem disabled={pinUpdating} onClick={onTogglePin}>{chat.pinnedAt ? <PinOff className="h-4 w-4" /> : <Pin className="h-4 w-4" />}{chat.pinnedAt ? copy.unpin : copy.pin}</DropdownMenuItem>\n',
    '            {canOperate && <DropdownMenuItem disabled={pinUpdating} onClick={onTogglePin}>{chat.pinnedAt ? <PinOff className="h-4 w-4" /> : <Pin className="h-4 w-4" />}{chat.pinnedAt ? copy.unpin : copy.pin}</DropdownMenuItem>}\n',
    'conversation_header_pin',
)
data = replace_once(
    data,
    '            {chat.conversationState !== "Open" && <DropdownMenuItem disabled={stateUpdating} onClick={() => onSetState("Open")}><RotateCcw className="h-4 w-4" />{copy.reopen}</DropdownMenuItem>}\n            {chat.conversationState !== "Closed" && <DropdownMenuItem disabled={stateUpdating} onClick={() => onSetState("Closed")}><CheckCircle2 className="h-4 w-4" />{copy.closeConversation}</DropdownMenuItem>}\n            {chat.conversationState !== "Archived" && <DropdownMenuItem disabled={stateUpdating} onClick={() => onSetState("Archived")}><Archive className="h-4 w-4" />{copy.archiveConversation}</DropdownMenuItem>}\n',
    '            {canOperate && chat.conversationState !== "Open" && <DropdownMenuItem disabled={stateUpdating} onClick={() => onSetState("Open")}><RotateCcw className="h-4 w-4" />{copy.reopen}</DropdownMenuItem>}\n            {canOperate && chat.conversationState !== "Closed" && <DropdownMenuItem disabled={stateUpdating} onClick={() => onSetState("Closed")}><CheckCircle2 className="h-4 w-4" />{copy.closeConversation}</DropdownMenuItem>}\n            {canOperate && chat.conversationState !== "Archived" && <DropdownMenuItem disabled={stateUpdating} onClick={() => onSetState("Archived")}><Archive className="h-4 w-4" />{copy.archiveConversation}</DropdownMenuItem>}\n',
    'conversation_header_state',
)
write(rel, data)


# 4) CRM context panel: whatsapp.send is additive to existing account.canManage routing rule.
rel = 'client/src/components/wa/CustomerContextPanel.tsx'
data = read(rel)
data = replace_once(
    data,
    '  copy: WhatsAppInboxCopy;\n  onSaveRouting: (input: { tags: string[]; assignedUserId: number | null }) => void;\n',
    '  copy: WhatsAppInboxCopy;\n  canOperate?: boolean;\n  onSaveRouting: (input: { tags: string[]; assignedUserId: number | null }) => void;\n',
    'customer_context_prop',
)
data = replace_once(
    data,
    'export function CustomerContextPanel({ chat, account, client, lead, clientLoading, leadLoading, clientRestricted, leadRestricted, participants = [], participantsLoading, copy, onSaveRouting, routingUpdating, onOpenClient, onOpenLead }: Props) {',
    'export function CustomerContextPanel({ chat, account, client, lead, clientLoading, leadLoading, clientRestricted, leadRestricted, participants = [], participantsLoading, copy, canOperate = true, onSaveRouting, routingUpdating, onOpenClient, onOpenLead }: Props) {',
    'customer_context_destructure',
)
data = replace_once(
    data,
    '  const canEditRouting = Boolean(account?.canManage);\n',
    '  const canEditRouting = canOperate && Boolean(account?.canManage);\n',
    'customer_context_routing_gate',
)
write(rel, data)


# 5) Timeline: reply/forward are outbound actions; copy/read remains available.
rel = 'client/src/components/wa/MessageTimeline.tsx'
data = read(rel)
data = replace_once(
    data,
    '  copy: WhatsAppInboxCopy;\n  onRefresh: () => void;\n',
    '  copy: WhatsAppInboxCopy;\n  canSendActions?: boolean;\n  onRefresh: () => void;\n',
    'message_timeline_prop',
)
data = replace_once(
    data,
    'export function MessageTimeline({ messages, loading, loadingOlder, hasOlder, error, chatId, locale, isRTL, copy, onRefresh, onLoadOlder, onReply, onForward, onVisibleLatestInbound }: Props) {',
    'export function MessageTimeline({ messages, loading, loadingOlder, hasOlder, error, chatId, locale, isRTL, copy, canSendActions = true, onRefresh, onLoadOlder, onReply, onForward, onVisibleLatestInbound }: Props) {',
    'message_timeline_destructure',
)
data = replace_once(
    data,
    '                    const canForward =\n                      !["Failed", "Pending"].includes(String(message.status || "")) &&\n',
    '                    const canForward =\n                      canSendActions &&\n                      !["Failed", "Pending"].includes(String(message.status || "")) &&\n',
    'message_timeline_forward_gate',
)
data = replace_once(
    data,
    '<div className={cn("absolute -top-2 flex items-center gap-1 opacity-0 transition group-hover:opacity-100 group-focus-within:opacity-100", outbound ? "-start-[6.75rem]" : "-end-[6.75rem]")}><button type="button" onClick={() => onReply(message)} className="rounded-lg bg-white p-1.5 text-slate-500 shadow-md ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-700" aria-label={copy.reply}><Reply className="h-3.5 w-3.5" /></button>{canForward && <button type="button" onClick={() => onForward(message)} className="rounded-lg bg-white p-1.5 text-slate-500 shadow-md ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-700" aria-label={copy.forwardMessage}><Forward className="h-3.5 w-3.5" /></button>}<button type="button" onClick={() => copyMessage(message)} className="rounded-lg bg-white p-1.5 text-slate-500 shadow-md ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-700" aria-label={copy.copy}><Copy className="h-3.5 w-3.5" /></button></div>',
    '<div className={cn("absolute -top-2 flex items-center gap-1 opacity-0 transition group-hover:opacity-100 group-focus-within:opacity-100", outbound ? "-start-[6.75rem]" : "-end-[6.75rem]")}>{canSendActions && <button type="button" onClick={() => onReply(message)} className="rounded-lg bg-white p-1.5 text-slate-500 shadow-md ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-700" aria-label={copy.reply}><Reply className="h-3.5 w-3.5" /></button>}{canForward && <button type="button" onClick={() => onForward(message)} className="rounded-lg bg-white p-1.5 text-slate-500 shadow-md ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-700" aria-label={copy.forwardMessage}><Forward className="h-3.5 w-3.5" /></button>}<button type="button" onClick={() => copyMessage(message)} className="rounded-lg bg-white p-1.5 text-slate-500 shadow-md ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-700" aria-label={copy.copy}><Copy className="h-3.5 w-3.5" /></button></div>',
    'message_timeline_reply_forward_ui',
)
write(rel, data)


# 6) Inbox: consume effective permission and gate every WA operator path.
rel = 'client/src/pages/wa/WAGatewayInbox.tsx'
data = read(rel)
data = replace_once(
    data,
    'import { useLanguage } from "@/contexts/LanguageContext";\n',
    'import { useLanguage } from "@/contexts/LanguageContext";\nimport { usePermissions } from "@/contexts/PermissionContext";\n',
    'inbox_permission_import',
)
data = replace_once(
    data,
    '  const { lang, isRTL } = useLanguage();\n',
    '  const { lang, isRTL } = useLanguage();\n  const { can } = usePermissions();\n',
    'inbox_permission_hook',
)
data = replace_once(
    data,
    '  const isAdmin = isAdminRole(user?.role) && !isTaraModeratorRole(user?.role);\n',
    '  const isAdmin = isAdminRole(user?.role) && !isTaraModeratorRole(user?.role);\n  const canSendWhatsApp = can("whatsapp.send");\n  const canManageWhatsApp = can("whatsapp.manage");\n',
    'inbox_permission_flags',
)
data = replace_once(
    data,
    '  async function submitForward(targetChatIds: number[], clientRequestId: string) {\n    if (!forwardSource) return { failedCount: targetChatIds.length, results: targetChatIds.map((chatId) => ({ chatId, success: false, retryable: false })) };\n',
    '  async function submitForward(targetChatIds: number[], clientRequestId: string) {\n    if (!canSendWhatsApp || !forwardSource) return { failedCount: targetChatIds.length, results: targetChatIds.map((chatId) => ({ chatId, success: false, retryable: false })) };\n',
    'inbox_submit_forward_gate',
)
data = replace_once(
    data,
    '  async function allowUnknownForwardRetry(targetChatIds: number[], clientRequestId: string) {\n    if (!forwardSource) return { failedCount: targetChatIds.length, results: targetChatIds.map((chatId) => ({ chatId, success: false, retryable: false })) };\n',
    '  async function allowUnknownForwardRetry(targetChatIds: number[], clientRequestId: string) {\n    if (!canSendWhatsApp || !forwardSource) return { failedCount: targetChatIds.length, results: targetChatIds.map((chatId) => ({ chatId, success: false, retryable: false })) };\n',
    'inbox_forward_retry_gate',
)
data = replace_once(
    data,
    '  function queueProfilePictureRefresh(chatId: number): Promise<boolean> {\n    if (!Number.isInteger(chatId) || chatId <= 0) return Promise.resolve(false);\n',
    '  function queueProfilePictureRefresh(chatId: number): Promise<boolean> {\n    if (!canSendWhatsApp || !Number.isInteger(chatId) || chatId <= 0) return Promise.resolve(false);\n',
    'inbox_profile_refresh_gate',
)
data = replace_once(
    data,
    '  function markVisibleInboundMessage(messageId: number) {\n    if (typeof document !== "undefined" && document.visibilityState !== "visible") return;\n',
    '  function markVisibleInboundMessage(messageId: number) {\n    if (!canSendWhatsApp) return;\n    if (typeof document !== "undefined" && document.visibilityState !== "visible") return;\n',
    'inbox_mark_read_gate',
)
data = replace_once(
    data,
    '  function send() {\n    if (!selected || !currentDraft.trim() || sendingChatId.current !== null || sendingMessage || !selectedAccountRecord?.connected || Boolean(selected.isReadOnly) || selected.chatType === "Newsletter") return;\n',
    '  function send() {\n    if (!canSendWhatsApp || !selected || !currentDraft.trim() || sendingChatId.current !== null || sendingMessage || !selectedAccountRecord?.connected || Boolean(selected.isReadOnly) || selected.chatType === "Newsletter") return;\n',
    'inbox_send_gate',
)
data = replace_once(
    data,
    '      copy={c}\n      onSaveRouting={(input) => updateChatRouting.mutate({ chatId: selected.id, ...input })}\n',
    '      copy={c}\n      canOperate={canSendWhatsApp}\n      onSaveRouting={(input) => { if (canSendWhatsApp) updateChatRouting.mutate({ chatId: selected.id, ...input }); }}\n',
    'inbox_context_panel_gate',
)
data = replace_once(
    data,
    'onManageAccounts={isAdmin ? () => navigate("/wa-gateway/accounts") : undefined}',
    'onManageAccounts={canManageWhatsApp ? () => navigate("/wa-gateway/accounts") : undefined}',
    'inbox_manage_accounts_gate',
)
data = replace_once(
    data,
    '                    selectedChatIds={bulkSelectedChatIds}\n                    bulkUpdating={bulkUpdateChats.isPending}\n',
    '                    selectedChatIds={bulkSelectedChatIds}\n                    canOperate={canSendWhatsApp}\n                    bulkUpdating={bulkUpdateChats.isPending}\n',
    'inbox_conversation_list_gate',
)
data = replace_once(
    data,
    '                    onToggleSelection={(chatId) => setBulkSelectedChatIds((current) => current.includes(chatId) ? current.filter((id) => id !== chatId) : [...current, chatId].slice(-100))}\n',
    '                    onToggleSelection={(chatId) => { if (canSendWhatsApp) setBulkSelectedChatIds((current) => current.includes(chatId) ? current.filter((id) => id !== chatId) : [...current, chatId].slice(-100)); }}\n',
    'inbox_toggle_selection_gate',
)
data = replace_once(
    data,
    '                    onBulkAction={(action) => bulkSelectedChatIds.length && bulkUpdateChats.mutate({ chatIds: bulkSelectedChatIds, action })}\n',
    '                    onBulkAction={(action) => canSendWhatsApp && bulkSelectedChatIds.length && bulkUpdateChats.mutate({ chatIds: bulkSelectedChatIds, action })}\n',
    'inbox_bulk_action_gate',
)
data = replace_once(
    data,
    '<ConversationHeader chat={selected} account={selectedAccountRecord} isRTL={isRTL} contextVisible={contextVisible} copy={c} onBack={() => setMobileChatOpen(false)} onToggleContext={toggleContext} onCopyPhone={async () => { await navigator.clipboard.writeText(selected.phoneNumber || selected.jid); toast.success(c.copied); }} onSetState={(state) => setChatState.mutate({ chatId: selected.id, state })} onTogglePin={() => setChatPinned.mutate({ chatId: selected.id, pinned: !Boolean(selected.pinnedAt) })}',
    '<ConversationHeader chat={selected} account={selectedAccountRecord} isRTL={isRTL} contextVisible={contextVisible} copy={c} canOperate={canSendWhatsApp} onBack={() => setMobileChatOpen(false)} onToggleContext={toggleContext} onCopyPhone={async () => { await navigator.clipboard.writeText(selected.phoneNumber || selected.jid); toast.success(c.copied); }} onSetState={(state) => { if (canSendWhatsApp) setChatState.mutate({ chatId: selected.id, state }); }} onTogglePin={() => { if (canSendWhatsApp) setChatPinned.mutate({ chatId: selected.id, pinned: !Boolean(selected.pinnedAt) }); }}',
    'inbox_header_gate',
)
data = replace_once(
    data,
    'copy={c} onRefresh={() => messagesQ.refetch()} onLoadOlder={loadOlderMessages} onReply={setReplyTo} onForward={setForwardSource} onVisibleLatestInbound={markVisibleInboundMessage}',
    'copy={c} canSendActions={canSendWhatsApp} onRefresh={() => messagesQ.refetch()} onLoadOlder={loadOlderMessages} onReply={(message) => { if (canSendWhatsApp) setReplyTo(message); }} onForward={(message) => { if (canSendWhatsApp) setForwardSource(message); }} onVisibleLatestInbound={markVisibleInboundMessage}',
    'inbox_timeline_gate',
)
data = replace_once(
    data,
    'disabled={!selectedAccountRecord?.connected || Boolean(selected.isReadOnly) || selected.chatType === "Newsletter"} disabledReason={Boolean(selected.isReadOnly) || selected.chatType === "Newsletter" ? c.readOnly : null}',
    'disabled={!canSendWhatsApp || !selectedAccountRecord?.connected || Boolean(selected.isReadOnly) || selected.chatType === "Newsletter"} disabledReason={!canSendWhatsApp || Boolean(selected.isReadOnly) || selected.chatType === "Newsletter" ? c.readOnly : null}',
    'inbox_composer_gate',
)
data = replace_once(
    data,
    '<ForwardMessageDialog open={Boolean(forwardSource)}',
    '<ForwardMessageDialog open={canSendWhatsApp && Boolean(forwardSource)}',
    'inbox_forward_dialog_gate',
)
write(rel, data)


# Static postchecks: exact permission and UI gates, no server/router/CSS changes.
checks = {
    'client/src/contexts/PermissionContext.tsx': [
        '"whatsapp.view"', '"whatsapp.send"', '"whatsapp.manage"',
    ],
    'client/src/pages/wa/WAGatewayInbox.tsx': [
        'usePermissions', 'can("whatsapp.send")', 'can("whatsapp.manage")',
        'if (!canSendWhatsApp) return;',
        'canOperate={canSendWhatsApp}',
        'canSendActions={canSendWhatsApp}',
        'disabled={!canSendWhatsApp || !selectedAccountRecord?.connected',
        'open={canSendWhatsApp && Boolean(forwardSource)}',
        'onManageAccounts={canManageWhatsApp ?',
    ],
    'client/src/components/wa/ConversationList.tsx': [
        'canOperate?: boolean', 'disabled={!canOperate}', 'canOperate && selectedChatIds.length > 0',
    ],
    'client/src/components/wa/ConversationHeader.tsx': [
        'canOperate?: boolean', 'canOperate && <DropdownMenuItem disabled={pinUpdating}',
        'canOperate && chat.conversationState !== "Closed"',
    ],
    'client/src/components/wa/CustomerContextPanel.tsx': [
        'canOperate?: boolean', 'const canEditRouting = canOperate && Boolean(account?.canManage);',
    ],
    'client/src/components/wa/MessageTimeline.tsx': [
        'canSendActions?: boolean', 'canSendActions &&', '{canSendActions && <button type="button" onClick={() => onReply(message)}',
    ],
}
for rel, needles in checks.items():
    content = read(rel)
    missing = [needle for needle in needles if needle not in content]
    if missing:
        raise SystemExit(f'POSTCHECK_FAILED={rel}:{missing}')

print(f'PATCH={PATCH}')
print(f'BASELINE={BASELINE}')
print('MODULES=whatsapp_frontend')
print('WHATSAPP_SEND_PERMISSION_EXPOSED=YES')
print('INBOX_SEND_ACTIONS_GATE=whatsapp.send')
print('INBOX_MARK_READ_GATE=whatsapp.send')
print('INBOX_STATE_PIN_BULK_GATE=whatsapp.send')
print('INBOX_ROUTING_GATE=whatsapp.send+existing_account_canManage')
print('INBOX_REPLY_FORWARD_GATE=whatsapp.send')
print('INBOX_PROFILE_REFRESH_GATE=whatsapp.send')
print('INBOX_MEDIA_COMPOSER_GATE=whatsapp.send')
print('ACCOUNT_MANAGEMENT_UI_GATE=whatsapp.manage')
print('TARA_CONTROLS_CHANGED=NO')
print('ROUTERS_CHANGED=NO')
print('SERVER_CHANGED=NO')
print('CSS_CHANGED=NO')
print('FRONTEND_VISUAL_STRUCTURE_CHANGED=NO')
print('DB_SCHEMA_CHANGED=NO')
print('DATA_CHANGED=NO')
print('FILES_CHANGED=client/src/contexts/PermissionContext.tsx,client/src/pages/wa/WAGatewayInbox.tsx,client/src/components/wa/ConversationList.tsx,client/src/components/wa/ConversationHeader.tsx,client/src/components/wa/CustomerContextPanel.tsx,client/src/components/wa/MessageTimeline.tsx')
