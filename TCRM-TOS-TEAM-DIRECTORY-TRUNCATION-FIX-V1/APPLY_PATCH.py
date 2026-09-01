#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

PATCH_ID = "TCRM-TOS-TEAM-DIRECTORY-TRUNCATION-FIX-V1"
REL_PATH = Path("server/services/tosIntegrationService.ts")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fail(message: str, code: int = 2) -> int:
    print(f"[ABORT] {message}", file=sys.stderr)
    return code


def esbuild_command(root: Path, target: Path, outfile: Path) -> list[str]:
    local = root / "node_modules" / ".bin" / "esbuild"
    if local.is_file():
        return [str(local), str(target), "--format=esm", "--log-level=error", f"--outfile={outfile}"]
    return ["pnpm", "exec", "esbuild", str(target), "--format=esm", "--log-level=error", f"--outfile={outfile}"]


def parse_with_esbuild(root: Path, target: Path) -> tuple[int, str]:
    fd, name = tempfile.mkstemp(prefix="tcrm-tos-parse-", suffix=".mjs")
    os.close(fd)
    outfile = Path(name)
    try:
        proc = subprocess.run(
            esbuild_command(root, target, outfile),
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=90,
        )
        return proc.returncode, proc.stdout or ""
    except FileNotFoundError:
        return 127, "esbuild/pnpm not found"
    except subprocess.TimeoutExpired:
        return 124, "esbuild parse timed out"
    finally:
        try:
            outfile.unlink(missing_ok=True)
        except Exception:
            pass


def main() -> int:
    root = Path(sys.argv[1]).expanduser().resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
    target = root / REL_PATH

    if not target.is_file():
        return fail(f"Target file not found: {target}")

    original = target.read_text(encoding="utf-8")
    original_sha = sha256(target)

    required_markers = [
        "export async function getTosProjectTeamDirectory",
        "if (!body)",
        "console.warn();",
    ]
    missing = [marker for marker in required_markers if marker not in original]
    if missing:
        return fail(
            "Expected live fallback/truncation markers are missing: " + ", ".join(missing) +
            ". Refusing to modify an unknown version."
        )

    before_rc, before_output = parse_with_esbuild(root, target)
    if before_rc == 0:
        print(f"[OK] {REL_PATH} already parses successfully; no write needed.")
        print(f"[SHA256] {original_sha}  {REL_PATH}")
        return 0

    if "Unexpected end of file" not in before_output:
        return fail(
            "The file does not parse, but the error is not the diagnosed Unexpected end of file.\n" +
            before_output.strip()
        )

    # This patch is intentionally minimal: append exactly one function-closing brace.
    # It is accepted only if that single brace makes esbuild parse the whole TypeScript file.
    updated = original.rstrip() + "\n}\n"

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = root / ".patch-backups" / PATCH_ID / timestamp / REL_PATH
    backup.parent.mkdir(parents=True, exist_ok=False)
    shutil.copy2(target, backup)

    temp = target.with_name(target.name + f".{PATCH_ID}.tmp")
    try:
        temp.write_text(updated, encoding="utf-8")
        os.replace(temp, target)
    finally:
        if temp.exists():
            temp.unlink()

    after_rc, after_output = parse_with_esbuild(root, target)
    if after_rc != 0:
        shutil.copy2(backup, target)
        restored_sha = sha256(target)
        return fail(
            "Appending one closing brace did not restore valid TypeScript. Original file was automatically restored.\n"
            f"Restored SHA256: {restored_sha}\n"
            + after_output.strip()
        )

    post_sha = sha256(target)
    print(f"[APPLIED] {PATCH_ID}")
    print(f"[TARGET] {target}")
    print(f"[BACKUP] {backup}")
    print(f"[SHA256 BEFORE] {original_sha}")
    print(f"[SHA256 AFTER ] {post_sha}")
    print("[CHANGE] Appended exactly one missing closing brace at EOF.")
    print("[VALIDATION] esbuild parser now accepts tosIntegrationService.ts.")
    print("[SCOPE] No API logic, payload, TOS source, database, or frontend changes made by this patch.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
