#!/usr/bin/env python3
from pathlib import Path
import shutil
import sys
import time

ROOT = Path(__file__).resolve().parent
FILES = ROOT / "files"
TARGETS = [
    "server/security/phase3ScopeFilters.ts",
    "scripts/verify-advanced-permissions-phase3a.ts",
]


def die(msg: str):
    print(f"[Phase3A Review Fix] ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)


def main():
    project = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    required = [
        project / "server/security/permissionEngine.ts",
        project / "server/security/phase3ScopeFilters.ts",
        project / "server/_core/trpc.ts",
        project / "server/routers.ts",
        project / "server/db.ts",
    ]
    for p in required:
        if not p.exists():
            die(f"Missing required file: {p.relative_to(project)}")

    current_scope = (project / "server/security/phase3ScopeFilters.ts").read_text(encoding="utf-8")
    if "TCRM Advanced Permissions — Phase 3A" not in current_scope:
        die("Phase 3A implementation is not present; refusing to apply this corrective patch.")

    trpc = (project / "server/_core/trpc.ts").read_text(encoding="utf-8")
    routers = (project / "server/routers.ts").read_text(encoding="utf-8")
    if "leadsViewScope" not in trpc or "dealsViewScope" not in trpc or "clientsViewScope" not in trpc:
        die("Expected Phase 3A tRPC scope guards are missing.")
    if "buildLeadScopeCondition" not in routers or "assertRowScope" not in routers:
        die("Expected Phase 3A router integration is missing.")

    # Idempotent: if reviewed marker already exists, keep replacing from the canonical patch files.
    backup_root = project / ".patch-backups" / f"advanced-permissions-phase3a-review-fix-{int(time.time())}"
    for rel in TARGETS:
        src = FILES / rel
        dst = project / rel
        if not src.exists():
            die(f"Patch package incomplete: missing files/{rel}")
        if dst.exists():
            backup = backup_root / rel
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dst, backup)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"[Phase3A Review Fix] installed {rel}")

    print("\n[Phase3A Review Fix] Applied successfully.")
    print(f"[Phase3A Review Fix] Backup: {backup_root}")
    print("[Phase3A Review Fix] No DB migration and no git command executed.")
    print("Run:")
    print("  pnpm exec tsx scripts/verify-advanced-permissions-phase3a.ts")
    print("  pnpm check")
    print("  pnpm build")
    print("  pnpm test")


if __name__ == "__main__":
    main()
