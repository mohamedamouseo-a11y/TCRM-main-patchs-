# Evolution Sync + LID Fix2

Apply on top of current local Fix1 changes. Do not reset/discard.

Fix only these 2 gaps:

1. Historical sync LID resolution
- Do not rely only on message webhooks.
- During Evolution chat/contact/message sync, if the SAME payload/record explicitly contains LID + PN mapping (`remoteJid` + `remoteJidAlt`, `participant` + `participantAlt`, or equivalent same-record evidence), backfill the existing LID chat phone deterministically.
- Never map by suffix/type, LIKE, order, or LIMIT 1.
- No duplicate chat creation.

2. Truncation correctness
- `truncated=true` only when the hard cap stops collection BEFORE remote exhaustion.
- If exactly maxRecords are collected and remote data is exhausted, return `truncated=false`.
- Preserve multi-page exhaustion and hard cap.

Add focused tests for both cases. Run focused tests, build, full tests. No git operations.