#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import subprocess

ROOT = pathlib.Path.cwd()
EXPECTED_BRANCH = "main"
EXPECTED_HEAD = "5f9cf7fe182126684454e7361cf119491e685b10"

TARGETS = {
    "darwish": (pathlib.Path("client/src/pages/DarwishPage.tsx"), "74f9a2f1d82ecfc371818ec110d3b435de18e08a"),
    "zaghloul": (pathlib.Path("client/src/pages/ZaghloulV5Page.tsx"), "0e5f936a82ea9ddf49e7e5368445299c6a709494"),
    "tara": (pathlib.Path("client/src/pages/TaraAgentPage.tsx"), "6cfe876e92a8923455bc36569070da6d3f6429ae"),
    "felfel": (pathlib.Path("client/src/pages/FelfelPage.tsx"), "c5461926d6ddca86cf2ce2e5f62daf3347ed9e32"),
}

EXPECTED_NUMSTAT = {
    "client/src/pages/DarwishPage.tsx": (1, 1),
    "client/src/pages/FelfelPage.tsx": (1, 1),
    "client/src/pages/TaraAgentPage.tsx": (7, 2),
    "client/src/pages/ZaghloulV5Page.tsx": (7, 2),
}


def run(*args: str, check: bool = True) -> str:
    p = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"command failed ({' '.join(args)}): {p.stderr.strip() or p.stdout.strip()}")
    return p.stdout


def git_blob(path: pathlib.Path) -> str:
    return run("git", "hash-object", str(path)).strip()


def read(path: pathlib.Path) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require_repo_state() -> None:
    branch = run("git", "branch", "--show-current").strip()
    head = run("git", "rev-parse", "HEAD").strip()
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(f"branch mismatch: expected {EXPECTED_BRANCH}, got {branch}")
    if head != EXPECTED_HEAD:
        raise RuntimeError(f"HEAD mismatch: expected {EXPECTED_HEAD}, got {head}")

    status_lines = [line for line in run("git", "status", "--porcelain").splitlines() if line.strip()]
    expected_paths = set(EXPECTED_NUMSTAT)
    actual_paths = set()
    for line in status_lines:
        if len(line) < 4:
            raise RuntimeError(f"unexpected porcelain status line: {line!r}")
        status = line[:2]
        path = line[3:]
        actual_paths.add(path)
        if status != " M":
            raise RuntimeError(f"unexpected staged/untracked/conflicted status for {path}: {status!r}")
    if actual_paths != expected_paths:
        raise RuntimeError(f"dirty path set mismatch: expected {sorted(expected_paths)}, got {sorted(actual_paths)}")

    diff_names = {line.strip() for line in run("git", "diff", "--name-only").splitlines() if line.strip()}
    if diff_names != expected_paths:
        raise RuntimeError(f"diff path set mismatch: expected {sorted(expected_paths)}, got {sorted(diff_names)}")

    subprocess.run(["git", "diff", "--check"], cwd=ROOT, check=True)

    numstat = {}
    for line in run("git", "diff", "--numstat").splitlines():
        if not line.strip():
            continue
        added, deleted, path = line.split("\t", 2)
        if not added.isdigit() or not deleted.isdigit():
            raise RuntimeError(f"non-text/binary diff is not allowed: {line}")
        numstat[path] = (int(added), int(deleted))
    if numstat != EXPECTED_NUMSTAT:
        raise RuntimeError(f"numstat mismatch: expected {EXPECTED_NUMSTAT}, got {numstat}")

    for name, (path, expected_blob) in TARGETS.items():
        actual = git_blob(path)
        if actual != expected_blob:
            raise RuntimeError(f"{name} pre-applied target blob mismatch: expected {expected_blob}, got {actual}")


def require_semantics() -> None:
    texts = {name: read(path) for name, (path, _) in TARGETS.items()}

    for name, text in texts.items():
        if text.count('data-ai-staff-command="context-v1"') != 1:
            raise RuntimeError(f"{name}: shared command marker count mismatch")

    required = {
        "darwish": [
            'data-darwish-priority-command="v4"',
            'data-darwish-workspace="supervisor-v3"',
            'data-ai-staff-refresh="darwish-v1"',
            'const [darwishWorkspace, setDarwishWorkspace] = useState("intelligence")',
        ],
        "zaghloul": [
            '// @ts-nocheck',
            'data-zaghloul-engagement-command="v3"',
            'data-zaghloul-workspace="grouped-nav-v2"',
            'data-ai-staff-refresh="zaghloul-v1"',
            'const zaghloulWorkspaceLabel =',
            'Current workspace: ${zaghloulWorkspaceLabel}',
            'Read & navigate only',
            'dashboard: "Dashboard"',
            'inbox: "Inbox"',
            'contacts: "Contacts"',
            'pipelines: "Pipelines"',
            'broadcasts: "Broadcasts"',
            'automations: "Automations"',
            'flows: "Flows"',
            'aiagents: "AI Agents"',
            'team: "Team"',
            'settings: "Settings"',
            'developer: "Developer"',
        ],
        "tara": [
            '// @ts-nocheck',
            'data-tara-sales-command="v3"',
            'data-tara-workspace="control-center-v2"',
            'data-ai-staff-refresh="tara-v1"',
            'const taraWorkspaceLabel =',
            'voice: "Voice & ElevenLabs"',
            'moderators: "Moderator"',
            'Current workspace: ${taraWorkspaceLabel}',
            'Campaign scope: ${scopeId}',
            'const initialTab = typeof window !== "undefined" && new URLSearchParams(window.location.search).get("tab") === "social" ? "social" : "settings";',
        ],
        "felfel": [
            'data-felfel-meeting-command="v9"',
            'data-felfel-workspace="meeting-intelligence-v8"',
            'data-ai-staff-refresh="felfel-v1"',
            'TCRM_FELFEL_REFRESH_COMPLETION_V1',
            'const [felfelWorkspace, setFelfelWorkspace] = useState("live")',
        ],
    }
    for name, items in required.items():
        missing = [item for item in items if item not in texts[name]]
        if missing:
            raise RuntimeError(f"{name}: missing intended/preserved Phase 13 markers: {', '.join(missing)}")

    command_bounds = {
        "darwish": ('data-darwish-priority-command="v4"', 'data-darwish-workspace="supervisor-v3"'),
        "zaghloul": ('data-zaghloul-engagement-command="v3"', 'data-zaghloul-workspace="grouped-nav-v2"'),
        "tara": ('data-tara-sales-command="v3"', '<Tabs value={taraWorkspace} onValueChange={setTaraWorkspace}'),
        "felfel": ('data-felfel-meeting-command="v9"', 'data-felfel-workspace="meeting-intelligence-v8"'),
    }
    for name, (start_marker, end_marker) in command_bounds.items():
        text = texts[name]
        start = text.index(start_marker)
        end = text.index(end_marker, start)
        command = text[start:end]
        if '.mutate(' in command:
            raise RuntimeError(f"{name}: command layer contains mutation call")

    diff = run("git", "diff", "--unified=0")
    added_lines = [line[1:] for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++")]
    deleted_lines = [line[1:] for line in diff.splitlines() if line.startswith("-") and not line.startswith("---")]
    if len(added_lines) != 16 or len(deleted_lines) != 6:
        raise RuntimeError(f"diff line-count mismatch: expected +16/-6, got +{len(added_lines)}/-{len(deleted_lines)}")
    if any('.mutate(' in line for line in added_lines):
        raise RuntimeError("Phase 13 diff unexpectedly adds a mutation call")


def main() -> None:
    require_repo_state()
    require_semantics()
    print("RESUME_STATE=PREAPPLIED_PHASE13_TARGET")
    for name, (path, _) in TARGETS.items():
        print(f"{name.upper()}_TARGET_BLOB={git_blob(path)}")
    print("RESUME_VERIFY=PASS")


if __name__ == "__main__":
    main()
