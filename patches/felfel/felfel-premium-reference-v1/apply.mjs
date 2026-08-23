#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

/**
 * TCRM — Felfel Premium Reference UX/UI V1
 * Source: mohamedamouseo-a11y/TCRM-MAIN-Tamiyouz-CRM- (main)
 * Target: client/src/pages/FelfelPage.tsx
 * Scope: UI/UX + local portrait only. No API/DB/router/service behavior changes.
 */
const mode = process.argv[2] ?? '--check';
const tag = '[felfel-uxui-v1]';
const patchDir = path.dirname(fileURLToPath(import.meta.url));
const target = path.resolve(process.cwd(), 'client/src/pages/FelfelPage.tsx');
const avatarTarget = path.resolve(process.cwd(), 'client/public/ai-staff/felfel-avatar.webp');
const marker = 'data-felfel-uxui="premium-v1"';

if (!['--check', '--apply', '--verify'].includes(mode)) process.exit(2);
if (!fs.existsSync(target)) {
  console.error(`${tag} target not found: ${target}`);
  process.exit(2);
}
const raw = fs.readFileSync(target, 'utf8');
const crlf = raw.includes('\r\n');
let source = raw.replace(/\r\n/g, '\n');

function fail(message) { console.error(`${tag} ${message}`); process.exit(1); }
function once(label, before, after) {
  const count = source.split(before).length - 1;
  if (count !== 1) fail(`${label}: expected 1 anchor, found ${count}`);
  source = source.replace(before, after);
}
function regexOnce(label, regex, after) {
  const re = new RegExp(regex.source, regex.flags.includes('g') ? regex.flags : regex.flags + 'g');
  const count = source.match(re)?.length ?? 0;
  if (count !== 1) fail(`${label}: expected 1 region, found ${count}`);
  source = source.replace(regex, after);
}
function verify(text) {
  for (const [name, ok] of [
    ['marker', text.includes(marker)],
    ['portrait', text.includes('/ai-staff/felfel-avatar.webp')],
    ['metrics', text.includes('const felfelMetrics = [')],
    ['live workspace', text.includes('Felfel will automatically join, transcribe, extract insights')],
  ]) if (!ok) fail(`verify: ${name} missing`);
  if (!fs.existsSync(avatarTarget) || fs.statSync(avatarTarget).size < 3000) fail('verify: portrait missing or invalid');
  console.log(`${tag} verification passed`);
}

if (mode === '--verify') { verify(source); process.exit(0); }
if (source.includes(marker)) {
  console.log(`${tag} already applied`);
  if (mode === '--apply') verify(source);
  process.exit(0);
}

once(
  'metrics-model',
  '  const currentNativeId = status?.nativeId || meeting?.nativeId;',
  String.raw`  const currentNativeId = status?.nativeId || meeting?.nativeId;
  const felfelMetrics = [
    { label: ar ? "الاجتماعات" : "Meetings Processed", value: meetingsQ.data?.length ?? 0, Icon: History, tone: "bg-violet-500/10 text-violet-600 dark:text-violet-300", hint: ar ? "السجل المحمّل" : "Loaded history" },
    { label: ar ? "اجتماع نشط" : "Active Meeting", value: status?.active ? 1 : 0, Icon: Video, tone: "bg-blue-500/10 text-blue-600 dark:text-blue-300", hint: ar ? "الجلسة الحالية" : "Current session" },
    { label: ar ? "مقاطع التفريغ" : "Transcript Segments", value: transcript?.segments?.length ?? 0, Icon: Mic2, tone: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-300", hint: ar ? "الاجتماع الحالي" : "Current meeting" },
    { label: ar ? "المهام" : "Action Items", value: intelligence?.actionItems?.length ?? 0, Icon: CheckCircle2, tone: "bg-orange-500/10 text-orange-600 dark:text-orange-300", hint: ar ? "آخر تحليل" : "Latest analysis" },
    { label: ar ? "المتابعات" : "Follow-ups", value: crmClientId ? (followUpsQ.data?.length ?? 0) : 0, Icon: Clock3, tone: "bg-indigo-500/10 text-indigo-600 dark:text-indigo-300", hint: ar ? "للعميل المحدد" : "Selected client" },
    { label: ar ? "الأرشيف" : "Archive Saves", value: crmClientId ? (archivesQ.data?.length ?? 0) : 0, Icon: ExternalLink, tone: "bg-rose-500/10 text-rose-600 dark:text-rose-300", hint: ar ? "للعميل المحدد" : "Selected client" },
  ];`,
);

const oldHero = String.raw`      <div className="mx-auto flex max-w-[1600px] flex-col gap-5 p-4 md:p-6 xl:p-8" dir={isRTL ? "rtl" : "ltr"}>
        <div className="flex flex-col gap-4 rounded-2xl border bg-gradient-to-br from-orange-500/10 via-card to-card p-5 shadow-sm md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-orange-500/15 text-2xl" aria-hidden="true">🌶️</div>
            <div>
              <h1 className="text-2xl font-black tracking-tight md:text-3xl">{ar ? "فلفل" : "Felfel"}</h1>
              <p className="mt-1 text-muted-foreground">{ar ? "متخصص ذكاء اجتماعات AI" : "AI Meeting Intelligence Specialist"}</p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={health?.healthy ? "default" : "secondary"}>
              <span className="me-1.5 inline-block h-2 w-2 rounded-full bg-current" />
              {health?.healthy ? (ar ? "متصل" : "Connected") : (ar ? "جار الفحص" : "Checking")}
            </Badge>
            <Badge variant="outline">Vexa Lite</Badge>
          </div>
        </div>`;

const newHero = String.raw`      <div className="mx-auto flex max-w-[1660px] flex-col gap-4 p-4 md:p-5 xl:p-6" dir={isRTL ? "rtl" : "ltr"}>
        <section data-felfel-uxui="premium-v1" className="relative overflow-hidden rounded-[26px] border border-border/70 bg-card shadow-[0_18px_55px_-36px_rgba(15,23,42,0.55)]">
          <div className="pointer-events-none absolute -start-24 -top-24 h-64 w-64 rounded-full bg-orange-500/10 blur-3xl" />
          <div className="relative flex flex-col gap-5 p-5 md:p-6 xl:flex-row xl:items-center xl:justify-between">
            <div className="flex min-w-0 flex-col gap-5 md:flex-row md:items-center">
              <div className="relative mx-auto h-[148px] w-[148px] shrink-0 md:mx-0">
                <div className="h-full w-full overflow-hidden rounded-full border-8 border-muted/80 bg-muted shadow-inner ring-1 ring-border/70"><img src="/ai-staff/felfel-avatar.webp" alt={ar ? "فلفل" : "Felfel"} className="h-full w-full object-cover" /></div>
                <span className={"absolute bottom-3 end-2 h-6 w-6 rounded-full border-4 border-card " + (health?.healthy ? "bg-emerald-500" : "bg-muted-foreground")} />
              </div>
              <div className="min-w-0">
                <p className="mb-2 text-[11px] font-black uppercase tracking-[0.22em] text-orange-600 dark:text-orange-300">AI STAFF AGENT</p>
                <div className="flex flex-wrap items-center gap-2"><h1 className="text-3xl font-black tracking-[-0.035em] md:text-[38px]">{ar ? "فلفل" : "Felfel"}</h1><span className="grid h-8 w-8 place-items-center rounded-lg border border-orange-500/20 bg-orange-500/10 text-lg">🌶️</span></div>
                <p className="mt-1.5 text-base font-semibold text-muted-foreground">{ar ? "أخصائي ذكاء الاجتماعات بالذكاء الاصطناعي" : "AI Meeting Intelligence Specialist"}</p>
                <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">{ar ? "يحلل الاجتماعات، يفرّغ المحادثات نصيًا، يستخرج المهام، وينظم المتابعات والأرشيف داخل CRM." : "Analyzes meetings, transcribes conversations, extracts action items, and keeps CRM follow-ups and meeting archives organized."}</p>
                <div className="mt-4 flex flex-wrap gap-2">{[[ar ? "ذكاء الاجتماعات" : "Meeting Intelligence", Activity], [ar ? "التفريغ" : "Transcription", Mic2], [ar ? "المهام" : "Action Items", CheckCircle2], [ar ? "المتابعات" : "Follow-ups", Clock3]].map(([label, Icon]: any) => <Badge key={String(label)} variant="outline" className="h-8 gap-1.5 rounded-full border-border/70 bg-background/80 px-3 text-[11px] font-bold shadow-sm"><Icon className="h-3.5 w-3.5 text-orange-500" />{label}</Badge>)}</div>
              </div>
            </div>
            <div className="flex shrink-0 flex-col items-start gap-2 xl:items-end"><div className="flex flex-wrap items-center gap-2"><Badge variant="outline" className={"h-10 gap-2 rounded-xl px-4 font-bold " + (health?.healthy ? "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/70 dark:bg-emerald-950/40 dark:text-emerald-300" : "bg-muted/50 text-muted-foreground")}><span className={"h-2.5 w-2.5 rounded-full " + (health?.healthy ? "bg-emerald-500" : "bg-muted-foreground/60")} />{health?.healthy ? (ar ? "متصل" : "Connected") : (ar ? "جار الفحص" : "Checking")}</Badge><Badge variant="outline" className="h-10 gap-2 rounded-xl bg-background/80 px-4 font-bold shadow-sm"><RefreshCw className="h-4 w-4" />Vexa Lite</Badge></div><p className="text-[11px] font-medium text-muted-foreground">{ar ? "تحديث صحة الخدمة تلقائيًا كل 30 ثانية" : "Service health refreshes automatically every 30 seconds"}</p></div>
          </div>
        </section>
        <section className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">{felfelMetrics.map(({ label, value, Icon, tone, hint }) => <Card key={label} className="group rounded-2xl border-border/70 bg-card shadow-[0_12px_32px_-27px_rgba(15,23,42,0.7)] transition-all duration-200 hover:-translate-y-0.5 hover:border-orange-500/25 hover:shadow-md"><CardContent className="flex min-h-[116px] items-center gap-3 p-4"><div className={"grid h-11 w-11 shrink-0 place-items-center rounded-2xl " + tone}><Icon className="h-5 w-5" /></div><div className="min-w-0"><p className="text-[27px] font-black leading-none tracking-[-0.04em]">{value}</p><p className="mt-1.5 truncate text-xs font-bold">{label}</p><p className="mt-1 truncate text-[10px] font-medium text-muted-foreground">{hint}</p></div></CardContent></Card>)}</section>`;
once('hero-metrics', oldHero, newHero);

regexOnce('remove-old-meeting-form', /        <Card className="border-border\/70 shadow-sm">[\s\S]*?        <\/Card>\n\n        <Tabs defaultValue="live"/, '        <Tabs defaultValue="live"');

once(
  'tabs-style',
  '          <TabsList className="h-auto w-full flex-nowrap justify-start gap-1 overflow-x-auto rounded-2xl bg-muted/60 p-1.5 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden [&_[role=tab]]:shrink-0">',
  '          <TabsList className="h-auto w-full flex-nowrap justify-start gap-1 overflow-x-auto rounded-2xl border border-border/70 bg-card p-1.5 shadow-sm [scrollbar-width:none] [&::-webkit-scrollbar]:hidden [&_[role=tab]]:h-10 [&_[role=tab]]:shrink-0 [&_[role=tab]]:rounded-xl [&_[role=tab]]:px-4 [&_[role=tab]]:text-xs [&_[role=tab]]:font-bold [&_[data-state=active]]:bg-orange-500/10 [&_[data-state=active]]:text-orange-600 [&_[data-state=active]]:shadow-none dark:[&_[data-state=active]]:text-orange-300">',
);

const newLive = String.raw`          <TabsContent value="live" className="mt-3 space-y-4">
            <div className="grid gap-4 xl:grid-cols-2">
              <Card className="overflow-hidden rounded-2xl border-border/70 shadow-sm"><CardHeader className="pb-3"><CardTitle className="flex items-center gap-2 text-base"><Video className="h-5 w-5 text-orange-500" />{ar ? "اجتماع جديد" : "New Meeting"}</CardTitle><CardDescription>{ar ? "الصق رابط الاجتماع وفلفل سينضم ويبدأ المعالجة فورًا." : "Paste a meeting link and Felfel will join and process it in real time."}</CardDescription></CardHeader><CardContent className="space-y-3">
                <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_180px]"><div className="space-y-2"><Label htmlFor="felfel-meeting-url">{ar ? "رابط الاجتماع" : "Meeting URL"}</Label><Input id="felfel-meeting-url" dir="ltr" value={meetingUrl} onChange={(event) => setMeetingUrl(event.target.value)} placeholder="https://meet.google.com/abc-defg-hij" aria-invalid={Boolean(meetingUrl) && !urlValid} className="h-11 rounded-xl" /></div><div className="space-y-2"><Label>{ar ? "المنصة" : "Platform"}</Label><div className="flex h-11 items-center gap-2 rounded-xl border bg-muted/20 px-3 text-sm font-semibold"><Video className="h-4 w-4 text-emerald-600" />{platform ? platformLabel(platform, ar) : (ar ? "تلقائي" : "Auto-detect")}</div></div></div>
                <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_160px] lg:items-end"><div className="space-y-2"><Label htmlFor="felfel-bot-name">{ar ? "اسم الوكيل" : "Bot Name"}</Label><Input id="felfel-bot-name" value={botName} onChange={(event) => setBotName(event.target.value)} maxLength={100} className="h-11 rounded-xl" /></div><Button onClick={() => createMeetingM.mutate({ meetingUrl: meetingUrl.trim(), botName: botName.trim() || "Felfel" })} disabled={!urlValid || createMeetingM.isPending} className="h-11 gap-2 rounded-xl bg-orange-600 font-bold text-white hover:bg-orange-700">{createMeetingM.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Mic2 className="h-4 w-4" />}{ar ? "دخول الاجتماع" : "Join Meeting"}</Button></div>
                {meetingUrl && <p className={"text-xs font-medium " + (urlValid ? "text-emerald-600" : "text-destructive")}>{urlValid ? (ar ? "الرابط مدعوم وجاهز." : "Supported meeting link. Ready to join.") : (ar ? "استخدم Google Meet أو Teams أو Zoom أو Jitsi." : "Use Google Meet, Teams, Zoom, or Jitsi.")}</p>}
                <div className="flex items-start gap-2 rounded-xl border border-orange-500/20 bg-orange-500/5 p-3 text-xs leading-5 text-muted-foreground"><span className="mt-0.5 text-orange-500">✦</span><span>{ar ? "فلفل سينضم تلقائيًا، يفرّغ الاجتماع، يستخرج الرؤى والمهام، ثم يتيح مزامنتها مع CRM بعد موافقتك." : "Felfel will automatically join, transcribe, extract insights and action items, then let you sync approved results to your CRM."}</span></div>
              </CardContent></Card>
              <Card className="overflow-hidden rounded-2xl border-border/70 shadow-sm"><CardHeader className="pb-3"><div className="flex items-start justify-between gap-3"><div><CardTitle className="flex items-center gap-2 text-base"><Activity className="h-5 w-5 text-emerald-600" />{ar ? "حالة الاجتماع المباشر" : "Live Meeting Status"}</CardTitle><CardDescription className="mt-1">{meeting ? platformLabel(currentPlatform, ar) : (ar ? "لا يوجد اجتماع نشط" : "No active meeting")}</CardDescription></div><Badge variant="outline" className={"rounded-full px-3 py-1 text-[11px] font-bold " + (status?.active ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "bg-muted/40 text-muted-foreground")}>{status?.active ? (ar ? "يستمع" : "Listening") : (ar ? "غير نشط" : "Idle")}</Badge></div></CardHeader><CardContent>{!meeting ? <div className="grid min-h-[210px] place-items-center rounded-2xl border border-dashed bg-muted/10 text-center"><div><Video className="mx-auto h-8 w-8 text-muted-foreground/50" /><p className="mt-3 text-sm font-bold">{ar ? "ابدأ اجتماعًا من النموذج المجاور" : "Start a meeting from the form next to this panel"}</p><p className="mt-1 text-xs text-muted-foreground">{ar ? "ستظهر الحالة والمعلومات هنا مباشرة." : "Live status and meeting metadata will appear here."}</p></div></div> : statusQ.isLoading ? <div className="flex min-h-[210px] items-center justify-center gap-2 text-sm text-muted-foreground"><RefreshCw className="h-4 w-4 animate-spin" />{ar ? "جار تحميل الحالة..." : "Loading status..."}</div> : statusQ.error ? <QueryError ar={ar} message={statusQ.error.message} /> : <div className="space-y-4"><div><p className="text-sm font-black">{botName || "Felfel"}</p><p className="mt-1 truncate font-mono text-xs text-muted-foreground" dir="ltr">{currentNativeId || "—"}</p></div><div className="grid grid-cols-2 gap-2 sm:grid-cols-4"><div className="rounded-xl border bg-emerald-500/5 p-3"><p className="text-[10px] font-bold uppercase text-muted-foreground">{ar ? "الحالة" : "Status"}</p><p className="mt-1 text-sm font-black">{currentStatus}</p></div><div className="rounded-xl border bg-blue-500/5 p-3"><p className="text-[10px] font-bold uppercase text-muted-foreground">{ar ? "المنصة" : "Platform"}</p><p className="mt-1 truncate text-sm font-black">{platformLabel(currentPlatform, ar)}</p></div><div className="rounded-xl border bg-violet-500/5 p-3"><p className="text-[10px] font-bold uppercase text-muted-foreground">{ar ? "المقاطع" : "Segments"}</p><p className="mt-1 text-sm font-black">{transcript?.segments?.length ?? 0}</p></div><div className="rounded-xl border bg-orange-500/5 p-3"><p className="text-[10px] font-bold uppercase text-muted-foreground">{ar ? "بدأ" : "Started"}</p><p className="mt-1 truncate text-xs font-bold">{formatTimestamp(status?.startedAt, ar)}</p></div></div><div className="flex flex-wrap items-center gap-2 border-t pt-3">{meeting.meetingUrl && <Button asChild size="sm" variant="outline" className="rounded-xl"><a href={meeting.meetingUrl} target="_blank" rel="noreferrer"><ExternalLink className="me-1.5 h-3.5 w-3.5" />{ar ? "فتح الاجتماع" : "Open Meeting"}</a></Button>}<Button size="sm" variant="destructive" className="rounded-xl" onClick={() => leaveMeetingM.mutate({ platform: meeting.platform as "google_meet" | "teams" | "zoom" | "jitsi", nativeId: meeting.nativeId })} disabled={leaveMeetingM.isPending}>{leaveMeetingM.isPending ? <Loader2 className="me-1.5 h-3.5 w-3.5 animate-spin" /> : <LogOut className="me-1.5 h-3.5 w-3.5" />}{ar ? "مغادرة" : "Leave"}</Button></div></div>}</CardContent></Card>
            </div>
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{[
              { title: ar ? "التفريغ والذكاء" : "Transcript & Intelligence", text: ar ? "تفريغ مباشر وتحليل مدعوم بالذكاء الاصطناعي." : "Real-time transcription with AI-powered insights.", value: transcript?.segments?.length ?? 0, Icon: Mic2 },
              { title: ar ? "المهام" : "Action Items", text: ar ? "مهام مستخرجة مع الموافقة قبل إنشاءها." : "AI-extracted tasks with approval before CRM creation.", value: intelligence?.actionItems?.length ?? 0, Icon: CheckCircle2 },
              { title: ar ? "متابعات CRM" : "CRM Follow-ups", text: ar ? "متابعات تتم مزامنتها مع CRM بعد الموافقة." : "Follow-ups synced to CRM after approval.", value: crmClientId ? (followUpsQ.data?.length ?? 0) : 0, Icon: Clock3 },
              { title: ar ? "أرشيف الاجتماعات" : "Meeting Archive", text: ar ? "أرشيف منظم داخل CRM وGoogle Drive." : "Structured archive saved to CRM and Google Drive.", value: crmClientId ? (archivesQ.data?.length ?? 0) : 0, Icon: ExternalLink },
            ].map(({ title, text, value, Icon }) => <Card key={title} className="rounded-2xl border-border/70 shadow-sm"><CardContent className="flex min-h-[126px] items-center justify-between gap-3 p-4"><div className="min-w-0"><div className="flex items-center gap-2"><Icon className="h-4 w-4 text-orange-500" /><p className="text-sm font-black">{title}</p></div><p className="mt-2 text-xs leading-5 text-muted-foreground">{text}</p></div><div className="grid h-12 min-w-12 place-items-center rounded-2xl bg-muted/50 px-3 text-lg font-black">{value}</div></CardContent></Card>)}</div>
          </TabsContent>`;
regexOnce('live-workspace', /          <TabsContent value="live" className="mt-4">[\s\S]*?          <\/TabsContent>/, newLive);

if (mode === '--check') { console.log(`${tag} check passed`); process.exit(0); }
const payload = path.join(patchDir, 'felfel-avatar.b64');
if (!fs.existsSync(payload)) fail('avatar payload missing');
const b64 = fs.readFileSync(payload, 'utf8').trim();
if (b64.length < 5000) fail('avatar payload invalid');
fs.mkdirSync(path.dirname(avatarTarget), { recursive: true });
fs.writeFileSync(avatarTarget, Buffer.from(b64, 'base64'));
fs.writeFileSync(target, crlf ? source.replace(/\n/g, '\r\n') : source, 'utf8');
console.log(`${tag} applied`);
console.log(`${tag} next: npm run check && node <patch-path>/apply.mjs --verify`);
