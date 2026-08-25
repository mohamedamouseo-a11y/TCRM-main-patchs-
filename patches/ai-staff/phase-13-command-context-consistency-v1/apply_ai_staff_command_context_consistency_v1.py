#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
import subprocess

ROOT = pathlib.Path.cwd()
TARGETS = {
    "darwish": (pathlib.Path("client/src/pages/DarwishPage.tsx"), "9534afddf3b242c03bcf25f9c05568b277e735d5"),
    "zaghloul": (pathlib.Path("client/src/pages/ZaghloulV5Page.tsx"), "2663ad9dc4d66c39349323225ea207894562bf78"),
    "tara": (pathlib.Path("client/src/pages/TaraAgentPage.tsx"), "0268ea64d4a796b662e308de0a69f7252279d6b9"),
    "felfel": (pathlib.Path("client/src/pages/FelfelPage.tsx"), "d2bb3032bf851e6070780bd86a69b66b86f32c1d"),
}


def git_blob(path: pathlib.Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], cwd=ROOT, text=True).strip()


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
    return replace_once(
        text,
        '<Card data-darwish-priority-command="v4" className=',
        '<Card data-darwish-priority-command="v4" data-ai-staff-command="context-v1" className=',
        "Darwish shared command marker",
    )


def patch_zaghloul(text: str) -> str:
    text = replace_once(
        text,
        '  const [zaghloulWorkspace, setZaghloulWorkspace] = useState("dashboard");\n',
        '''  const [zaghloulWorkspace, setZaghloulWorkspace] = useState("dashboard");\n  const zaghloulWorkspaceLabel = (ar ? {\n    dashboard: "لوحة التحكم", inbox: "صندوق الوارد", contacts: "جهات الاتصال", pipelines: "مسارات البيع", broadcasts: "الحملات الجماعية", automations: "الأتمتة", flows: "التدفقات", aiagents: "وكلاء الذكاء الاصطناعي", team: "الفريق", settings: "الإعدادات", developer: "المطور",\n  } : {\n    dashboard: "Dashboard", inbox: "Inbox", contacts: "Contacts", pipelines: "Pipelines", broadcasts: "Broadcasts", automations: "Automations", flows: "Flows", aiagents: "AI Agents", team: "Team", settings: "Settings", developer: "Developer",\n  })[zaghloulWorkspace] || zaghloulWorkspace;\n''',
        "Zaghloul workspace label",
    )
    text = replace_once(
        text,
        '<Card data-zaghloul-engagement-command="v3" className=',
        '<Card data-zaghloul-engagement-command="v3" data-ai-staff-command="context-v1" className=',
        "Zaghloul shared command marker",
    )
    return replace_once(
        text,
        '<Badge variant="secondary" className="w-fit rounded-full px-3 py-1.5 text-[11px] font-bold">{ar ? "واجهة قراءة وتنقل" : "Read & navigate"}</Badge>',
        '<div className="flex flex-wrap items-center gap-2"><Badge variant="secondary" className="w-fit rounded-full px-3 py-1.5 text-[11px] font-bold">{ar ? `المساحة الحالية: ${zaghloulWorkspaceLabel}` : `Current workspace: ${zaghloulWorkspaceLabel}`}</Badge><Badge variant="outline" className="w-fit rounded-full px-3 py-1.5 text-[10px] font-bold text-muted-foreground">{ar ? "قراءة وتنقل فقط" : "Read & navigate only"}</Badge></div>',
        "Zaghloul current workspace context",
    )


def patch_tara(text: str) -> str:
    text = replace_once(
        text,
        '    const [taraWorkspace, setTaraWorkspace] = useState(initialTab);\n',
        '''    const [taraWorkspace, setTaraWorkspace] = useState(initialTab);\n    const taraWorkspaceLabel = (isRTL ? {\n      settings: "الإعدادات", providers: "مزودو الذكاء الاصطناعي", voice: "الصوت وElevenLabs", moderators: "المودريتور", campaigns: "الحملات", qualification: "التأهيل", followups: "المتابعات", social: "القنوات الاجتماعية", knowledge: "المعرفة", test: "الاختبار", logs: "السجلات",\n    } : {\n      settings: "Settings", providers: "AI Providers", voice: "Voice & ElevenLabs", moderators: "Moderator", campaigns: "Campaigns", qualification: "Qualification", followups: "Follow-ups", social: "Social Channels", knowledge: "Knowledge", test: "Test", logs: "Logs",\n    })[taraWorkspace] || taraWorkspace;\n''',
        "Tara workspace label",
    )
    text = replace_once(
        text,
        '<Card data-tara-sales-command="v3" className=',
        '<Card data-tara-sales-command="v3" data-ai-staff-command="context-v1" className=',
        "Tara shared command marker",
    )
    return replace_once(
        text,
        '<Badge variant="secondary" className="w-fit rounded-full px-3 py-1.5 text-[11px] font-bold">{isRTL ? (scopeId ? `نطاق الحملة: ${scopeId}` : "النطاق الحالي: عام") : (scopeId ? `Campaign scope: ${scopeId}` : "Current scope: Global")}</Badge>',
        '<div className="flex flex-wrap items-center gap-2"><Badge variant="secondary" className="w-fit rounded-full px-3 py-1.5 text-[11px] font-bold">{isRTL ? `المساحة الحالية: ${taraWorkspaceLabel}` : `Current workspace: ${taraWorkspaceLabel}`}</Badge><Badge variant="outline" className="w-fit rounded-full px-3 py-1.5 text-[10px] font-bold text-muted-foreground">{isRTL ? (scopeId ? `نطاق الحملة: ${scopeId}` : "النطاق: عام") : (scopeId ? `Campaign scope: ${scopeId}` : "Scope: Global")}</Badge></div>',
        "Tara current workspace context",
    )


def patch_felfel(text: str) -> str:
    return replace_once(
        text,
        '<Card data-felfel-meeting-command="v9" className=',
        '<Card data-felfel-meeting-command="v9" data-ai-staff-command="context-v1" className=',
        "Felfel shared command marker",
    )


PATCHERS = {
    "darwish": patch_darwish,
    "zaghloul": patch_zaghloul,
    "tara": patch_tara,
    "felfel": patch_felfel,
}


def verify() -> None:
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
        ],
    }
    for name, items in required.items():
        missing = [item for item in items if item not in texts[name]]
        if missing:
            raise RuntimeError(f"{name}: missing preserved/Phase 13 markers: {', '.join(missing)}")

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
            if 'data-ai-staff-command="context-v1"' in text:
                raise RuntimeError(f"{name}: Phase 13 marker already present")
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
