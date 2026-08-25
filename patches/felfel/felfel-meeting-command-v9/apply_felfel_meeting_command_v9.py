#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
import subprocess

ROOT = pathlib.Path.cwd()
TARGET = pathlib.Path("client/src/pages/FelfelPage.tsx")
EXPECTED_BLOB = "4cd0b430e2c24e41d8aa7bed5204fdb6fec329b4"


def git_blob(path: pathlib.Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], cwd=ROOT, text=True).strip()


def read() -> str:
    return (ROOT / TARGET).read_text(encoding="utf-8")


def write(text: str) -> None:
    (ROOT / TARGET).write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def require_base() -> None:
    actual = git_blob(TARGET)
    if actual != EXPECTED_BLOB:
        raise RuntimeError(f"Felfel base blob mismatch: expected {EXPECTED_BLOB}, got {actual}")


def patched(text: str) -> str:
    text = replace_once(
        text,
        '''  const [manualRefreshPending, setManualRefreshPending] = useState(false);\n  const [lastRefreshedAt, setLastRefreshedAt] = useState<Date | null>(null);\n''',
        '''  const [manualRefreshPending, setManualRefreshPending] = useState(false);\n  const [lastRefreshedAt, setLastRefreshedAt] = useState<Date | null>(null);\n  const [felfelWorkspace, setFelfelWorkspace] = useState("live");\n''',
        "controlled meeting workspace state",
    )

    text = replace_once(
        text,
        '''        <Tabs data-felfel-workspace="meeting-intelligence-v8" defaultValue="live" className="w-full space-y-4">\n''',
        '''        <Card data-felfel-meeting-command="v9" className="overflow-hidden rounded-[22px] border border-orange-500/15 bg-gradient-to-r from-orange-500/[0.055] via-card to-card shadow-[0_14px_36px_-30px_rgba(15,23,42,0.72)]">\n          <CardContent className="p-4 md:p-5">\n            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">\n              <div>\n                <div className="flex flex-wrap items-center gap-2">\n                  <p className="text-sm font-black">{ar ? "مركز قيادة الاجتماعات" : "Meeting Command"}</p>\n                  <Badge variant="outline" className="rounded-full border-orange-500/20 bg-background/80 text-[10px] font-bold text-orange-700 dark:text-orange-300">{ar ? "تنقل فقط — بدون تنفيذ" : "Navigation only — no execution"}</Badge>\n                </div>\n                <p className="mt-1 max-w-3xl text-xs leading-5 text-muted-foreground">{ar ? "انتقل مباشرة إلى مرحلة الاجتماع المطلوبة باستخدام الحالة الحالية، بدون بدء اجتماع أو تحليل أو إنشاء أي عنصر داخل CRM." : "Jump directly to the right meeting stage using the current state without joining a meeting, running analysis, or creating anything in CRM."}</p>\n              </div>\n              <Badge variant="secondary" className="w-fit rounded-full px-3 py-1.5 text-[11px] font-bold">{ar ? `المساحة الحالية: ${felfelWorkspace === "live" ? "الاجتماع المباشر" : felfelWorkspace === "transcript" ? "التفريغ" : felfelWorkspace === "intelligence" ? "الذكاء" : "الاجتماعات الأخيرة"}` : `Current: ${felfelWorkspace === "live" ? "Live Meeting" : felfelWorkspace === "transcript" ? "Transcript" : felfelWorkspace === "intelligence" ? "Intelligence" : "Recent Meetings"}`}</Badge>\n            </div>\n            <div className="mt-4 grid gap-2 sm:grid-cols-2 xl:grid-cols-4">\n              {[\n                { key: "live", label: ar ? "الاجتماع المباشر" : "Live Meeting", value: status?.active ? 1 : 0, hint: ar ? "جلسة نشطة" : "active session", Icon: Activity },\n                { key: "transcript", label: ar ? "التفريغ النصي" : "Transcript", value: transcript?.segments?.length ?? 0, hint: ar ? "مقاطع جاهزة" : "segments available", Icon: Mic2 },\n                { key: "intelligence", label: ar ? "ذكاء الاجتماع" : "Meeting Intelligence", value: intelligence?.actionItems?.length ?? 0, hint: ar ? "مهام مستخرجة" : "extracted action items", Icon: CheckCircle2 },\n                { key: "history", label: ar ? "الاجتماعات الأخيرة" : "Recent Meetings", value: meetingsQ.data?.length ?? 0, hint: ar ? "اجتماعات محمّلة" : "meetings loaded", Icon: History },\n              ].map(({ key, label, value, hint, Icon }) => (\n                <button\n                  key={key}\n                  type="button"\n                  aria-pressed={felfelWorkspace === key}\n                  onClick={() => setFelfelWorkspace(key)}\n                  className={"flex min-h-[88px] items-center justify-between gap-3 rounded-2xl border p-3.5 text-start transition-all " + (felfelWorkspace === key ? "border-orange-500/30 bg-orange-500/10 shadow-sm" : "border-border/70 bg-background/75 hover:border-orange-500/20 hover:bg-orange-500/[0.04]")}\n                >\n                  <span className="flex min-w-0 items-center gap-3"><span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-orange-500/10 text-orange-700 dark:text-orange-300"><Icon className="h-4 w-4" /></span><span className="min-w-0"><span className="block truncate text-xs font-black">{label}</span><span className="mt-1 block truncate text-[10px] font-medium text-muted-foreground">{hint}</span></span></span>\n                  <span className="text-xl font-black tracking-tight">{value}</span>\n                </button>\n              ))}\n            </div>\n          </CardContent>\n        </Card>\n\n        <Tabs data-felfel-workspace="meeting-intelligence-v8" value={felfelWorkspace} onValueChange={setFelfelWorkspace} className="w-full space-y-4">\n''',
        "meeting command and controlled tabs",
    )

    return text


def verify() -> None:
    text = read()
    required = [
        'data-felfel-meeting-command="v9"',
        'const [felfelWorkspace, setFelfelWorkspace] = useState("live")',
        'data-felfel-workspace="meeting-intelligence-v8" value={felfelWorkspace} onValueChange={setFelfelWorkspace}',
        'aria-pressed={felfelWorkspace === key}',
        'onClick={() => setFelfelWorkspace(key)}',
        'value: status?.active ? 1 : 0',
        'value: transcript?.segments?.length ?? 0',
        'value: intelligence?.actionItems?.length ?? 0',
        'value: meetingsQ.data?.length ?? 0',
        'data-felfel-workspace-summary="v8"',
        'data-ai-staff-shell="consistency-v1"',
        'data-ai-staff-hero="consistency-v1"',
        'data-ai-staff-refresh="felfel-v1"',
        'TCRM_FELFEL_REFRESH_COMPLETION_V1',
        'const refreshFelfelData = async',
        'const boundedRefetch = async',
        'Promise.race',
        '6_000',
        'data-felfel-section="crm-approved-actions"',
        'data-felfel-section="follow-up-planner"',
        'data-felfel-section="meeting-archive"',
        'data-felfel-section="felfel-take"',
        'const createMeetingM = trpc.felfel.createMeeting.useMutation',
        'const leaveMeetingM = trpc.felfel.leaveMeeting.useMutation',
        'const analyzeMeetingM = trpc.felfel.analyzeMeeting.useMutation',
        'const createApprovedTasksM = trpc.felfel.createApprovedTasks.useMutation',
        'const createFollowUpM = trpc.felfel.createFollowUp.useMutation',
        'const archiveMeetingM = trpc.felfel.archiveMeeting.useMutation',
        'const createCurrentFollowUp =',
        'const archiveCurrentMeeting =',
        'const submitApprovedActions =',
        '<TabsTrigger value="live"',
        '<TabsTrigger value="transcript"',
        '<TabsTrigger value="intelligence"',
        '<TabsTrigger value="history"',
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise RuntimeError("Missing Phase 12/preserved markers: " + ", ".join(missing))

    if text.count('data-felfel-meeting-command="v9"') != 1:
        raise RuntimeError("Meeting Command marker count mismatch")
    if text.count('data-felfel-workspace="meeting-intelligence-v8"') != 1:
        raise RuntimeError("Felfel workspace marker count mismatch")

    command_start = text.index('data-felfel-meeting-command="v9"')
    tabs_start = text.index('data-felfel-workspace="meeting-intelligence-v8"', command_start)
    command_block = text[command_start:tabs_start]
    if '.mutate(' in command_block:
        raise RuntimeError("Meeting Command must be navigation-only; mutation call detected")

    print(f"FELFEL_TARGET_BLOB={git_blob(TARGET)}")
    print("VERIFY=PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--apply", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = parser.parse_args()

    if args.check:
        require_base()
        print(f"FELFEL_BASE_BLOB={EXPECTED_BLOB}")
        print("CHECK=PASS")
        return

    if args.apply:
        require_base()
        text = read()
        if 'data-felfel-meeting-command="v9"' in text:
            raise RuntimeError("Phase 12 marker already present")
        write(patched(text))
        print(f"FELFEL_TARGET_BLOB={git_blob(TARGET)}")
        print("APPLY=PASS")
        return

    verify()


if __name__ == "__main__":
    main()
