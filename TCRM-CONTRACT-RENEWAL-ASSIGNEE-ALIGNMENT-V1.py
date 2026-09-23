#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path

PATCH_NAME = "TCRM_CONTRACT_RENEWAL_ASSIGNEE_ALIGNMENT_V1"
EXPECTED_MAIN_COMMIT = "a359b82be80095e25af94ab7571f086778586d63"
EXPECTED_BLOBS = {
    "server/services/accountManagementSecurity.ts": "4592262583c9f3a14294add2675474381ccffe35",
    "client/src/pages/ClientProfile.tsx": "1028098f0533e870171743b95481596bc208acc5",
}
TARGETS = tuple(EXPECTED_BLOBS)
BACKUP_DIR = Path(".tcrm-patch-backups") / PATCH_NAME


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("utf-8")
    return hashlib.sha1(header + data).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"ANCHOR_FAIL={label}:expected_1_found_{count}")
    return text.replace(old, new, 1)


def run_git_diff_check() -> None:
    proc = subprocess.run(
        ["git", "diff", "--check", "--", *TARGETS],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if proc.returncode != 0:
        raise RuntimeError("GIT_DIFF_CHECK_FAIL=" + proc.stdout.strip().replace("\n", " | "))


def restore_backups() -> None:
    for rel in TARGETS:
        src = BACKUP_DIR / rel
        dst = Path(rel)
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def main() -> int:
    root = Path.cwd()
    originals: dict[str, str] = {}
    for rel, expected in EXPECTED_BLOBS.items():
        path = root / rel
        if not path.is_file():
            print("PATCH=FAIL")
            print(f"ERROR=MISSING_SOURCE:{rel}")
            return 2
        raw = path.read_bytes()
        actual = git_blob_sha(raw)
        if actual != expected:
            print("PATCH=STOP")
            print(f"SOURCE_GUARD_FAIL={rel}")
            print(f"EXPECTED_BLOB={expected}")
            print(f"ACTUAL_BLOB={actual}")
            print("ERROR=SOURCE_CHANGED_DO_NOT_FORCE")
            return 3
        originals[rel] = raw.decode("utf-8")

    updated = dict(originals)

    updated["server/services/accountManagementSecurity.ts"] = replace_once(
        updated["server/services/accountManagementSecurity.ts"],
        '''  const targetId = positiveInteger(targetUserId);
  if (!targetId) deny("Invalid renewal assignee");
  const target = await readActiveUser(targetId);
  if (!target || normalizeUserRole(target.role) !== "AccountManager") deny("Invalid renewal assignee");

  const role = normalizeUserRole(actor.role);
  if (role === "Admin") return;''',
        '''  const targetId = positiveInteger(targetUserId);
  if (!targetId) deny("Invalid renewal assignee");
  const target = await readActiveUser(targetId);
  if (!target) deny("Invalid renewal assignee");

  const role = normalizeUserRole(actor.role);
  const targetRole = normalizeUserRole(target.role);
  const adminSelfAssignment = role === "Admin" && targetRole === "Admin" && targetId === Number(actor.id);
  if (adminSelfAssignment) return;
  if (targetRole !== "AccountManager") deny("Invalid renewal assignee");
  if (role === "Admin") return;''',
        "allow_admin_self_renewal_assignment",
    )

    updated["client/src/pages/ClientProfile.tsx"] = replace_once(
        updated["client/src/pages/ClientProfile.tsx"],
        '''                          {(managersQ.data ?? []).map((m: any) => (
                            <SelectItem key={m.id} value={String(m.id)}>{m.name}</SelectItem>
                          ))}''',
        '''                          {(assignableManagersQ.data ?? []).map((m: any) => (
                            <SelectItem key={m.id} value={String(m.id)}>{m.name}</SelectItem>
                          ))}''',
        "renewal_dropdown_canonical_assignable_managers",
    )

    must_have = {
        "server/services/accountManagementSecurity.ts": [
            'const adminSelfAssignment = role === "Admin" && targetRole === "Admin" && targetId === Number(actor.id);',
            'if (adminSelfAssignment) return;',
            'if (targetRole !== "AccountManager") deny("Invalid renewal assignee");',
        ],
        "client/src/pages/ClientProfile.tsx": [
            '(assignableManagersQ.data ?? []).map((m: any) => (',
        ],
    }
    for rel, markers in must_have.items():
        for marker in markers:
            if marker not in updated[rel]:
                raise RuntimeError(f"VERIFY_MARKER_FAIL={rel}:{marker}")

    if BACKUP_DIR.exists():
        shutil.rmtree(BACKUP_DIR)
    for rel in TARGETS:
        src = root / rel
        dst = root / BACKUP_DIR / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    try:
        for rel in TARGETS:
            (root / rel).write_text(updated[rel], encoding="utf-8")
        run_git_diff_check()
    except Exception:
        restore_backups()
        raise

    print("PATCH=PASS")
    print("PATCH_NAME=" + PATCH_NAME)
    print("BASE_MAIN_COMMIT=" + EXPECTED_MAIN_COMMIT)
    print("FILES_CHANGED=" + ";".join(TARGETS))
    print("RENEWAL_ASSIGNEE_SOURCE=CANONICAL_ASSIGNABLE_MANAGERS")
    print("ADMIN_SELF_ASSIGNMENT=ALLOWED")
    print("OTHER_NON_ACCOUNT_MANAGER_ROLES=BLOCKED")
    print("PERMISSION_ENGINE=UNCHANGED")
    print("AUDIT=UNCHANGED")
    print("DB_MIGRATION=NO")
    print("BACKUP=" + str(BACKUP_DIR))
    print("GIT_DIFF_CHECK=PASS")
    print("ERROR=NONE")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("PATCH=FAIL")
        print("ERROR=" + str(exc).replace("\n", " | "))
        raise SystemExit(1)
