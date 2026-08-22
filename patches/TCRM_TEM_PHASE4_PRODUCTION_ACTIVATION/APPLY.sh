#!/usr/bin/env bash
set -Eeuo pipefail

PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${TCRM_TARGET:-/var/www/TCRM-MAIN}"

bash "$PATCH_DIR/APPLY_CORE.sh"

ACTIVATE="$TARGET/services/tem-mautic/phase4-activate.sh"
[[ -f "$ACTIVATE" ]] || { echo "Phase 4 activation helper missing after core apply" >&2; exit 1; }

ACTIVATE="$ACTIVATE" python3 <<'PY'
from pathlib import Path
import os
p = Path(os.environ["ACTIVATE"])
s = p.read_text()
old = '''  printf '%s' "${line#*=}" | sed -E "s/^[[:space:]]*['\\\"]?(.*?)['\\\"]?[[:space:]]*$/\\1/"\n'''
new = '''  local value="${line#*=}"\n  value="${value#"${value%%[![:space:]]*}"}"\n  value="${value%"${value##*[![:space:]]}"}"\n  if [[ ${#value} -ge 2 ]]; then\n    if [[ "${value:0:1}" == '\"' && "${value: -1}" == '\"' ]]; then value="${value:1:${#value}-2}"; fi\n    if [[ "${value:0:1}" == "'" && "${value: -1}" == "'" ]]; then value="${value:1:${#value}-2}"; fi\n  fi\n  printf '%s' "$value"\n'''
if old not in s:
    if 'local value="${line#*=}"' in s:
        raise SystemExit(0)
    raise SystemExit("runtime env parser anchor not found")
p.write_text(s.replace(old, new, 1))
PY

chmod 0755 "$ACTIVATE"
bash -n "$ACTIVATE"
bash -n "$TARGET/services/tem-mautic/phase4-disable.sh"
bash "$PATCH_DIR/VERIFY.sh"
echo "FINAL_MARKER=TCRM_TEM_PHASE4_PATCH_APPLIED_AND_VERIFIED_OK"
