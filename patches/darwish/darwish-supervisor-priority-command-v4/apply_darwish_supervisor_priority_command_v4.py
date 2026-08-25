#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
import subprocess

ROOT = pathlib.Path.cwd()
TARGET = pathlib.Path("client/src/pages/DarwishPage.tsx")
EXPECTED_BLOB = "f90ee0ad2c3f73663e914e3ddad93963795d215f"


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
        raise RuntimeError(f"Darwish base blob mismatch: expected {EXPECTED_BLOB}, got {actual}")


def patched(text: str) -> str:
    text = replace_once(
        text,
        '''  const [manualRefreshPending, setManualRefreshPending] = useState(false);\n  const [lastRefreshedAt, setLastRefreshedAt] = useState<Date | null>(null);\n''',
        '''  const [manualRefreshPending, setManualRefreshPending] = useState(false);\n  const [lastRefreshedAt, setLastRefreshedAt] = useState<Date | null>(null);\n  const [darwishWorkspace, setDarwishWorkspace] = useState("intelligence");\n''',
        "controlled workspace state",
    )

    text = replace_once(
        text,
        '''      </section>\n\n      <Card data-darwish-workspace="supervisor-v3" className="overflow-hidden rounded-[22px] border border-border/70 bg-card shadow-[0_14px_36px_-30px_rgba(15,23,42,0.72)]">\n''',
        '''      </section>\n\n      <Card data-darwish-priority-command="v4" className="overflow-hidden rounded-[22px] border border-cyan-500/15 bg-gradient-to-r from-cyan-500/[0.055] via-card to-card shadow-[0_14px_36px_-30px_rgba(15,23,42,0.72)]">\n        <CardContent className="p-4 md:p-5">\n          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">\n            <div>\n              <div className="flex flex-wrap items-center gap-2">\n                <p className="text-sm font-black">{ar ? "مركز أولويات المشرف" : "Supervisor Priority Command"}</p>\n                <Badge variant="outline" className="rounded-full border-cyan-500/20 bg-background/80 text-[10px] font-bold text-cyan-700 dark:text-cyan-300">{ar ? "تنقل فقط — بدون تنفيذ" : "Navigation only — no execution"}</Badge>\n              </div>\n              <p className="mt-1 max-w-3xl text-xs leading-5 text-muted-foreground">{ar ? "اختصر الطريق إلى مساحة العمل المطلوبة حسب الإشارة الحالية. الأرقام للعرض فقط ولا تنفذ أي إجراء أو تعديل بيانات." : "Jump directly to the right supervisor workspace using the current signals. These indicators are read-only and never execute an action or modify data."}</p>\n            </div>\n            <Badge variant="secondary" className="w-fit rounded-full px-3 py-1.5 text-[11px] font-bold">{ar ? `المساحة الحالية: ${darwishWorkspace === "intelligence" ? "ذكاء العملاء" : darwishWorkspace === "supervision" ? "الإشراف" : darwishWorkspace === "actions" ? "الإجراءات" : "التشغيل"}` : `Current: ${darwishWorkspace === "intelligence" ? "Customer Intelligence" : darwishWorkspace === "supervision" ? "Supervision" : darwishWorkspace === "actions" ? "Actions" : "Operations"}`}</Badge>\n          </div>\n          <div className="mt-4 grid gap-2 sm:grid-cols-2 xl:grid-cols-4">\n            {[\n              { key: "intelligence", label: ar ? "ذكاء العملاء" : "Customer Intelligence", value: intelligenceStatsQ.data?.urgent || 0, hint: ar ? "إشارات عاجلة" : "urgent signals", Icon: Brain },\n              { key: "supervision", label: ar ? "الإشراف" : "Supervision", value: supervisorQ.data?.activeAlerts || 0, hint: ar ? "تنبيهات نشطة" : "active alerts", Icon: Users2 },\n              { key: "actions", label: ar ? "الإجراءات والأتمتة" : "Actions & Automation", value: actionStatsQ.data?.proposed || 0, hint: ar ? "مقترحات بانتظار قرار" : "proposals awaiting decision", Icon: Sparkles },\n              { key: "operations", label: ar ? "التشغيل والربط" : "Operations & Mapping", value: mappingCountsQ.data?.unmappedClients || 0, hint: ar ? "عملاء غير مربوطين" : "unmapped clients", Icon: Server },\n            ].map(({ key, label, value, hint, Icon }) => (\n              <button\n                key={key}\n                type="button"\n                aria-pressed={darwishWorkspace === key}\n                onClick={() => setDarwishWorkspace(key)}\n                className={"flex min-h-[88px] items-center justify-between gap-3 rounded-2xl border p-3.5 text-start transition-all " + (darwishWorkspace === key ? "border-cyan-500/30 bg-cyan-500/10 shadow-sm" : "border-border/70 bg-background/75 hover:border-cyan-500/20 hover:bg-cyan-500/[0.04]")}\n              >\n                <span className="flex min-w-0 items-center gap-3"><span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-cyan-500/10 text-cyan-700 dark:text-cyan-300"><Icon className="h-4 w-4" /></span><span className="min-w-0"><span className="block truncate text-xs font-black">{label}</span><span className="mt-1 block truncate text-[10px] font-medium text-muted-foreground">{hint}</span></span></span>\n                <span className="text-xl font-black tracking-tight">{value}</span>\n              </button>\n            ))}\n          </div>\n        </CardContent>\n      </Card>\n\n      <Card data-darwish-workspace="supervisor-v3" className="overflow-hidden rounded-[22px] border border-border/70 bg-card shadow-[0_14px_36px_-30px_rgba(15,23,42,0.72)]">\n''',
        "priority command card",
    )

    text = replace_once(
        text,
        '''      <Tabs defaultValue="intelligence" className="space-y-4">\n''',
        '''      <Tabs value={darwishWorkspace} onValueChange={setDarwishWorkspace} className="space-y-4">\n''',
        "controlled supervisor tabs",
    )

    return text


def verify() -> None:
    text = read()
    required = [
        'data-darwish-priority-command="v4"',
        'const [darwishWorkspace, setDarwishWorkspace] = useState("intelligence")',
        '<Tabs value={darwishWorkspace} onValueChange={setDarwishWorkspace}',
        'aria-pressed={darwishWorkspace === key}',
        'mappingCountsQ.data?.unmappedClients || 0',
        'data-darwish-workspace="supervisor-v3"',
        'data-ai-staff-shell="consistency-v1"',
        'data-ai-staff-refresh="darwish-v1"',
        'const refreshDarwishData = async',
        'const refreshActionsM = trpc.darwish.refreshActions.useMutation',
        'const draftReplyM = trpc.darwish.draftReply.useMutation',
        'const approveActionM = trpc.darwish.approveAction.useMutation',
        'const rejectActionM = trpc.darwish.rejectAction.useMutation',
        'const executeActionM = trpc.darwish.executeAction.useMutation',
        'const upsertM = trpc.darwish.upsertGroupLink.useMutation',
        'const deleteM = trpc.darwish.deleteGroupLink.useMutation',
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise RuntimeError("Missing Phase 9/preserved markers: " + ", ".join(missing))
    if text.count('data-darwish-priority-command="v4"') != 1:
        raise RuntimeError("Priority command marker count mismatch")
    if text.count('data-darwish-workspace="supervisor-v3"') != 1:
        raise RuntimeError("Supervisor workspace marker count mismatch")
    print(f"DARWISH_TARGET_BLOB={git_blob(TARGET)}")
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
        print(f"DARWISH_BASE_BLOB={EXPECTED_BLOB}")
        print("CHECK=PASS")
        return
    if args.apply:
        require_base()
        text = read()
        if 'data-darwish-priority-command="v4"' in text:
            raise RuntimeError("Phase 9 marker already present")
        write(patched(text))
        print(f"DARWISH_TARGET_BLOB={git_blob(TARGET)}")
        print("APPLY=PASS")
        return
    verify()


if __name__ == "__main__":
    main()
