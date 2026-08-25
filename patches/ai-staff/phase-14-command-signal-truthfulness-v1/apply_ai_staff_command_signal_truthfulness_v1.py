#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
import subprocess

ROOT = pathlib.Path.cwd()

TARGETS = {
    "darwish": (pathlib.Path("client/src/pages/DarwishPage.tsx"), "74f9a2f1d82ecfc371818ec110d3b435de18e08a"),
    "zaghloul": (pathlib.Path("client/src/pages/ZaghloulV5Page.tsx"), "0e5f936a82ea9ddf49e7e5368445299c6a709494"),
    "tara": (pathlib.Path("client/src/pages/TaraAgentPage.tsx"), "6cfe876e92a8923455bc36569070da6d3f6429ae"),
    "felfel": (pathlib.Path("client/src/pages/FelfelPage.tsx"), "c5461926d6ddca86cf2ce2e5f62daf3347ed9e32"),
}


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def git_blob(path: pathlib.Path) -> str:
    return run("git", "hash-object", str(path))


def read(path: pathlib.Path) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: pathlib.Path, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def require_bases() -> None:
    mismatches = []
    for name, (path, expected) in TARGETS.items():
        actual = git_blob(path)
        if actual != expected:
            mismatches.append(f"{name}: expected {expected}, got {actual}")
    if mismatches:
        raise RuntimeError("Base blob mismatch(s): " + "; ".join(mismatches))


def patch_darwish(text: str) -> str:
    text = replace_once(
        text,
        'data-darwish-priority-command="v4" data-ai-staff-command="context-v1"',
        'data-darwish-priority-command="v4" data-ai-staff-command="context-v1" data-ai-staff-signal-truth="v1"',
        "Darwish signal truth marker",
    )
    replacements = [
        ('value: intelligenceStatsQ.data?.urgent || 0', 'value: intelligenceStatsQ.data === undefined ? "—" : (intelligenceStatsQ.data?.urgent || 0)', "Darwish intelligence signal"),
        ('value: supervisorQ.data?.activeAlerts || 0', 'value: supervisorQ.data === undefined ? "—" : (supervisorQ.data?.activeAlerts || 0)', "Darwish supervision signal"),
        ('value: actionStatsQ.data?.proposed || 0', 'value: actionStatsQ.data === undefined ? "—" : (actionStatsQ.data?.proposed || 0)', "Darwish actions signal"),
        ('value: mappingCountsQ.data?.unmappedClients || 0', 'value: mappingCountsQ.data === undefined ? "—" : (mappingCountsQ.data?.unmappedClients || 0)', "Darwish mapping signal"),
    ]
    for old, new, label in replacements:
        text = replace_once(text, old, new, label)
    return text


def patch_zaghloul(text: str) -> str:
    text = replace_once(
        text,
        'data-zaghloul-engagement-command="v3" data-ai-staff-command="context-v1"',
        'data-zaghloul-engagement-command="v3" data-ai-staff-command="context-v1" data-ai-staff-signal-truth="v1"',
        "Zaghloul signal truth marker",
    )
    replacements = [
        ('value: dashboardQ.data?.totalContacts ?? contactsQ.data?.total ?? 0', 'value: dashboardQ.data === undefined && contactsQ.data === undefined ? "—" : (dashboardQ.data?.totalContacts ?? contactsQ.data?.total ?? 0)', "Zaghloul audience signal"),
        ('value: dashboardQ.data?.unreadMessages ?? inboxQ.data?.counters?.unread ?? 0', 'value: dashboardQ.data === undefined && inboxQ.data === undefined ? "—" : (dashboardQ.data?.unreadMessages ?? inboxQ.data?.counters?.unread ?? 0)', "Zaghloul inbox signal"),
        ('value: automationsQ.data?.items?.length ?? 0', 'value: automationsQ.data === undefined ? "—" : (automationsQ.data?.items?.length ?? 0)', "Zaghloul automation signal"),
        ('value: teamQ.data?.total ?? 0', 'value: teamQ.data === undefined ? "—" : (teamQ.data?.total ?? 0)', "Zaghloul team signal"),
    ]
    for old, new, label in replacements:
        text = replace_once(text, old, new, label)
    return text


def patch_tara(text: str) -> str:
    text = replace_once(
        text,
        'data-tara-sales-command="v3" data-ai-staff-command="context-v1"',
        'data-tara-sales-command="v3" data-ai-staff-command="context-v1" data-ai-staff-signal-truth="v1"',
        "Tara signal truth marker",
    )
    replacements = [
        ('value: campaigns.length', 'value: campaignsQ.data === undefined ? "—" : campaigns.length', "Tara campaigns signal"),
        ('value: (fieldsQ.data || []).length', 'value: fieldsQ.data === undefined ? "—" : (fieldsQ.data || []).length', "Tara qualification signal"),
        ('value: (followupsQ.data || []).length', 'value: followupsQ.data === undefined ? "—" : (followupsQ.data || []).length', "Tara followups signal"),
        ('value: (knowledgeQ.data || []).length', 'value: knowledgeQ.data === undefined ? "—" : (knowledgeQ.data || []).length', "Tara knowledge signal"),
    ]
    for old, new, label in replacements:
        text = replace_once(text, old, new, label)
    return text


def patch_felfel(text: str) -> str:
    text = replace_once(
        text,
        'data-felfel-meeting-command="v9" data-ai-staff-command="context-v1"',
        'data-felfel-meeting-command="v9" data-ai-staff-command="context-v1" data-ai-staff-signal-truth="v1"',
        "Felfel signal truth marker",
    )
    text = replace_once(
        text,
        'value: transcript?.segments?.length ?? 0',
        'value: meeting && transcriptQ.data === undefined ? "—" : (transcript?.segments?.length ?? 0)',
        "Felfel transcript signal",
    )
    text = replace_once(
        text,
        'value: meetingsQ.data?.length ?? 0',
        'value: meetingsQ.data === undefined ? "—" : (meetingsQ.data?.length ?? 0)',
        "Felfel history signal",
    )
    return text


PATCHERS = {
    "darwish": patch_darwish,
    "zaghloul": patch_zaghloul,
    "tara": patch_tara,
    "felfel": patch_felfel,
}


def verify() -> None:
    texts = {name: read(path) for name, (path, _) in TARGETS.items()}

    for name, text in texts.items():
        if text.count('data-ai-staff-signal-truth="v1"') != 1:
            raise RuntimeError(f"{name}: signal truth marker count mismatch")
        if text.count('data-ai-staff-command="context-v1"') != 1:
            raise RuntimeError(f"{name}: Phase 13 command marker count mismatch")

    required = {
        "darwish": [
            'intelligenceStatsQ.data === undefined ? "—"',
            'supervisorQ.data === undefined ? "—"',
            'actionStatsQ.data === undefined ? "—"',
            'mappingCountsQ.data === undefined ? "—"',
            'data-darwish-priority-command="v4"',
            'data-ai-staff-refresh="darwish-v1"',
            'const refreshDarwishData = async',
        ],
        "zaghloul": [
            '// @ts-nocheck',
            'dashboardQ.data === undefined && contactsQ.data === undefined ? "—"',
            'dashboardQ.data === undefined && inboxQ.data === undefined ? "—"',
            'automationsQ.data === undefined ? "—"',
            'teamQ.data === undefined ? "—"',
            'data-zaghloul-engagement-command="v3"',
            'data-zaghloul-workspace="grouped-nav-v2"',
            'const refreshZaghloulData = async',
        ],
        "tara": [
            '// @ts-nocheck',
            'campaignsQ.data === undefined ? "—"',
            'fieldsQ.data === undefined ? "—"',
            'followupsQ.data === undefined ? "—"',
            'knowledgeQ.data === undefined ? "—"',
            'data-tara-sales-command="v3"',
            'data-tara-workspace="control-center-v2"',
            'const refreshTaraData = async',
            'const initialTab = typeof window !== "undefined" && new URLSearchParams(window.location.search).get("tab") === "social" ? "social" : "settings";',
        ],
        "felfel": [
            'meeting && transcriptQ.data === undefined ? "—"',
            'meetingsQ.data === undefined ? "—"',
            'data-felfel-meeting-command="v9"',
            'data-felfel-workspace="meeting-intelligence-v8"',
            'TCRM_FELFEL_REFRESH_COMPLETION_V1',
            'const refreshFelfelData = async',
            '6_000',
        ],
    }
    for name, items in required.items():
        missing = [item for item in items if item not in texts[name]]
        if missing:
            raise RuntimeError(f"{name}: missing Phase 14/preserved marker(s): {', '.join(missing)}")

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
        if '.mutate(' in text[start:end]:
            raise RuntimeError(f"{name}: command layer must remain mutation-free")

    for name, (path, _) in TARGETS.items():
        print(f"{name.upper()}_TARGET_BLOB={git_blob(path)}")
    print("VERIFY=PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--apply", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = parser.parse_args()

    if args.check:
        require_bases()
        for name, (_, expected) in TARGETS.items():
            print(f"{name.upper()}_BASE_BLOB={expected}")
        print("CHECK=PASS")
        return

    if args.apply:
        require_bases()
        current = {name: read(path) for name, (path, _) in TARGETS.items()}
        for name, text in current.items():
            if 'data-ai-staff-signal-truth="v1"' in text:
                raise RuntimeError(f"{name}: Phase 14 marker already present")
        patched = {name: PATCHERS[name](text) for name, text in current.items()}
        for name, (path, _) in TARGETS.items():
            write(path, patched[name])
        for name, (path, _) in TARGETS.items():
            print(f"{name.upper()}_TARGET_BLOB={git_blob(path)}")
        print("APPLY=PASS")
        return

    verify()


if __name__ == "__main__":
    main()
