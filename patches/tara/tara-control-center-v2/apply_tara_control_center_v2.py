#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

TARGET = Path('client/src/pages/TaraAgentPage.tsx')
BASE_BLOB = '96e08eb01adfb6e7428aa585a0e2712e1fb20331'
MARKER = 'data-tara-workspace="control-center-v2"'

OLD_NAV = r'''
        <TabsList className="h-auto w-full flex-nowrap justify-start gap-0 overflow-x-auto rounded-2xl border border-border/70 bg-card px-3 py-0 shadow-sm [scrollbar-width:none] [&::-webkit-scrollbar]:hidden [&_[role=tab]]:h-12 [&_[role=tab]]:shrink-0 [&_[role=tab]]:rounded-none [&_[role=tab]]:border-b-2 [&_[role=tab]]:border-transparent [&_[role=tab]]:bg-transparent [&_[role=tab]]:px-4 [&_[role=tab]]:text-xs [&_[role=tab]]:font-semibold [&_[role=tab][data-state=active]]:border-primary [&_[role=tab][data-state=active]]:text-primary [&_[role=tab][data-state=active]]:shadow-none">
          <TabsTrigger value="settings"><Settings2 className="ms-2 h-4 w-4"/>{taraText("\u0627\u0644\u0625\u0639\u062F\u0627\u062F\u0627\u062A")}</TabsTrigger>
          <TabsTrigger value="providers"><KeyRound className="ms-2 h-4 w-4"/>{taraText("\u0645\u0641\u0627\u062A\u064A\u062D \u0627\u0644\u0630\u0643\u0627\u0621")}</TabsTrigger>
          <TabsTrigger value="voice"><Volume2 className="ms-2 h-4 w-4"/>{taraText("\u0627\u0644\u0635\u0648\u062A \u0648ElevenLabs")}</TabsTrigger>
          {canManageModerators && <TabsTrigger value="moderators"><ShieldCheck className="ms-2 h-4 w-4"/>{taraText("\u0627\u0644\u0645\u0648\u062F\u0631\u064A\u062A\u0648\u0631")}</TabsTrigger>}
          <TabsTrigger value="campaigns"><Brain className="ms-2 h-4 w-4"/>{taraText("\u0627\u0644\u062D\u0645\u0644\u0627\u062A")}</TabsTrigger>
          <TabsTrigger value="qualification"><FileQuestion className="ms-2 h-4 w-4"/>{taraText("\u0627\u0644\u062A\u0623\u0647\u064A\u0644")}</TabsTrigger>
          <TabsTrigger value="knowledge"><Database className="ms-2 h-4 w-4"/>{taraText("\u0627\u0644\u0645\u0639\u0631\u0641\u0629")}</TabsTrigger>
          <TabsTrigger value="followups"><RefreshCw className="ms-2 h-4 w-4"/>{taraText("\u0627\u0644\u0645\u062A\u0627\u0628\u0639\u0627\u062A")}</TabsTrigger>
          <TabsTrigger value="social"><MessageSquareText className="ms-2 h-4 w-4"/>{taraText("\u0627\u0644\u0642\u0646\u0648\u0627\u062A \u0627\u0644\u0627\u062C\u062A\u0645\u0627\u0639\u064A\u0629")}</TabsTrigger>
          <TabsTrigger value="test"><Send className="ms-2 h-4 w-4"/>{taraText("\u0627\u0644\u0627\u062E\u062A\u0628\u0627\u0631")}</TabsTrigger>
          <TabsTrigger value="logs"><Activity className="ms-2 h-4 w-4"/>{taraText("\u0627\u0644\u0633\u062C\u0644")}</TabsTrigger>
        </TabsList>
'''

NEW_NAV = r'''
        <div data-tara-workspace="control-center-v2" className="overflow-x-auto rounded-2xl border border-border/70 bg-card p-2 shadow-sm [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          <TabsList className="h-auto min-w-max justify-start gap-2 rounded-none bg-transparent p-0">
            <div data-tara-nav-group="profile-runtime" className="rounded-xl border border-border/60 bg-muted/20 p-1.5">
              <p className="px-2 pb-1 text-[9px] font-black uppercase tracking-[0.16em] text-muted-foreground">{isRTL ? "الهوية والتشغيل" : "Profile & Runtime"}</p>
              <div className="flex items-center gap-1">
                <TabsTrigger value="settings" className="h-9 rounded-lg px-3 text-xs data-[state=active]:bg-background data-[state=active]:shadow-sm"><Settings2 className="ms-1.5 h-3.5 w-3.5"/>{taraText("\u0627\u0644\u0625\u0639\u062F\u0627\u062F\u0627\u062A")}</TabsTrigger>
                <TabsTrigger value="providers" className="h-9 rounded-lg px-3 text-xs data-[state=active]:bg-background data-[state=active]:shadow-sm"><KeyRound className="ms-1.5 h-3.5 w-3.5"/>{taraText("\u0645\u0641\u0627\u062A\u064A\u062D \u0627\u0644\u0630\u0643\u0627\u0621")}</TabsTrigger>
                <TabsTrigger value="voice" className="h-9 rounded-lg px-3 text-xs data-[state=active]:bg-background data-[state=active]:shadow-sm"><Volume2 className="ms-1.5 h-3.5 w-3.5"/>{taraText("\u0627\u0644\u0635\u0648\u062A \u0648ElevenLabs")}</TabsTrigger>
                {canManageModerators && <TabsTrigger value="moderators" className="h-9 rounded-lg px-3 text-xs data-[state=active]:bg-background data-[state=active]:shadow-sm"><ShieldCheck className="ms-1.5 h-3.5 w-3.5"/>{taraText("\u0627\u0644\u0645\u0648\u062F\u0631\u064A\u062A\u0648\u0631")}</TabsTrigger>}
              </div>
            </div>
            <div data-tara-nav-group="sales-operations" className="rounded-xl border border-border/60 bg-muted/20 p-1.5">
              <p className="px-2 pb-1 text-[9px] font-black uppercase tracking-[0.16em] text-muted-foreground">{isRTL ? "عمليات المبيعات" : "Sales Operations"}</p>
              <div className="flex items-center gap-1">
                <TabsTrigger value="campaigns" className="h-9 rounded-lg px-3 text-xs data-[state=active]:bg-background data-[state=active]:shadow-sm"><Brain className="ms-1.5 h-3.5 w-3.5"/>{taraText("\u0627\u0644\u062D\u0645\u0644\u0627\u062A")}</TabsTrigger>
                <TabsTrigger value="qualification" className="h-9 rounded-lg px-3 text-xs data-[state=active]:bg-background data-[state=active]:shadow-sm"><FileQuestion className="ms-1.5 h-3.5 w-3.5"/>{taraText("\u0627\u0644\u062A\u0623\u0647\u064A\u0644")}</TabsTrigger>
                <TabsTrigger value="followups" className="h-9 rounded-lg px-3 text-xs data-[state=active]:bg-background data-[state=active]:shadow-sm"><RefreshCw className="ms-1.5 h-3.5 w-3.5"/>{taraText("\u0627\u0644\u0645\u062A\u0627\u0628\u0639\u0627\u062A")}</TabsTrigger>
                <TabsTrigger value="social" className="h-9 rounded-lg px-3 text-xs data-[state=active]:bg-background data-[state=active]:shadow-sm"><MessageSquareText className="ms-1.5 h-3.5 w-3.5"/>{taraText("\u0627\u0644\u0642\u0646\u0648\u0627\u062A \u0627\u0644\u0627\u062C\u062A\u0645\u0627\u0639\u064A\u0629")}</TabsTrigger>
              </div>
            </div>
            <div data-tara-nav-group="knowledge" className="rounded-xl border border-border/60 bg-muted/20 p-1.5">
              <p className="px-2 pb-1 text-[9px] font-black uppercase tracking-[0.16em] text-muted-foreground">{isRTL ? "المعرفة" : "Knowledge"}</p>
              <div className="flex items-center gap-1">
                <TabsTrigger value="knowledge" className="h-9 rounded-lg px-3 text-xs data-[state=active]:bg-background data-[state=active]:shadow-sm"><Database className="ms-1.5 h-3.5 w-3.5"/>{taraText("\u0627\u0644\u0645\u0639\u0631\u0641\u0629")}</TabsTrigger>
              </div>
            </div>
            <div data-tara-nav-group="diagnostics" className="rounded-xl border border-border/60 bg-muted/20 p-1.5">
              <p className="px-2 pb-1 text-[9px] font-black uppercase tracking-[0.16em] text-muted-foreground">{isRTL ? "التشخيص" : "Diagnostics"}</p>
              <div className="flex items-center gap-1">
                <TabsTrigger value="test" className="h-9 rounded-lg px-3 text-xs data-[state=active]:bg-background data-[state=active]:shadow-sm"><Send className="ms-1.5 h-3.5 w-3.5"/>{taraText("\u0627\u0644\u0627\u062E\u062A\u0628\u0627\u0631")}</TabsTrigger>
                <TabsTrigger value="logs" className="h-9 rounded-lg px-3 text-xs data-[state=active]:bg-background data-[state=active]:shadow-sm"><Activity className="ms-1.5 h-3.5 w-3.5"/>{taraText("\u0627\u0644\u0633\u062C\u0644")}</TabsTrigger>
              </div>
            </div>
          </TabsList>
        </div>
'''

CARD_CONTENT_OLD = '<CardContent className="grid gap-6 p-5 md:grid-cols-2 md:p-7 [&_input]:h-11 [&_input]:rounded-xl [&_label]:text-[13px] [&_label]:font-semibold [&_textarea]:rounded-xl">'
CARD_CONTENT_NEW = '''<CardContent className="grid gap-4 p-5 md:grid-cols-2 md:p-7 [&_input]:h-11 [&_input]:rounded-xl [&_label]:text-[13px] [&_label]:font-semibold [&_textarea]:rounded-xl">
          <details open data-tara-settings-section="profile-language" className="group overflow-hidden rounded-2xl border border-border/70 bg-card md:col-span-2">
            <summary className="flex cursor-pointer list-none items-center justify-between gap-4 px-5 py-4 marker:hidden">
              <div><p className="font-black">{isRTL ? "الهوية واللغة" : "Profile & Language"}</p><p className="mt-1 text-xs text-muted-foreground">{isRTL ? "هوية تارا، أسلوب الرد، التعليمات، واللغات." : "Tara identity, tone, instructions and language behavior."}</p></div>
              <Badge variant="secondary" className="rounded-full">{isRTL ? "أساسي" : "Core"}</Badge>
            </summary>
            <div className="grid gap-6 border-t border-border/60 p-5 md:grid-cols-2 md:p-6">'''

TIMEZONE_OLD = '          <div className="space-y-2"><Label>Timezone</Label><Input value={settings.timezone || "Africa/Cairo"} onChange={e => setSettings({ ...settings, timezone: e.target.value })}/></div>'
TIMEZONE_NEW = '''            </div>
          </details>

          <details data-tara-settings-section="runtime-policy" className="group overflow-hidden rounded-2xl border border-border/70 bg-card md:col-span-2">
            <summary className="flex cursor-pointer list-none items-center justify-between gap-4 px-5 py-4 marker:hidden">
              <div><p className="font-black">{isRTL ? "سياسة التشغيل" : "Runtime Policy"}</p><p className="mt-1 text-xs text-muted-foreground">{isRTL ? "المنطقة الزمنية، ساعات العمل، التأخير، وحدود الرد." : "Timezone, business hours, timing and reply limits."}</p></div>
              <Badge variant="outline" className="rounded-full">{isRTL ? "تشغيل" : "Runtime"}</Badge>
            </summary>
            <div className="grid gap-6 border-t border-border/60 p-5 md:grid-cols-2 md:p-6">
          <div className="space-y-2"><Label>Timezone</Label><Input value={settings.timezone || "Africa/Cairo"} onChange={e => setSettings({ ...settings, timezone: e.target.value })}/></div>'''

HANDOFF_OLD = '          <div className="space-y-2 md:col-span-2"><Label>{taraText("\\u0643\\u0644\\u0645\\u0627\\u062A \\u0627\\u0644\\u062A\\u062D\\u0648\\u064A\\u0644 \\u0644\\u0645\\u0648\\u0638\\u0641 \\u2014 \\u0633\\u0637\\u0631 \\u0644\\u0643\\u0644 \\u0643\\u0644\\u0645\\u0629")}</Label><Textarea dir="auto" value={settings.handoffKeywordsText || ""} onChange={e => setSettings({ ...settings, handoffKeywordsText: e.target.value })}/></div>'
HANDOFF_NEW = '''            </div>
          </details>

          <details data-tara-settings-section="automation-safety" className="group overflow-hidden rounded-2xl border border-amber-200/70 bg-amber-50/20 dark:border-amber-900/50 dark:bg-amber-950/10 md:col-span-2">
            <summary className="flex cursor-pointer list-none items-center justify-between gap-4 px-5 py-4 marker:hidden">
              <div><p className="font-black">{isRTL ? "الأتمتة والتحويل البشري" : "Automation & Handoff"}</p><p className="mt-1 text-xs text-muted-foreground">{isRTL ? "كلمات التحويل وإرسال الردود تلقائيًا — راجعها قبل التفعيل." : "Handoff keywords and automatic sending — review before enabling."}</p></div>
              <Badge variant="outline" className="rounded-full border-amber-300/70 text-amber-700 dark:text-amber-300">{isRTL ? "حساس" : "Sensitive"}</Badge>
            </summary>
            <div className="grid gap-6 border-t border-amber-200/60 p-5 dark:border-amber-900/40 md:grid-cols-2 md:p-6">
          <div className="space-y-2 md:col-span-2"><Label>{taraText("\\u0643\\u0644\\u0645\\u0627\\u062A \\u0627\\u0644\\u062A\\u062D\\u0648\\u064A\\u0644 \\u0644\\u0645\\u0648\\u0638\\u0641 \\u2014 \\u0633\\u0637\\u0631 \\u0644\\u0643\\u0644 \\u0643\\u0644\\u0645\\u0629")}</Label><Textarea dir="auto" value={settings.handoffKeywordsText || ""} onChange={e => setSettings({ ...settings, handoffKeywordsText: e.target.value })}/></div>'''

STICKY_OLD = '          <div className="sticky bottom-3 z-20 flex flex-wrap items-center gap-2 rounded-2xl border border-border/70 bg-background/90 p-3 shadow-[0_16px_40px_-24px_rgba(15,23,42,0.5)] backdrop-blur-xl md:col-span-2">'
STICKY_NEW = '''            </div>
          </details>

          <div className="sticky bottom-3 z-20 flex flex-wrap items-center gap-2 rounded-2xl border border-border/70 bg-background/90 p-3 shadow-[0_16px_40px_-24px_rgba(15,23,42,0.5)] backdrop-blur-xl md:col-span-2">'''

TRIGGERS = ['settings', 'providers', 'voice', 'moderators', 'campaigns', 'qualification', 'knowledge', 'followups', 'social', 'test', 'logs']


def git_blob(path: Path) -> str:
    return subprocess.check_output(['git', 'hash-object', str(path)], text=True).strip()


def require_once(text: str, needle: str, label: str) -> None:
    count = text.count(needle)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly once, found {count}')


def transformed(text: str) -> str:
    if MARKER in text:
        return text
    require_once(text, OLD_NAV, 'legacy navigation')
    require_once(text, CARD_CONTENT_OLD, 'settings card content')
    require_once(text, TIMEZONE_OLD, 'timezone anchor')
    require_once(text, HANDOFF_OLD, 'handoff anchor')
    require_once(text, STICKY_OLD, 'sticky action anchor')
    text = text.replace(OLD_NAV, NEW_NAV, 1)
    text = text.replace(CARD_CONTENT_OLD, CARD_CONTENT_NEW, 1)
    text = text.replace(TIMEZONE_OLD, TIMEZONE_NEW, 1)
    text = text.replace(HANDOFF_OLD, HANDOFF_NEW, 1)
    text = text.replace(STICKY_OLD, STICKY_NEW, 1)
    return text


def verify(text: str) -> None:
    require_once(text, MARKER, 'workspace marker')
    for group in ['profile-runtime', 'sales-operations', 'knowledge', 'diagnostics']:
        require_once(text, f'data-tara-nav-group="{group}"', f'nav group {group}')
    for section in ['profile-language', 'runtime-policy', 'automation-safety']:
        require_once(text, f'data-tara-settings-section="{section}"', f'settings section {section}')
    if OLD_NAV in text:
        raise SystemExit('legacy flat navigation still present')
    for value in TRIGGERS:
        require_once(text, f'<TabsTrigger value="{value}"', f'tab trigger {value}')
        require_once(text, f'<TabsContent value="{value}"', f'tab content {value}')
    for preserved in [
        'TARA_REFERENCE_DASHBOARD_V3', 'tara-avatar.jpg', 'settingsPayload', 'saveSettingsM',
        'testProviderM', 'processQueueM', 'TaraProviderSettingsPanel', 'TaraVoiceSettingsPanel',
        'TaraSocialChannelsPanel', 'TaraModeratorManagementPanel'
    ]:
        if preserved not in text:
            raise SystemExit(f'missing preserved marker: {preserved}')


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--apply', action='store_true')
    mode.add_argument('--verify', action='store_true')
    args = parser.parse_args()

    if not TARGET.exists():
        raise SystemExit(f'missing target: {TARGET}')

    current = TARGET.read_text(encoding='utf-8')
    current_blob = git_blob(TARGET)

    if args.check:
        if MARKER in current:
            verify(current)
            print(f'CHECK=PASS ALREADY_APPLIED=YES BLOB={current_blob}')
            return 0
        if current_blob != BASE_BLOB:
            raise SystemExit(f'baseline blob mismatch: expected {BASE_BLOB}, got {current_blob}')
        candidate = transformed(current)
        verify(candidate)
        print(f'CHECK=PASS BASE_BLOB={current_blob}')
        return 0

    if args.apply:
        if MARKER in current:
            verify(current)
            print(f'APPLY=PASS ALREADY_APPLIED=YES BLOB={current_blob}')
            return 0
        if current_blob != BASE_BLOB:
            raise SystemExit(f'baseline blob mismatch: expected {BASE_BLOB}, got {current_blob}')
        candidate = transformed(current)
        verify(candidate)
        TARGET.write_text(candidate, encoding='utf-8')
        final_blob = git_blob(TARGET)
        print(f'APPLY=PASS FINAL_BLOB={final_blob}')
        return 0

    verify(current)
    print(f'VERIFY=PASS FINAL_BLOB={current_blob}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
