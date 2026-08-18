#!/usr/bin/env bash
set -euo pipefail
TARGET=${TCRM_PATH:-/var/www/TCRM-MAIN}
PATCH=ZAGHLOUL_V5R3R5_TSC_SOURCE_FIX_ACCOUNT_PROBE
WORK=/tmp/$PATCH
BACKUP=$WORK/backup
BASELINE=${ZAGHLOUL_V5R3_BASELINE_HEAD:-c7ca52c5bb0495400ed327601d50cf6c7a363c73}
cd "$TARGET"
rm -rf "$WORK"
mkdir -p "$BACKUP"
printf '%s\n' "$BASELINE" > "$WORK/baseline_head"
git rev-parse HEAD > "$WORK/candidate_head.before"

V5=server/services/zaghloul-v5/v5Service.ts
BAD='client/src/pages/zaghloul-v5/automations/[id]/logs/page.tsx'
cp "$V5" "$BACKUP/v5Service.ts.before"

if [ -f "$BAD" ]; then
  if grep -qE 'from ["'"']next/(navigation|router)|from ["'"']next-intl["'"']' "$BAD"; then
    mkdir -p "$BACKUP/$(dirname "$BAD")"
    cp "$BAD" "$BACKUP/$BAD"
    rm -f "$BAD"
    echo MISPLACED_NEXT_PAGE=REMOVED
  else
    echo MISPLACED_NEXT_PAGE=UNEXPECTED_CONTENT
    exit 3
  fi
else
  echo MISPLACED_NEXT_PAGE=ALREADY_ABSENT
fi

python3 - "$V5" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); s=p.read_text()
old='''    total: chats?.total || 0,\n    pagination: {\n      page: input.page || 1,\n      pageSize: input.pageSize || 20,\n      total: chats?.total || 0,\n      totalPages: Math.max(1, Math.ceil((chats?.total || 0) / (input.pageSize || 20))),\n    },\n    counters: {\n      unread: counts?.unread || 0,\n      open: counts?.open || 0,\n      closed: counts?.closed || 0,\n      archived: counts?.archived || 0,\n    },'''
new='''    total: counts?.totalConversations || items.length,\n    pagination: {\n      page: input.page || 1,\n      pageSize: input.pageSize || 20,\n      total: counts?.totalConversations || items.length,\n      totalPages: Math.max(1, Math.ceil((counts?.totalConversations || items.length) / (input.pageSize || 20))),\n    },\n    counters: {\n      unread: counts?.totalUnread || 0,\n      open: items.filter((item) => item.state === "Open").length,\n      closed: items.filter((item) => item.state === "Closed").length,\n      archived: items.filter((item) => item.state === "Archived").length,\n    },'''
if old not in s:
    raise SystemExit('EXPECTED_INBOX_MAPPING_NOT_FOUND')
s=s.replace(old,new,1)
old2='const messages: V5Message[] = (result?.messages || []).map((msg: any) => ({'
new2='const messages: V5Message[] = (result?.items || []).map((msg: any) => ({'
if old2 not in s:
    raise SystemExit('EXPECTED_MESSAGE_MAPPING_NOT_FOUND')
s=s.replace(old2,new2,1)
p.write_text(s)
PY

grep -q 'authMode: "TCRM_SESSION"' "$V5" || { echo AUTH_SOURCE_MARKER=FAIL; exit 4; }
echo APPLY=PASS
