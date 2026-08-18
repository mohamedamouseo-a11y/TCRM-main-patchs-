#!/usr/bin/env bash
set -euo pipefail
TARGET=${TCRM_PATH:-/var/www/TCRM-MAIN}
PATCH=ZAGHLOUL_V5R3R2_TSC_LOCATION_NORMALIZATION_ACCOUNT_PROBE
WORK=/tmp/$PATCH
BASELINE=${ZAGHLOUL_V5R3_BASELINE_HEAD:-c7ca52c5bb0495400ed327601d50cf6c7a363c73}
rm -rf "$WORK"
mkdir -p "$WORK"
cd "$TARGET"
git rev-parse --is-inside-work-tree >/dev/null
printf '%s\n' "$BASELINE" > "$WORK/baseline_head"
git rev-parse HEAD > "$WORK/candidate_head"
# Verify baseline object exists; do not mutate source.
git cat-file -e "$BASELINE^{commit}"
# Required account auth source marker must already be present from V5R3R1.
grep -q 'authMode' server/services/zaghloul-v5/v5Service.ts
grep -q 'TCRM_SESSION' server/services/zaghloul-v5/v5Service.ts
# Prepare detached baseline worktree for location-independent tsc comparison.
BASE_WT="$WORK/baseline-worktree"
git worktree add --detach "$BASE_WT" "$BASELINE" >/dev/null
printf 'PRECHECK=PASS\nBASELINE_HEAD=%s\nCANDIDATE_HEAD=%s\n' "$BASELINE" "$(git rev-parse HEAD)"
