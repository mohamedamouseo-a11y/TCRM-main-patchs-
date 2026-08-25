#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

TARGET = Path("client/src/pages/ZaghloulV5Page.tsx")
BASE_BLOB = "ee9cde356d999519e95a594a501175fd80039b1b"
MARKER = 'data-zaghloul-workspace="grouped-nav-v2"'

OLD_ROOT = '<Tabs defaultValue="dashboard" className="w-full space-y-4">'
NEW_ROOT = '<Tabs defaultValue="dashboard" className="w-full space-y-4" data-zaghloul-workspace="grouped-nav-v2">'

OLD_NAV = '''          <TabsList className="h-auto w-full flex-nowrap justify-start gap-1 overflow-x-auto rounded-2xl border border-border/70 bg-muted/30 p-1.5 shadow-sm [scrollbar-width:none] [&::-webkit-scrollbar]:hidden [&_[role=tab]]:h-10 [&_[role=tab]]:shrink-0 [&_[role=tab]]:rounded-xl [&_[role=tab]]:border-b-2 [&_[role=tab]]:border-transparent [&_[role=tab]]:px-4 [&_[role=tab]]:text-xs [&_[role=tab]]:font-bold [&_[data-state=active]]:border-violet-500 [&_[data-state=active]]:bg-background [&_[data-state=active]]:text-foreground [&_[data-state=active]]:shadow-sm">
            <TabsTrigger value="dashboard" className="gap-1.5"><BarChart3 className="h-3.5 w-3.5" />{ar ? "لوحة التحكم" : "Dashboard"}</TabsTrigger>
            <TabsTrigger value="inbox" className="gap-1.5"><MessageSquare className="h-3.5 w-3.5" />{ar ? "الصندوق" : "Inbox"}</TabsTrigger>
            <TabsTrigger value="contacts" className="gap-1.5"><Users className="h-3.5 w-3.5" />{ar ? "جهات الاتصال" : "Contacts"}</TabsTrigger>
            <TabsTrigger value="pipelines" className="gap-1.5"><TrendingUp className="h-3.5 w-3.5" />{ar ? "المبيعات" : "Pipelines"}</TabsTrigger>
            <TabsTrigger value="broadcasts" className="gap-1.5"><Send className="h-3.5 w-3.5" />{ar ? "البث" : "Broadcasts"}</TabsTrigger>
            <TabsTrigger value="automations" className="gap-1.5"><Zap className="h-3.5 w-3.5" />{ar ? "الأتمتة" : "Automations"}</TabsTrigger>
            <TabsTrigger value="flows" className="gap-1.5"><GitBranch className="h-3.5 w-3.5" />{ar ? "التدفقات" : "Flows"}</TabsTrigger>
            <TabsTrigger value="aiagents" className="gap-1.5"><Bot className="h-3.5 w-3.5" />{ar ? "وكلاء AI" : "AI Agents"}</TabsTrigger>
            <TabsTrigger value="team" className="gap-1.5"><Users className="h-3.5 w-3.5" />{ar ? "الفريق" : "Team"}</TabsTrigger>
            <TabsTrigger value="settings" className="gap-1.5"><Settings className="h-3.5 w-3.5" />{ar ? "الإعدادات" : "Settings"}</TabsTrigger>
            <TabsTrigger value="developer" className="gap-1.5"><Code2 className="h-3.5 w-3.5" />{ar ? "المطور" : "Developer"}</TabsTrigger>
          </TabsList>'''

NEW_NAV = '''          <TabsList aria-label={ar ? "تنقل مساحة عمل زغلول" : "Zaghloul workspace navigation"} className="h-auto w-full items-stretch justify-start gap-0 overflow-x-auto rounded-2xl border border-border/70 bg-card/75 p-2 shadow-sm [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
            <div className="flex min-w-max items-stretch gap-2">
              <div className="rounded-xl border border-border/60 bg-muted/25 p-1.5">
                <p className="px-2 pb-1 text-[10px] font-black uppercase tracking-[0.16em] text-muted-foreground">{ar ? "مساحة العمل" : "Core workspace"}</p>
                <div className="flex gap-1">
                  <TabsTrigger value="dashboard" className="h-9 gap-1.5 rounded-lg border-b-2 border-transparent px-3 text-xs font-bold data-[state=active]:border-violet-500 data-[state=active]:bg-background data-[state=active]:shadow-sm"><BarChart3 className="h-3.5 w-3.5" />{ar ? "لوحة التحكم" : "Dashboard"}</TabsTrigger>
                  <TabsTrigger value="contacts" className="h-9 gap-1.5 rounded-lg border-b-2 border-transparent px-3 text-xs font-bold data-[state=active]:border-violet-500 data-[state=active]:bg-background data-[state=active]:shadow-sm"><Users className="h-3.5 w-3.5" />{ar ? "جهات الاتصال" : "Contacts"}</TabsTrigger>
                  <TabsTrigger value="pipelines" className="h-9 gap-1.5 rounded-lg border-b-2 border-transparent px-3 text-xs font-bold data-[state=active]:border-violet-500 data-[state=active]:bg-background data-[state=active]:shadow-sm"><TrendingUp className="h-3.5 w-3.5" />{ar ? "المبيعات" : "Pipelines"}</TabsTrigger>
                </div>
              </div>

              <div className="rounded-xl border border-border/60 bg-violet-500/5 p-1.5">
                <p className="px-2 pb-1 text-[10px] font-black uppercase tracking-[0.16em] text-violet-700 dark:text-violet-300">{ar ? "التفاعل" : "Engagement"}</p>
                <div className="flex gap-1">
                  <TabsTrigger value="inbox" className="h-9 gap-1.5 rounded-lg border-b-2 border-transparent px-3 text-xs font-bold data-[state=active]:border-violet-500 data-[state=active]:bg-background data-[state=active]:shadow-sm"><MessageSquare className="h-3.5 w-3.5" />{ar ? "الصندوق" : "Inbox"}</TabsTrigger>
                  <TabsTrigger value="broadcasts" className="h-9 gap-1.5 rounded-lg border-b-2 border-transparent px-3 text-xs font-bold data-[state=active]:border-violet-500 data-[state=active]:bg-background data-[state=active]:shadow-sm"><Send className="h-3.5 w-3.5" />{ar ? "البث" : "Broadcasts"}</TabsTrigger>
                </div>
              </div>

              <div className="rounded-xl border border-border/60 bg-indigo-500/5 p-1.5">
                <p className="px-2 pb-1 text-[10px] font-black uppercase tracking-[0.16em] text-indigo-700 dark:text-indigo-300">{ar ? "الأتمتة" : "Automation"}</p>
                <div className="flex gap-1">
                  <TabsTrigger value="automations" className="h-9 gap-1.5 rounded-lg border-b-2 border-transparent px-3 text-xs font-bold data-[state=active]:border-violet-500 data-[state=active]:bg-background data-[state=active]:shadow-sm"><Zap className="h-3.5 w-3.5" />{ar ? "الأتمتة" : "Automations"}</TabsTrigger>
                  <TabsTrigger value="flows" className="h-9 gap-1.5 rounded-lg border-b-2 border-transparent px-3 text-xs font-bold data-[state=active]:border-violet-500 data-[state=active]:bg-background data-[state=active]:shadow-sm"><GitBranch className="h-3.5 w-3.5" />{ar ? "التدفقات" : "Flows"}</TabsTrigger>
                  <TabsTrigger value="aiagents" className="h-9 gap-1.5 rounded-lg border-b-2 border-transparent px-3 text-xs font-bold data-[state=active]:border-violet-500 data-[state=active]:bg-background data-[state=active]:shadow-sm"><Bot className="h-3.5 w-3.5" />{ar ? "وكلاء AI" : "AI Agents"}</TabsTrigger>
                </div>
              </div>

              <div className="rounded-xl border border-border/60 bg-muted/25 p-1.5">
                <p className="px-2 pb-1 text-[10px] font-black uppercase tracking-[0.16em] text-muted-foreground">{ar ? "الإدارة" : "Administration"}</p>
                <div className="flex gap-1">
                  <TabsTrigger value="team" className="h-9 gap-1.5 rounded-lg border-b-2 border-transparent px-3 text-xs font-bold data-[state=active]:border-violet-500 data-[state=active]:bg-background data-[state=active]:shadow-sm"><Users className="h-3.5 w-3.5" />{ar ? "الفريق" : "Team"}</TabsTrigger>
                  <TabsTrigger value="settings" className="h-9 gap-1.5 rounded-lg border-b-2 border-transparent px-3 text-xs font-bold data-[state=active]:border-violet-500 data-[state=active]:bg-background data-[state=active]:shadow-sm"><Settings className="h-3.5 w-3.5" />{ar ? "الإعدادات" : "Settings"}</TabsTrigger>
                  <TabsTrigger value="developer" className="h-9 gap-1.5 rounded-lg border-b-2 border-transparent px-3 text-xs font-bold data-[state=active]:border-violet-500 data-[state=active]:bg-background data-[state=active]:shadow-sm"><Code2 className="h-3.5 w-3.5" />{ar ? "المطور" : "Developer"}</TabsTrigger>
                </div>
              </div>
            </div>
          </TabsList>'''

TAB_VALUES = [
    "dashboard", "inbox", "contacts", "pipelines", "broadcasts",
    "automations", "flows", "aiagents", "team", "settings", "developer",
]
GROUP_MARKERS = ["Core workspace", "Engagement", "Automation", "Administration"]


def git_blob(path: Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()


def read_source() -> str:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target: {TARGET}")
    return TARGET.read_text(encoding="utf-8")


def check() -> None:
    blob = git_blob(TARGET)
    if blob != BASE_BLOB:
        raise SystemExit(f"ERROR: baseline blob mismatch: expected {BASE_BLOB}, got {blob}")
    src = read_source()
    if OLD_ROOT not in src:
        raise SystemExit("ERROR: expected Tabs root not found")
    if src.count(OLD_NAV) != 1:
        raise SystemExit(f"ERROR: expected legacy navigation block exactly once, found {src.count(OLD_NAV)}")
    if MARKER in src:
        raise SystemExit("ERROR: Phase 3 marker already present")
    print(f"CHECK=PASS baseline_blob={blob}")


def apply() -> None:
    check()
    src = read_source()
    src = src.replace(OLD_ROOT, NEW_ROOT, 1)
    src = src.replace(OLD_NAV, NEW_NAV, 1)
    TARGET.write_text(src, encoding="utf-8")
    print(f"APPLY=PASS target_blob={git_blob(TARGET)}")


def verify() -> None:
    src = read_source()
    if MARKER not in src:
        raise SystemExit("ERROR: workspace marker missing")
    if OLD_NAV in src:
        raise SystemExit("ERROR: legacy flat navigation still present")
    for group in GROUP_MARKERS:
        if group not in src:
            raise SystemExit(f"ERROR: missing group marker: {group}")
    for value in TAB_VALUES:
        count = src.count(f'<TabsTrigger value="{value}"')
        if count != 1:
            raise SystemExit(f"ERROR: tab {value!r} expected exactly once, found {count}")
        if f'<TabsContent value="{value}"' not in src:
            raise SystemExit(f"ERROR: matching TabsContent missing for {value!r}")
    required = [
        "Workspace capabilities",
        "AI Outreach & Engagement Specialist",
        "Zaghloul professional portrait",
        "WACRM integration inside TCRM",
    ]
    for item in required:
        if item not in src:
            raise SystemExit(f"ERROR: required existing surface missing: {item}")
    print(f"VERIFY=PASS target_blob={git_blob(TARGET)} marker={MARKER}")


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--apply", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.check:
        check()
    elif args.apply:
        apply()
    else:
        verify()


if __name__ == "__main__":
    main()
