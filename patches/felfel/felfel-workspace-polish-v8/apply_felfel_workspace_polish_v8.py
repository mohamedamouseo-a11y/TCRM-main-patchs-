#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
import re
import subprocess

ROOT = pathlib.Path.cwd()
TARGET = pathlib.Path("client/src/pages/FelfelPage.tsx")
EXPECTED_BLOB = "a0bf37f53ef8d657793d8b4afa2b366133ed7e28"


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


def wrap_card_by_anchor(text: str, anchor: str, marker: str, ar_label: str, en_label: str, open_default: bool = False) -> str:
    if text.count(anchor) != 1:
        raise RuntimeError(f"{marker}: expected one anchor, found {text.count(anchor)}")
    anchor_index = text.index(anchor)
    card_start = text.rfind("<Card", 0, anchor_index)
    if card_start < 0:
        raise RuntimeError(f"{marker}: opening Card not found")

    token_re = re.compile(r"<Card(?:\s[^>]*)?>|</Card>")
    depth = 0
    card_end = None
    for match in token_re.finditer(text, card_start):
        token = match.group(0)
        if token.startswith("</Card"):
            depth -= 1
            if depth == 0:
                card_end = match.end()
                break
        else:
            depth += 1
    if card_end is None:
        raise RuntimeError(f"{marker}: matching Card close not found")

    original = text[card_start:card_end]
    open_attr = " open" if open_default else ""
    wrapper = f'''<details data-felfel-section="{marker}"{open_attr} className="group overflow-hidden rounded-2xl border border-border/70 bg-card shadow-sm">
                            <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-4 py-3 text-sm font-black transition-colors hover:bg-muted/40 [&::-webkit-details-marker]:hidden"><span>{{ar ? "{ar_label}" : "{en_label}"}}</span><span className="text-xs font-semibold text-muted-foreground transition-transform group-open:rotate-180">⌄</span></summary>
                            <div className="border-t border-border/60 p-3 md:p-4">
{original}
                            </div>
                          </details>'''
    return text[:card_start] + wrapper + text[card_end:]


def require_base() -> None:
    actual = git_blob(TARGET)
    if actual != EXPECTED_BLOB:
        raise RuntimeError(f"Felfel base blob mismatch: expected {EXPECTED_BLOB}, got {actual}")


def patched(text: str) -> str:
    text = replace_once(
        text,
        '''function EmptyState({ ar, label }: { ar: boolean; label: string }) {
  return <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">{ar ? `لا توجد ${label} حاليًا` : `No ${label} available`}</div>;
}
''',
        '''function EmptyState({ ar, label }: { ar: boolean; label: string }) {
  return (
    <div className="grid min-h-[210px] place-items-center rounded-2xl border border-dashed border-border/80 bg-gradient-to-b from-background to-muted/15 p-6 text-center">
      <div className="max-w-md">
        <div className="relative mx-auto grid h-16 w-16 place-items-center rounded-full bg-orange-500/10 text-orange-600 dark:text-orange-300"><span className="absolute -start-2 top-1 text-xs">✦</span><Video className="h-7 w-7" /><span className="absolute -end-2 bottom-1 text-[10px]">✦</span></div>
        <p className="mt-3 text-sm font-black text-foreground">{ar ? `لا توجد ${label} حاليًا` : `No ${label} available`}</p>
        <p className="mt-1 text-xs leading-5 text-muted-foreground">{ar ? "ابدأ اجتماعًا جديدًا أو اختر اجتماعًا سابقًا عندما يكون متاحًا؛ ستظهر البيانات هنا بدون تغيير أي شيء تلقائيًا." : "Start a new meeting or select a previous one when available. Felfel will surface the data here without taking any automatic CRM action."}</p>
      </div>
    </div>
  );
}
''',
        "premium empty state",
    )

    text = replace_once(
        text,
        '''        {healthQ.error && <QueryError ar={ar} message={healthQ.error.message} />}
        {capabilitiesQ.error && <QueryError ar={ar} message={capabilitiesQ.error.message} />}

        <Tabs defaultValue="live" className="w-full space-y-4">
''',
        '''        {healthQ.error && <QueryError ar={ar} message={healthQ.error.message} />}
        {capabilitiesQ.error && <QueryError ar={ar} message={capabilitiesQ.error.message} />}

        <Card data-felfel-workspace-summary="v8" className="rounded-2xl border-border/70 bg-card shadow-[0_12px_28px_-26px_rgba(15,23,42,0.65)]">
          <CardContent className="flex flex-col gap-3 p-4 md:flex-row md:items-center md:justify-between">
            <div><p className="text-sm font-black">{ar ? "مساحة عمل ذكاء الاجتماعات" : "Meeting Intelligence Workspace"}</p><p className="mt-1 text-xs text-muted-foreground">{ar ? "اعرف حالة الجلسة والتفريغ والتحليل وربط CRM قبل فتح التفاصيل." : "See session, transcript, analysis, and CRM context at a glance before opening detailed work areas."}</p></div>
            <div className="flex flex-wrap gap-2 text-[11px] font-bold">
              <Badge variant="outline" className="rounded-full">{meeting ? (ar ? `جلسة: ${currentStatus}` : `Session: ${currentStatus}`) : (ar ? "لا توجد جلسة نشطة" : "No active session")}</Badge>
              <Badge variant="outline" className="rounded-full">{ar ? `التفريغ: ${transcript?.segments?.length ?? 0}` : `Transcript: ${transcript?.segments?.length ?? 0}`}</Badge>
              <Badge variant={intelligence ? "outline" : "secondary"} className="rounded-full">{intelligence ? (ar ? "التحليل جاهز" : "Analysis ready") : (ar ? "بانتظار التحليل" : "Awaiting analysis")}</Badge>
              <Badge variant={crmClientId ? "outline" : "secondary"} className="rounded-full">{crmClientId ? (ar ? "CRM مربوط" : "CRM linked") : (ar ? "CRM غير مربوط" : "CRM not linked")}</Badge>
            </div>
          </CardContent>
        </Card>

        <Tabs data-felfel-workspace="meeting-intelligence-v8" defaultValue="live" className="w-full space-y-4">
''',
        "workspace summary and marker",
    )

    text = wrap_card_by_anchor(text, '"CRM Context & Approved Actions"', "crm-approved-actions", "ربط CRM والمهام المعتمدة", "CRM Context & Approved Actions", False)
    text = wrap_card_by_anchor(text, '"Follow-up Planner"', "follow-up-planner", "خطة المتابعة", "Follow-up Planner", False)
    text = wrap_card_by_anchor(text, '"Meeting Archive & Google Drive"', "meeting-archive", "أرشيف الاجتماع وGoogle Drive", "Meeting Archive & Google Drive", False)
    text = wrap_card_by_anchor(text, '"Felfel\'s Take"', "felfel-take", "رأي فلفل", "Felfel's Take", True)

    return text


def verify() -> None:
    text = read()
    required = [
        'data-felfel-workspace="meeting-intelligence-v8"',
        'data-felfel-workspace-summary="v8"',
        'data-felfel-section="crm-approved-actions"',
        'data-felfel-section="follow-up-planner"',
        'data-felfel-section="meeting-archive"',
        'data-felfel-section="felfel-take"',
        'data-ai-staff-refresh="felfel-v1"',
        'TCRM_FELFEL_REFRESH_COMPLETION_V1',
        'const refreshFelfelData = async',
        'const createMeetingM = trpc.felfel.createMeeting.useMutation',
        'const leaveMeetingM = trpc.felfel.leaveMeeting.useMutation',
        'const analyzeMeetingM = trpc.felfel.analyzeMeeting.useMutation',
        'const createApprovedTasksM = trpc.felfel.createApprovedTasks.useMutation',
        'const createFollowUpM = trpc.felfel.createFollowUp.useMutation',
        'const archiveMeetingM = trpc.felfel.archiveMeeting.useMutation',
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise RuntimeError("Missing markers after patch: " + ", ".join(missing))
    if text.count('data-felfel-section="crm-approved-actions"') != 1:
        raise RuntimeError("CRM approved actions wrapper count mismatch")
    if text.count('data-felfel-section="follow-up-planner"') != 1:
        raise RuntimeError("Follow-up wrapper count mismatch")
    if text.count('data-felfel-section="meeting-archive"') != 1:
        raise RuntimeError("Archive wrapper count mismatch")
    if text.count('data-felfel-section="felfel-take"') != 1:
        raise RuntimeError("Felfel take wrapper count mismatch")
    print(f"FELFEL_TARGET_BLOB={git_blob(TARGET)}")
    print("VERIFY=PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["--check", "--apply", "--verify"])
    args = parser.parse_args()

    if args.mode == "--check":
        require_base()
        print(f"BASE_FELFEL_BLOB={EXPECTED_BLOB}")
        print("CHECK=PASS")
        return

    if args.mode == "--apply":
        require_base()
        text = patched(read())
        write(text)
        print(f"FELFEL_TARGET_BLOB={git_blob(TARGET)}")
        print("APPLY=PASS")
        return

    verify()


if __name__ == "__main__":
    main()
