#!/usr/bin/env bash
set -Eeuo pipefail

PATCH_NAME="ZAGHLOUL_V5R2R1_RUNTIME_PARITY_VERIFICATION"
TARGET="${TCRM_PATH:-/var/www/TCRM-MAIN}"
WORK="/tmp/${PATCH_NAME}"
EXPECTED_UPSTREAM="6ed9191189e71d2e69d9380422f9415ecc589266"
PARITY="$TARGET/server/services/zaghloul-v5/WACRM_PARITY.json"
UPSTREAM="$TARGET/apps/zaghloul-wacrm/.wacrm-upstream-commit"

fail(){ echo "PREFLIGHT=FAIL:$1"; exit 1; }

[[ -d "$TARGET/.git" ]] || fail TARGET_NOT_GIT_REPO
[[ -f "$PARITY" ]] || fail PARITY_MANIFEST_MISSING
[[ -f "$UPSTREAM" ]] || fail UPSTREAM_PIN_MISSING
[[ "$(tr -d '\r\n' < "$UPSTREAM")" == "$EXPECTED_UPSTREAM" ]] || fail UPSTREAM_PIN_MISMATCH
[[ -d "$TARGET/apps/zaghloul-wacrm" ]] || fail WACRM_SOURCE_MISSING

rm -rf "$WORK"
mkdir -p "$WORK"
chmod 700 "$WORK"

cd "$TARGET"
HEAD_BEFORE="$(git rev-parse HEAD)"
TREE_BEFORE="$(git status --porcelain=v1 --untracked-files=all | sha256sum | awk '{print $1}')"
TRACKED_HASH_BEFORE="$(git ls-files -z | sort -z | xargs -0 sha256sum 2>/dev/null | sha256sum | awk '{print $1}')"

printf '%s\n' "$HEAD_BEFORE" > "$WORK/head.before"
printf '%s\n' "$TREE_BEFORE" > "$WORK/tree.before"
printf '%s\n' "$TRACKED_HASH_BEFORE" > "$WORK/tracked.before"

git status --porcelain=v1 --untracked-files=all > "$WORK/status.before"

node - "$PARITY" > "$WORK/parity.ids" <<'NODE'
const fs=require('fs');
const p=process.argv[2];
const d=JSON.parse(fs.readFileSync(p,'utf8'));
const a=Array.isArray(d)?d:d.features;
if(!Array.isArray(a)||a.length!==15) throw new Error('PARITY_COUNT_NOT_15');
for(const x of a){
  if(x?.status!=='complete') throw new Error(`PARITY_NOT_COMPLETE:${x?.id||'unknown'}`);
  if(!x?.id) throw new Error('PARITY_ID_MISSING');
  console.log(x.id);
}
NODE

EXPECTED_IDS='shared-inbox
contacts-tags-custom-fields-import-dedup
sales-pipelines-kanban-deals
broadcasts-templates-delivery-read-variables
automations-builder-triggers-branches-waits-tags-webhooks
flows-builder-buttons-branches-media
ai-agents-draft-auto-reply-kb-playground-handoff
realtime-dashboard-analytics-activity
team-accounts-roles-invites-ownership
account-management
public-rest-api-api-keys-scopes-rate-limits
outbound-event-webhooks-hmac
mcp-server
chat-actions-reactions-reply-copy
media-persistence-inbound-outbound'
printf '%s\n' "$EXPECTED_IDS" | sort > "$WORK/expected.ids"
sort "$WORK/parity.ids" > "$WORK/parity.sorted"
cmp -s "$WORK/expected.ids" "$WORK/parity.sorted" || fail PARITY_IDS_MISMATCH

cat > "$WORK/README.txt" <<EOF
Temporary verification workspace for $PATCH_NAME.
Do not modify production source to make probes pass.
Runtime harness/results may be created only inside this directory.
Required result file: $WORK/RUNTIME_PARITY_RESULTS.json
EOF

chmod -R go-rwx "$WORK"

echo "PREFLIGHT=PASS"
echo "TARGET_HEAD=$HEAD_BEFORE"
echo "UPSTREAM_PIN=$EXPECTED_UPSTREAM"
echo "PARITY_DECLARED_COUNT=15"
echo "WORKSPACE=$WORK"
echo "SOURCE_MUTATION=NONE"
echo "NEXT=EXECUTE_OPENHANDS_TASK_THEN_VERIFY"
