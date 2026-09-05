# Evolution Sync LID Fix4

Fix one remaining truncation edge only.

If `maxRecords` is reached **mid-page**, and the current fetched page still contains additional rows after the cap, then `truncated` must be `true` immediately. Do NOT rely only on probing the next page because that can skip unseen rows remaining in the current page and return a false `truncated=false`.

Required behavior:
- cap reached before consuming all rows in current page => `truncated=true`
- cap reached exactly at end of current page => probe next page; empty => false, data => true
- preserve all previous Fix1-Fix3 behavior

Add focused tests for both cases. Run focused tests + build only. No git operations.