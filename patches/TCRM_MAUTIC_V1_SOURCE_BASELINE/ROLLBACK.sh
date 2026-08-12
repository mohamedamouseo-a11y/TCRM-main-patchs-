#!/usr/bin/env bash
set -Eeuo pipefail

PATCH_NAME="TCRM_MAUTIC_V1_SOURCE_BASELINE"
TARGET="${TCRM_PATH:-/var/www/TCRM-MAIN}"
DEST_REL="external/mautic"
DEST="$TARGET/$DEST_REL"
LOCK_FILE="$DEST/TCRM_UPSTREAM.lock"
EXPECTED_COMMIT="27a76aff64aed8e50f6dd784ea86ec95d45d4616"
BASELINE_MANIFEST="$DEST/TCRM_SOURCE_BASELINE.sha256"

fail() { echo "ERROR=$1" >&2; exit "${2:-2}"; }

git -C "$TARGET" rev-parse --is-inside-work-tree >/dev/null 2>&1 || fail "TARGET_NOT_GIT_WORKTREE:$TARGET"
[[ -d "$DEST" ]] || { echo "STATE=ALREADY_ABSENT"; exit 0; }
[[ -f "$LOCK_FILE" ]] || fail "REFUSE_ROLLBACK_NO_LOCK"
grep -Fxq "PATCH=$PATCH_NAME" "$LOCK_FILE" || fail "REFUSE_ROLLBACK_PATCH_MISMATCH"
grep -Fxq "MAUTIC_COMMIT=$EXPECTED_COMMIT" "$LOCK_FILE" || fail "REFUSE_ROLLBACK_COMMIT_MISMATCH"
grep -Fxq "TCRM_STAGE=source-baseline" "$LOCK_FILE" || fail "REFUSE_ROLLBACK_STAGE_CHANGED"
[[ -f "$BASELINE_MANIFEST" ]] || fail "REFUSE_ROLLBACK_BASELINE_MANIFEST_MISSING"
command -v sha256sum >/dev/null || fail "MISSING_COMMAND:sha256sum"
LOCK_MANIFEST_SHA256="$(sed -n 's/^MAUTIC_MANIFEST_SHA256=//p' "$LOCK_FILE" | head -n1)"
[[ "$LOCK_MANIFEST_SHA256" =~ ^[0-9a-f]{64}$ ]] || fail "REFUSE_ROLLBACK_LOCK_MANIFEST_SHA256_INVALID"
ACTUAL_MANIFEST_SHA256="$(sha256sum "$BASELINE_MANIFEST" | awk '{print $1}')"
[[ "$ACTUAL_MANIFEST_SHA256" == "$LOCK_MANIFEST_SHA256" ]] || fail "REFUSE_ROLLBACK_MANIFEST_HASH_MISMATCH"
(cd "$DEST" && sha256sum -c "$(basename "$BASELINE_MANIFEST")" >/dev/null) || fail "REFUSE_ROLLBACK_SOURCE_INTEGRITY_FAILED"

# Refuse to remove the source after later TCRM-Mautic patches have marked it as customized.
[[ ! -e "$DEST/TCRM_CUSTOMIZED.lock" ]] || fail "REFUSE_ROLLBACK_CUSTOMIZED_SOURCE"

command -v python3 >/dev/null || fail "MISSING_COMMAND:python3"
command -v pnpm >/dev/null || fail "MISSING_COMMAND:pnpm"

rm -rf "$DEST"
rmdir "$TARGET/external" 2>/dev/null || true

python3 - "$TARGET/.gitignore" <<'PYROLLBACK'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text()
begin = "# BEGIN TCRM MAUTIC V1 SOURCE"
end = "# END TCRM MAUTIC V1 SOURCE"
if begin in s or end in s:
    if begin not in s or end not in s or s.index(begin) > s.index(end):
        raise SystemExit("Malformed TCRM Mautic gitignore block; refusing rollback")
    start = s.index(begin)
    stop = s.index(end, start) + len(end)
    before = s[:start].rstrip("\n")
    after = s[stop:].lstrip("\n")
    p.write_text(before + "\n" + ("\n" + after if after else ""))
PYROLLBACK

(cd "$TARGET" && pnpm check)
(cd "$TARGET" && pnpm build)

echo "PATCH=$PATCH_NAME"
echo "ROLLBACK=PASS"
echo "FINAL_MARKER=${PATCH_NAME}_ROLLBACK_OK"
