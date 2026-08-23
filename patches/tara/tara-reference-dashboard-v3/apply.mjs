#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

/**
 * TCRM — Tara Reference Dashboard V3
 * Visual-only Tara redesign aligned to the approved reference mockup.
 * Scope: client/src/pages/TaraAgentPage.tsx + existing Tara portrait asset only.
 * No API, DB, routes, permissions, settings semantics, or Tara business logic changes.
 */

const mode = process.argv[2] ?? '--check';
const cwd = process.cwd();
const target = path.resolve(cwd, 'client/src/pages/TaraAgentPage.tsx');
const avatarTarget = path.resolve(cwd, 'client/src/assets/ai-staff/tara-avatar.jpg');
const patchDir = path.dirname(fileURLToPath(import.meta.url));
const fallbackAvatarB64 = path.resolve(patchDir, '../tara-professional-identity-v2.3/tara-avatar-160.jpg.b64');
const PATCH_MARKER = 'TARA_REFERENCE_DASHBOARD_V3';

function fail(message, code = 1) {
  console.error(`[tara-reference-dashboard-v3] ${message}`);
  process.exit(code);
}
function info(message) {
  console.log(`[tara-reference-dashboard-v3] ${message}`);
}
function replaceOnce(input, before, after, label) {
  if (!input.includes(before)) fail(`expected block not found: ${label}`);
  return input.replace(before, after);
}

if (!fs.existsSync(target)) fail(`target not found: ${target}`, 2);
const originalRaw = fs.readFileSync(target, 'utf8');
const usesCRLF = originalRaw.includes('\r\n');
let source = originalRaw.replace(/\r\n/g, '\n');

const identityHelper = `function getTaraIdentity(isRTL: boolean) {
    return isRTL
        ? {
            badge: "AI STAFF AGENT",
            primaryTitle: "أخصائي المبيعات الهاتفية وتأهيل العملاء المحتملين بالذكاء الاصطناعي",
            secondaryTitle: "AI Telesales & Lead Qualification Specialist",
            summary: "تارا أخصائية مبيعات مدعومة بالذكاء الاصطناعي تركز على تأهيل العملاء المحتملين، وإدارة محادثات العملاء، وتنفيذ المتابعات الهادفة لدعم التحويل إلى فرص بيع فعلية.",
            focus: ["المبيعات الهاتفية", "تأهيل العملاء", "المتابعات", "محادثات العملاء"],
            alt: "الصورة المهنية لتارا",
        }
        : {
            badge: "AI STAFF AGENT",
            primaryTitle: "AI Telesales & Lead Qualification Specialist",
            secondaryTitle: "أخصائي المبيعات الهاتفية وتأهيل العملاء المحتملين بالذكاء الاصطناعي",
            summary: "Tara is your AI-powered telesales specialist focused on lead qualification, customer conversations, and meaningful follow-ups that help convert prospects into loyal customers.",
            focus: ["Telesales", "Lead Qualification", "Follow-ups", "Customer Conversations"],
            alt: "Professional portrait of Tara",
        };
}`;

const metricsBinding = `    const metricItems = [
        { label: isRTL ? "الحملات" : "Campaigns", value: counts.campaigns, Icon: Brain, bubble: "bg-violet-100 text-violet-700 dark:bg-violet-950/50 dark:text-violet-300" },
        { label: isRTL ? "المحادثات" : "Conversations", value: counts.conversations, Icon: MessageSquareText, bubble: "bg-blue-100 text-blue-700 dark:bg-blue-950/50 dark:text-blue-300" },
        { label: isRTL ? "الجلسات النشطة" : "Active Sessions", value: counts.active, Icon: Activity, bubble: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300" },
        { label: isRTL ? "التحويلات البشرية" : "Human Handoffs", value: counts.handoff, Icon: Users, bubble: "bg-orange-100 text-orange-700 dark:bg-orange-950/50 dark:text-orange-300" },
        { label: isRTL ? "عمليات الذكاء" : "AI Operations", value: counts.runs, Icon: Bot, bubble: "bg-indigo-100 text-indigo-700 dark:bg-indigo-950/50 dark:text-indigo-300" },
        { label: isRTL ? "الأخطاء" : "Errors", value: counts.failedRuns, Icon: ShieldCheck, bubble: "bg-rose-100 text-rose-700 dark:bg-rose-950/50 dark:text-rose-300" },
    ];`;

const heroAndMetrics = `      {/* ${PATCH_MARKER} */}
      <section className="rounded-[26px] border border-border/70 bg-card p-5 shadow-sm md:p-6">
        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_auto] xl:items-start">
          <div className="flex min-w-0 flex-col gap-5 sm:flex-row sm:items-start">
            <div className="relative mx-auto h-[112px] w-[112px] shrink-0 sm:mx-0">
              <div className="h-full w-full overflow-hidden rounded-full border-[5px] border-background bg-muted ring-1 ring-border/70 shadow-md">
                <img src={taraAvatar} alt={taraIdentity.alt} draggable={false} className="block h-full w-full object-cover object-[50%_22%]" />
              </div>
              <span className={"absolute bottom-1 end-1 h-5 w-5 rounded-full border-[3px] border-card shadow-sm " + (settings.enabled ? "bg-emerald-500" : "bg-muted-foreground")} />
            </div>

            <div className="min-w-0 flex-1 text-center sm:text-start">
              <p className="text-[10px] font-black uppercase tracking-[0.28em] text-primary">{taraIdentity.badge}</p>
              <div className="mt-2 flex flex-wrap items-center justify-center gap-2 sm:justify-start">
                <h1 className="text-3xl font-black tracking-[-0.04em] text-foreground md:text-4xl">Tara</h1>
                <span className="grid h-8 w-8 place-items-center rounded-lg bg-primary/10 text-primary"><Bot className="h-4 w-4" /></span>
              </div>
              <p className="mt-2 text-sm font-extrabold text-primary md:text-base">{taraIdentity.primaryTitle}</p>
              <p className="mt-1 text-sm font-semibold text-muted-foreground">{taraIdentity.secondaryTitle}</p>
              <p className="mt-3 max-w-3xl text-sm leading-6 text-muted-foreground">{taraIdentity.summary}</p>
              <div className="mt-4 flex flex-wrap justify-center gap-2 sm:justify-start">
                {taraIdentity.focus.map((item: string) => (
                  <span key={item} className="inline-flex items-center gap-1.5 rounded-full border border-primary/10 bg-primary/[0.045] px-3 py-1.5 text-[11px] font-bold text-foreground">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />{item}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-2 sm:justify-start xl:justify-end">
            <Badge variant="outline" className={"h-10 gap-2 rounded-xl px-4 text-xs font-bold " + (settings.enabled ? "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/70 dark:bg-emerald-950/40 dark:text-emerald-300" : "border-border bg-muted/50 text-muted-foreground")}>
              <span className={"h-2 w-2 rounded-full " + (settings.enabled ? "bg-emerald-500 shadow-[0_0_0_4px_rgba(16,185,129,0.10)]" : "bg-muted-foreground/60")} />
              {settings.enabled ? (isRTL ? "مفعلة" : "Enabled") : (isRTL ? "متوقفة" : "Disabled")}
            </Badge>
            <Button variant="outline" className="h-10 rounded-xl bg-background px-4 shadow-none" onClick={() => refresh()}>
              <RefreshCw className="ms-2 h-4 w-4" />{isRTL ? "تحديث" : "Refresh"}
            </Button>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
        {metricItems.map(({ label, value, Icon, bubble }: any) => (
          <Card key={label} className="rounded-2xl border-border/70 bg-card shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md">
            <CardContent className="flex min-h-[132px] flex-col justify-between p-4">
              <div className={"grid h-10 w-10 place-items-center rounded-xl " + bubble}><Icon className="h-5 w-5" /></div>
              <div className="mt-4">
                <p className="text-[28px] font-black leading-none tracking-[-0.04em] text-foreground">{Number(value || 0).toLocaleString()}</p>
                <p className="mt-2 text-xs font-semibold text-muted-foreground">{label}</p>
                <p className="mt-2 text-[10px] font-medium text-muted-foreground/70">{isRTL ? "بيانات لوحة التحكم المباشرة" : "Live dashboard data"}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </section>`;

function installIdentityHelper(input) {
  const start = input.indexOf('function getTaraIdentity(isRTL: boolean)');
  if (start !== -1) {
    const end = input.indexOf('function textLines(value: unknown)', start);
    if (end === -1) fail('existing Tara identity helper end marker not found');
    return input.slice(0, start) + identityHelper + '\n' + input.slice(end);
  }
  const anchor = input.indexOf('function textLines(value: unknown)');
  if (anchor === -1) fail('textLines helper anchor not found');
  return input.slice(0, anchor) + identityHelper + '\n' + input.slice(anchor);
}

function installBindings(input) {
  const countsLine = '    const counts: any = dashboardQ.data?.counts || {};\n';
  if (!input.includes(countsLine)) fail('dashboard counts binding not found');

  if (!input.includes('const taraIdentity = getTaraIdentity(isRTL);')) {
    input = replaceOnce(input, countsLine, countsLine + '    const taraIdentity = getTaraIdentity(isRTL);\n', 'Tara identity binding');
  }
  if (!input.includes('const metricItems = [')) {
    const identityLine = '    const taraIdentity = getTaraIdentity(isRTL);\n';
    input = replaceOnce(input, identityLine, identityLine + metricsBinding + '\n', 'metric bindings');
  }
  return input;
}

function replaceHeroMetrics(input) {
  if (input.includes(`{/* ${PATCH_MARKER} */}`)) return input;

  const tabsMarker = '      <Tabs defaultValue={initialTab} className="space-y-4">';
  const end = input.indexOf(tabsMarker);
  if (end === -1) fail('top-level Tara tabs marker not found');

  const startMarkers = [
    '      <section className="relative overflow-hidden',
    '      <div className="flex flex-col gap-4 rounded-2xl border bg-gradient-to-br',
  ];
  let start = -1;
  for (const marker of startMarkers) {
    start = input.lastIndexOf(marker, end);
    if (start !== -1) break;
  }
  if (start === -1) fail('Tara hero start marker not found');
  return input.slice(0, start) + heroAndMetrics + '\n\n' + input.slice(end);
}

function restyleTabs(input) {
  const tabsMarker = '      <Tabs defaultValue={initialTab} className="space-y-4">';
  const tabsPos = input.indexOf(tabsMarker);
  if (tabsPos === -1) fail('top-level Tara tabs marker not found for restyle');
  const listStart = input.indexOf('        <TabsList className="', tabsPos);
  if (listStart === -1) fail('top-level TabsList not found');
  const close = input.indexOf('">', listStart);
  if (close === -1) fail('top-level TabsList class close not found');
  const replacement = '        <TabsList className="h-auto w-full flex-nowrap justify-start gap-0 overflow-x-auto rounded-2xl border border-border/70 bg-card px-3 py-0 shadow-sm [scrollbar-width:none] [&::-webkit-scrollbar]:hidden [&_[role=tab]]:h-12 [&_[role=tab]]:shrink-0 [&_[role=tab]]:rounded-none [&_[role=tab]]:border-b-2 [&_[role=tab]]:border-transparent [&_[role=tab]]:bg-transparent [&_[role=tab]]:px-4 [&_[role=tab]]:text-xs [&_[role=tab]]:font-semibold [&_[role=tab][data-state=active]]:border-primary [&_[role=tab][data-state=active]]:text-primary [&_[role=tab][data-state=active]]:shadow-none">';
  return input.slice(0, listStart) + replacement + input.slice(close + 2);
}

function ensureAvatar() {
  if (fs.existsSync(avatarTarget) && fs.statSync(avatarTarget).size > 4000) return;
  if (!fs.existsSync(fallbackAvatarB64)) fail(`fallback avatar payload missing: ${fallbackAvatarB64}`);
  const raw = fs.readFileSync(fallbackAvatarB64, 'utf8').trim();
  const buf = Buffer.from(raw, 'base64');
  if (buf.length < 4000 || buf[0] !== 0xff || buf[1] !== 0xd8) fail('fallback Tara avatar payload is invalid');
  fs.mkdirSync(path.dirname(avatarTarget), { recursive: true });
  fs.writeFileSync(avatarTarget, buf);
}

function isPatched(input) {
  return input.includes(PATCH_MARKER)
    && input.includes('AI Telesales & Lead Qualification Specialist')
    && input.includes('Customer Conversations')
    && input.includes('const metricItems = [')
    && input.includes('Live dashboard data')
    && input.includes('src={taraAvatar}')
    && input.includes('[&_[role=tab][data-state=active]]:border-primary');
}

if (mode === '--check') {
  if (!source.includes('function TaraAdminAgentPage')) fail('TaraAdminAgentPage not found');
  if (!source.includes('const counts: any = dashboardQ.data?.counts || {};')) fail('Tara dashboard counts binding not found');
  if (!source.includes('<Tabs defaultValue={initialTab} className="space-y-4">')) fail('Tara top-level tabs not found');
  if (!source.includes('import taraAvatar from "@/assets/ai-staff/tara-avatar.jpg";') && !source.includes('import CRMLayout from "@/components/CRMLayout";')) fail('Tara page import anchor not found');
  info(isPatched(source) ? 'already patched' : 'ready to apply Tara reference dashboard V3');
  process.exit(0);
}

if (mode === '--apply') {
  if (!source.includes('import taraAvatar from "@/assets/ai-staff/tara-avatar.jpg";')) {
    source = replaceOnce(
      source,
      'import CRMLayout from "@/components/CRMLayout";\n',
      'import CRMLayout from "@/components/CRMLayout";\nimport taraAvatar from "@/assets/ai-staff/tara-avatar.jpg";\n',
      'Tara avatar import',
    );
  }

  source = installIdentityHelper(source);
  source = installBindings(source);
  source = replaceHeroMetrics(source);
  source = restyleTabs(source);
  ensureAvatar();

  if (!isPatched(source)) fail('patch did not reach expected final source state');
  const output = usesCRLF ? source.replace(/\n/g, '\r\n') : source;
  fs.writeFileSync(target, output, 'utf8');
  info('Tara reference dashboard V3 applied');
  process.exit(0);
}

if (mode === '--verify') {
  if (!isPatched(source)) fail('expected Tara reference dashboard V3 markers are missing');
  if (!fs.existsSync(avatarTarget) || fs.statSync(avatarTarget).size < 4000) fail('Tara portrait asset missing or invalid');
  info('verification passed');
  process.exit(0);
}

fail(`unknown mode: ${mode}`);