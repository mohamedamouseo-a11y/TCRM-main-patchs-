#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

/**
 * TCRM — Tara Professional Identity V2.1 compatibility fix
 * Target: client/src/pages/TaraAgentPage.tsx
 * Compatible with Premium V1 where metricCards sits between counts and busy.
 * Adds: AI-generated real-person avatar, bilingual professional job title,
 * localized role summary, expertise tags, and profile-style hero treatment.
 * Scope: UX/UI only. No API/DB/permissions/routes/business logic changes.
 */

const mode = process.argv[2] ?? '--check';
const cwd = process.cwd();
const target = path.resolve(cwd, 'client/src/pages/TaraAgentPage.tsx');
const patchDir = path.dirname(fileURLToPath(import.meta.url));
const avatarB64Path = path.join(patchDir, 'tara-avatar-320.jpg.b64');
const avatarTarget = path.resolve(cwd, 'public/ai-staff/tara-avatar.jpg');

function fail(message, code = 1) {
  console.error(`[tara-identity-v2.1] ${message}`);
  process.exit(code);
}
function info(message) {
  console.log(`[tara-identity-v2.1] ${message}`);
}
function replaceOnce(input, before, after, label) {
  if (!input.includes(before)) fail(`expected block not found: ${label}`);
  return input.replace(before, after);
}
function insertAfter(input, anchor, insertion, label) {
  const index = input.indexOf(anchor);
  if (index === -1) fail(`expected anchor not found: ${label}`);
  const at = index + anchor.length;
  return input.slice(0, at) + insertion + input.slice(at);
}

if (!fs.existsSync(target)) fail(`target not found: ${target}`, 2);
const originalRaw = fs.readFileSync(target, 'utf8');
const usesCRLF = originalRaw.includes('\r\n');
let source = originalRaw.replace(/\r\n/g, '\n');

const identityHelper = `function getTaraIdentity(isRTL: boolean) {
    return isRTL
        ? {
            badge: "فريق الذكاء الاصطناعي",
            profileTag: "الملف الوظيفي",
            jobTitle: "أخصائي المبيعات الهاتفية وتأهيل العملاء المحتملين بالذكاء الاصطناعي",
            summary: "تتولى محادثات المبيعات الأولية، وتأهيل العملاء المحتملين، والمتابعات، وتجهيز الحالات للتسليم إلى فريق المبيعات.",
            focus: ["المبيعات الهاتفية", "تأهيل العملاء المحتملين", "المتابعات"],
            alt: "الصورة المهنية لتارا",
        }
        : {
            badge: "AI STAFF",
            profileTag: "Professional Profile",
            jobTitle: "AI Telesales & Lead Qualification Specialist",
            summary: "Handles first-response sales conversations, lead qualification, follow-ups, and sales handoff preparation.",
            focus: ["Telesales", "Lead Qualification", "Follow-ups"],
            alt: "Professional portrait of Tara",
        };
}
`;

function replaceHero(input) {
  const hero = `      <section className="relative overflow-hidden rounded-[30px] border border-primary/15 bg-[radial-gradient(circle_at_top_right,hsl(var(--primary)/0.12),transparent_35%),linear-gradient(135deg,hsl(var(--background)),hsl(var(--card)),hsl(var(--primary)/0.04))] p-5 shadow-[0_18px_60px_-30px_hsl(var(--primary)/0.45)] md:p-6">
        <div className="pointer-events-none absolute inset-y-0 end-0 w-44 bg-gradient-to-s from-primary/[0.04] via-primary/[0.02] to-transparent" />
        <div className="relative flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex min-w-0 items-start gap-4">
            <div className="relative h-[76px] w-[76px] shrink-0 overflow-hidden rounded-[22px] bg-muted ring-4 ring-primary/10 shadow-lg shadow-primary/15">
              <img src="/ai-staff/tara-avatar.jpg" alt={taraIdentity.alt} className="h-full w-full object-cover" />
              <span className={"absolute -bottom-1 -end-1 h-5 w-5 rounded-full border-[3px] border-card " + (settings.enabled ? "bg-emerald-500" : "bg-muted-foreground")} />
            </div>
            <div className="min-w-0">
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <span className="inline-flex items-center rounded-full border border-primary/15 bg-primary/5 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.18em] text-primary/80">{taraIdentity.badge}</span>
                <span className="inline-flex items-center rounded-full border border-border/70 bg-background/75 px-2.5 py-1 text-[11px] font-semibold text-muted-foreground">{taraIdentity.profileTag}</span>
              </div>
              <h1 className="truncate text-[30px] font-black tracking-[-0.04em] text-foreground md:text-[34px]">Tara</h1>
              <p className="mt-1 text-sm font-bold text-primary/90 md:text-base">{taraIdentity.jobTitle}</p>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">{taraIdentity.summary}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {taraIdentity.focus.map((item: string) => <span key={item} className="inline-flex items-center rounded-full border border-border/70 bg-background/85 px-3 py-1 text-xs font-semibold text-foreground shadow-sm">{item}</span>)}
              </div>
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-2 self-start lg:self-auto">
            <Badge variant="outline" className={"h-9 gap-2 rounded-full px-3.5 text-xs font-bold " + (settings.enabled ? "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/70 dark:bg-emerald-950/40 dark:text-emerald-300" : "border-border bg-muted/50 text-muted-foreground")}>
              <span className={"h-2 w-2 rounded-full " + (settings.enabled ? "bg-emerald-500 shadow-[0_0_0_4px_rgba(16,185,129,0.12)]" : "bg-muted-foreground/60")} />
              {settings.enabled ? taraText("مفعلة") : taraText("متوقفة")}
            </Badge>
            <Button variant="outline" className="h-10 rounded-xl bg-background/80 px-4 shadow-sm backdrop-blur" onClick={() => refresh()}><RefreshCw className="ms-2 h-4 w-4"/>{taraText("تحديث")}</Button>
          </div>
        </div>
      </section>`;

  const startMarkers = [
    '      <section className="relative overflow-hidden',
    '      <div className="flex flex-col gap-4 rounded-2xl border bg-gradient-to-br',
  ];
  const endMarkers = [
    '      <section className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">',
    '      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">',
  ];

  let start = -1;
  for (const marker of startMarkers) {
    start = input.indexOf(marker);
    if (start !== -1) break;
  }
  if (start === -1) fail('Tara hero start marker not found');

  let end = -1;
  for (const marker of endMarkers) {
    end = input.indexOf(marker, start);
    if (end !== -1) break;
  }
  if (end === -1) fail('Tara metrics marker not found');

  return input.slice(0, start) + hero + '\n\n' + input.slice(end);
}

function isPatched(input) {
  return input.includes('function getTaraIdentity(isRTL: boolean)')
    && input.includes('AI Telesales & Lead Qualification Specialist')
    && input.includes('const taraIdentity = getTaraIdentity(isRTL);')
    && input.includes('src="/ai-staff/tara-avatar.jpg"');
}

if (mode === '--check') {
  if (!source.includes('function TaraAdminAgentPage')) fail('TaraAdminAgentPage not found');
  if (!source.includes('const counts: any = dashboardQ.data?.counts || {};')) fail('Tara dashboard counts block not found');
  if (!source.includes('const emptyFollowup =')) fail('Tara seed model block not found');
  if (!fs.existsSync(avatarB64Path)) fail(`avatar payload not found: ${avatarB64Path}`);
  info(isPatched(source) ? 'already patched' : 'ready to apply');
  process.exit(0);
}

if (mode === '--apply') {
  if (!fs.existsSync(avatarB64Path)) fail(`avatar payload not found: ${avatarB64Path}`);

  if (!source.includes('function getTaraIdentity(isRTL: boolean)')) {
    const anchor = 'const emptyFollowup = { campaignSettingId: null, enabled: true, attemptNumber: 1, delayMinutes: 60, messageTemplate: "", stopOnReply: true, businessHoursOnly: true };\n';
    source = replaceOnce(source, anchor, anchor + identityHelper, 'identity helper insertion');
  }

  if (!source.includes('const taraIdentity = getTaraIdentity(isRTL);')) {
    const countsAnchor = '    const counts: any = dashboardQ.data?.counts || {};';
    source = insertAfter(source, countsAnchor, '\n    const taraIdentity = getTaraIdentity(isRTL);', 'identity binding after counts');
  }

  source = replaceHero(source);
  if (!isPatched(source)) fail('patch did not reach expected source state');

  fs.mkdirSync(path.dirname(avatarTarget), { recursive: true });
  const avatarBase64 = fs.readFileSync(avatarB64Path, 'utf8').trim();
  fs.writeFileSync(avatarTarget, Buffer.from(avatarBase64, 'base64'));

  const output = usesCRLF ? source.replace(/\n/g, '\r\n') : source;
  fs.writeFileSync(target, output, 'utf8');
  info('applied Tara identity V2.1 and installed avatar asset');
  process.exit(0);
}

if (mode === '--verify') {
  if (!isPatched(source)) fail('expected Tara identity source markers are missing');
  if (!fs.existsSync(avatarTarget)) fail(`avatar was not installed: ${avatarTarget}`);
  if (fs.statSync(avatarTarget).size < 10000) fail('avatar file looks invalid or too small');
  info('verification passed');
  process.exit(0);
}

fail(`unknown mode: ${mode}`);
