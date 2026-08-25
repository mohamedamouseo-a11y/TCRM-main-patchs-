#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import subprocess
from pathlib import Path

TARGET = Path("client/src/pages/DarwishPage.tsx")
BASE_BLOB = "372246b4fc4f4adf3f6b7b8c3f2a1ac12dfbac2e"
MARKER = 'data-darwish-workspace="supervisor-v2"'

TABS_IMPORT = 'import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";\n'
LABEL_IMPORT = 'import { Label } from "@/components/ui/label";\n'
OLD_ROOT = '<div dir={isRTL ? "rtl" : "ltr"} className="mx-auto max-w-7xl space-y-6 p-4 md:p-6">'
NEW_ROOT = '<div dir={isRTL ? "rtl" : "ltr"} className="mx-auto max-w-[1660px] space-y-4 p-4 md:p-5 xl:p-6">'

INTEGRATION_ANCHOR = '      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-6">\n        <Card><CardHeader className="pb-2"><CardTitle className="flex items-center gap-2 text-base"><Server className="h-4 w-4" />{ar ? "حالة Chatwoot" : "Chatwoot"}</CardTitle>'
VOICE_ANCHOR = '      <DarwishVoiceOfCustomerPanel />'
SUPERVISOR_ANCHOR = '      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">\n        <Card><CardHeader className="pb-2"><CardTitle className="text-base">{ar ? "حالات تحت المراقبة" : "Monitored"}</CardTitle>'
ACTION_ANCHOR = '      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">\n        <Card><CardHeader className="pb-2"><CardTitle className="text-base">{ar ? "مقترحات معلقة" : "Proposed"}</CardTitle>'
OPERATIONS_ANCHOR = '      <Card><CardHeader><CardTitle>{ar ? "ربط مجموعة بعميل" : "Link a group to a client"}</CardTitle>'
ROOT_END = '\n    </div>\n  </CRMLayout>;'
LIMITED_AUTOMATION = '\n\n      <DarwishLimitedAutomationCard />'

WORKSPACE_OPEN = '''      <Card data-darwish-workspace="supervisor-v2" className="overflow-hidden rounded-[22px] border-border/70 bg-card shadow-[0_14px_36px_-30px_rgba(15,23,42,0.72)]">
        <CardContent className="flex flex-col gap-4 p-4 md:flex-row md:items-center md:justify-between md:p-5">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-sm font-black">{ar ? "مساحة عمل المشرف" : "Supervisor Workspace"}</p>
              <Badge variant="outline" className="rounded-full bg-cyan-500/5 text-[11px] font-bold text-cyan-700 dark:text-cyan-300"><ShieldCheck className="me-1 h-3.5 w-3.5" />{ar ? "تحكم بشري" : "Human controlled"}</Badge>
            </div>
            <p className="mt-1 max-w-3xl text-xs leading-5 text-muted-foreground">{ar ? "تم تنظيم أدوات درويش في أربع مساحات مركزة بدل الصفحة الطويلة، بدون حذف أي وظيفة أو تغيير منطق الموافقات." : "Darwish is organized into four focused work areas instead of one long page, without removing capabilities or changing approval logic."}</p>
          </div>
          <div className="flex flex-wrap gap-2 text-xs">
            <Badge variant="secondary" className="rounded-full px-3 py-1.5">{ar ? `تنبيهات: ${supervisorQ.data?.activeAlerts || 0}` : `Alerts: ${supervisorQ.data?.activeAlerts || 0}`}</Badge>
            <Badge variant="secondary" className="rounded-full px-3 py-1.5">{actionCapabilitiesQ.data?.approvedOutboundEnabled ? (ar ? "Outbound معتمد" : "Approved outbound") : (ar ? "Outbound مقفول" : "Outbound locked")}</Badge>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="intelligence" className="space-y-4">
        <TabsList className="sticky top-2 z-20 h-auto w-full flex-nowrap justify-start gap-1 overflow-x-auto rounded-2xl border border-border/70 bg-background/90 p-1.5 shadow-sm backdrop-blur-xl [scrollbar-width:none] [&::-webkit-scrollbar]:hidden [&_[role=tab]]:h-11 [&_[role=tab]]:shrink-0 [&_[role=tab]]:rounded-xl [&_[role=tab]]:px-4 [&_[role=tab]]:text-xs [&_[role=tab]]:font-bold [&_[data-state=active]]:bg-cyan-500/10 [&_[data-state=active]]:text-cyan-700 [&_[data-state=active]]:shadow-none dark:[&_[data-state=active]]:text-cyan-300">
          <TabsTrigger value="intelligence" className="gap-2"><Brain className="h-4 w-4" />{ar ? "ذكاء العملاء" : "Customer Intelligence"}</TabsTrigger>
          <TabsTrigger value="supervision" className="gap-2"><Users2 className="h-4 w-4" />{ar ? "الإشراف" : "Supervision"}</TabsTrigger>
          <TabsTrigger value="actions" className="gap-2"><Sparkles className="h-4 w-4" />{ar ? "الإجراءات والأتمتة" : "Actions & Automation"}</TabsTrigger>
          <TabsTrigger value="operations" className="gap-2"><Server className="h-4 w-4" />{ar ? "التشغيل والربط" : "Operations & Mapping"}</TabsTrigger>
        </TabsList>

        <TabsContent value="intelligence" className="mt-0 space-y-4">
'''

BETWEEN_INTELLIGENCE_SUPERVISION = '''        </TabsContent>

        <TabsContent value="supervision" className="mt-0 space-y-4">
'''

BETWEEN_SUPERVISION_ACTIONS = '''        </TabsContent>

        <TabsContent value="actions" className="mt-0 space-y-4">
          <DarwishLimitedAutomationCard />
'''

BETWEEN_ACTIONS_OPERATIONS = '''        </TabsContent>

        <TabsContent value="operations" className="mt-0 space-y-4">
'''

WORKSPACE_CLOSE = '''        </TabsContent>
      </Tabs>
'''


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()


def repo_head() -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return None


def require_once(text: str, needle: str, label: str) -> int:
    count = text.count(needle)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    return text.index(needle)


def transform(source: str) -> str:
    if MARKER in source:
        raise SystemExit("Patch marker already present; refusing to reapply")

    require_once(source, LABEL_IMPORT, "Label import")
    require_once(source, OLD_ROOT, "Darwish root layout")
    require_once(source, INTEGRATION_ANCHOR, "integration section")
    require_once(source, VOICE_ANCHOR, "Voice of Customer section")
    require_once(source, SUPERVISOR_ANCHOR, "supervision section")
    require_once(source, ACTION_ANCHOR, "action section")
    require_once(source, OPERATIONS_ANCHOR, "operations section")
    require_once(source, ROOT_END, "page root close")
    require_once(source, LIMITED_AUTOMATION, "Limited Safe Automation card")

    source = source.replace(LABEL_IMPORT, LABEL_IMPORT + TABS_IMPORT, 1)
    source = source.replace(OLD_ROOT, NEW_ROOT, 1)

    integration_start = source.index(INTEGRATION_ANCHOR)
    voice_start = source.index(VOICE_ANCHOR)
    supervisor_start = source.index(SUPERVISOR_ANCHOR)
    action_start = source.index(ACTION_ANCHOR)
    operations_start = source.index(OPERATIONS_ANCHOR)
    root_end = source.rindex(ROOT_END)

    if not (integration_start < voice_start < supervisor_start < action_start < operations_start < root_end):
        raise SystemExit("Unexpected Darwish section ordering; refusing to modify")

    prefix = source[:integration_start]
    integration = source[integration_start:voice_start]
    intelligence = source[voice_start:supervisor_start]
    supervision = source[supervisor_start:action_start]
    actions = source[action_start:operations_start]
    operations = source[operations_start:root_end]
    suffix = source[root_end:]

    if intelligence.count(LIMITED_AUTOMATION) != 1:
        raise SystemExit("Limited Safe Automation card is not in the expected intelligence segment")
    intelligence = intelligence.replace(LIMITED_AUTOMATION, "", 1)

    rebuilt = (
        prefix
        + WORKSPACE_OPEN
        + intelligence
        + BETWEEN_INTELLIGENCE_SUPERVISION
        + supervision
        + BETWEEN_SUPERVISION_ACTIONS
        + actions
        + BETWEEN_ACTIONS_OPERATIONS
        + integration
        + operations
        + WORKSPACE_CLOSE
        + suffix
    )

    if rebuilt.count(MARKER) != 1:
        raise SystemExit("Workspace marker verification failed")
    if rebuilt.count("<DarwishLimitedAutomationCard />") != 1:
        raise SystemExit("Limited Safe Automation must remain exactly once")
    for value in ("intelligence", "supervision", "actions", "operations"):
        if rebuilt.count(f'<TabsContent value="{value}"') != 1:
            raise SystemExit(f"TabsContent {value} missing or duplicated")
    return rebuilt


def verify_text(text: str) -> None:
    checks = [
        MARKER,
        'defaultValue="intelligence"',
        '<TabsTrigger value="intelligence"',
        '<TabsTrigger value="supervision"',
        '<TabsTrigger value="actions"',
        '<TabsTrigger value="operations"',
        '<DarwishVoiceOfCustomerPanel />',
        '<DarwishDemandProblemIntelligencePanel />',
        '<DarwishCustomerMemoryPanel />',
        '<DarwishHandlingIntelligencePanel />',
        '<DarwishManagementIntelligencePanel />',
        '<DarwishLimitedAutomationCard />',
        '"Human action queue"',
        '"Link a group to a client"',
        '"Recent group jobs"',
    ]
    missing = [item for item in checks if item not in text]
    if missing:
        raise SystemExit("Verification failed; missing: " + ", ".join(missing))
    if text.count("<DarwishLimitedAutomationCard />") != 1:
        raise SystemExit("Verification failed; Limited Safe Automation count is not 1")


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()

    if not TARGET.exists():
        raise SystemExit(f"Missing target: {TARGET}")

    raw = TARGET.read_bytes()
    current_blob = git_blob_sha(raw)
    head = repo_head()

    if args.verify:
        text = raw.decode("utf-8")
        verify_text(text)
        print(f"VERIFY=PASS blob={current_blob} head={head or 'unknown'} marker={MARKER}")
        return

    if current_blob != BASE_BLOB:
        raise SystemExit(f"Baseline mismatch: expected {BASE_BLOB}, got {current_blob}; HEAD={head or 'unknown'}")

    text = raw.decode("utf-8")
    result = transform(text)
    result_blob = git_blob_sha(result.encode("utf-8"))

    if args.check:
        verify_text(result)
        print(f"CHECK=PASS base_blob={current_blob} target_blob={result_blob} head={head or 'unknown'}")
        return

    TARGET.write_text(result, encoding="utf-8")
    verify_text(TARGET.read_text(encoding="utf-8"))
    print(f"APPLY=PASS base_blob={current_blob} target_blob={result_blob} head={head or 'unknown'}")


if __name__ == "__main__":
    main()
