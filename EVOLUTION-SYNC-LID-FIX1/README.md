# Evolution API WhatsApp Sync + LID Resolution — Fix1

Target source baseline before local unpushed work: `78273711727e834ca88029e39ff0f6ae302d427a`.

This is a correction pass over the local Evolution sync/LID implementation. Do not reset or discard the current local changes.

## Blocking issues to fix before push

### 1. Unsafe LID -> phone backfill
Do NOT associate a `@lid` chat with a PN contact merely because one JID ends with `@lid` and another ends with `@s.whatsapp.net`, and do NOT use `LIMIT 1` to choose a candidate. Suffix/type alone is not identity evidence and can assign the wrong phone number to the wrong conversation.

Backfill is allowed only when the LID and PN identities are explicitly linked by the same Evolution payload/record/event, for example `remoteJid` + `remoteJidAlt`, `participant` + `participantAlt`, or another explicit same-record mapping. Existing stored mappings may be reused only if they were created from such explicit evidence.

If no deterministic mapping exists, leave `phoneNumber` unresolved. Never guess.

### 2. Pagination/truncation
Raising `maxRecords` from 20,000 to 50,000 is not a complete fix for incomplete sync. Preserve a configurable safety cap, but detect when the cap is reached before the remote collection is exhausted and report/return a truncation condition instead of silently treating the sync as complete.

If the Evolution endpoint exposes page/cursor/hasMore/total metadata, continue until exhausted or the configured hard cap. Add a focused test proving a multi-page collection is not dropped and a cap hit is detectable.

## Keep
- Resolve `remoteJidAlt` / `participantAlt` for inbound and outbound messages when the chat is a direct `@lid` chat.
- Never parse a bare `@lid` identifier as a phone number.
- Preserve group/newsletter/broadcast behavior.
- Preserve authorization, session/account ownership, webhook security, audit, Tara and permission wiring.

## Required tests
- Direct PN JID phone extraction.
- Direct LID + `remoteJidAlt`.
- Direct LID + `participantAlt`.
- Outbound LID resolution.
- Deterministic existing LID chat backfill.
- Two different LID chats + two PN contacts cannot cross-map.
- Contact record with PN only and no explicit LID relation must NOT backfill an arbitrary LID chat.
- No duplicate chat after a deterministic LID->PN backfill.
- Groups/newsletters/broadcasts unaffected.
- Multi-page sync reaches subsequent pages.
- Hard cap/truncation is detectable and not reported as a fully completed sync.

Do not commit/push/merge/reset/rebase.