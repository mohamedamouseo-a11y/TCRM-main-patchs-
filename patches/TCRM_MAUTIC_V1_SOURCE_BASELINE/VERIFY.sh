#!/usr/bin/env bash
set -Eeuo pipefail

PATCH_NAME="TCRM_MAUTIC_V1_SOURCE_BASELINE"
TARGET="${TCRM_PATH:-/var/www/TCRM-MAIN}"
DEST_REL="external/mautic"
DEST="$TARGET/$DEST_REL"
EXPECTED_VERSION="7.1.2"
EXPECTED_COMMIT="789364ee4aaf8aef5e6d91642336c1f446d5521b"
LOCK_FILE="$DEST/TCRM_UPSTREAM.lock"
BASELINE_MANIFEST="$DEST/TCRM_SOURCE_BASELINE.sha256"

fail() { echo "ERROR=$1" >&2; exit "${2:-2}"; }
version_ge() {
  local have="$1" need="$2"
  [[ "$(printf '%s\n%s\n' "$need" "$have" | sort -V | head -n1)" == "$need" ]]
}
version_le() {
  local have="$1" max="$2"
  [[ "$(printf '%s\n%s\n' "$have" "$max" | sort -V | tail -n1)" == "$max" ]]
}

git -C "$TARGET" rev-parse --is-inside-work-tree >/dev/null 2>&1 || fail "TARGET_NOT_GIT_WORKTREE:$TARGET"
[[ -d "$DEST" ]] || fail "MAUTIC_SOURCE_MISSING:$DEST"
[[ -f "$LOCK_FILE" ]] || fail "UPSTREAM_LOCK_MISSING"
[[ ! -e "$DEST/.git" ]] || fail "NESTED_GIT_METADATA_PRESENT"

grep -Fxq "PATCH=$PATCH_NAME" "$LOCK_FILE" || fail "LOCK_PATCH_MISMATCH"
grep -Fxq "MAUTIC_VERSION=$EXPECTED_VERSION" "$LOCK_FILE" || fail "LOCK_VERSION_MISMATCH"
grep -Fxq "MAUTIC_COMMIT=$EXPECTED_COMMIT" "$LOCK_FILE" || fail "LOCK_COMMIT_MISMATCH"
grep -Fxq "MAUTIC_LICENSE=GPL-3.0" "$LOCK_FILE" || fail "LOCK_LICENSE_MISMATCH"
grep -Fxq "TCRM_STAGE=source-baseline" "$LOCK_FILE" || fail "LOCK_STAGE_MISMATCH"
[[ ! -e "$DEST/TCRM_CUSTOMIZED.lock" ]] || fail "SOURCE_ALREADY_CUSTOMIZED_USE_LATER_PATCH_VERIFY"

command -v php >/dev/null || fail "MISSING_COMMAND:php"
command -v composer >/dev/null || fail "MISSING_COMMAND:composer"
command -v pnpm >/dev/null || fail "MISSING_COMMAND:pnpm"
command -v sha256sum >/dev/null || fail "MISSING_COMMAND:sha256sum"

[[ -f "$BASELINE_MANIFEST" ]] || fail "BASELINE_MANIFEST_MISSING"
LOCK_MANIFEST_SHA256="$(sed -n 's/^MAUTIC_MANIFEST_SHA256=//p' "$LOCK_FILE" | head -n1)"
[[ "$LOCK_MANIFEST_SHA256" =~ ^[0-9a-f]{64}$ ]] || fail "LOCK_MANIFEST_SHA256_INVALID"
ACTUAL_MANIFEST_SHA256="$(sha256sum "$BASELINE_MANIFEST" | awk '{print $1}')"
[[ "$ACTUAL_MANIFEST_SHA256" == "$LOCK_MANIFEST_SHA256" ]] || fail "BASELINE_MANIFEST_HASH_MISMATCH"
(cd "$DEST" && sha256sum -c "$(basename "$BASELINE_MANIFEST")" >/dev/null) || fail "BASELINE_SOURCE_INTEGRITY_FAILED"
PHP_VERSION="$(php -r 'echo PHP_MAJOR_VERSION.".".PHP_MINOR_VERSION.".".PHP_RELEASE_VERSION;')"
version_ge "$PHP_VERSION" "8.2.0" || fail "PHP_TOO_OLD:$PHP_VERSION"
version_le "$PHP_VERSION" "8.5.99" || fail "PHP_UNSUPPORTED_NEWER_THAN_8_5:$PHP_VERSION"
PHP_MODULES="$(php -m | tr '[:upper:]' '[:lower:]')"
REQUIRED_PHP_EXTENSIONS=(xml imap zip intl curl gd mbstring bcmath)
for ext in "${REQUIRED_PHP_EXTENSIONS[@]}"; do
  grep -Fxq "${ext,,}" <<<"$PHP_MODULES" || fail "MISSING_PHP_EXTENSION:$ext"
done
if ! grep -Eq '^(mysqli|pdo_mysql)$' <<<"$PHP_MODULES"; then
  fail "MISSING_PHP_MYSQL_EXTENSION:mysqli_or_pdo_mysql"
fi

[[ -f "$DEST/composer.json" ]] || fail "MISSING_MAUTIC_COMPOSER_JSON"
[[ -f "$DEST/package.json" ]] || fail "MISSING_MAUTIC_PACKAGE_JSON"
grep -Eq '"license"[[:space:]]*:[[:space:]]*"GPL-3\.0"' "$DEST/composer.json" || fail "LICENSE_METADATA_MISMATCH"
(cd "$DEST" && composer validate --no-check-publish --no-interaction >/dev/null)

grep -Fxq "# BEGIN TCRM MAUTIC V1 SOURCE" "$TARGET/.gitignore" || fail "TCRM_GITIGNORE_MAUTIC_BLOCK_MISSING"
grep -Fxq "!external/mautic/**" "$TARGET/.gitignore" || fail "TCRM_GITIGNORE_MAUTIC_UNIGNORE_MISSING"
grep -Fxq "# END TCRM MAUTIC V1 SOURCE" "$TARGET/.gitignore" || fail "TCRM_GITIGNORE_MAUTIC_BLOCK_INCOMPLETE"

if (cd "$TARGET" && git check-ignore -q "$DEST_REL/composer.json"); then
  fail "MAUTIC_SOURCE_IS_GIT_IGNORED"
fi
(cd "$TARGET" && git check-ignore -q --no-index "$DEST_REL/vendor/__tcrm_probe__") || fail "MAUTIC_VENDOR_NOT_IGNORED"
(cd "$TARGET" && git check-ignore -q --no-index "$DEST_REL/node_modules/__tcrm_probe__") || fail "MAUTIC_NODE_MODULES_NOT_IGNORED"

(cd "$TARGET" && pnpm check)
(cd "$TARGET" && pnpm build)

if ! (cd "$TARGET" && git diff --quiet -- . ':(exclude).gitignore'); then
  fail "UNEXPECTED_TRACKED_CHANGE_OUTSIDE_GITIGNORE"
fi
UNEXPECTED_UNTRACKED="$(cd "$TARGET" && git ls-files --others --exclude-standard | grep -vE '^external/mautic/' || true)"
[[ -z "$UNEXPECTED_UNTRACKED" ]] || fail "UNEXPECTED_UNTRACKED_FILES_OUTSIDE_MAUTIC"

echo "PATCH=$PATCH_NAME"
echo "SOURCE_PRESENT=YES"
echo "MAUTIC_VERSION=$EXPECTED_VERSION"
echo "MAUTIC_COMMIT=$EXPECTED_COMMIT"
echo "PHP_VERSION=$PHP_VERSION"
echo "RUNTIME_ACTIVATED=NO"
echo "VERIFY=PASS"
echo "FINAL_MARKER=${PATCH_NAME}_VERIFY_OK"
