#!/usr/bin/env python3
# TCRM_DEVELOPER_HUB_TRUSTED_SQL_SYNC_BOOTSTRAP_V1

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

EXPECTED_HEAD = "90b1d4573626e0fad4c7629df1b062e939099e7e"
TARGET = Path("server/services/developerHubGitHubSecurity.ts")
MARKER = "TCRM_DEVELOPER_HUB_TRUSTED_SQL_SYNC_BOOTSTRAP_V1"

OLD_HELPER_ANCHOR = '''function isBackupFeatureSourceName(base: string) {
  return /(?:^|[._-])backup(?:[._-]|$)/i.test(base);
}
'''

NEW_HELPER = '''function isBackupFeatureSourceName(base: string) {
  return /(?:^|[._-])backup(?:[._-]|$)/i.test(base);
}

function isTrustedSourceFilePath(filePath: string) {
  const normalized = String(filePath || "").replace(/\\\\/g, "/").replace(/^\\.\\//, "");
  const segments = normalized.toLowerCase().split("/").filter(Boolean);
  if (segments.length < 2 || !TRUSTED_SOURCE_ROOTS.has(segments[0])) return false;
  return TRUSTED_SOURCE_EXTENSIONS.test(path.posix.basename(normalized));
}
'''

OLD_CONTEXT = '''  const segments = lower.split("/").filter(Boolean);
  const directorySegments = segments.slice(0, -1);

  if (segments.length > 1 && isGeneratedPatchPackageRoot(segments[0])) {'''

NEW_CONTEXT = '''  const segments = lower.split("/").filter(Boolean);
  const directorySegments = segments.slice(0, -1);
  const trustedSource = isTrustedSourceFilePath(normalized);

  if (segments.length > 1 && isGeneratedPatchPackageRoot(segments[0])) {'''

OLD_SQL_BLOCK = '''  if (/\\.(pem|key|p12|pfx|ppk|jks|keystore|sqlite|sqlite3|db|dump|sql|zip|7z|rar|tar|tgz|gz)$/i.test(base)) {
    return "blocked secret, database, or archive file";
  }'''

NEW_SQL_BLOCK = '''  if (/\\.(pem|key|p12|pfx|ppk|jks|keystore|sqlite|sqlite3|db|dump|sql|zip|7z|rar|tar|tgz|gz)$/i.test(base)) {
    if (!(base.endsWith(".sql") && trustedSource)) return "blocked secret, database, or archive file";
  }'''


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def fail(message: str) -> None:
    print(f"ERROR={message}")
    raise SystemExit(1)


def read_text() -> str:
    if not TARGET.is_file():
        fail(f"missing {TARGET}")
    return TARGET.read_text(encoding="utf-8")


def ensure_repo_guard() -> None:
    try:
        root = Path(git("rev-parse", "--show-toplevel")).resolve()
        head = git("rev-parse", "HEAD")
        branch = git("branch", "--show-current")
    except Exception as exc:
        fail(f"git preflight failed: {exc}")
    if Path.cwd().resolve() != root:
        fail("run from repository root")
    if branch != "main":
        fail(f"expected main branch, got {branch}")
    if head != EXPECTED_HEAD:
        fail(f"expected bootstrap HEAD {EXPECTED_HEAD}, got {head}")


def is_patched(text: str) -> bool:
    return (
        MARKER in text
        and "function isTrustedSourceFilePath" in text
        and "const trustedSource = isTrustedSourceFilePath(normalized);" in text
        and 'if (!(base.endsWith(".sql") && trustedSource)) return "blocked secret, database, or archive file";' in text
    )


def is_old_eligible(text: str) -> bool:
    return (
        "function isTrustedSourceFilePath" not in text
        and OLD_HELPER_ANCHOR in text
        and OLD_CONTEXT in text
        and OLD_SQL_BLOCK in text
    )


def check() -> None:
    ensure_repo_guard()
    text = read_text()
    if is_patched(text):
        print("CHECK=ALREADY_PATCHED")
        return
    if not is_old_eligible(text):
        fail("source does not match guarded old Developer Hub security shape")
    print("CHECK=PASS")
    print("SCOPE=server/services/developerHubGitHubSecurity.ts")
    print("PURPOSE=allow versioned trusted-source .sql migrations while preserving database/archive/secret blocks")


def apply() -> None:
    ensure_repo_guard()
    text = read_text()
    if is_patched(text):
        print("APPLY=ALREADY_PATCHED")
        return
    if not is_old_eligible(text):
        fail("source does not match guarded old Developer Hub security shape")
    updated = text
    updated = updated.replace(OLD_HELPER_ANCHOR, NEW_HELPER, 1)
    updated = updated.replace(OLD_CONTEXT, NEW_CONTEXT, 1)
    updated = updated.replace(OLD_SQL_BLOCK, NEW_SQL_BLOCK, 1)
    updated = f"// {MARKER}\n" + updated
    if not is_patched(updated):
        fail("internal verification failed before write")
    TARGET.write_text(updated, encoding="utf-8")
    print("APPLY=PASS")
    print(f"CHANGED_FILE={TARGET}")


def verify() -> None:
    ensure_repo_guard()
    text = read_text()
    if not is_patched(text):
        fail("bootstrap marker/logic missing")
    if OLD_SQL_BLOCK in text:
        fail("unconditional SQL block still present")
    print("VERIFY=PASS")
    print("TRUSTED_SQL_EXCEPTION=PRESENT")
    print("OTHER_SECRET_DATABASE_ARCHIVE_BLOCKS=PRESERVED_BY_CODE_PATH")


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.check:
        check()
    elif args.apply:
        apply()
    else:
        verify()


if __name__ == "__main__":
    main()
