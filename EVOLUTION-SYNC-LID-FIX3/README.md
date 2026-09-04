# Evolution Sync + LID Fix3

Two correctness fixes only. Apply on top of current local Fix1+Fix2 changes. Do not reset/discard.

1. LID backfill must never overwrite an existing non-null phone. Add `phoneNumber IS NULL` to the update condition (or equivalent) and test it.

2. `lastPageFull` is not enough to prove truncation: an exact-full final page can be remote exhaustion. When the cap is hit, determine whether more remote data actually exists using endpoint metadata (`hasMore`/`next`/`total`) when available, otherwise perform a minimal one-page/one-record probe past the cap without storing beyond the cap. `truncated=true` only if more data is confirmed. Add tests for: exact-full final page => false; exact-full with another page => true.

Keep all existing deterministic LID mapping, auth/security, and unrelated modules unchanged. Focused tests + build + full tests. No git operations.