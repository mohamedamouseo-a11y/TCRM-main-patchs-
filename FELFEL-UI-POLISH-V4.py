#!/usr/bin/env python3
# FELFEL_UI_POLISH_V4_COMPACT_WORKSPACE
from pathlib import Path
import subprocess

ROOT = Path('/var/www/TCRM-MAIN')
EXPECTED = '7019ea102eddda2cbf3f40d3a35111058b7c56f0'

if not ROOT.exists():
    raise SystemExit('TCRM root not found')

try:
    head = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
except Exception as exc:
    raise SystemExit(f'cannot read git HEAD: {exc}')
if head != EXPECTED:
    raise SystemExit(f'BASE_MISMATCH expected={EXPECTED[:8]} actual={head[:8]}')


def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def write(rel, text):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected 1 anchor, found {count}')
    return text.replace(old, new, 1)


workspace = r'''// FELFEL_UI_POLISH_V4_COMPACT_WORKSPACE
// @ts-nocheck
import { useState } from "react";
import { Link } from "wouter";
import {
  BrainCircuit,
  CalendarDays,
  ChevronDown,
  ChevronUp,
  Clock3,
  Headphones,
  Mic2,
  MonitorPlay,
  Radio,
  UserRound,
  UsersRound,
  Video as VideoIcon,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import FelfelMeetingTitleEditor from "@/components/felfel/FelfelMeetingTitleEditor";
import FelfelRecordingPlayer from "@/components/felfel/FelfelRecordingPlayer";
import FelfelTranscriptPanel from "@/components/felfel/FelfelTranscriptPanel";
import FelfelMeetingIntelligencePanel from "@/components/felfel/FelfelMeetingIntelligencePanel";

function displayDate(value: unknown, ar: boolean) {
  if (!value) return "—";
  const date = new Date(String(value));
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString(ar ? "ar-EG" : "en-US", { dateStyle: "medium", timeStyle: "short" });
}

function durationLabel(meeting: any) {
  const stored = Number(meeting?.recordingDurationSec || 0);
  let seconds = stored;
  if ((!Number.isFinite(seconds) || seconds <= 0) && meeting?.startedAt && meeting?.endedAt) {
    const start = new Date(meeting.startedAt).getTime();
    const end = new Date(meeting.endedAt).getTime();
    if (Number.isFinite(start) && Number.isFinite(end) && end > start) seconds = Math.round((end - start) / 1000);
  }
  if (!Number.isFinite(seconds) || seconds <= 0) return "—";
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainder = Math.round(seconds % 60).toString().padStart(2, "0");
  return hours > 0 ? `${hours}:${String(minutes).padStart(2, "0")}:${remainder}` : `${minutes}:${remainder}`;
}

function statusVariant(status: string) {
  if (status === "completed") return "default" as const;
  if (status === "failed") return "destructive" as const;
  return "secondary" as const;
}

function statusDot(status: string) {
  if (status === "completed") return "bg-emerald-500";
  if (status === "failed") return "bg-red-500";
  if (["live", "processing", "joining", "waiting"].includes(status)) return "bg-orange-500";
  return "bg-slate-400";
}

function FelfelMeetingScene({ meeting, ar }: { meeting: any; ar: boolean }) {
  return (
    <div className="relative min-h-[210px] overflow-hidden rounded-2xl border border-violet-500/15 bg-gradient-to-br from-violet-500/10 via-background to-orange-500/10 p-4">
      <div className="pointer-events-none absolute -end-10 -top-12 h-40 w-40 rounded-full bg-violet-500/10 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-14 -start-10 h-36 w-36 rounded-full bg-orange-500/10 blur-3xl" />
      <div className="relative flex h-full min-h-[178px] flex-col justify-between">
        <div className="flex items-center justify-between gap-2">
          <div className="inline-flex items-center gap-2 rounded-full border border-border/70 bg-background/80 px-3 py-1.5 text-[11px] font-bold shadow-sm backdrop-blur">
            <span className={`h-2 w-2 rounded-full ${statusDot(String(meeting?.status || ""))}`} />
            {ar ? "فلفل داخل مساحة الاجتماع" : "Felfel meeting workspace"}
          </div>
          <Badge variant="outline" className="bg-background/75">{meeting?.platform || "meeting"}</Badge>
        </div>

        <div className="flex items-center justify-center py-2">
          <div className="relative">
            <div className="absolute -inset-3 rounded-full border border-violet-500/20 bg-violet-500/5" />
            <div className="relative h-24 w-24 overflow-hidden rounded-full border-4 border-background bg-muted shadow-xl">
              <img src="/ai-staff/felfel-avatar.webp" alt="Felfel" className="h-full w-full object-cover object-[50%_18%]" />
            </div>
            <div className="absolute -bottom-1 -end-1 grid h-8 w-8 place-items-center rounded-full border-2 border-background bg-emerald-500 text-white shadow"><Radio className="h-4 w-4" /></div>
          </div>
        </div>

        <div className="grid grid-cols-[1fr_auto_1fr] items-end gap-2">
          <div className="rounded-xl border border-border/60 bg-background/75 p-2.5 shadow-sm backdrop-blur">
            <div className="flex items-center gap-2"><div className="grid h-8 w-8 place-items-center rounded-full bg-blue-500/10 text-blue-600"><UserRound className="h-4 w-4" /></div><div className="min-w-0"><p className="truncate text-[11px] font-bold">{meeting?.invokerName || (ar ? "مستدعي فلفل" : "Felfel invoker")}</p><p className="truncate text-[10px] text-muted-foreground">{meeting?.invokerRole || "CRM"}</p></div></div>
          </div>
          <div className="flex items-center gap-1 rounded-full border border-border/70 bg-background/90 px-2 py-1.5 shadow-sm"><span className="grid h-7 w-7 place-items-center rounded-full bg-muted"><Mic2 className="h-3.5 w-3.5" /></span><span className="grid h-7 w-7 place-items-center rounded-full bg-muted"><VideoIcon className="h-3.5 w-3.5" /></span><span className="grid h-7 w-7 place-items-center rounded-full bg-muted"><UsersRound className="h-3.5 w-3.5" /></span></div>
          <div className="rounded-xl border border-border/60 bg-background/75 p-2.5 shadow-sm backdrop-blur">
            <div className="flex items-center gap-2"><div className="grid h-8 w-8 place-items-center rounded-full bg-orange-500/10 text-orange-600"><MonitorPlay className="h-4 w-4" /></div><div className="min-w-0"><p className="truncate text-[11px] font-bold">{meeting?.clientName || (ar ? "العميل" : "Client")}</p><p className="truncate text-[10px] text-muted-foreground">{ar ? "سياق الاجتماع" : "Meeting context"}</p></div></div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function FelfelMeetingWorkspaceCard({
  meeting,
  crmHref,
  isRTL,
  ar,
}: {
  meeting: any;
  crmHref?: string | null;
  isRTL: boolean;
  ar: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  const [tab, setTab] = useState("overview");
  const status = String(meeting?.status || "scheduled");
  const recordingFailed = String(meeting?.recordingStatus || "") === "failed";
  const hasPlayableRecording = Boolean((Array.isArray(meeting?.recordingMedia) && meeting.recordingMedia.length) || meeting?.recordingDriveUrl);
  const analysis = meeting?.analysisData || {};

  return (
    <div className="overflow-hidden rounded-[20px] border border-border/70 bg-card shadow-sm transition-shadow hover:shadow-md" data-felfel-meeting-card="compact-v4">
      <div className="flex flex-col gap-3 px-4 py-3 md:flex-row md:items-center md:justify-between">
        <div className="flex min-w-0 flex-1 items-start gap-3">
          <Button type="button" variant="ghost" size="icon" className="mt-0.5 h-9 w-9 shrink-0 rounded-xl border border-border/60" onClick={() => setExpanded((value) => !value)} aria-expanded={expanded}>
            {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </Button>
          <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-violet-500/10 text-violet-600"><VideoIcon className="h-5 w-5" /></div>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <FelfelMeetingTitleEditor meetingId={Number(meeting.id)} title={meeting.title} ownerUserId={meeting.ownerUserId} isRTL={isRTL} />
              <Badge variant={statusVariant(status)} className="rounded-full">{status}</Badge>
              <Badge variant="outline" className="rounded-full">#{meeting.id}</Badge>
            </div>
            <div className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-muted-foreground">
              <span className="inline-flex items-center gap-1"><CalendarDays className="h-3.5 w-3.5" />{displayDate(meeting.startedAt || meeting.scheduledAt || meeting.createdAt, ar)}</span>
              <span className="inline-flex items-center gap-1"><Clock3 className="h-3.5 w-3.5" />{durationLabel(meeting)}</span>
              <span className="inline-flex items-center gap-1"><VideoIcon className="h-3.5 w-3.5" />{meeting.platform || "—"}</span>
              <span className="inline-flex items-center gap-1"><UserRound className="h-3.5 w-3.5" />{meeting.invokerName || `#${meeting.ownerUserId || "—"}`}</span>
            </div>
          </div>
        </div>

        <div className="flex shrink-0 flex-wrap items-center gap-1.5 ps-12 md:ps-0">
          <Badge variant="outline" className={recordingFailed ? "rounded-full border-red-500/25 bg-red-500/5 text-red-600" : "rounded-full border-emerald-500/20 bg-emerald-500/5 text-emerald-700 dark:text-emerald-300"}>{ar ? "التسجيل" : "Recording"}: {meeting.recordingStatus || "not_started"}</Badge>
          <Badge variant="outline" className="rounded-full border-blue-500/20 bg-blue-500/5 text-blue-700 dark:text-blue-300">{ar ? "التفريغ" : "Transcript"}: {meeting.transcriptStatus || "not_started"}</Badge>
          <Badge variant="outline" className="rounded-full border-violet-500/20 bg-violet-500/5 text-violet-700 dark:text-violet-300">{ar ? "التحليل" : "Analysis"}: {meeting.analysisStatus || "not_started"}</Badge>
        </div>
      </div>

      {expanded && (
        <div className="border-t border-border/60 bg-muted/[0.12] p-3 md:p-4">
          <Tabs value={tab} onValueChange={setTab} dir={isRTL ? "rtl" : "ltr"}>
            <TabsList className="grid h-auto w-full grid-cols-3 rounded-xl bg-muted/65 p-1">
              <TabsTrigger value="overview" className="rounded-lg py-2 text-xs">{ar ? "نظرة عامة" : "Overview"}</TabsTrigger>
              <TabsTrigger value="media" className="rounded-lg py-2 text-xs"><Headphones className="me-1.5 h-3.5 w-3.5" />{ar ? "التسجيل والتفريغ" : "Recording & Transcript"}</TabsTrigger>
              <TabsTrigger value="intelligence" className="rounded-lg py-2 text-xs"><BrainCircuit className="me-1.5 h-3.5 w-3.5" />{ar ? "ذكاء الاجتماع" : "Intelligence"}</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="mt-3">
              <div className="grid gap-3 xl:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)]">
                <FelfelMeetingScene meeting={meeting} ar={ar} />
                <div className="grid content-start gap-3 sm:grid-cols-2">
                  <div className="rounded-xl border border-border/60 bg-background p-3"><p className="text-[11px] font-bold text-muted-foreground">{ar ? "العميل" : "Client"}</p>{crmHref ? <Link href={crmHref}><a className="mt-1 block truncate text-sm font-bold text-primary hover:underline">{meeting.clientName || `#${meeting.clientId || meeting.leadId}`}</a></Link> : <p className="mt-1 text-sm font-bold">{meeting.clientName || "—"}</p>}</div>
                  <div className="rounded-xl border border-border/60 bg-background p-3"><p className="text-[11px] font-bold text-muted-foreground">{ar ? "استدعى فلفل" : "Invoked by"}</p><p className="mt-1 text-sm font-bold">{meeting.invokerName || `User #${meeting.ownerUserId || "—"}`}</p><p className="mt-1 text-[11px] text-muted-foreground">{meeting.invokerRole || "—"}</p></div>
                  <div className="rounded-xl border border-border/60 bg-background p-3"><p className="text-[11px] font-bold text-muted-foreground">{ar ? "بداية الاجتماع" : "Started"}</p><p className="mt-1 text-xs font-semibold">{displayDate(meeting.startedAt, ar)}</p></div>
                  <div className="rounded-xl border border-border/60 bg-background p-3"><p className="text-[11px] font-bold text-muted-foreground">{ar ? "نهاية الاجتماع" : "Ended"}</p><p className="mt-1 text-xs font-semibold">{displayDate(meeting.endedAt, ar)}</p></div>
                  {analysis?.summary && <div className="sm:col-span-2 rounded-xl border border-orange-500/15 bg-orange-500/[0.035] p-3"><p className="text-[11px] font-black text-orange-700 dark:text-orange-300">{ar ? "ملخص سريع" : "Quick summary"}</p><p className="mt-1 line-clamp-4 text-sm leading-6">{analysis.summary}</p></div>}
                </div>
              </div>
            </TabsContent>

            <TabsContent value="media" className="mt-3">
              <div className="grid gap-3 xl:grid-cols-2">
                {recordingFailed && !hasPlayableRecording ? (
                  <div className="flex min-h-36 items-center justify-center rounded-2xl border border-red-500/20 bg-red-500/[0.035] p-5 text-center">
                    <div><div className="mx-auto grid h-10 w-10 place-items-center rounded-full bg-red-500/10 text-red-600"><VideoIcon className="h-5 w-5" /></div><p className="mt-2 text-sm font-bold text-red-700 dark:text-red-300">{ar ? "التسجيل غير متاح لهذا الاجتماع" : "Recording is unavailable for this meeting"}</p><p className="mt-1 text-xs text-muted-foreground">{ar ? "التفريغ والتحليل يفضلوا متاحين بشكل مستقل." : "Transcript and intelligence remain available independently."}</p></div>
                  </div>
                ) : (
                  <FelfelRecordingPlayer media={meeting.recordingMedia} driveUrl={meeting.recordingDriveUrl} durationSec={meeting.recordingDurationSec} sizeBytes={meeting.recordingSizeBytes} isRTL={isRTL} />
                )}
                <FelfelTranscriptPanel segments={meeting.transcriptSegments} status={meeting.transcriptStatus} isRTL={isRTL} />
              </div>
            </TabsContent>

            <TabsContent value="intelligence" className="mt-0">
              <FelfelMeetingIntelligencePanel meeting={meeting} isRTL={isRTL} />
            </TabsContent>
          </Tabs>
        </div>
      )}
    </div>
  );
}
'''

new_rel = 'client/src/components/felfel/FelfelMeetingWorkspaceCard.tsx'
new_path = ROOT / new_rel
if new_path.exists():
    existing = new_path.read_text(encoding='utf-8')
    if 'FELFEL_UI_POLISH_V4_COMPACT_WORKSPACE' in existing:
        raise SystemExit('already_applied')
    raise RuntimeError(f'{new_rel} already exists without V4 marker')
write(new_rel, workspace)

# Operational dashboard: preserve hero; compact filters; replace always-open meeting bodies with compact workspace cards.
rel = 'client/src/components/felfel/FelfelOperationalDashboard.tsx'
text = read(rel)
text = replace_once(
    text,
    'import FelfelMeetingIntelligencePanel from "@/components/felfel/FelfelMeetingIntelligencePanel";\n',
    'import FelfelMeetingIntelligencePanel from "@/components/felfel/FelfelMeetingIntelligencePanel";\nimport FelfelMeetingWorkspaceCard from "@/components/felfel/FelfelMeetingWorkspaceCard";\n',
    'dashboard workspace import',
)
text = replace_once(text, 'data-felfel-operational-dashboard="phase1-v1"', 'data-felfel-operational-dashboard="ui-polish-v4"', 'dashboard marker')
text = replace_once(text, 'className="grid gap-3 lg:grid-cols-4 2xl:grid-cols-7"', 'className="grid gap-2 md:grid-cols-2 xl:grid-cols-8"', 'compact filters grid')
text = replace_once(text, 'className="relative lg:col-span-2 2xl:col-span-2"', 'className="relative md:col-span-2 xl:col-span-2"', 'compact search span')
text = replace_once(
    text,
    '<div className="grid grid-cols-2 gap-2"><Input type="date" value={fromDate}',
    '<div className="grid grid-cols-2 gap-2 md:col-span-2 xl:col-span-2"><Input type="date" value={fromDate}',
    'date filters span',
)
start_token = '            return (\n              <Card key={meeting.id} className="overflow-hidden rounded-[22px] border-border/70 shadow-sm">'
end_token = '              </Card>\n            );'
start = text.find(start_token)
if start < 0:
    raise RuntimeError('dashboard meeting card start anchor not found')
end = text.find(end_token, start)
if end < 0:
    raise RuntimeError('dashboard meeting card end anchor not found')
end += len(end_token)
replacement = '''            return (\n              <FelfelMeetingWorkspaceCard\n                key={meeting.id}\n                meeting={meeting}\n                crmHref={crmHref}\n                isRTL={isRTL}\n                ar={ar}\n              />\n            );'''
text = text[:start] + replacement + text[end:]
write(rel, text)

# Client Pool: keep Meetings as a first-level peer tab and prevent it wrapping below the other tabs.
rel = 'client/src/pages/ClientPool.tsx'
text = read(rel)
text = replace_once(
    text,
    '<div className="mb-4 flex flex-wrap gap-2 rounded-2xl border border-border bg-card p-1">',
    '<div className="mb-4 flex gap-2 overflow-x-auto rounded-2xl border border-border bg-card p-1 [scrollbar-width:thin]">',
    'client pool tab row no-wrap',
)
old = '''                              size="sm"\n                              className="rounded-xl"\n                              onClick={e => {'''
new = '''                              size="sm"\n                              className="shrink-0 rounded-xl"\n                              onClick={e => {'''
text = replace_once(text, old, new, 'client pool peer tab button')
write(rel, text)

print('FELFEL_UI_POLISH_V4_PATCHED=YES')
print('FILES=3')
