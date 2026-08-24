#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import subprocess
import sys

PATCH_ID = "FELFEL-UXUI-REFERENCE-DESIGN-V2"
BASELINE_SHA = "8d64505bb264d3c8aeb5e956a54cd08bc336945d"
TARGET = "client/src/pages/FelfelPage.tsx"
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()


def run(*args: str) -> str:
    p = subprocess.run(list(args), cwd=root, text=True, capture_output=True)
    if p.returncode != 0:
        sys.stdout.write(p.stdout)
        sys.stderr.write(p.stderr)
        raise SystemExit(f"Command failed ({p.returncode}): {' '.join(args)}")
    return p.stdout.strip()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected anchor exactly once, found {count}")
    return text.replace(old, new, 1)


if run("git", "rev-parse", "--show-toplevel") != str(root):
    raise SystemExit("Run this patch from the canonical TCRM repository root")

head = run("git", "rev-parse", "HEAD")
if head != BASELINE_SHA:
    raise SystemExit(f"{PATCH_ID} requires baseline {BASELINE_SHA}; found {head}")

status_before = run("git", "status", "--short")
if status_before:
    raise SystemExit("Refusing to apply Felfel UX/UI patch on a dirty worktree:\n" + status_before)

path = root / TARGET
if not path.is_file():
    raise SystemExit(f"Missing target file: {TARGET}")

text = path.read_text(encoding="utf-8")
required = [
    'data-felfel-uxui="premium-v1"',
    '/ai-staff/felfel-avatar.webp',
    'Meetings Processed',
    'Live Meeting Status',
    'Transcript & Intelligence',
    'Service capabilities',
]
for marker in required:
    if marker not in text:
        raise SystemExit(f"Expected Felfel premium-v1 marker missing: {marker}")

# 1) Import the puzzle icon used by the reference design's Service Capabilities card.
text = replace_once(
    text,
    'import { Activity, Bot, CheckCircle2, Clock3, ExternalLink, History, Loader2, LogOut, Mic2, RefreshCw, Video } from "lucide-react";',
    'import { Activity, Bot, CheckCircle2, Clock3, ExternalLink, History, Loader2, LogOut, Mic2, Puzzle, RefreshCw, Video } from "lucide-react";',
    "lucide Puzzle import",
)

# 2) Hero/card surface: match the supplied reference while preserving all current content and behavior.
text = replace_once(text, 'data-felfel-uxui="premium-v1"', 'data-felfel-uxui="reference-v2"', "design marker")
text = replace_once(
    text,
    'className="relative overflow-hidden rounded-[26px] border border-border/70 bg-card shadow-[0_18px_55px_-36px_rgba(15,23,42,0.55)]"',
    'className="relative overflow-hidden rounded-[26px] border border-border/70 bg-gradient-to-br from-orange-500/10 via-card to-card shadow-[0_20px_60px_-38px_rgba(15,23,42,0.58)]"',
    "hero surface",
)
text = replace_once(
    text,
    'className="pointer-events-none absolute -start-24 -top-24 h-64 w-64 rounded-full bg-orange-500/10 blur-3xl"',
    'className="pointer-events-none absolute -start-20 -top-24 h-72 w-72 rounded-full bg-orange-400/15 blur-3xl"',
    "hero glow",
)
text = replace_once(
    text,
    'className="relative flex flex-col gap-5 p-5 md:p-6 xl:flex-row xl:items-center xl:justify-between"',
    'className="relative flex flex-col gap-6 p-5 md:p-7 xl:flex-row xl:items-center xl:justify-between"',
    "hero spacing",
)

# 3) Avatar: guaranteed inner circular clipping + tuned face/shoulder positioning.
old_avatar = '''              <div className="relative mx-auto h-[148px] w-[148px] shrink-0 md:mx-0">\n                <div className="h-full w-full overflow-hidden rounded-full border-8 border-muted/80 bg-muted shadow-inner ring-1 ring-border/70"><img src="/ai-staff/felfel-avatar.webp" alt={ar ? "فلفل" : "Felfel"} className="h-full w-full object-cover" /></div>\n                <span className={"absolute bottom-3 end-2 h-6 w-6 rounded-full border-4 border-card " + (health?.healthy ? "bg-emerald-500" : "bg-muted-foreground")} />\n              </div>'''
new_avatar = '''              <div className="relative mx-auto h-[152px] w-[152px] shrink-0 md:mx-0">\n                <div className="h-full w-full rounded-full border border-border/70 bg-background/90 p-[7px] shadow-[0_16px_38px_-24px_rgba(15,23,42,0.75)] ring-1 ring-white/60 dark:ring-white/10">\n                  <div className="h-full w-full overflow-hidden rounded-full bg-muted">\n                    <img src="/ai-staff/felfel-avatar.webp" alt={ar ? "فلفل" : "Felfel"} className="h-full w-full scale-105 object-cover object-[50%_18%]" />\n                  </div>\n                </div>\n                <span className={"absolute bottom-2.5 end-1.5 h-6 w-6 rounded-full border-4 border-card shadow-sm " + (health?.healthy ? "bg-emerald-500" : "bg-muted-foreground")} />\n              </div>'''
text = replace_once(text, old_avatar, new_avatar, "avatar framing")

# 4) Metric cards: slightly roomier, cleaner hierarchy, equal visual weight.
old_metrics = '''        <section className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">{felfelMetrics.map(({ label, value, Icon, tone, hint }) => <Card key={label} className="group rounded-2xl border-border/70 bg-card shadow-[0_12px_32px_-27px_rgba(15,23,42,0.7)] transition-all duration-200 hover:-translate-y-0.5 hover:border-orange-500/25 hover:shadow-md"><CardContent className="flex min-h-[116px] items-center gap-3 p-4"><div className={"grid h-11 w-11 shrink-0 place-items-center rounded-2xl " + tone}><Icon className="h-5 w-5" /></div><div className="min-w-0"><p className="text-[27px] font-black leading-none tracking-[-0.04em]">{value}</p><p className="mt-1.5 truncate text-xs font-bold">{label}</p><p className="mt-1 truncate text-[10px] font-medium text-muted-foreground">{hint}</p></div></CardContent></Card>)}</section>'''
new_metrics = '''        <section className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">{felfelMetrics.map(({ label, value, Icon, tone, hint }) => <Card key={label} className="group rounded-2xl border-border/70 bg-card shadow-[0_14px_34px_-28px_rgba(15,23,42,0.72)] transition-all duration-200 hover:-translate-y-0.5 hover:border-orange-500/25 hover:shadow-md"><CardContent className="flex min-h-[124px] items-center gap-3.5 p-4"><div className={"grid h-12 w-12 shrink-0 place-items-center rounded-2xl " + tone}><Icon className="h-5 w-5" /></div><div className="min-w-0"><p className="text-[28px] font-black leading-none tracking-[-0.04em]">{value}</p><p className="mt-2 truncate text-xs font-black">{label}</p><p className="mt-1 truncate text-[10px] font-medium text-muted-foreground">{hint}</p></div></CardContent></Card>)}</section>'''
text = replace_once(text, old_metrics, new_metrics, "metric card redesign")

# 5) Tabs: white raised active tab + orange underline, matching the reference image.
old_tabs_list = '          <TabsList className="h-auto w-full flex-nowrap justify-start gap-1 overflow-x-auto rounded-2xl border border-border/70 bg-card p-1.5 shadow-sm [scrollbar-width:none] [&::-webkit-scrollbar]:hidden [&_[role=tab]]:h-10 [&_[role=tab]]:shrink-0 [&_[role=tab]]:rounded-xl [&_[role=tab]]:px-4 [&_[role=tab]]:text-xs [&_[role=tab]]:font-bold [&_[data-state=active]]:bg-orange-500/10 [&_[data-state=active]]:text-orange-600 [&_[data-state=active]]:shadow-none dark:[&_[data-state=active]]:text-orange-300">'
new_tabs_list = '          <TabsList className="h-auto w-full flex-nowrap justify-start gap-1 overflow-x-auto rounded-2xl border border-border/70 bg-muted/30 p-1.5 shadow-sm [scrollbar-width:none] [&::-webkit-scrollbar]:hidden [&_[role=tab]]:h-10 [&_[role=tab]]:shrink-0 [&_[role=tab]]:rounded-xl [&_[role=tab]]:px-4 [&_[role=tab]]:text-xs [&_[role=tab]]:font-bold [&_[data-state=active]]:bg-background [&_[data-state=active]]:text-foreground [&_[data-state=active]]:shadow-sm">'
text = replace_once(text, old_tabs_list, new_tabs_list, "tabs list")

trigger_suffix = ' relative data-[state=active]:text-foreground data-[state=active]:after:absolute data-[state=active]:after:-bottom-1.5 data-[state=active]:after:inset-x-3 data-[state=active]:after:h-0.5 data-[state=active]:after:rounded-full data-[state=active]:after:bg-orange-500 data-[state=active]:after:content-[\'\']'
for value in ("live", "transcript", "intelligence", "history"):
    anchor = f'<TabsTrigger value="{value}" className="gap-1.5">'
    replacement = f'<TabsTrigger value="{value}" className={{"gap-1.5" + "{trigger_suffix}"}}>'
    text = replace_once(text, anchor, replacement, f"{value} tab trigger")

# 6) New Meeting card polish + reference orange CTA.
text = replace_once(
    text,
    '<Card className="overflow-hidden rounded-2xl border-border/70 shadow-sm"><CardHeader className="pb-3"><CardTitle className="flex items-center gap-2 text-base"><Video className="h-5 w-5 text-orange-500" />{ar ? "اجتماع جديد" : "New Meeting"}</CardTitle>',
    '<Card className="overflow-hidden rounded-2xl border-border/70 shadow-[0_14px_34px_-29px_rgba(15,23,42,0.72)]"><CardHeader className="pb-3"><CardTitle className="flex items-center gap-2 text-base"><Video className="h-5 w-5 text-orange-500" />{ar ? "اجتماع جديد" : "New Meeting"}</CardTitle>',
    "new meeting card",
)
text = replace_once(
    text,
    'className="h-11 gap-2 rounded-xl bg-orange-600 font-bold text-white hover:bg-orange-700"',
    'className="h-11 gap-2 rounded-xl bg-gradient-to-r from-orange-600 to-orange-400 font-bold text-white shadow-sm hover:from-orange-700 hover:to-orange-500"',
    "join CTA",
)

# 7) Live empty state: stronger focal camera circle, softer panel background.
old_empty = '''<div className="grid min-h-[210px] place-items-center rounded-2xl border border-dashed bg-muted/10 text-center"><div><Video className="mx-auto h-8 w-8 text-muted-foreground/50" /><p className="mt-3 text-sm font-bold">{ar ? "ابدأ اجتماعًا من النموذج المجاور" : "Start a meeting from the form next to this panel"}</p><p className="mt-1 text-xs text-muted-foreground">{ar ? "ستظهر الحالة والمعلومات هنا مباشرة." : "Live status and meeting metadata will appear here."}</p></div></div>'''
new_empty = '''<div className="grid min-h-[210px] place-items-center rounded-2xl border border-dashed border-border/80 bg-gradient-to-b from-background to-muted/15 text-center"><div><div className="relative mx-auto grid h-16 w-16 place-items-center rounded-full bg-orange-500/10 text-muted-foreground"><span className="absolute -start-2 top-2 text-xs text-orange-400">✦</span><Video className="h-8 w-8" /><span className="absolute -end-2 bottom-2 text-[10px] text-orange-400">✦</span></div><p className="mt-3 text-sm font-bold">{ar ? "ابدأ اجتماعًا من النموذج المجاور" : "Start a meeting from the form next to this panel"}</p><p className="mt-1 text-xs text-muted-foreground">{ar ? "ستظهر الحالة والمعلومات هنا مباشرة." : "Live status and meeting metadata will appear here."}</p></div></div>'''
text = replace_once(text, old_empty, new_empty, "live empty state")

# 8) Bottom summary cards: reference icon bubble and quieter counter chip.
old_summary = '''].map(({ title, text, value, Icon }) => <Card key={title} className="rounded-2xl border-border/70 shadow-sm"><CardContent className="flex min-h-[126px] items-center justify-between gap-3 p-4"><div className="min-w-0"><div className="flex items-center gap-2"><Icon className="h-4 w-4 text-orange-500" /><p className="text-sm font-black">{title}</p></div><p className="mt-2 text-xs leading-5 text-muted-foreground">{text}</p></div><div className="grid h-12 min-w-12 place-items-center rounded-2xl bg-muted/50 px-3 text-lg font-black">{value}</div></CardContent></Card>)}</div>'''
new_summary = '''].map(({ title, text, value, Icon }) => <Card key={title} className="rounded-2xl border-border/70 shadow-[0_12px_28px_-25px_rgba(15,23,42,0.7)]"><CardContent className="flex min-h-[126px] items-center justify-between gap-3 p-4"><div className="min-w-0"><div className="flex items-center gap-2.5"><span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-orange-500/10"><Icon className="h-4 w-4 text-orange-600" /></span><p className="text-sm font-black">{title}</p></div><p className="mt-2 text-xs leading-5 text-muted-foreground">{text}</p></div><div className="grid h-11 min-w-11 place-items-center rounded-2xl bg-muted/40 px-3 text-lg font-black">{value}</div></CardContent></Card>)}</div>'''
text = replace_once(text, old_summary, new_summary, "summary cards")

# 9) Service capabilities card: reference white card + green puzzle visual.
old_caps = '''        <Card className="border-border/70 bg-muted/20 shadow-none"><CardHeader className="pb-2"><CardTitle className="flex items-center gap-2 text-sm font-bold"><CheckCircle2 className="h-5 w-5" />{ar ? "قدرات الخدمة" : "Service capabilities"}</CardTitle></CardHeader><CardContent className="flex flex-wrap gap-2 pb-4">{capabilitiesQ.data?.capabilities && Object.entries(capabilitiesQ.data.capabilities).map(([key, value]) => <Badge key={key} variant={value && typeof value === "object" && "state" in value && (value as any).state === "not_configured" ? "secondary" : "outline"}>{key}</Badge>)}{!Object.keys(capabilitiesQ.data?.capabilities || {}).length && <span className="text-sm text-muted-foreground">{ar ? "لا توجد قدرات متاحة" : "No capability data available"}</span>}</CardContent></Card>'''
new_caps = '''        <Card className="rounded-2xl border-border/70 bg-card shadow-[0_12px_28px_-26px_rgba(15,23,42,0.65)]"><CardHeader className="pb-2"><CardTitle className="flex items-center gap-3 text-sm font-black"><span className="grid h-10 w-10 place-items-center rounded-full bg-emerald-500/10 text-emerald-600"><Puzzle className="h-5 w-5" /></span>{ar ? "قدرات الخدمة" : "Service capabilities"}</CardTitle></CardHeader><CardContent className="flex flex-wrap gap-2 pb-5 ps-[68px]">{capabilitiesQ.data?.capabilities && Object.entries(capabilitiesQ.data.capabilities).map(([key, value]) => <Badge key={key} variant={value && typeof value === "object" && "state" in value && (value as any).state === "not_configured" ? "secondary" : "outline"} className="rounded-full border-emerald-500/15 bg-emerald-500/10 px-3 text-emerald-700 dark:text-emerald-300">{key}</Badge>)}{!Object.keys(capabilitiesQ.data?.capabilities || {}).length && <span className="text-sm text-muted-foreground">{ar ? "لا توجد قدرات متاحة" : "No capability data available"}</span>}</CardContent></Card>'''
text = replace_once(text, old_caps, new_caps, "service capabilities")

path.write_text(text, encoding="utf-8")

run("git", "diff", "--check", "--", TARGET)
status_after = run("git", "status", "--short")
expected = f" M {TARGET}"
if status_after.strip() != expected:
    raise SystemExit(f"Unexpected worktree after patch. Expected only {expected!r}, found:\n{status_after}")

updated = path.read_text(encoding="utf-8")
for marker in (
    'data-felfel-uxui="reference-v2"',
    'object-[50%_18%]',
    'bg-gradient-to-r from-orange-600 to-orange-400',
    'data-[state=active]:after:bg-orange-500',
    '<Puzzle className="h-5 w-5" />',
):
    if marker not in updated:
        raise SystemExit(f"Post-apply design marker missing: {marker}")

print(f"{PATCH_ID} applied")
print(f"BASELINE={BASELINE_SHA}")
print(f"MODIFIED_FILE={TARGET}")
print("AVATAR_INNER_CIRCLE_CLIPPING=YES")
print("AVATAR_OBJECT_POSITION=50%_18%")
print("REFERENCE_HERO_SURFACE=YES")
print("REFERENCE_METRIC_CARDS=YES")
print("REFERENCE_ORANGE_TAB_UNDERLINE=YES")
print("REFERENCE_NEW_MEETING_CTA=YES")
print("REFERENCE_LIVE_EMPTY_STATE=YES")
print("REFERENCE_SUMMARY_CARDS=YES")
print("REFERENCE_SERVICE_CAPABILITIES=YES")
print("BACKEND_CHANGED=NO")
print("ROUTER_CHANGED=NO")
print("DB_SCHEMA_CHANGED=NO")
print("FUNCTIONAL_BEHAVIOR_CHANGED=NO")
print("NO_BUILD_RESTART_COMMIT_PUSH_FETCH_PULL_RESET_MERGE_REBASE_PERFORMED=YES")