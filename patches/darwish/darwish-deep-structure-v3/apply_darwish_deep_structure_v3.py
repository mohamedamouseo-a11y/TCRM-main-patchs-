#!/usr/bin/env python3
import argparse
import pathlib
import subprocess
import sys

FILE = pathlib.Path("client/src/pages/DarwishPage.tsx")
BASE_BLOB = "dd8a66589f74d79331a26a319eb6222d7a937393"
MARKER = 'data-darwish-workspace="supervisor-v3"'

DETAIL_CLASS = "group overflow-hidden rounded-2xl border border-border/70 bg-card shadow-sm"
SUMMARY_CLASS = "flex cursor-pointer list-none items-center justify-between gap-3 px-4 py-3 text-sm font-black transition-colors hover:bg-muted/40 [&::-webkit-details-marker]:hidden"


def git_blob(path: pathlib.Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()


def details_open(key: str, ar_label: str, en_label: str, open_by_default: bool = False) -> str:
    open_attr = " open" if open_by_default else ""
    return (
        f'      <details data-darwish-section="{key}"{open_attr} className="{DETAIL_CLASS}">\n'
        f'        <summary className="{SUMMARY_CLASS}"><span>{{ar ? "{ar_label}" : "{en_label}"}}</span><span className="text-xs font-semibold text-muted-foreground group-open:rotate-180">⌄</span></summary>\n'
        f'        <div className="border-t border-border/60 p-3 md:p-4">\n'
    )


def details_close() -> str:
    return "\n        </div>\n      </details>"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly 1 match, found {count}")
    return text.replace(old, new, 1)


def wrap_exact_component(text: str, component: str, key: str, ar_label: str, en_label: str, open_by_default: bool = False) -> str:
    old = f"      <{component} />"
    new = details_open(key, ar_label, en_label, open_by_default) + f"      <{component} />" + details_close()
    return replace_once(text, old, new, key)


def wrap_between(text: str, start_marker: str, end_marker: str, key: str, ar_label: str, en_label: str, open_by_default: bool = False) -> str:
    start = text.find(start_marker)
    if start < 0:
        raise RuntimeError(f"{key}: start marker not found")
    end = text.find(end_marker, start + len(start_marker))
    if end < 0:
        raise RuntimeError(f"{key}: end marker not found")
    chunk = text[start:end].rstrip()
    wrapped = details_open(key, ar_label, en_label, open_by_default) + chunk + details_close() + "\n\n"
    return text[:start] + wrapped + text[end:]


def transform(source: str) -> str:
    if MARKER in source:
        return source

    text = source
    text = replace_once(text, 'data-darwish-workspace="supervisor-v2"', MARKER, "workspace marker")
    text = replace_once(
        text,
        'Darwish is organized into four focused work areas instead of one long page, without removing capabilities or changing approval logic.',
        'Darwish keeps four focused work areas, now with progressive disclosure inside each area so the supervisor sees the right level of detail without excessive scrolling.',
        "workspace English description",
    )
    text = replace_once(
        text,
        'تم تنظيم أدوات درويش في أربع مساحات مركزة بدل الصفحة الطويلة، بدون حذف أي وظيفة أو تغيير منطق الموافقات.',
        'تظل أدوات درويش داخل أربع مساحات واضحة، مع إظهار تدريجي للتفاصيل داخل كل مساحة لتقليل التمرير مع الحفاظ على كل الوظائف ومنطق الموافقات.',
        "workspace Arabic description",
    )

    # Customer Intelligence: keep every capability but collapse the long stack into focused sections.
    text = wrap_exact_component(text, "DarwishVoiceOfCustomerPanel", "intelligence-voc", "صوت العميل", "Voice of Customer", True)
    text = wrap_exact_component(text, "DarwishDemandProblemIntelligencePanel", "intelligence-demand", "الطلب والمشكلات", "Demand & Problems")
    text = wrap_exact_component(text, "DarwishCustomerMemoryPanel", "intelligence-memory", "ذاكرة العميل", "Customer Memory")
    text = wrap_exact_component(text, "DarwishHandlingIntelligencePanel", "intelligence-handling", "ذكاء التعامل", "Handling Intelligence")
    text = wrap_exact_component(text, "DarwishManagementIntelligencePanel", "intelligence-management", "ذكاء الإدارة", "Management Intelligence")

    latest_start = '      <Card><CardHeader><CardTitle>{ar ? "أحدث تحليلات درويش" : "Latest Darwish intelligence"}'
    latest_end = '\n\n        </TabsContent>\n\n        <TabsContent value="supervision"'
    text = wrap_between(text, latest_start, latest_end, "intelligence-latest", "أحدث التحليلات", "Latest Intelligence")

    # Supervision: summary metrics stay visible; detailed supervisor areas collapse below them.
    supervision_grid = '      <div className="grid gap-4 lg:grid-cols-2">'
    digest_start = '      <Card><CardHeader><CardTitle>{ar ? "ملخص الإدارة اليومي" : "Daily management digest"}'
    text = wrap_between(text, supervision_grid, digest_start, "supervision-alerts-team", "التنبيهات وأداء الفريق", "Alerts & Team Performance", True)

    supervision_end = '\n\n        </TabsContent>\n\n        <TabsContent value="actions"'
    text = wrap_between(text, digest_start, supervision_end, "supervision-digest", "الملخص الإداري", "Management Digest")

    # Actions: status metrics remain visible; automation and queue become explicit workflow sections.
    text = wrap_exact_component(text, "DarwishLimitedAutomationCard", "actions-automation", "الأتمتة الآمنة المحدودة", "Limited Safe Automation", True)

    queue_start = '      <Card><CardHeader><div className="flex flex-wrap items-center justify-between gap-2"><div><CardTitle>{ar ? "طابور الإجراءات البشرية" : "Human action queue"}'
    actions_end = '\n\n        </TabsContent>\n\n        <TabsContent value="operations"'
    text = wrap_between(text, queue_start, actions_end, "actions-queue", "طابور الإجراءات البشرية", "Human Action Queue", True)

    # Operations: health cards remain visible; heavy setup/detail blocks are collapsed.
    text = wrap_exact_component(text, "DarwishDataReadinessCard", "operations-readiness", "جاهزية البيانات", "Data Readiness")

    link_start = '      <Card><CardHeader><CardTitle>{ar ? "ربط مجموعة بعميل" : "Link a group to a client"}'
    mappings_start = '      <Card><CardHeader><CardTitle>{ar ? "الروابط الحالية" : "Current mappings"}'
    jobs_start = '      <Card><CardHeader><CardTitle>{ar ? "الأحداث الأخيرة" : "Recent group jobs"}'
    operations_end = '        </TabsContent>\n      </Tabs>'

    text = wrap_between(text, link_start, mappings_start, "operations-link", "ربط مجموعة بعميل", "Link Group to Client")
    text = wrap_between(text, mappings_start, jobs_start, "operations-mappings", "الروابط الحالية", "Current Mappings", True)
    text = wrap_between(text, jobs_start, operations_end, "operations-jobs", "الأحداث الأخيرة", "Recent Group Jobs")

    return text


def verify_source(text: str) -> None:
    required = [
        MARKER,
        'value="intelligence"', 'value="supervision"', 'value="actions"', 'value="operations"',
        "DarwishVoiceOfCustomerPanel", "DarwishDemandProblemIntelligencePanel", "DarwishCustomerMemoryPanel",
        "DarwishHandlingIntelligencePanel", "DarwishManagementIntelligencePanel", "DarwishLimitedAutomationCard",
        "refreshActionsM", "draftReplyM", "approveActionM", "rejectActionM", "executeActionM", "upsertM", "deleteM",
    ]
    for token in required:
        if token not in text:
            raise RuntimeError(f"verify: missing required token: {token}")

    section_keys = [
        "intelligence-voc", "intelligence-demand", "intelligence-memory", "intelligence-handling",
        "intelligence-management", "intelligence-latest", "supervision-alerts-team", "supervision-digest",
        "actions-automation", "actions-queue", "operations-readiness", "operations-link",
        "operations-mappings", "operations-jobs",
    ]
    for key in section_keys:
        token = f'data-darwish-section="{key}"'
        if text.count(token) != 1:
            raise RuntimeError(f"verify: {token} count={text.count(token)}")

    if 'data-darwish-workspace="supervisor-v2"' in text:
        raise RuntimeError("verify: legacy supervisor-v2 marker still present")
    if text.count("<DarwishLimitedAutomationCard />") != 1:
        raise RuntimeError("verify: Limited Safe Automation must remain exactly once")


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--apply", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = parser.parse_args()

    if not FILE.exists():
        print(f"FAIL: missing {FILE}", file=sys.stderr)
        return 2

    current_blob = git_blob(FILE)
    source = FILE.read_text(encoding="utf-8")

    if args.check:
        if current_blob != BASE_BLOB:
            print(f"CHECK=FAIL expected={BASE_BLOB} actual={current_blob}", file=sys.stderr)
            return 3
        if MARKER in source:
            print("CHECK=FAIL patch already appears applied", file=sys.stderr)
            return 4
        # Dry-run transformation proves all guarded anchors are present.
        target = transform(source)
        verify_source(target)
        print(f"CHECK=PASS BASE_BLOB={current_blob}")
        return 0

    if args.apply:
        if current_blob != BASE_BLOB:
            print(f"APPLY=FAIL expected={BASE_BLOB} actual={current_blob}", file=sys.stderr)
            return 5
        target = transform(source)
        verify_source(target)
        FILE.write_text(target, encoding="utf-8")
        print(f"APPLY=PASS TARGET_BLOB={git_blob(FILE)}")
        return 0

    try:
        verify_source(source)
    except Exception as exc:
        print(f"VERIFY=FAIL {exc}", file=sys.stderr)
        return 6
    print(f"VERIFY=PASS TARGET_BLOB={current_blob}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
