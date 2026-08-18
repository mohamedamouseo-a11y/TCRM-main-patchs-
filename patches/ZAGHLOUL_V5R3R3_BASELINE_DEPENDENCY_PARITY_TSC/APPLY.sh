#!/usr/bin/env bash
set -euo pipefail
TARGET=${TCRM_PATH:-/var/www/TCRM-MAIN}
PATCH=ZAGHLOUL_V5R3R3_BASELINE_DEPENDENCY_PARITY_TSC
WORK=/tmp/$PATCH
BASELINE=${ZAGHLOUL_V5R3_BASELINE_HEAD:-c7ca52c5bb0495400ed327601d50cf6c7a363c73}
rm -rf "$WORK"
mkdir -p "$WORK"
cd "$TARGET"
git rev-parse --is-inside-work-tree >/dev/null
git cat-file -e "$BASELINE^{commit}"
[ -x node_modules/.bin/tsc ] || { echo LOCAL_TSC=FAIL; exit 2; }
printf '%s\n' "$BASELINE" > "$WORK/baseline_head"
git rev-parse HEAD > "$WORK/candidate_head"
BASE_WT="$WORK/baseline-worktree"
git worktree add --detach "$BASE_WT" "$BASELINE" >/dev/null
for f in package.json pnpm-lock.yaml package-lock.json yarn.lock; do
  if [ -f "$TARGET/$f" ] || [ -f "$BASE_WT/$f" ]; then
    [ -f "$TARGET/$f" ] && [ -f "$BASE_WT/$f" ] || { echo "DEPENDENCY_MANIFEST_MISMATCH=$f"; exit 3; }
    cmp -s "$TARGET/$f" "$BASE_WT/$f" || { echo "DEPENDENCY_MANIFEST_MISMATCH=$f"; exit 3; }
  fi
done
ln -s "$TARGET/node_modules" "$BASE_WT/node_modules"
printf 'PRECHECK=PASS\nBASELINE_HEAD=%s\nCANDIDATE_HEAD=%s\n' "$BASELINE" "$(git rev-parse HEAD)"
