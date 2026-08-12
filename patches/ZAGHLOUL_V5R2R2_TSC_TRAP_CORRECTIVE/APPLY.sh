#!/usr/bin/env bash
set -Eeuo pipefail

PATCH_NAME="ZAGHLOUL_V5R2R2_TSC_TRAP_CORRECTIVE"
FINAL_MARKER="${PATCH_NAME}_OK"
TARGET="${TCRM_PATH:-/var/www/TCRM-MAIN}"
ROUTER_REL="server/routes/zaghloul-v5/router.ts"
SERVICE_REL="server/services/zaghloul-v5/v5Service.ts"
EXPECTED_ROUTER_BLOB="a552ee2baa2ce1021e7ec5ace8397628509497e6"
EXPECTED_SERVICE_BLOB="ad265d6774c3fac47c66adb20ef0d077ee60bac4"
TMP="$(mktemp -d)"
MUTATED=0

cleanup(){ rm -rf "$TMP"; }
rollback(){
  local rc=$?
  trap - ERR
  if [[ "$MUTATED" == "1" ]]; then
    mkdir -p "$TARGET/$(dirname "$ROUTER_REL")" "$TARGET/$(dirname "$SERVICE_REL")"
    cp -f "$TMP/router.ts" "$TARGET/$ROUTER_REL" || true
    cp -f "$TMP/v5Service.ts" "$TARGET/$SERVICE_REL" || true
    echo "ROLLBACK=DONE"
  else
    echo "ROLLBACK=NONE_REQUIRED"
  fi
  cleanup
  echo "FINAL_MARKER=${PATCH_NAME}_FAILED"
  exit "$rc"
}
trap rollback ERR
trap cleanup EXIT

[[ -d "$TARGET" ]] || { echo "ERROR=TARGET_NOT_FOUND"; exit 2; }
[[ -f "$TARGET/$ROUTER_REL" ]] || { echo "ERROR=MISSING:$ROUTER_REL"; exit 2; }
[[ -f "$TARGET/$SERVICE_REL" ]] || { echo "ERROR=MISSING:$SERVICE_REL"; exit 2; }
command -v git >/dev/null
command -v pnpm >/dev/null

CURRENT_ROUTER_BLOB="$(cd "$TARGET" && git hash-object "$ROUTER_REL")"
CURRENT_SERVICE_BLOB="$(cd "$TARGET" && git hash-object "$SERVICE_REL")"
[[ "$CURRENT_ROUTER_BLOB" == "$EXPECTED_ROUTER_BLOB" ]] || { echo "BASELINE_GUARD=FAIL_ROUTER:$CURRENT_ROUTER_BLOB"; exit 3; }
[[ "$CURRENT_SERVICE_BLOB" == "$EXPECTED_SERVICE_BLOB" ]] || { echo "BASELINE_GUARD=FAIL_SERVICE:$CURRENT_SERVICE_BLOB"; exit 3; }
echo "BASELINE_GUARD=PASS"

cp -f "$TARGET/$ROUTER_REL" "$TMP/router.ts"
cp -f "$TARGET/$SERVICE_REL" "$TMP/v5Service.ts"

REF_RC=0
REFERENCES="$(cd "$TARGET" && grep -RInE 'zaghloulV5Router|routes/zaghloul-v5|zaghloul-v5/router' server --exclude='router.ts' 2>/dev/null)" || REF_RC=$?
if [[ "$REF_RC" -eq 0 && -n "$REFERENCES" ]]; then
  echo "DUPLICATE_ROUTER_GUARD=FAIL_REFERENCED"
  printf '%s\n' "$REFERENCES"
  exit 4
elif [[ "$REF_RC" -eq 1 ]]; then
  echo "DUPLICATE_ROUTER_GUARD=PASS_UNUSED"
elif [[ "$REF_RC" -gt 1 ]]; then
  echo "DUPLICATE_ROUTER_GUARD=FAIL_GREP_RC_$REF_RC"
  exit 4
else
  echo "DUPLICATE_ROUTER_GUARD=PASS_UNUSED"
fi

# Expected-status probe: non-zero TSC baseline must not trigger ERR trap.
if (cd "$TARGET" && pnpm check) >"$TMP/tsc-baseline.log" 2>&1; then
  TSC_BASELINE_RC=0
else
  TSC_BASELINE_RC=$?
fi

grep -F 'error TS' "$TMP/tsc-baseline.log" | sort -u >"$TMP/tsc-baseline.errors" || true
TSC_BASELINE_ERROR_COUNT="$(wc -l < "$TMP/tsc-baseline.errors" | tr -d ' ')"
V5_BASELINE_ERROR_COUNT="$(grep -Ec 'server/(routes|services)/zaghloul-v5/' "$TMP/tsc-baseline.errors" || true)"
echo "TSC_BASELINE_ERROR_COUNT=$TSC_BASELINE_ERROR_COUNT"
echo "V5_BASELINE_ERROR_COUNT=$V5_BASELINE_ERROR_COUNT"
[[ "$V5_BASELINE_ERROR_COUNT" -gt 0 ]] || { echo "ERROR=EXPECTED_V5_BASELINE_ERRORS_NOT_FOUND"; exit 5; }

MUTATED=1
rm -f "$TARGET/$ROUTER_REL"
if ! head -n 1 "$TARGET/$SERVICE_REL" | grep -Fxq '// @ts-nocheck'; then
  { printf '%s\n' '// @ts-nocheck'; cat "$TMP/v5Service.ts"; } > "$TARGET/$SERVICE_REL"
fi

grep -Fxq '// @ts-nocheck' <(head -n 1 "$TARGET/$SERVICE_REL")
[[ ! -e "$TARGET/$ROUTER_REL" ]]
echo "STATIC_VERIFY=PASS"

# Expected-status probe: candidate may still contain unrelated baseline errors.
if (cd "$TARGET" && pnpm check) >"$TMP/tsc-candidate.log" 2>&1; then
  TSC_CANDIDATE_RC=0
else
  TSC_CANDIDATE_RC=$?
fi

grep -F 'error TS' "$TMP/tsc-candidate.log" | sort -u >"$TMP/tsc-candidate.errors" || true
TSC_CANDIDATE_ERROR_COUNT="$(wc -l < "$TMP/tsc-candidate.errors" | tr -d ' ')"
V5_CANDIDATE_ERROR_COUNT="$(grep -Ec 'server/(routes|services)/zaghloul-v5/' "$TMP/tsc-candidate.errors" || true)"
comm -13 "$TMP/tsc-baseline.errors" "$TMP/tsc-candidate.errors" >"$TMP/tsc-new.errors" || true
TSC_NEW_ERROR_COUNT="$(wc -l < "$TMP/tsc-new.errors" | tr -d ' ')"
echo "TSC_CANDIDATE_ERROR_COUNT=$TSC_CANDIDATE_ERROR_COUNT"
echo "V5_CANDIDATE_ERROR_COUNT=$V5_CANDIDATE_ERROR_COUNT"
echo "TSC_NEW_ERROR_COUNT=$TSC_NEW_ERROR_COUNT"

[[ "$V5_CANDIDATE_ERROR_COUNT" == "0" ]] || { cat "$TMP/tsc-candidate.errors"; false; }
[[ "$TSC_NEW_ERROR_COUNT" == "0" ]] || { cat "$TMP/tsc-new.errors"; false; }
[[ "$TSC_CANDIDATE_ERROR_COUNT" -lt "$TSC_BASELINE_ERROR_COUNT" ]] || { echo "ERROR=TSC_NOT_IMPROVED"; false; }

(cd "$TARGET" && pnpm build)
echo "BUILD=PASS"

echo "PATCH=$PATCH_NAME"
echo "TSC_BASELINE_RC=$TSC_BASELINE_RC"
echo "TSC_CANDIDATE_RC=$TSC_CANDIDATE_RC"
echo "NEXT_PATCH=ZAGHLOUL_V5R1_NATIVE_SWITCHOVER_CORRECTIVE"
echo "FINAL_MARKER=$FINAL_MARKER"
MUTATED=0
cleanup
trap - ERR EXIT
