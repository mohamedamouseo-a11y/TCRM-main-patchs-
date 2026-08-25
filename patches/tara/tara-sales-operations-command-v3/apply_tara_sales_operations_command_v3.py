#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
import subprocess

ROOT = pathlib.Path.cwd()
TARGET = pathlib.Path("client/src/pages/TaraAgentPage.tsx")
EXPECTED_BLOB = "7a804f534d2be5ee1dd3da2d535ff4bf6c16724b"


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
        raise RuntimeError(f"Tara base blob mismatch: expected {EXPECTED_BLOB}, got {actual}")


def patched(text: str) -> str:
    text = replace_once(
        text,
        '    const [manualRefreshPending, setManualRefreshPending] = useState(false);\n    const [lastRefreshedAt, setLastRefreshedAt] = useState<Date | null>(null);\n',
        '    const [manualRefreshPending, setManualRefreshPending] = useState(false);\n    const [lastRefreshedAt, setLastRefreshedAt] = useState<Date | null>(null);\n    const [taraWorkspace, setTaraWorkspace] = useState(initialTab);\n',
        "controlled Tara workspace state",
    )

    text = replace_once(
        text,
        '      </section>\n\n      <Tabs defaultValue={initialTab} className="space-y-4">\n',
        '''      </section>\n\n      <Card data-tara-sales-command="v3" className="overflow-hidden rounded-[22px] border border-primary/15 bg-gradient-to-r from-primary/[0.055] via-card to-card shadow-[0_14px_36px_-30px_rgba(15,23,42,0.72)]">\n        <CardContent className="p-4 md:p-5">\n          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">\n            <div>\n              <div className="flex flex-wrap items-center gap-2">\n                <p className="text-sm font-black">{isRTL ? "مركز عمليات المبيعات" : "Sales Operations Command"}</p>\n                <Badge variant="outline" className="rounded-full border-primary/20 bg-background/80 text-[10px] font-bold text-primary">{isRTL ? "تنقل فقط — بدون تنفيذ" : "Navigation only — no execution"}</Badge>\n              </div>\n              <p className="mt-1 max-w-3xl text-xs leading-5 text-muted-foreground">{isRTL ? "انتقل مباشرة إلى إعداد المبيعات المطلوب باستخدام البيانات المحملة حاليًا. هذه المؤشرات للعرض والتنقل فقط ولا تحفظ أو ترسل أو تشغل أي إجراء." : "Jump directly to the sales setup that needs attention using already-loaded data. These indicators are read-only navigation and never save, send, or execute an operation."}</p>\n            </div>\n            <Badge variant="secondary" className="w-fit rounded-full px-3 py-1.5 text-[11px] font-bold">{isRTL ? (scopeId ? `نطاق الحملة: ${scopeId}` : "النطاق الحالي: عام") : (scopeId ? `Campaign scope: ${scopeId}` : "Current scope: Global")}</Badge>\n          </div>\n          <div className="mt-4 grid gap-2 sm:grid-cols-2 xl:grid-cols-4">\n            {[\n              { key: "campaigns", label: isRTL ? "الحملات" : "Campaigns", value: campaigns.length, hint: isRTL ? "إعدادات الحملات الحالية" : "configured campaigns", Icon: Brain },\n              { key: "qualification", label: isRTL ? "التأهيل" : "Qualification", value: (fieldsQ.data || []).length, hint: isRTL ? "حقول التأهيل في النطاق" : "qualification fields in scope", Icon: FileQuestion },\n              { key: "followups", label: isRTL ? "المتابعات" : "Follow-ups", value: (followupsQ.data || []).length, hint: isRTL ? "قواعد المتابعة في النطاق" : "follow-up rules in scope", Icon: RefreshCw },\n              { key: "knowledge", label: isRTL ? "المعرفة" : "Knowledge", value: (knowledgeQ.data || []).length, hint: isRTL ? "عناصر المعرفة في النطاق" : "knowledge items in scope", Icon: Database },\n            ].map(({ key, label, value, hint, Icon }) => (\n              <button\n                key={key}\n                type="button"\n                aria-pressed={taraWorkspace === key}\n                onClick={() => setTaraWorkspace(key)}\n                className={"flex min-h-[88px] items-center justify-between gap-3 rounded-2xl border p-3.5 text-start transition-all " + (taraWorkspace === key ? "border-primary/30 bg-primary/10 shadow-sm" : "border-border/70 bg-background/75 hover:border-primary/20 hover:bg-primary/[0.04]")}\n              >\n                <span className="flex min-w-0 items-center gap-3"><span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-primary/10 text-primary"><Icon className="h-4 w-4" /></span><span className="min-w-0"><span className="block truncate text-xs font-black">{label}</span><span className="mt-1 block truncate text-[10px] font-medium text-muted-foreground">{hint}</span></span></span>\n                <span className="text-xl font-black tracking-tight">{value}</span>\n              </button>\n            ))}\n          </div>\n        </CardContent>\n      </Card>\n\n      <Tabs value={taraWorkspace} onValueChange={setTaraWorkspace} className="space-y-4">\n''',
        "sales operations command and controlled tabs",
    )

    return text


def verify() -> None:
    text = read()
    required = [
        'data-tara-sales-command="v3"',
        'const [taraWorkspace, setTaraWorkspace] = useState(initialTab)',
        '<Tabs value={taraWorkspace} onValueChange={setTaraWorkspace}',
        'aria-pressed={taraWorkspace === key}',
        'onClick={() => setTaraWorkspace(key)}',
        'value: campaigns.length',
        'value: (fieldsQ.data || []).length',
        'value: (followupsQ.data || []).length',
        'value: (knowledgeQ.data || []).length',
        'data-tara-workspace="control-center-v2"',
        'data-ai-staff-shell="consistency-v1"',
        'data-ai-staff-refresh="tara-v1"',
        'const refreshTaraData = async',
        'const saveSettingsM = trpc.tara.saveSettings.useMutation',
        'const saveCampaignM = trpc.tara.saveCampaign.useMutation',
        'const saveFieldM = trpc.tara.saveQualificationField.useMutation',
        'const saveKnowledgeM = trpc.tara.saveKnowledge.useMutation',
        'const saveFollowupM = trpc.tara.saveFollowupRule.useMutation',
        'const processQueueM = trpc.tara.processQueue.useMutation',
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise RuntimeError("Missing Phase 11/preserved markers: " + ", ".join(missing))
    if text.count('data-tara-sales-command="v3"') != 1:
        raise RuntimeError("Sales command marker count mismatch")
    if text.count('data-tara-workspace="control-center-v2"') != 1:
        raise RuntimeError("Tara workspace marker count mismatch")
    start = text.index('data-tara-sales-command="v3"')
    end = text.index('data-tara-workspace="control-center-v2"', start)
    command_block = text[start:end]
    if '.mutate(' in command_block:
        raise RuntimeError("Sales command must remain mutation-free")
    print(f"TARA_TARGET_BLOB={git_blob(TARGET)}")
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
        print(f"TARA_BASE_BLOB={EXPECTED_BLOB}")
        print("CHECK=PASS")
        return
    if args.apply:
        require_base()
        text = read()
        if 'data-tara-sales-command="v3"' in text:
            raise RuntimeError("Phase 11 marker already present")
        write(patched(text))
        print(f"TARA_TARGET_BLOB={git_blob(TARGET)}")
        print("APPLY=PASS")
        return
    verify()


if __name__ == "__main__":
    main()
