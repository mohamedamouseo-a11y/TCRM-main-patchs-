#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
import subprocess

ROOT = pathlib.Path.cwd()
TARGET = pathlib.Path("client/src/pages/ZaghloulV5Page.tsx")
EXPECTED_BLOB = "ad2fa7ce229e4826dc6c22d524b30d28f43d76a7"


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
        raise RuntimeError(f"Zaghloul base blob mismatch: expected {EXPECTED_BLOB}, got {actual}")


def patched(text: str) -> str:
    text = replace_once(
        text,
        '''  const [manualRefreshPending, setManualRefreshPending] = useState(false);\n  const [lastRefreshedAt, setLastRefreshedAt] = useState<Date | null>(null);\n''',
        '''  const [manualRefreshPending, setManualRefreshPending] = useState(false);\n  const [lastRefreshedAt, setLastRefreshedAt] = useState<Date | null>(null);\n  const [zaghloulWorkspace, setZaghloulWorkspace] = useState("dashboard");\n''',
        "controlled workspace state",
    )

    text = replace_once(
        text,
        '''        {/* Main tabs */}\n        <Tabs defaultValue="dashboard" className="w-full space-y-4" data-zaghloul-workspace="grouped-nav-v2">\n''',
        '''        <Card data-zaghloul-engagement-command="v3" className="overflow-hidden rounded-[22px] border border-violet-500/15 bg-gradient-to-r from-violet-500/[0.055] via-card to-card shadow-[0_14px_36px_-30px_rgba(15,23,42,0.72)]">\n          <CardContent className="p-4 md:p-5">\n            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">\n              <div>\n                <div className="flex flex-wrap items-center gap-2">\n                  <p className="text-sm font-black">{ar ? "مركز قيادة التفاعل" : "Engagement Command"}</p>\n                  <Badge variant="outline" className="rounded-full border-violet-500/20 bg-background/80 text-[10px] font-bold text-violet-700 dark:text-violet-300">{ar ? "تنقل تشغيلي فقط" : "Navigation only"}</Badge>\n                </div>\n                <p className="mt-1 max-w-3xl text-xs leading-5 text-muted-foreground">{ar ? "أربع إشارات سريعة تنقلك مباشرة إلى مساحة العمل الأهم الآن، بدون إرسال أو تعديل أو تشغيل أي إجراء." : "Four live signals take the operator directly to the most relevant workspace without sending, editing, or running any business action."}</p>\n              </div>\n              <Badge variant="secondary" className="w-fit rounded-full px-3 py-1.5 text-[11px] font-bold">{ar ? "واجهة قراءة وتنقل" : "Read & navigate"}</Badge>\n            </div>\n            <div className="mt-4 grid gap-2 sm:grid-cols-2 xl:grid-cols-4">\n              {[\n                { key: "contacts", label: ar ? "الجمهور" : "Audience", value: dashboardQ.data?.totalContacts ?? contactsQ.data?.total ?? 0, hint: ar ? "جهات اتصال" : "contacts", Icon: Users },\n                { key: "inbox", label: ar ? "انتباه الصندوق" : "Inbox Attention", value: dashboardQ.data?.unreadMessages ?? inboxQ.data?.counters?.unread ?? 0, hint: ar ? "رسائل غير مقروءة" : "unread messages", Icon: MessageSquare },\n                { key: "automations", label: ar ? "الأتمتة" : "Automation", value: automationsQ.data?.items?.length ?? 0, hint: ar ? "رحلات متاحة" : "available journeys", Icon: Zap },\n                { key: "team", label: ar ? "الفريق والإدارة" : "Team & Admin", value: teamQ.data?.total ?? 0, hint: ar ? "أعضاء الفريق" : "team members", Icon: Shield },\n              ].map(({ key, label, value, hint, Icon }) => (\n                <button\n                  key={key}\n                  type="button"\n                  aria-pressed={zaghloulWorkspace === key}\n                  onClick={() => setZaghloulWorkspace(key)}\n                  className={"flex min-h-[88px] items-center justify-between gap-3 rounded-2xl border p-3.5 text-start transition-all " + (zaghloulWorkspace === key ? "border-violet-500/30 bg-violet-500/10 shadow-sm" : "border-border/70 bg-background/75 hover:border-violet-500/20 hover:bg-violet-500/[0.04]")}\n                >\n                  <span className="flex min-w-0 items-center gap-3"><span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-violet-500/10 text-violet-700 dark:text-violet-300"><Icon className="h-4 w-4" /></span><span className="min-w-0"><span className="block truncate text-xs font-black">{label}</span><span className="mt-1 block truncate text-[10px] font-medium text-muted-foreground">{hint}</span></span></span>\n                  <span className="text-xl font-black tracking-tight">{value}</span>\n                </button>\n              ))}\n            </div>\n          </CardContent>\n        </Card>\n\n        {/* Main tabs */}\n        <Tabs value={zaghloulWorkspace} onValueChange={setZaghloulWorkspace} className="w-full space-y-4" data-zaghloul-workspace="grouped-nav-v2">\n''',
        "engagement command and controlled tabs",
    )

    return text


def verify() -> None:
    text = read()
    required = [
        'data-zaghloul-engagement-command="v3"',
        'const [zaghloulWorkspace, setZaghloulWorkspace] = useState("dashboard")',
        '<Tabs value={zaghloulWorkspace} onValueChange={setZaghloulWorkspace}',
        'aria-pressed={zaghloulWorkspace === key}',
        'dashboardQ.data?.totalContacts',
        'dashboardQ.data?.unreadMessages',
        'automationsQ.data?.items?.length',
        'teamQ.data?.total',
        'data-zaghloul-workspace="grouped-nav-v2"',
        'data-ai-staff-refresh="zaghloul-v1"',
        'data-ai-staff-shell="consistency-v1"',
        'const refreshZaghloulData = async',
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise RuntimeError("Missing Phase 10/preserved markers: " + ", ".join(missing))
    if text.count('data-zaghloul-engagement-command="v3"') != 1:
        raise RuntimeError("Engagement command marker count mismatch")
    for tab in ["dashboard", "inbox", "contacts", "pipelines", "broadcasts", "automations", "flows", "aiagents", "team", "settings", "developer"]:
        if text.count(f'<TabsTrigger value="{tab}"') != 1:
            raise RuntimeError(f"TabsTrigger count mismatch for {tab}")
        if text.count(f'<TabsContent value="{tab}"') != 1:
            raise RuntimeError(f"TabsContent count mismatch for {tab}")
    print(f"ZAGHLOUL_TARGET_BLOB={git_blob(TARGET)}")
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
        print(f"ZAGHLOUL_BASE_BLOB={EXPECTED_BLOB}")
        print("CHECK=PASS")
        return
    if args.apply:
        require_base()
        text = read()
        if 'data-zaghloul-engagement-command="v3"' in text:
            raise RuntimeError("Phase 10 marker already present")
        write(patched(text))
        print(f"ZAGHLOUL_TARGET_BLOB={git_blob(TARGET)}")
        print("APPLY=PASS")
        return
    verify()


if __name__ == "__main__":
    main()
