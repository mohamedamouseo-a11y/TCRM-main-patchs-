#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import pathlib
import subprocess
import sys

PATCH_ID = "FELFEL-UXUI-REFERENCE-DESIGN-V6"
BASELINE_HEAD = "90b1d4573626e0fad4c7629df1b062e939099e7e"
SOURCE_COMMIT = "42212ebe025a7b1a556042a67f818d93c3a38350"
TARGET = "client/src/pages/FelfelPage.tsx"
AVATAR = "client/public/ai-staff/felfel-avatar.webp"
EXPECTED_HEAD_BLOB = "3d1c2ebc9212d59f34d0ffad78040cf1b334e55c"
EXPECTED_SOURCE_BLOB = "cd541f5ff161fad39ca0e98b0791917bca4243ac"
EXPECTED_AVATAR_BLOB = "21e7557ee99908b5a9893bb5503d0e662c23d7b1"
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()


def run(*args: str) -> str:
    p = subprocess.run(list(args), cwd=root, text=True, capture_output=True)
    if p.returncode != 0:
        sys.stdout.write(p.stdout)
        sys.stderr.write(p.stderr)
        raise SystemExit(f"Command failed ({p.returncode}): {' '.join(args)}")
    return p.stdout.strip()


def run_bytes(*args: str) -> bytes:
    p = subprocess.run(list(args), cwd=root, capture_output=True)
    if p.returncode != 0:
        sys.stdout.buffer.write(p.stdout)
        sys.stderr.buffer.write(p.stderr)
        raise SystemExit(f"Command failed ({p.returncode}): {' '.join(args)}")
    return p.stdout


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected anchor exactly once, found {count}")
    return text.replace(old, new, 1)


def build_design(source: str, marker: str) -> str:
    text = source
    for required in (
        'data-felfel-uxui="premium-v1"',
        '/ai-staff/felfel-avatar.webp',
        'Meetings Processed',
        'Live Meeting Status',
        'Transcript & Intelligence',
        'Service capabilities',
    ):
        if required not in text:
            raise SystemExit(f"Premium source marker missing: {required}")

    text = replace_once(
        text,
        'import { Activity, Bot, CheckCircle2, Clock3, ExternalLink, History, Loader2, LogOut, Mic2, RefreshCw, Video } from "lucide-react";',
        'import { Activity, Bot, CheckCircle2, Clock3, ExternalLink, History, Loader2, LogOut, Mic2, Puzzle, RefreshCw, Video } from "lucide-react";',
        "Puzzle import",
    )
    text = replace_once(text, 'data-felfel-uxui="premium-v1"', f'data-felfel-uxui="{marker}"', "design marker")
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

    old_avatar = '''              <div className="relative mx-auto h-[148px] w-[148px] shrink-0 md:mx-0">\n                <div className="h-full w-full overflow-hidden rounded-full border-8 border-muted/80 bg-muted shadow-inner ring-1 ring-border/70"><img src="/ai-staff/felfel-avatar.webp" alt={ar ? "فلفل" : "Felfel"} className="h-full w-full object-cover" /></div>\n                <span className={"absolute bottom-3 end-2 h-6 w-6 rounded-full border-4 border-card " + (health?.healthy ? "bg-emerald-500" : "bg-muted-foreground")} />\n              </div>'''
    new_avatar = '''              <div className="relative mx-auto h-[152px] w-[152px] shrink-0 md:mx-0">\n                <div className="h-full w-full rounded-full border border-border/70 bg-background/90 p-[7px] shadow-[0_16px_38px_-24px_rgba(15,23,42,0.75)] ring-1 ring-white/60 dark:ring-white/10">\n                  <div className="h-full w-full overflow-hidden rounded-full bg-muted">\n                    <img src="/ai-staff/felfel-avatar.webp" alt={ar ? "فلفل" : "Felfel"} className="h-full w-full scale-105 object-cover object-[50%_18%]" />\n                  </div>\n                </div>\n                <span className={"absolute bottom-2.5 end-1.5 h-6 w-6 rounded-full border-4 border-card shadow-sm " + (health?.healthy ? "bg-emerald-500" : "bg-muted-foreground")} />\n              </div>'''
    text = replace_once(text, old_avatar, new_avatar, "avatar framing")

    old_metrics = '''        <section className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">{felfelMetrics.map(({ label, value, Icon, tone, hint }) => <Card key={label} className="group rounded-2xl border-border/70 bg-card shadow-[0_12px_32px_-27px_rgba(15,23,42,0.7)] transition-all duration-200 hover:-translate-y-0.5 hover:border-orange-500/25 hover:shadow-md"><CardContent className="flex min-h-[116px] items-center gap-3 p-4"><div className={"grid h-11 w-11 shrink-0 place-items-center rounded-2xl " + tone}><Icon className="h-5 w-5" /></div><div className="min-w-0"><p className="text-[27px] font-black leading-none tracking-[-0.04em]">{value}</p><p className="mt-1.5 truncate text-xs font-bold">{label}</p><p className="mt-1 truncate text-[10px] font-medium text-muted-foreground">{hint}</p></div></CardContent></Card>)}</section>'''
    new_metrics = '''        <section className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">{felfelMetrics.map(({ label, value, Icon, tone, hint }) => <Card key={label} className="group rounded-2xl border-border/70 bg-card shadow-[0_14px_34px_-28px_rgba(15,23,42,0.72)] transition-all duration-200 hover:-translate-y-0.5 hover:border-orange-500/25 hover:shadow-md"><CardContent className="flex min-h-[124px] items-center gap-3.5 p-4"><div className={"grid h-12 w-12 shrink-0 place-items-center rounded-2xl " + tone}><Icon className="h-5 w-5" /></div><div className="min-w-0"><p className="text-[28px] font-black leading-none tracking-[-0.04em]">{value}</p><p className="mt-2 truncate text-xs font-black">{label}</p><p className="mt-1 truncate text-[10px] font-medium text-muted-foreground">{hint}</p></div></CardContent></Card>)}</section>'''
    text = replace_once(text, old_metrics, new_metrics, "metric cards")

    old_tabs = '          <TabsList className="h-auto w-full flex-nowrap justify-start gap-1 overflow-x-auto rounded-2xl border border-border/70 bg-card p-1.5 shadow-sm [scrollbar-width:none] [&::-webkit-scrollbar]:hidden [&_[role=tab]]:h-10 [&_[role=tab]]:shrink-0 [&_[role=tab]]:rounded-xl [&_[role=tab]]:px-4 [&_[role=tab]]:text-xs [&_[role=tab]]:font-bold [&_[data-state=active]]:bg-orange-500/10 [&_[data-state=active]]:text-orange-600 [&_[data-state=active]]:shadow-none dark:[&_[data-state=active]]:text-orange-300">'
    new_tabs = '          <TabsList className="h-auto w-full flex-nowrap justify-start gap-1 overflow-x-auto rounded-2xl border border-border/70 bg-muted/30 p-1.5 shadow-sm [scrollbar-width:none] [&::-webkit-scrollbar]:hidden [&_[role=tab]]:h-10 [&_[role=tab]]:shrink-0 [&_[role=tab]]:rounded-xl [&_[role=tab]]:border-b-2 [&_[role=tab]]:border-transparent [&_[role=tab]]:px-4 [&_[role=tab]]:text-xs [&_[role=tab]]:font-bold [&_[data-state=active]]:border-orange-500 [&_[data-state=active]]:bg-background [&_[data-state=active]]:text-foreground [&_[data-state=active]]:shadow-sm">'
    text = replace_once(text, old_tabs, new_tabs, "tabs")

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

    old_empty = '''<div className="grid min-h-[210px] place-items-center rounded-2xl border border-dashed bg-muted/10 text-center"><div><Video className="mx-auto h-8 w-8 text-muted-foreground/50" /><p className="mt-3 text-sm font-bold">{ar ? "ابدأ اجتماعًا من النموذج المجاور" : "Start a meeting from the form next to this panel"}</p><p className="mt-1 text-xs text-muted-foreground">{ar ? "ستظهر الحالة والمعلومات هنا مباشرة." : "Live status and meeting metadata will appear here."}</p></div></div>'''
    new_empty = '''<div className="grid min-h-[210px] place-items-center rounded-2xl border border-dashed border-border/80 bg-gradient-to-b from-background to-muted/15 text-center"><div><div className="relative mx-auto grid h-16 w-16 place-items-center rounded-full bg-orange-500/10 text-muted-foreground"><span className="absolute -start-2 top-2 text-xs text-orange-400">✦</span><Video className="h-8 w-8" /><span className="absolute -end-2 bottom-2 text-[10px] text-orange-400">✦</span></div><p className="mt-3 text-sm font-bold">{ar ? "ابدأ اجتماعًا من النموذج المجاور" : "Start a meeting from the form next to this panel"}</p><p className="mt-1 text-xs text-muted-foreground">{ar ? "ستظهر الحالة والمعلومات هنا مباشرة." : "Live status and meeting metadata will appear here."}</p></div></div>'''
    text = replace_once(text, old_empty, new_empty, "live empty state")

    old_summary = '''].map(({ title, text, value, Icon }) => <Card key={title} className="rounded-2xl border-border/70 shadow-sm"><CardContent className="flex min-h-[126px] items-center justify-between gap-3 p-4"><div className="min-w-0"><div className="flex items-center gap-2"><Icon className="h-4 w-4 text-orange-500" /><p className="text-sm font-black">{title}</p></div><p className="mt-2 text-xs leading-5 text-muted-foreground">{text}</p></div><div className="grid h-12 min-w-12 place-items-center rounded-2xl bg-muted/50 px-3 text-lg font-black">{value}</div></CardContent></Card>)}</div>'''
    new_summary = '''].map(({ title, text, value, Icon }) => <Card key={title} className="rounded-2xl border-border/70 shadow-[0_12px_28px_-25px_rgba(15,23,42,0.7)]"><CardContent className="flex min-h-[126px] items-center justify-between gap-3 p-4"><div className="min-w-0"><div className="flex items-center gap-2.5"><span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-orange-500/10"><Icon className="h-4 w-4 text-orange-600" /></span><p className="text-sm font-black">{title}</p></div><p className="mt-2 text-xs leading-5 text-muted-foreground">{text}</p></div><div className="grid h-11 min-w-11 place-items-center rounded-2xl bg-muted/40 px-3 text-lg font-black">{value}</div></CardContent></Card>)}</div>'''
    text = replace_once(text, old_summary, new_summary, "summary cards")

    old_caps = '''        <Card className="border-border/70 bg-muted/20 shadow-none"><CardHeader className="pb-2"><CardTitle className="flex items-center gap-2 text-sm font-bold"><CheckCircle2 className="h-5 w-5" />{ar ? "قدرات الخدمة" : "Service capabilities"}</CardTitle></CardHeader><CardContent className="flex flex-wrap gap-2 pb-4">{capabilitiesQ.data?.capabilities && Object.entries(capabilitiesQ.data.capabilities).map(([key, value]) => <Badge key={key} variant={value && typeof value === "object" && "state" in value && (value as any).state === "not_configured" ? "secondary" : "outline"}>{key}</Badge>)}{!Object.keys(capabilitiesQ.data?.capabilities || {}).length && <span className="text-sm text-muted-foreground">{ar ? "لا توجد قدرات متاحة" : "No capability data available"}</span>}</CardContent></Card>'''
    new_caps = '''        <Card className="rounded-2xl border-border/70 bg-card shadow-[0_12px_28px_-26px_rgba(15,23,42,0.65)]"><CardHeader className="pb-2"><CardTitle className="flex items-center gap-3 text-sm font-black"><span className="grid h-10 w-10 place-items-center rounded-full bg-emerald-500/10 text-emerald-600"><Puzzle className="h-5 w-5" /></span>{ar ? "قدرات الخدمة" : "Service capabilities"}</CardTitle></CardHeader><CardContent className="flex flex-wrap gap-2 pb-5 ps-[68px]">{capabilitiesQ.data?.capabilities && Object.entries(capabilitiesQ.data.capabilities).map(([key, value]) => <Badge key={key} variant={value && typeof value === "object" && "state" in value && (value as any).state === "not_configured" ? "secondary" : "outline"} className="rounded-full border-emerald-500/15 bg-emerald-500/10 px-3 text-emerald-700 dark:text-emerald-300">{key}</Badge>)}{!Object.keys(capabilitiesQ.data?.capabilities || {}).length && <span className="text-sm text-muted-foreground">{ar ? "لا توجد قدرات متاحة" : "No capability data available"}</span>}</CardContent></Card>'''
    text = replace_once(text, old_caps, new_caps, "service capabilities")
    return text


def porcelain_lines() -> list[str]:
    out = run("git", "status", "--porcelain=v1", "--untracked-files=all")
    return [line for line in out.splitlines() if line.strip()]


if run("git", "rev-parse", "--show-toplevel") != str(root):
    raise SystemExit("Run from canonical TCRM repository root")
branch = run("git", "branch", "--show-current")
head = run("git", "rev-parse", "HEAD")
if branch != "main" or head != BASELINE_HEAD:
    raise SystemExit(f"{PATCH_ID} requires main at {BASELINE_HEAD}; found {branch} at {head}")
if run("git", "diff", "--cached", "--name-only"):
    raise SystemExit("Staged changes exist; refusing recovery")
tracked_dirty = [p for p in run("git", "diff", "--name-only").splitlines() if p.strip()]
if any(p != TARGET for p in tracked_dirty):
    raise SystemExit(f"Unexpected tracked changes: {tracked_dirty}")

source_page_bytes = run_bytes("git", "show", f"{SOURCE_COMMIT}:{TARGET}")
source_avatar_bytes = run_bytes("git", "show", f"{SOURCE_COMMIT}:{AVATAR}")
if git_blob_sha(source_page_bytes) != EXPECTED_SOURCE_BLOB:
    raise SystemExit("Preserved premium page blob mismatch")
if git_blob_sha(source_avatar_bytes) != EXPECTED_AVATAR_BLOB:
    raise SystemExit("Preserved avatar blob mismatch")
source_text = source_page_bytes.decode("utf-8")
canonical_v5 = build_design(source_text, "reference-v5").encode("utf-8")
canonical_v6 = build_design(source_text, "reference-v6").encode("utf-8")
known_page_blobs = {
    EXPECTED_HEAD_BLOB,
    EXPECTED_SOURCE_BLOB,
    git_blob_sha(canonical_v5),
    git_blob_sha(canonical_v6),
}

page = root / TARGET
avatar = root / AVATAR
if not page.is_file():
    raise SystemExit(f"Missing {TARGET}")
current_page_blob = run("git", "hash-object", TARGET)
if current_page_blob not in known_page_blobs:
    raise SystemExit(f"Unknown Felfel partial state: {current_page_blob}; refusing overwrite")
if avatar.exists() and run("git", "hash-object", AVATAR) != EXPECTED_AVATAR_BLOB:
    raise SystemExit("Existing Felfel avatar is not the validated asset")

status_before = porcelain_lines()
mautic_before = sum(1 for line in status_before if line.startswith("?? external/mautic/"))
for line in status_before:
    if line in {f" M {TARGET}", f"?? {AVATAR}"} or line.startswith("?? external/mautic/"):
        continue
    raise SystemExit(f"Unexpected worktree entry before recovery: {line}")

page.write_bytes(canonical_v6)
avatar.parent.mkdir(parents=True, exist_ok=True)
if not avatar.exists():
    avatar.write_bytes(source_avatar_bytes)

run("git", "diff", "--check", "--", TARGET)
tracked_after = [p for p in run("git", "diff", "--name-only").splitlines() if p.strip()]
if tracked_after != [TARGET]:
    raise SystemExit(f"Unexpected tracked diff after recovery: {tracked_after}")
if run("git", "hash-object", TARGET) != git_blob_sha(canonical_v6):
    raise SystemExit("Canonical V6 page verification failed")
if run("git", "hash-object", AVATAR) != EXPECTED_AVATAR_BLOB:
    raise SystemExit("Canonical avatar verification failed")

status_after = porcelain_lines()
mautic_after = sum(1 for line in status_after if line.startswith("?? external/mautic/"))
if mautic_after != mautic_before:
    raise SystemExit(f"Mautic count changed: {mautic_before} -> {mautic_after}")
for line in status_after:
    if line in {f" M {TARGET}", f"?? {AVATAR}"} or line.startswith("?? external/mautic/"):
        continue
    raise SystemExit(f"Unexpected worktree entry after recovery: {line}")

updated = page.read_text(encoding="utf-8")
for marker in (
    'data-felfel-uxui="reference-v6"',
    'object-[50%_18%]',
    'border-orange-500',
    'bg-gradient-to-r from-orange-600 to-orange-400',
    '<Puzzle className="h-5 w-5" />',
):
    if marker not in updated:
        raise SystemExit(f"V6 marker missing: {marker}")

print(f"{PATCH_ID} applied")
print(f"BRANCH={branch}")
print(f"HEAD={head}")
print(f"PAGE_STATE_BEFORE={current_page_blob}")
print(f"CANONICAL_V5_BLOB={git_blob_sha(canonical_v5)}")
print(f"CANONICAL_V6_BLOB={git_blob_sha(canonical_v6)}")
print(f"AVATAR_BLOB={EXPECTED_AVATAR_BLOB}")
print(f"MAUTIC_UNTRACKED_COUNT_PRESERVED={mautic_after}")
print("RECOVERY_IDEMPOTENT=YES")
print("MODIFIED_TRACKED_FILE=client/src/pages/FelfelPage.tsx")
print("AVATAR_ASSET_READY=YES")
print("BACKEND_CHANGED=NO")
print("ROUTER_CHANGED=NO")
print("DB_SCHEMA_CHANGED=NO")
print("FUNCTIONAL_BEHAVIOR_CHANGED=NO")
print("EXTERNAL_MAUTIC_CHANGED=NO")
print("NO_CLEAN_STASH_RESET_SWITCH_FETCH_PULL_MERGE_REBASE_COMMIT_PUSH=YES")
