#!/usr/bin/env bash
set -Eeuo pipefail

PATCH_NAME="TCRM_MAUTIC_V1_SOURCE_BASELINE"
FINAL_MARKER="${PATCH_NAME}_OK"
TARGET="${TCRM_PATH:-/var/www/TCRM-MAIN}"
DEST_REL="external/mautic"
DEST="$TARGET/$DEST_REL"
UPSTREAM_REPO="https://github.com/mautic/mautic.git"
UPSTREAM_TAG="7.1.2"
EXPECTED_COMMIT="789364ee4aaf8aef5e6d91642336c1f446d5521b"
LOCK_FILE="TCRM_UPSTREAM.lock"
BASELINE_MANIFEST="TCRM_SOURCE_BASELINE.sha256"
EXPECTED_TCRM_GITIGNORE_BLOB="a01582cdcb61e9e117d10aa0f53d4b18e472d8c9"
GITIGNORE_BEGIN="# BEGIN TCRM MAUTIC V1 SOURCE"
GITIGNORE_END="# END TCRM MAUTIC V1 SOURCE"
TMP="$(mktemp -d)"
MUTATED=0

cleanup() {
  rm -rf "$TMP"
}

rollback() {
  local rc=$?
  trap - ERR
  if [[ "$MUTATED" == "1" ]]; then
    [[ -d "$DEST" ]] && rm -rf "$DEST"
    rmdir "$TARGET/external" 2>/dev/null || true
    if [[ -f "$TMP/tcrm.gitignore" ]]; then
      cp -f "$TMP/tcrm.gitignore" "$TARGET/.gitignore"
    fi
    if git -C "$TARGET" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
      git -C "$TARGET" restore --worktree -- . 2>/dev/null || true
    fi
    echo "ROLLBACK=DONE"
  fi
  cleanup
  echo "FINAL_MARKER=${PATCH_NAME}_FAILED"
  exit "$rc"
}

trap rollback ERR
trap cleanup EXIT

fail() {
  echo "ERROR=$1" >&2
  exit "${2:-2}"
}

version_ge() {
  local have="$1" need="$2"
  [[ "$(printf '%s\n%s\n' "$need" "$have" | sort -V | head -n1)" == "$need" ]]
}

version_le() {
  local have="$1" max="$2"
  [[ "$(printf '%s\n%s\n' "$have" "$max" | sort -V | tail -n1)" == "$max" ]]
}

[[ -d "$TARGET" ]] || fail "TARGET_NOT_FOUND:$TARGET"
git -C "$TARGET" rev-parse --is-inside-work-tree >/dev/null 2>&1 || fail "TARGET_NOT_GIT_WORKTREE:$TARGET"
command -v git >/dev/null || fail "MISSING_COMMAND:git"
command -v pnpm >/dev/null || fail "MISSING_COMMAND:pnpm"
command -v php >/dev/null || fail "MISSING_COMMAND:php"
command -v composer >/dev/null || fail "MISSING_COMMAND:composer"
command -v node >/dev/null || fail "MISSING_COMMAND:node"
command -v npm >/dev/null || fail "MISSING_COMMAND:npm"
command -v sha256sum >/dev/null || fail "MISSING_COMMAND:sha256sum"
command -v xargs >/dev/null || fail "MISSING_COMMAND:xargs"

PHP_VERSION="$(php -r 'echo PHP_MAJOR_VERSION.".".PHP_MINOR_VERSION.".".PHP_RELEASE_VERSION;')"
version_ge "$PHP_VERSION" "8.2.0" || fail "PHP_TOO_OLD:$PHP_VERSION:NEED_8.2+"
version_le "$PHP_VERSION" "8.5.99" || fail "PHP_UNSUPPORTED_NEWER_THAN_8_5:$PHP_VERSION"
echo "PHP_VERSION=$PHP_VERSION"

PHP_MODULES="$(php -m | tr '[:upper:]' '[:lower:]')"
REQUIRED_PHP_EXTENSIONS=(xml imap zip intl curl gd mbstring bcmath)
for ext in "${REQUIRED_PHP_EXTENSIONS[@]}"; do
  grep -Fxq "${ext,,}" <<<"$PHP_MODULES" || fail "MISSING_PHP_EXTENSION:$ext"
done
if ! grep -Eq '^(mysqli|pdo_mysql)$' <<<"$PHP_MODULES"; then
  fail "MISSING_PHP_MYSQL_EXTENSION:mysqli_or_pdo_mysql"
fi
echo "PHP_EXTENSIONS=PASS"

echo "COMPOSER_VERSION=$(composer --version --no-ansi 2>/dev/null | head -n1)"
echo "NODE_VERSION=$(node --version)"
echo "NPM_VERSION=$(npm --version)"

FREE_KB="$(df -Pk "$TARGET" | awk 'NR==2 {print $4}')"
[[ "$FREE_KB" =~ ^[0-9]+$ ]] || fail "DISK_CHECK_FAILED"
(( FREE_KB >= 1048576 )) || fail "INSUFFICIENT_DISK_SPACE_KB:$FREE_KB:NEED_AT_LEAST_1048576"
echo "DISK_FREE_KB=$FREE_KB"

if [[ -e "$DEST" ]]; then
  [[ -f "$DEST/$LOCK_FILE" ]] || fail "DESTINATION_ALREADY_EXISTS_WITHOUT_LOCK:$DEST"
  grep -Fxq "PATCH=$PATCH_NAME" "$DEST/$LOCK_FILE" || fail "EXISTING_LOCK_PATCH_MISMATCH"
  grep -Fxq "MAUTIC_VERSION=$UPSTREAM_TAG" "$DEST/$LOCK_FILE" || fail "EXISTING_LOCK_VERSION_MISMATCH"
  grep -Fxq "MAUTIC_COMMIT=$EXPECTED_COMMIT" "$DEST/$LOCK_FILE" || fail "EXISTING_LOCK_COMMIT_MISMATCH"
  [[ ! -e "$DEST/TCRM_CUSTOMIZED.lock" ]] || fail "SOURCE_ALREADY_CUSTOMIZED_USE_LATER_PATCH_VERIFY"
  [[ -f "$DEST/$BASELINE_MANIFEST" ]] || fail "BASELINE_MANIFEST_MISSING"
  LOCK_MANIFEST_SHA256="$(sed -n 's/^MAUTIC_MANIFEST_SHA256=//p' "$DEST/$LOCK_FILE" | head -n1)"
  [[ "$LOCK_MANIFEST_SHA256" =~ ^[0-9a-f]{64}$ ]] || fail "LOCK_MANIFEST_SHA256_INVALID"
  ACTUAL_MANIFEST_SHA256="$(sha256sum "$DEST/$BASELINE_MANIFEST" | awk '{print $1}')"
  [[ "$ACTUAL_MANIFEST_SHA256" == "$LOCK_MANIFEST_SHA256" ]] || fail "BASELINE_MANIFEST_HASH_MISMATCH"
  (cd "$DEST" && sha256sum -c "$BASELINE_MANIFEST" >/dev/null) || fail "BASELINE_SOURCE_INTEGRITY_FAILED"
  grep -Fxq "$GITIGNORE_BEGIN" "$TARGET/.gitignore" || fail "GITIGNORE_BLOCK_MISSING_ON_EXISTING_INSTALL"
  grep -Fxq "!external/mautic/**" "$TARGET/.gitignore" || fail "GITIGNORE_UNIGNORE_MISSING_ON_EXISTING_INSTALL"
  grep -Fxq "$GITIGNORE_END" "$TARGET/.gitignore" || fail "GITIGNORE_BLOCK_INCOMPLETE_ON_EXISTING_INSTALL"
  (cd "$DEST" && composer validate --no-check-publish --no-interaction >/dev/null)
  (cd "$TARGET" && pnpm check)
  (cd "$TARGET" && pnpm build)
  echo "PATCH=$PATCH_NAME"
  echo "STATE=ALREADY_APPLIED_VERIFIED"
  echo "FINAL_MARKER=$FINAL_MARKER"
  exit 0
fi

GIT_STATUS="$(cd "$TARGET" && git status --porcelain=v1)"
[[ -z "$GIT_STATUS" ]] || {
  printf '%s\n' "$GIT_STATUS"
  fail "TCRM_WORKTREE_NOT_CLEAN"
}
echo "TCRM_WORKTREE=PASS_CLEAN"

[[ -f "$TARGET/.gitignore" ]] || fail "MISSING_TCRM_GITIGNORE"
CURRENT_GITIGNORE_BLOB="$(cd "$TARGET" && git hash-object .gitignore)"
[[ "$CURRENT_GITIGNORE_BLOB" == "$EXPECTED_TCRM_GITIGNORE_BLOB" ]] || fail "TCRM_GITIGNORE_BASELINE_MISMATCH:$CURRENT_GITIGNORE_BLOB"
cp -f "$TARGET/.gitignore" "$TMP/tcrm.gitignore"

[[ -f "$TARGET/package.json" ]] || fail "MISSING_TCRM_PACKAGE_JSON"
[[ -f "$TARGET/pnpm-lock.yaml" ]] || fail "MISSING_TCRM_PNPM_LOCK"

# Production baseline must already be healthy before any mutation.
(cd "$TARGET" && pnpm check)
echo "TCRM_BASELINE_TYPECHECK=PASS"
(cd "$TARGET" && pnpm build)
echo "TCRM_BASELINE_BUILD=PASS"

# Baseline checks themselves must not dirty tracked/untracked source state.
POST_BASELINE_STATUS="$(cd "$TARGET" && git status --porcelain=v1 --untracked-files=all)"
[[ -z "$POST_BASELINE_STATUS" ]] || {
  printf '%s\n' "$POST_BASELINE_STATUS"
  fail "TCRM_BASELINE_CHECKS_DIRTIED_WORKTREE"
}
echo "TCRM_BASELINE_POST_BUILD_WORKTREE=PASS_CLEAN"

# Import only the exact upstream security release and verify its immutable commit.
git clone --quiet --depth 1 --branch "$UPSTREAM_TAG" "$UPSTREAM_REPO" "$TMP/mautic"
ACTUAL_COMMIT="$(git -C "$TMP/mautic" rev-parse HEAD)"
[[ "$ACTUAL_COMMIT" == "$EXPECTED_COMMIT" ]] || fail "UPSTREAM_COMMIT_MISMATCH:$ACTUAL_COMMIT"
[[ -z "$(git -C "$TMP/mautic" status --porcelain=v1)" ]] || fail "UPSTREAM_CLONE_NOT_CLEAN"
git -C "$TMP/mautic" ls-files > "$TMP/upstream-files.txt"
[[ -s "$TMP/upstream-files.txt" ]] || fail "UPSTREAM_TRACKED_FILE_LIST_EMPTY"
echo "UPSTREAM_TRACKED_FILES=$(wc -l < "$TMP/upstream-files.txt" | tr -d " ")"
echo "UPSTREAM_COMMIT=PASS:$ACTUAL_COMMIT"

# Immutable content manifest for every upstream-tracked source file.
(cd "$TMP/mautic" && git ls-files -z | LC_ALL=C sort -z | xargs -0 sha256sum -- > "$BASELINE_MANIFEST")
[[ -s "$TMP/mautic/$BASELINE_MANIFEST" ]] || fail "BASELINE_MANIFEST_EMPTY"
(cd "$TMP/mautic" && sha256sum -c "$BASELINE_MANIFEST" >/dev/null) || fail "BASELINE_MANIFEST_SELF_CHECK_FAILED"
BASELINE_MANIFEST_SHA256="$(sha256sum "$TMP/mautic/$BASELINE_MANIFEST" | awk '{print $1}')"
echo "BASELINE_MANIFEST_SHA256=$BASELINE_MANIFEST_SHA256"

[[ -f "$TMP/mautic/LICENSE.txt" || -f "$TMP/mautic/LICENSE" ]] || fail "UPSTREAM_LICENSE_FILE_MISSING"
grep -Eq '"license"[[:space:]]*:[[:space:]]*"GPL-3\.0"' "$TMP/mautic/composer.json" || fail "UPSTREAM_LICENSE_METADATA_MISMATCH"
(cd "$TMP/mautic" && composer validate --no-check-publish --no-interaction >/dev/null)
echo "MAUTIC_COMPOSER_VALIDATE=PASS"

# Remove nested VCS metadata so TCRM's parent repository can track the imported source.
rm -rf "$TMP/mautic/.git"
cat > "$TMP/mautic/$LOCK_FILE" <<LOCK
PATCH=$PATCH_NAME
MAUTIC_VERSION=$UPSTREAM_TAG
MAUTIC_COMMIT=$EXPECTED_COMMIT
MAUTIC_UPSTREAM=$UPSTREAM_REPO
MAUTIC_LICENSE=GPL-3.0
MAUTIC_MANIFEST_SHA256=$BASELINE_MANIFEST_SHA256
TCRM_STAGE=source-baseline
LOCK

cat >> "$TARGET/.gitignore" <<GITIGNORE

$GITIGNORE_BEGIN
!external/
!external/mautic/
!external/mautic/**
$GITIGNORE_END
GITIGNORE
MUTATED=1

mkdir -p "$TARGET/external"
mv "$TMP/mautic" "$DEST"

[[ -f "$DEST/composer.json" ]] || fail "IMPORT_MISSING_COMPOSER_JSON"
[[ -f "$DEST/package.json" ]] || fail "IMPORT_MISSING_PACKAGE_JSON"
[[ ! -e "$DEST/.git" ]] || fail "NESTED_GIT_METADATA_PRESENT"
grep -Fxq "MAUTIC_COMMIT=$EXPECTED_COMMIT" "$DEST/$LOCK_FILE" || fail "UPSTREAM_LOCK_INVALID"
[[ -f "$DEST/$BASELINE_MANIFEST" ]] || fail "IMPORTED_BASELINE_MANIFEST_MISSING"
(cd "$DEST" && sha256sum -c "$BASELINE_MANIFEST" >/dev/null) || fail "IMPORTED_SOURCE_INTEGRITY_FAILED"

if (cd "$TARGET" && git check-ignore -q "$DEST_REL/composer.json"); then
  fail "IMPORTED_SOURCE_IS_GIT_IGNORED"
fi

# Every file tracked by upstream must remain trackable from the parent TCRM repository.
sed "s#^#$DEST_REL/#" "$TMP/upstream-files.txt" > "$TMP/tcrm-upstream-paths.txt"
set +e
(cd "$TARGET" && git check-ignore --stdin < "$TMP/tcrm-upstream-paths.txt") > "$TMP/ignored-upstream.txt"
CHECK_IGNORE_RC=$?
set -e
if [[ $CHECK_IGNORE_RC -eq 0 && -s "$TMP/ignored-upstream.txt" ]]; then
  cat "$TMP/ignored-upstream.txt"
  fail "UPSTREAM_TRACKED_FILES_IGNORED_BY_TCRM"
fi
[[ $CHECK_IGNORE_RC -eq 1 ]] || fail "GIT_CHECK_IGNORE_FAILED:$CHECK_IGNORE_RC"
echo "UPSTREAM_TRACKED_FILES_VISIBLE=PASS"

# Runtime dependency directories must still stay ignored by Mautic's own .gitignore.
(cd "$TARGET" && git check-ignore -q --no-index "$DEST_REL/vendor/__tcrm_probe__") || fail "MAUTIC_VENDOR_NOT_IGNORED"
(cd "$TARGET" && git check-ignore -q --no-index "$DEST_REL/node_modules/__tcrm_probe__") || fail "MAUTIC_NODE_MODULES_NOT_IGNORED"

TRACKABLE_COUNT="$(cd "$TARGET" && git status --porcelain=v1 -- "$DEST_REL" | wc -l | tr -d ' ')"
(( TRACKABLE_COUNT > 0 )) || fail "IMPORTED_SOURCE_NOT_VISIBLE_TO_TCRM_GIT"
echo "TRACKABLE_STATUS_ENTRIES=$TRACKABLE_COUNT"

# Re-run TCRM gates after mutation. The imported PHP source must not regress TCRM.
(cd "$TARGET" && pnpm check)
echo "TCRM_CANDIDATE_TYPECHECK=PASS"
(cd "$TARGET" && pnpm build)
echo "TCRM_CANDIDATE_BUILD=PASS"

# Candidate checks may only leave the bounded .gitignore change and imported source.
if ! (cd "$TARGET" && git diff --quiet -- . ':(exclude).gitignore'); then
  fail "UNEXPECTED_TRACKED_CHANGE_OUTSIDE_GITIGNORE"
fi
UNEXPECTED_UNTRACKED="$(cd "$TARGET" && git ls-files --others --exclude-standard | grep -vE '^external/mautic/' || true)"
[[ -z "$UNEXPECTED_UNTRACKED" ]] || {
  printf '%s\n' "$UNEXPECTED_UNTRACKED"
  fail "UNEXPECTED_UNTRACKED_FILES_OUTSIDE_MAUTIC"
}
EXPECTED_GITIGNORE="$TMP/expected.gitignore"
cat "$TMP/tcrm.gitignore" > "$EXPECTED_GITIGNORE"
cat >> "$EXPECTED_GITIGNORE" <<GITIGNORE_EXPECTED

$GITIGNORE_BEGIN
!external/
!external/mautic/
!external/mautic/**
$GITIGNORE_END
GITIGNORE_EXPECTED
cmp -s "$EXPECTED_GITIGNORE" "$TARGET/.gitignore" || fail "TCRM_GITIGNORE_UNEXPECTED_CONTENT"
echo "TCRM_CANDIDATE_CHANGE_SCOPE=PASS"

# Lightweight source integrity checks; no DB, service, Nginx, cron, or mail changes occur here.
(cd "$DEST" && composer validate --no-check-publish --no-interaction >/dev/null)
php -r '$j=json_decode(file_get_contents($argv[1]), true, 512, JSON_THROW_ON_ERROR); if (($j["license"] ?? null) !== "GPL-3.0") { exit(2); }' "$DEST/composer.json"
echo "MAUTIC_SOURCE_VERIFY=PASS"

echo "PATCH=$PATCH_NAME"
echo "MAUTIC_VERSION=$UPSTREAM_TAG"
echo "MAUTIC_COMMIT=$EXPECTED_COMMIT"
echo "DESTINATION=$DEST"
echo "RUNTIME_ACTIVATED=NO"
echo "DB_CHANGED=NO"
echo "WEB_SERVER_CHANGED=NO"
echo "FINAL_MARKER=$FINAL_MARKER"

MUTATED=0
cleanup
trap - ERR EXIT
