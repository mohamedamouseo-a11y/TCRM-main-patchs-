#!/usr/bin/env python3
from pathlib import Path
import subprocess
import tempfile
import shutil
import hashlib
import os
import datetime

ROOT = Path.cwd()
REMOTE = "b016f9ada07e334b47bf95a19a59e667b7351b1b"
EXPECTED_HEAD = "ebf2f9839100b12e9fe4b7ea5e2ccbb4a7f89370"
EXPECTED_BRANCH = "main"
V28_MARKER = "TCRM Dashboard V28 Final Micro Polish"

CRITICAL = [
    "client/src/pages/AgentDashboard.tsx",
    "client/src/dashboard-premium-luminous-v16.css",
    "client/src/components/ReminderCalendar.tsx",
    "client/src/components/DateRangePicker.tsx",
    "client/src/pages/TeamDashboard.tsx",
    "client/src/pages/LeadsList.tsx",
    "server/security/permissionEngine.ts",
    "server/security/permissionCatalog.ts",
    "server/_core/trpc.ts",
    "server/routers.ts",
]

EXACT_EXCLUDES = {
    "patches/business-profile-intake-v1.patch",
}

EXCLUDE_PARTS = [
    ".tcrm-recovery-backups/",
    "node_modules/",
    "dist/",
    "build/",
    ".cache/",
    "coverage/",
]

SENSITIVE_PARTS = [
    ".env", "secret", "credential", "token", "private_key",
    "id_rsa", ".pem", ".key",
]

SOURCE_PREFIXES = (
    "client/src/",
    "server/",
    "shared/",
    "scripts/",
    "migrations/",
    "drizzle/",
)
SOURCE_FILES = {
    "package.json",
    "package-lock.json",
    "vite.config.ts",
    "tsconfig.json",
    "drizzle.config.ts",
}


def run(args, *, env=None, check=True, input_text=None):
    p = subprocess.run(
        args,
        cwd=str(ROOT),
        env=env,
        text=True,
        input=input_text,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and p.returncode != 0:
        raise RuntimeError(
            f"COMMAND_FAILED:{' '.join(args)}\nSTDOUT={p.stdout}\nSTDERR={p.stderr}"
        )
    return p


def out(args, *, env=None):
    return run(args, env=env).stdout.strip()


def exists_in_commit(commit, path):
    return run(
        ["git", "cat-file", "-e", f"{commit}:{path}"],
        check=False,
    ).returncode == 0


def is_source(path):
    return path.startswith(SOURCE_PREFIXES) or path in SOURCE_FILES


def excluded(path):
    lower = path.lower()
    if path in EXACT_EXCLUDES:
        return True
    if any(x in lower for x in EXCLUDE_PARTS):
        return True
    if any(x in lower for x in SENSITIVE_PARTS):
        return True
    return False


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------- hard preflight ----------
branch = out(["git", "branch", "--show-current"])
head = out(["git", "rev-parse", "HEAD"])
origin_main = out(["git", "rev-parse", "--verify", "refs/remotes/origin/main"])

if branch != EXPECTED_BRANCH:
    raise SystemExit(f"ERROR=UNEXPECTED_BRANCH:{branch}")
if head != EXPECTED_HEAD:
    raise SystemExit(f"ERROR=UNEXPECTED_HEAD:{head}")
if origin_main != REMOTE:
    raise SystemExit(f"ERROR=ORIGIN_MAIN_MOVED:{origin_main}")
if not exists_in_commit(REMOTE, "package.json"):
    raise SystemExit("ERROR=REMOTE_MAIN_OBJECT_NOT_AVAILABLE")

if out(["git", "diff", "--name-only", "--diff-filter=U"]):
    raise SystemExit("ERROR=UNMERGED_FILES_PRESENT")
if out(["git", "diff", "--cached", "--name-only"]):
    raise SystemExit("ERROR=STAGED_CHANGES_PRESENT")

for path in CRITICAL:
    p = ROOT / path
    if not p.is_file():
        raise SystemExit(f"ERROR=CRITICAL_FILE_MISSING:{path}")

css = (ROOT / "client/src/dashboard-premium-luminous-v16.css").read_text(encoding="utf-8")
if V28_MARKER not in css:
    raise SystemExit("ERROR=V28_MARKER_MISSING")

# ---------- classify D paths exactly as audited ----------
diff_rows = out(["git", "diff", "--name-status", REMOTE]).splitlines()
deleted_paths = []
for row in diff_rows:
    if not row:
        continue
    parts = row.split("\t")
    if parts[0] == "D":
        deleted_paths.append(parts[-1])

remote_only_missing = []
present_live_untracked = []
real_live_deletions = []
ambiguous = []

for path in deleted_paths:
    live_exists = (ROOT / path).exists()
    remote_has = exists_in_commit(REMOTE, path)
    head_has = exists_in_commit(EXPECTED_HEAD, path)

    if remote_has and not head_has and live_exists:
        present_live_untracked.append(path)
    elif remote_has and not head_has and not live_exists:
        remote_only_missing.append(path)
    elif remote_has and head_has and not live_exists:
        real_live_deletions.append(path)
    else:
        ambiguous.append(path)

if real_live_deletions:
    raise SystemExit("ERROR=REAL_LIVE_DELETIONS_REQUIRE_MANUAL_DECISION:" + "|".join(real_live_deletions))
if ambiguous:
    raise SystemExit("ERROR=AMBIGUOUS_DELETED_PATHS:" + "|".join(ambiguous))

# ---------- union of legitimate live differences ----------
remote_to_head = set(out(["git", "diff", "--name-only", REMOTE, "HEAD"]).splitlines())
head_to_worktree = set(out(["git", "diff", "--name-only", "HEAD"]).splitlines())
untracked = set(out(["git", "ls-files", "--others", "--exclude-standard"]).splitlines())

all_candidates = {p for p in (remote_to_head | head_to_worktree | untracked) if p}
overlay = []
manual_existing = []

for path in sorted(all_candidates):
    p = ROOT / path
    if not p.is_file():
        continue
    if excluded(path):
        continue
    if is_source(path):
        overlay.append(path)
    else:
        manual_existing.append(path)

if manual_existing:
    raise SystemExit("ERROR=UNCLASSIFIED_EXISTING_FILES:" + "|".join(manual_existing))

# All known PRESENT_IN_LIVE_UNTRACKED paths must be overlaid.
missing_overlay = sorted(set(present_live_untracked) - set(overlay))
if missing_overlay:
    raise SystemExit("ERROR=LIVE_UNTRACKED_NOT_OVERLAID:" + "|".join(missing_overlay))

# Snapshot bytes of every live file we will carry into the new commit.
manifest_before = {p: sha256_file(ROOT / p) for p in overlay}

# ---------- metadata backups ----------
stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
backup_dir = Path(tempfile.gettempdir()) / f"tcrm-reconcile-{stamp}"
backup_dir.mkdir(parents=True, exist_ok=False)

index_rel = out(["git", "rev-parse", "--git-path", "index"])
index_path = Path(index_rel)
if not index_path.is_absolute():
    index_path = ROOT / index_path
index_backup = backup_dir / "index.before"
if index_path.exists():
    shutil.copy2(index_path, index_backup)

exclude_rel = out(["git", "rev-parse", "--git-path", "info/exclude"])
exclude_path = Path(exclude_rel)
if not exclude_path.is_absolute():
    exclude_path = ROOT / exclude_path
exclude_existed = exclude_path.exists()
exclude_backup = backup_dir / "exclude.before"
if exclude_existed:
    shutil.copy2(exclude_path, exclude_backup)

(backup_dir / "old_head.txt").write_text(head + "\n", encoding="utf-8")
(backup_dir / "origin_main.txt").write_text(origin_main + "\n", encoding="utf-8")
(backup_dir / "overlay_paths.txt").write_text("\n".join(overlay) + "\n", encoding="utf-8")
(backup_dir / "remote_only_missing.txt").write_text("\n".join(remote_only_missing) + "\n", encoding="utf-8")

# ---------- build reconciliation tree with TEMP INDEX ----------
tmp_index_dir = Path(tempfile.mkdtemp(prefix="tcrm-reconcile-index-"))
tmp_index = tmp_index_dir / "index"
tmp_env = os.environ.copy()
tmp_env["GIT_INDEX_FILE"] = str(tmp_index)

metadata_changed = False
new_commit = None
backup_ref = f"refs/tcrm-backup/pre-reconcile-{stamp}"


def rollback():
    global metadata_changed
    try:
        current = out(["git", "rev-parse", "HEAD"])
        if current != head:
            run(["git", "update-ref", "refs/heads/main", head, current], check=False)
    except Exception:
        pass
    try:
        if index_backup.exists():
            shutil.copy2(index_backup, index_path)
    except Exception:
        pass
    try:
        if exclude_existed:
            shutil.copy2(exclude_backup, exclude_path)
        else:
            if exclude_path.exists():
                exclude_path.unlink()
    except Exception:
        pass
    metadata_changed = False


try:
    run(["git", "read-tree", REMOTE], env=tmp_env)

    for path in overlay:
        run(["git", "add", "--", path], env=tmp_env)

    tree = out(["git", "write-tree"], env=tmp_env)

    commit_env = os.environ.copy()
    commit_env.setdefault("GIT_AUTHOR_NAME", "Tamiyouz Developer Hub")
    commit_env.setdefault("GIT_AUTHOR_EMAIL", "developer-hub@tamiyouz.local")
    commit_env.setdefault("GIT_COMMITTER_NAME", "Tamiyouz Developer Hub")
    commit_env.setdefault("GIT_COMMITTER_EMAIL", "developer-hub@tamiyouz.local")

    message = (
        "Reconcile live TCRM state onto GitHub main\n\n"
        f"Base: {REMOTE}\n"
        f"Previous local HEAD: {EXPECTED_HEAD}\n"
        "Strategy: GitHub main base + current legitimate LIVE source overrides; "
        "GitHub-only missing files preserved.\n"
    )
    new_commit = out(
        ["git", "commit-tree", tree, "-p", REMOTE],
        env=commit_env,
    ) if False else None

    # commit-tree needs message on stdin; invoke explicitly.
    cp = subprocess.run(
        ["git", "commit-tree", tree, "-p", REMOTE],
        cwd=str(ROOT),
        env=commit_env,
        text=True,
        input=message,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if cp.returncode != 0:
        raise RuntimeError(f"COMMIT_TREE_FAILED:{cp.stderr}")
    new_commit = cp.stdout.strip()

    # Validate direct parent.
    parent = out(["git", "rev-parse", f"{new_commit}^1"])
    if parent != REMOTE:
        raise RuntimeError(f"PARENT_VALIDATION_FAILED:{parent}")

    # Every overlaid LIVE file must be byte-identical in the new commit.
    for path in overlay:
        live_blob = out(["git", "hash-object", "--", path])
        commit_blob = out(["git", "rev-parse", f"{new_commit}:{path}"])
        if live_blob != commit_blob:
            raise RuntimeError(f"LIVE_BLOB_MISMATCH:{path}")

    # Every GitHub-only missing path must remain exactly the GitHub version.
    for path in remote_only_missing:
        remote_blob = out(["git", "rev-parse", f"{REMOTE}:{path}"])
        commit_blob = out(["git", "rev-parse", f"{new_commit}:{path}"])
        if remote_blob != commit_blob:
            raise RuntimeError(f"REMOTE_ONLY_NOT_PRESERVED:{path}")

    # Protect old orphan history with a non-branch backup ref.
    run(["git", "update-ref", backup_ref, head])

    # Atomically repoint local main. This changes Git metadata only, not source bytes.
    run(["git", "update-ref", "refs/heads/main", new_commit, head])
    metadata_changed = True

    # Align current index to the new commit WITHOUT touching the worktree.
    run(["git", "read-tree", "--reset", new_commit])

    # GitHub-only files intentionally absent from LIVE filesystem stay in commit,
    # while skip-worktree prevents them appearing as local deletions.
    for path in remote_only_missing:
        run(["git", "update-index", "--skip-worktree", "--", path])

    # Ignore local recovery backups in this working copy only (never committed).
    exclude_path.parent.mkdir(parents=True, exist_ok=True)
    existing_exclude = exclude_path.read_text(encoding="utf-8") if exclude_path.exists() else ""
    ignore_line = ".tcrm-recovery-backups/"
    lines = existing_exclude.splitlines()
    if ignore_line not in lines:
        with exclude_path.open("a", encoding="utf-8") as f:
            if existing_exclude and not existing_exclude.endswith("\n"):
                f.write("\n")
            f.write(ignore_line + "\n")

    # Verify every overlaid source byte on disk is unchanged.
    manifest_after = {p: sha256_file(ROOT / p) for p in overlay}
    if manifest_after != manifest_before:
        raise RuntimeError("LIVE_SOURCE_BYTES_CHANGED")

    # New topology must be exactly 0 remote-only / 1 local-only.
    counts = out(["git", "rev-list", "--left-right", "--count", f"refs/remotes/origin/main...HEAD"])
    left, right = [int(x) for x in counts.split()]
    if (left, right) != (0, 1):
        raise RuntimeError(f"BAD_POST_RECONCILE_DIVERGENCE:{left},{right}")

    # Worktree/index should be clean after skip-worktree + local backup ignore.
    status = out(["git", "status", "--porcelain=v1", "--untracked-files=all"])
    if status:
        raise RuntimeError("POST_RECONCILE_STATUS_NOT_CLEAN:" + status.replace("\n", "|"))

    if run(["git", "diff", "--quiet", "HEAD"], check=False).returncode != 0:
        raise RuntimeError("UNSTAGED_DIFF_REMAINS")
    if run(["git", "diff", "--cached", "--quiet", "HEAD"], check=False).returncode != 0:
        raise RuntimeError("STAGED_DIFF_REMAINS")

except Exception as e:
    if metadata_changed:
        rollback()
    shutil.rmtree(tmp_index_dir, ignore_errors=True)
    print("RECONCILIATION=NO")
    print(f"BACKUP_DIR={backup_dir}")
    print(f"ERROR={str(e).replace(chr(10), '|')}")
    raise SystemExit(1)

shutil.rmtree(tmp_index_dir, ignore_errors=True)

print("RECONCILIATION=YES")
print(f"OLD_HEAD={head}")
print(f"REMOTE_BASE={REMOTE}")
print(f"NEW_HEAD={new_commit}")
print(f"NEW_PARENT={REMOTE}")
print(f"BACKUP_REF={backup_ref}")
print(f"BACKUP_DIR={backup_dir}")
print(f"LIVE_OVERRIDE_FILE_COUNT={len(overlay)}")
print(f"REMOTE_ONLY_FILES_PRESERVED={len(remote_only_missing)}")
print(f"PRESENT_LIVE_UNTRACKED_CARRIED={len(present_live_untracked)}")
print("WORKTREE_SOURCE_BYTES_CHANGED=NO")
print("REMOTE_ONLY_MATERIALIZED_TO_LIVE=NO")
print("POST_RECONCILE_REMOTE_ONLY_COMMITS=0")
print("POST_RECONCILE_LOCAL_ONLY_COMMITS=1")
print("WORKTREE_CLEAN=YES")
print("READY_FOR_DEVELOPER_HUB_PUSH=YES")
print("PUSH_PERFORMED=NO")
print("ERROR=NONE")
