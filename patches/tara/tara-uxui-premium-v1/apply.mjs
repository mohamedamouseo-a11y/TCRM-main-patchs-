#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

/**
 * TCRM — Tara UX/UI Premium V1
 * Source repo: mohamedamouseo-a11y/TCRM-MAIN-Tamiyouz-CRM- (main)
 * Target: client/src/pages/TaraAgentPage.tsx
 * Usage: node apply.mjs --check | --apply | --verify
 * Scope: visual/UX only. No API, DB, routing, permissions, or Tara behavior changes.
 */

const mode = process.argv[2] ?? '--check';
const target = path.resolve(process.cwd(), 'client/src/pages/TaraAgentPage.tsx');
if (!fs.existsSync(target)) {
  console.error(`[tara-uxui-v1] target not found: ${target}`);
  process.exit(2);
}
const originalRaw = fs.readFileSync(target, 'utf8');
const usesCRLF = originalRaw.includes('\r\n');
let source = originalRaw.replace(/\r\n/g, '\n');
const replacements = [
  {
    label: "metric-model",
    before: "    const counts: any = dashboardQ.data?.counts || {};\n    const busy = dashboardQ.isLoading || settingsQ.isLoading || campaignsQ.isLoading;",
    after: "    const counts: any = dashboardQ.data?.counts || {};\n    const metricCards = [\n        { label: taraText(\"\\u0627\\u0644\\u062D\\u0645\\u0644\\u0627\\u062A\"), value: counts.campaigns, Icon: Brain, iconTone: \"bg-violet-500/10 text-violet-600 dark:text-violet-300\", glowTone: \"bg-violet-500\", featured: false },\n        { label: taraText(\"\\u0627\\u0644\\u0645\\u062D\\u0627\\u062F\\u062B\\u0627\\u062A\"), value: counts.conversations, Icon: MessageSquareText, iconTone: \"bg-blue-500/10 text-blue-600 dark:text-blue-300\", glowTone: \"bg-blue-500\", featured: false },\n        { label: taraText(\"\\u062A\\u0627\\u0631\\u0627 \\u0646\\u0634\\u0637\\u0629\"), value: counts.active, Icon: Activity, iconTone: \"bg-emerald-500/10 text-emerald-600 dark:text-emerald-300\", glowTone: \"bg-emerald-500\", featured: false },\n        { label: taraText(\"\\u062A\\u062D\\u0648\\u064A\\u0644 \\u0628\\u0634\\u0631\\u064A\"), value: counts.handoff, Icon: Users, iconTone: \"bg-amber-500/10 text-amber-600 dark:text-amber-300\", glowTone: \"bg-amber-500\", featured: false },\n        { label: taraText(\"\\u0639\\u0645\\u0644\\u064A\\u0627\\u062A AI\"), value: counts.runs, Icon: Bot, iconTone: \"bg-primary/10 text-primary\", glowTone: \"bg-primary\", featured: true },\n        { label: taraText(\"\\u0623\\u062E\\u0637\\u0627\\u0621\"), value: counts.failedRuns, Icon: ShieldCheck, iconTone: \"bg-rose-500/10 text-rose-600 dark:text-rose-300\", glowTone: \"bg-rose-500\", featured: false },\n    ];\n    const busy = dashboardQ.isLoading || settingsQ.isLoading || campaignsQ.isLoading;",
  },
  {
    label: "hero-and-metrics",
    before: "    <div className=\"mx-auto max-w-[1600px] space-y-5 p-4 md:p-6 xl:p-8\" dir={isRTL ? \"rtl\" : \"ltr\"}>\n      <div className=\"flex flex-col gap-4 rounded-2xl border bg-gradient-to-br from-primary/10 via-card to-card p-5 shadow-sm md:flex-row md:items-center md:justify-between\">\n        <div className=\"flex items-center gap-4\"><div className=\"grid h-14 w-14 place-items-center rounded-2xl bg-primary text-primary-foreground shadow\"><Bot className=\"h-7 w-7\"/></div><div><h1 className=\"text-2xl font-black\">{taraText(\"\\u062A\\u0627\\u0631\\u0627 \\u2014 CRM AI Agent\")}</h1><p className=\"mt-1 text-sm text-muted-foreground\">{taraText(\"\\u0648\\u0643\\u064A\\u0644 \\u0645\\u0633\\u062A\\u0642\\u0644 \\u0639\\u0627\\u0645\\u061B \\u0633\\u0644\\u0648\\u0643\\u0647 \\u0648\\u0628\\u064A\\u0627\\u0646\\u0627\\u062A\\u0647 \\u062A\\u062A\\u062D\\u062F\\u062F \\u0645\\u0646 \\u062A\\u0639\\u0644\\u064A\\u0645\\u0627\\u062A \\u0627\\u0644\\u0634\\u0631\\u0643\\u0629 \\u0648\\u0627\\u0644\\u062D\\u0645\\u0644\\u0629.\")}</p></div></div>\n        <div className=\"flex items-center gap-2\"><Badge variant={settings.enabled ? \"default\" : \"secondary\"}>{settings.enabled ? taraText(\"\\u0645\\u0641\\u0639\\u0644\\u0629\") : taraText(\"\\u0645\\u062A\\u0648\\u0642\\u0641\\u0629\")}</Badge><Button variant=\"outline\" onClick={() => refresh()}><RefreshCw className=\"ms-2 h-4 w-4\"/>{taraText(\"\\u062A\\u062D\\u062F\\u064A\\u062B\")}</Button></div>\n      </div>\n\n      <div className=\"grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6\">\n        {[[taraText(\"\\u0627\\u0644\\u062D\\u0645\\u0644\\u0627\\u062A\"), counts.campaigns, Brain], [taraText(\"\\u0627\\u0644\\u0645\\u062D\\u0627\\u062F\\u062B\\u0627\\u062A\"), counts.conversations, MessageSquareText], [taraText(\"\\u062A\\u0627\\u0631\\u0627 \\u0646\\u0634\\u0637\\u0629\"), counts.active, Activity], [taraText(\"\\u062A\\u062D\\u0648\\u064A\\u0644 \\u0628\\u0634\\u0631\\u064A\"), counts.handoff, Users], [taraText(\"\\u0639\\u0645\\u0644\\u064A\\u0627\\u062A AI\"), counts.runs, Bot], [taraText(\"\\u0623\\u062E\\u0637\\u0627\\u0621\"), counts.failedRuns, ShieldCheck]].map(([label, value, Icon]: any) => <Card key={label} className=\"border-border/70 shadow-sm transition-shadow hover:shadow-md\"><CardContent className=\"flex min-h-[112px] flex-col justify-between p-4\"><div className=\"grid h-9 w-9 place-items-center rounded-xl bg-primary/10 text-primary\"><Icon className=\"h-4 w-4\"/></div><div><p className=\"text-2xl font-black tracking-tight\">{value || 0}</p><p className=\"mt-0.5 text-xs font-medium text-muted-foreground\">{label}</p></div></CardContent></Card>)}\n      </div>",
    after: "    <div className=\"mx-auto max-w-[1660px] space-y-5 p-4 md:p-6 xl:p-8\" dir={isRTL ? \"rtl\" : \"ltr\"}>\n      <section className=\"relative overflow-hidden rounded-[28px] border border-primary/15 bg-gradient-to-br from-card via-card to-primary/[0.06] p-5 shadow-[0_16px_50px_-28px_hsl(var(--primary)/0.45)] md:p-6\">\n        <div className=\"pointer-events-none absolute -end-20 -top-24 h-64 w-64 rounded-full bg-primary/10 blur-3xl\"/>\n        <div className=\"relative flex flex-col gap-5 md:flex-row md:items-center md:justify-between\">\n          <div className=\"flex min-w-0 items-center gap-4\">\n            <div className=\"relative grid h-16 w-16 shrink-0 place-items-center rounded-[20px] bg-gradient-to-br from-primary to-primary/80 text-primary-foreground shadow-lg shadow-primary/20 ring-4 ring-primary/10\">\n              <Bot className=\"h-8 w-8\"/>\n              <span className={`absolute -end-1 -bottom-1 h-4 w-4 rounded-full border-[3px] border-card ${settings.enabled ? \"bg-emerald-500\" : \"bg-muted-foreground\"}`}/>\n            </div>\n            <div className=\"min-w-0\">\n              <p className=\"mb-1 text-[11px] font-bold uppercase tracking-[0.18em] text-primary/80\">{isRTL ? \"فريق الذكاء الاصطناعي\" : \"AI Staff\"}</p>\n              <h1 className=\"truncate text-2xl font-black tracking-tight md:text-[28px]\">{taraText(\"\\u062A\\u0627\\u0631\\u0627 \\u2014 CRM AI Agent\")}</h1>\n              <p className=\"mt-1.5 max-w-3xl text-sm leading-6 text-muted-foreground\">{taraText(\"\\u0648\\u0643\\u064A\\u0644 \\u0645\\u0633\\u062A\\u0642\\u0644 \\u0639\\u0627\\u0645\\u061B \\u0633\\u0644\\u0648\\u0643\\u0647 \\u0648\\u0628\\u064A\\u0627\\u0646\\u0627\\u062A\\u0647 \\u062A\\u062A\\u062D\\u062F\\u062F \\u0645\\u0646 \\u062A\\u0639\\u0644\\u064A\\u0645\\u0627\\u062A \\u0627\\u0644\\u0634\\u0631\\u0643\\u0629 \\u0648\\u0627\\u0644\\u062D\\u0645\\u0644\\u0629.\")}</p>\n            </div>\n          </div>\n          <div className=\"flex shrink-0 items-center gap-2 self-start md:self-auto\">\n            <Badge variant=\"outline\" className={`h-9 gap-2 rounded-full px-3.5 text-xs font-bold ${settings.enabled ? \"border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/70 dark:bg-emerald-950/40 dark:text-emerald-300\" : \"border-border bg-muted/50 text-muted-foreground\"}`}>\n              <span className={`h-2 w-2 rounded-full ${settings.enabled ? \"bg-emerald-500 shadow-[0_0_0_4px_rgba(16,185,129,0.12)]\" : \"bg-muted-foreground/60\"}`}/>\n              {settings.enabled ? taraText(\"\\u0645\\u0641\\u0639\\u0644\\u0629\") : taraText(\"\\u0645\\u062A\\u0648\\u0642\\u0641\\u0629\")}\n            </Badge>\n            <Button variant=\"outline\" className=\"h-10 rounded-xl bg-background/80 px-4 shadow-sm backdrop-blur\" onClick={() => refresh()}><RefreshCw className=\"ms-2 h-4 w-4\"/>{taraText(\"\\u062A\\u062D\\u062F\\u064A\\u062B\")}</Button>\n          </div>\n        </div>\n      </section>\n\n      <section className=\"grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6\">\n        {metricCards.map(({ label, value, Icon, iconTone, glowTone, featured }: any) => <Card key={label} className={`group relative overflow-hidden rounded-2xl border-border/70 bg-card shadow-[0_10px_30px_-24px_rgba(15,23,42,0.55)] transition-all duration-200 hover:-translate-y-0.5 hover:border-primary/25 hover:shadow-md ${featured ? \"ring-1 ring-primary/25\" : \"\"}`}>\n          <div className={`pointer-events-none absolute -end-8 -top-8 h-24 w-24 rounded-full opacity-[0.08] blur-2xl ${glowTone}`}/>\n          <CardContent className=\"relative flex min-h-[132px] flex-col justify-between p-4 md:p-5\">\n            <div className={`grid h-10 w-10 place-items-center rounded-[14px] ${iconTone}`}><Icon className=\"h-[18px] w-[18px]\"/></div>\n            <div className=\"mt-5\">\n              <p className=\"text-[30px] font-black leading-none tracking-[-0.04em] text-foreground\">{value || 0}</p>\n              <p className=\"mt-2 text-xs font-semibold text-muted-foreground\">{label}</p>\n            </div>\n          </CardContent>\n        </Card>)}\n      </section>",
  },
  {
    label: "tabs-surface",
    before: "        <TabsList className=\"h-auto w-full flex-nowrap justify-start gap-1 overflow-x-auto rounded-2xl bg-muted/60 p-1.5 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden [&_[role=tab]]:shrink-0\">",
    after: "        <TabsList className=\"h-auto w-full flex-nowrap justify-start gap-1 overflow-x-auto rounded-2xl border border-border/60 bg-card/95 p-1.5 shadow-sm backdrop-blur [scrollbar-width:none] [&::-webkit-scrollbar]:hidden [&_[role=tab]]:h-9 [&_[role=tab]]:shrink-0 [&_[role=tab]]:rounded-xl [&_[role=tab]]:px-3.5 [&_[role=tab]]:text-xs [&_[role=tab]]:font-semibold [&_[data-state=active]]:bg-primary/10 [&_[data-state=active]]:text-primary [&_[data-state=active]]:shadow-none\">",
  },
  {
    label: "settings-card",
    before: "        <TabsContent value=\"settings\"><Card className=\"overflow-hidden border-border/70 shadow-sm\"><CardHeader className=\"border-b bg-muted/20\"><CardTitle>{taraText(\"\\u0627\\u0644\\u0625\\u0639\\u062F\\u0627\\u062F\\u0627\\u062A \\u0627\\u0644\\u0639\\u0627\\u0645\\u0629 \\u0627\\u0644\\u0645\\u0633\\u062A\\u0642\\u0644\\u0629\")}</CardTitle></CardHeader><CardContent className=\"grid gap-5 p-5 md:grid-cols-2 md:p-6\">\n          <div className=\"flex items-center justify-between rounded-2xl border p-4 md:col-span-2\"><div><p className=\"font-bold\">{taraText(\"\\u062A\\u0634\\u063A\\u064A\\u0644 \\u062A\\u0627\\u0631\\u0627\")}</p><p className=\"text-xs text-muted-foreground\">{taraText(\"\\u062A\\u0628\\u062F\\u0623 \\u0627\\u0644\\u0631\\u0633\\u0627\\u0626\\u0644 \\u0627\\u0644\\u062C\\u062F\\u064A\\u062F\\u0629 \\u0641\\u0642\\u0637 \\u0628\\u0639\\u062F \\u0627\\u0644\\u062A\\u0641\\u0639\\u064A\\u0644.\")}</p></div><Switch checked={Boolean(settings.enabled)} onCheckedChange={v => setSettings({ ...settings, enabled: v })}/></div>",
    after: "        <TabsContent value=\"settings\"><Card className=\"overflow-hidden rounded-[24px] border-border/70 shadow-[0_16px_48px_-34px_rgba(15,23,42,0.55)]\"><CardHeader className=\"flex-row items-center justify-between gap-4 border-b bg-gradient-to-r from-muted/35 via-background to-primary/[0.04] px-5 py-5 md:px-7\"><div><p className=\"mb-1 text-[11px] font-bold uppercase tracking-[0.16em] text-primary/80\">{isRTL ? \"مركز تحكم تارا\" : \"Tara Control Center\"}</p><CardTitle className=\"text-lg md:text-xl\">{taraText(\"\\u0627\\u0644\\u0625\\u0639\\u062F\\u0627\\u062F\\u0627\\u062A \\u0627\\u0644\\u0639\\u0627\\u0645\\u0629 \\u0627\\u0644\\u0645\\u0633\\u062A\\u0642\\u0644\\u0629\")}</CardTitle></div><div className={`hidden h-2.5 w-2.5 rounded-full sm:block ${settings.enabled ? \"bg-emerald-500 shadow-[0_0_0_5px_rgba(16,185,129,0.10)]\" : \"bg-muted-foreground/50\"}`}/></CardHeader><CardContent className=\"grid gap-6 p-5 md:grid-cols-2 md:p-7 [&_input]:h-11 [&_input]:rounded-xl [&_label]:text-[13px] [&_label]:font-semibold [&_textarea]:rounded-xl\">\n          <div className={`flex items-center justify-between rounded-2xl border p-4 md:col-span-2 ${settings.enabled ? \"border-emerald-200/80 bg-emerald-50/60 dark:border-emerald-900/60 dark:bg-emerald-950/20\" : \"border-border bg-muted/25\"}`}><div className=\"flex items-start gap-3\"><span className={`mt-1 h-2.5 w-2.5 shrink-0 rounded-full ${settings.enabled ? \"bg-emerald-500\" : \"bg-muted-foreground/50\"}`}/><div><p className=\"font-bold\">{taraText(\"\\u062A\\u0634\\u063A\\u064A\\u0644 \\u062A\\u0627\\u0631\\u0627\")}</p><p className=\"mt-1 text-xs leading-5 text-muted-foreground\">{taraText(\"\\u062A\\u0628\\u062F\\u0623 \\u0627\\u0644\\u0631\\u0633\\u0627\\u0626\\u0644 \\u0627\\u0644\\u062C\\u062F\\u064A\\u062F\\u0629 \\u0641\\u0642\\u0637 \\u0628\\u0639\\u062F \\u0627\\u0644\\u062A\\u0641\\u0639\\u064A\\u0644.\")}</p></div></div><Switch checked={Boolean(settings.enabled)} onCheckedChange={v => setSettings({ ...settings, enabled: v })}/></div>",
  },
  {
    label: "sticky-actions",
    before: "          <div className=\"sticky bottom-3 z-20 flex flex-wrap gap-2 rounded-2xl border bg-background/95 p-3 shadow-lg backdrop-blur md:col-span-2\"><Button onClick={() => saveSettingsM.mutate(settingsPayload())} disabled={saveSettingsM.isPending}>{saveSettingsM.isPending && <Loader2 className=\"ms-2 h-4 w-4 animate-spin\"/>}{taraText(\"\\u062D\\u0641\\u0638 \\u0627\\u0644\\u0625\\u0639\\u062F\\u0627\\u062F\\u0627\\u062A\")}</Button><Button variant=\"outline\" onClick={() => testProviderM.mutate()} disabled={testProviderM.isPending}>{taraText(\"\\u0627\\u062E\\u062A\\u0628\\u0627\\u0631 \\u0627\\u0644\\u0627\\u062A\\u0635\\u0627\\u0644\")}</Button><Button variant=\"secondary\" onClick={() => processQueueM.mutate({ limit: 10 })}>{taraText(\"\\u0645\\u0639\\u0627\\u0644\\u062C\\u0629 Queue \\u0627\\u0644\\u0622\\u0646\")}</Button></div>",
    after: "          <div className=\"sticky bottom-3 z-20 flex flex-wrap items-center gap-2 rounded-2xl border border-border/70 bg-background/90 p-3 shadow-[0_16px_40px_-24px_rgba(15,23,42,0.5)] backdrop-blur-xl md:col-span-2\"><Button className=\"rounded-xl px-5 shadow-sm shadow-primary/15\" onClick={() => saveSettingsM.mutate(settingsPayload())} disabled={saveSettingsM.isPending}>{saveSettingsM.isPending && <Loader2 className=\"ms-2 h-4 w-4 animate-spin\"/>}{taraText(\"\\u062D\\u0641\\u0638 \\u0627\\u0644\\u0625\\u0639\\u062F\\u0627\\u062F\\u0627\\u062A\")}</Button><Button className=\"rounded-xl\" variant=\"outline\" onClick={() => testProviderM.mutate()} disabled={testProviderM.isPending}>{taraText(\"\\u0627\\u062E\\u062A\\u0628\\u0627\\u0631 \\u0627\\u0644\\u0627\\u062A\\u0635\\u0627\\u0644\")}</Button><Button className=\"rounded-xl\" variant=\"secondary\" onClick={() => processQueueM.mutate({ limit: 10 })}>{taraText(\"\\u0645\\u0639\\u0627\\u0644\\u062C\\u0629 Queue \\u0627\\u0644\\u0622\\u0646\")}</Button><p className=\"ms-auto hidden text-xs text-muted-foreground lg:block\">{isRTL ? \"احفظ التعديلات لتطبيقها على تارا\" : \"Save changes to apply them to Tara\"}</p></div>",
  }
];

function inspect(input) {
  return replacements.map(({ label, before, after }) => ({
    label,
    oldCount: input.split(before).length - 1,
    newCount: input.split(after).length - 1,
  }));
}

if (mode === '--check') {
  const status = inspect(source);
  let ok = true;
  for (const item of status) {
    const ready = item.oldCount === 1 || item.newCount === 1;
    ok &&= ready;
    console.log(`[tara-uxui-v1] ${item.label}: old=${item.oldCount} new=${item.newCount} ${ready ? 'OK' : 'MISMATCH'}`);
  }
  process.exit(ok ? 0 : 3);
}
if (mode === '--verify') {
  const status = inspect(source);
  const ok = status.every(item => item.oldCount === 0 && item.newCount === 1);
  for (const item of status) console.log(`[tara-uxui-v1] ${item.label}: old=${item.oldCount} new=${item.newCount}`);
  console.log(ok ? '[tara-uxui-v1] verification passed' : '[tara-uxui-v1] verification failed');
  process.exit(ok ? 0 : 4);
}
if (mode !== '--apply') {
  console.error('Usage: node apply.mjs --check | --apply | --verify');
  process.exit(1);
}
for (const { label, before, after } of replacements) {
  const oldCount = source.split(before).length - 1;
  const newCount = source.split(after).length - 1;
  if (newCount === 1 && oldCount === 0) {
    console.log(`[tara-uxui-v1] ${label}: already applied`);
    continue;
  }
  if (oldCount !== 1) {
    console.error(`[tara-uxui-v1] ${label}: expected exactly one source match, found ${oldCount}. Aborting without writing.`);
    process.exit(5);
  }
  source = source.replace(before, after);
  console.log(`[tara-uxui-v1] ${label}: applied`);
}
const output = usesCRLF ? source.replace(/\n/g, '\r\n') : source;
fs.writeFileSync(target, output, 'utf8');
console.log(`[tara-uxui-v1] updated ${target}`);
console.log('[tara-uxui-v1] next: npm run check && node <patch-path>/apply.mjs --verify');
