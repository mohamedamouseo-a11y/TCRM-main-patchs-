#!/usr/bin/env bash
set -euo pipefail

TARGET="scripts/verify-smart-search-systemwide.mjs"

if [[ ! -f "$TARGET" ]]; then
  echo "ERROR: target file not found: $TARGET" >&2
  exit 2
fi

BEFORE_SHA="$(sha256sum "$TARGET" | awk '{print $1}')"
TMP_FILE="$(mktemp)"
trap 'rm -f "$TMP_FILE"' EXIT
cp "$TARGET" "$TMP_FILE"

python3 - "$TARGET" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
raw = path.read_bytes()

# Preserve the file's existing newline convention and bytes everywhere except
# spaces/tabs immediately before CRLF/LF or EOF.
cleaned = re.sub(rb'[\t ]+(?=\r?\n|\Z)', b'', raw)

if cleaned != raw:
    path.write_bytes(cleaned)
PY

AFTER_SHA="$(sha256sum "$TARGET" | awk '{print $1}')"

if cmp -s "$TMP_FILE" "$TARGET"; then
  echo "NO_CHANGE: no trailing whitespace was present in $TARGET"
else
  # Safety guard: ignoring end-of-line whitespace, the file must be identical.
  if ! diff -u --ignore-space-at-eol "$TMP_FILE" "$TARGET" >/dev/null; then
    echo "ERROR: cleanup changed more than trailing end-of-line whitespace; restoring original file" >&2
    cp "$TMP_FILE" "$TARGET"
    exit 3
  fi
  echo "FIXED: trailing whitespace removed from $TARGET"
fi

echo "BEFORE_SHA256=$BEFORE_SHA"
echo "AFTER_SHA256=$AFTER_SHA"

# Required push-gate validation.
if ! git diff --check; then
  echo "ERROR: git diff --check still reports whitespace errors" >&2
  exit 4
fi

echo "GIT_DIFF_CHECK=PASS"

# Confirm the target has no trailing spaces/tabs anywhere.
if grep -nE '[[:blank:]]+$' "$TARGET"; then
  echo "ERROR: trailing whitespace still exists in $TARGET" >&2
  exit 5
fi

echo "TARGET_TRAILING_WHITESPACE=0"
echo "FINAL_STATUS=PASS"
