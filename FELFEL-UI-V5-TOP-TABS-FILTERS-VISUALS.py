#!/usr/bin/env python3
# FELFEL_UI_V5_TOP_TABS_FILTERS_VISUALS
from pathlib import Path

ROOT = Path('/var/www/TCRM-MAIN')
PAGE = ROOT / 'client/src/pages/FelfelPage.tsx'
DASH = ROOT / 'client/src/components/felfel/FelfelOperationalDashboard.tsx'

for p in (PAGE, DASH):
    if not p.exists():
        raise SystemExit(f'missing:{p}')

def read(p): return p.read_text(encoding='utf-8')
def write(p, text): p.write_text(text, encoding='utf-8')
def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f'{label}: expected 1 anchor, found {n}')
    return text.replace(old, new, 1)

page = read(PAGE)
dash = read(DASH)

if 'FELFEL_UI_V5_TOP_TABS_FILTERS_VISUALS' in page and 'FELFEL_UI_V5_TOP_TABS_FILTERS_VISUALS' in dash:
    print('FELFEL_UI_V5_PATCHED=YES')
    raise SystemExit(0)

if 'FELFEL_UI_V5_TOP_TABS_FILTERS_VISUALS' not in page:
    page = replace_once(page,
        'import { useEffect, useMemo, useState } from "react";\n',
        '// FELFEL_UI_V5_TOP_TABS_FILTERS_VISUALS\nimport { useEffect, useMemo, useState } from "react";\n',
        'page marker')
    page = replace_once(page,
        '  const [felfelWorkspace, setFelfelWorkspace] = useState("live");',
        '  const [felfelWorkspace, setFelfelWorkspace] = useState("meetings");',
        'default meetings tab')
    page = replace_once(page,
        '        <FelfelOperationalDashboard showHero={false} />\n\n',
        '',
        'standalone dashboard')

    summary_start = page.find('        <Card data-felfel-workspace-summary="v8"')
    tabs_start = page.find('        <Tabs data-felfel-workspace="meeting-intelligence-v8"')
    if summary_start < 0 or tabs_start < 0 or tabs_start <= summary_start:
        raise RuntimeError('legacy workspace region anchors not found')
    page = page[:summary_start] + page[tabs_start:]

    page = replace_once(page,
        '        <Tabs data-felfel-workspace="meeting-intelligence-v8" value={felfelWorkspace} onValueChange={setFelfelWorkspace} className="w-full space-y-4">',
        '        <Tabs data-felfel-workspace="meeting-intelligence-v10" value={felfelWorkspace} onValueChange={setFelfelWorkspace} className="w-full space-y-4">',
        'tabs version')

    old_tabs = '''          <TabsList className="h-auto w-full flex-nowrap justify-start gap-1 overflow-x-auto rounded-2xl border border-border/70 bg-muted/30 p-1.5 shadow-sm [scrollbar-width:none] [&::-webkit-scrollbar]:hidden [&_[role=tab]]:h-10 [&_[role=tab]]:shrink-0 [&_[role=tab]]:rounded-xl [&_[role=tab]]:border-b-2 [&_[role=tab]]:border-transparent [&_[role=tab]]:px-4 [&_[role=tab]]:text-xs [&_[role=tab]]:font-bold [&_[data-state=active]]:border-orange-500 [&_[data-state=active]]:bg-background [&_[data-state=active]]:text-foreground [&_[data-state=active]]:shadow-sm">
            <TabsTrigger value="live" className="gap-1.5"><Activity className="h-3.5 w-3.5" />{ar ? "الاجتماع المباشر" : "Live meeting"}</TabsTrigger>'''
    new_tabs = '''          <TabsList className="sticky top-2 z-20 h-auto w-full flex-nowrap justify-start gap-1 overflow-x-auto rounded-2xl border border-border/70 bg-background/95 p-1.5 shadow-sm backdrop-blur [scrollbar-width:none] [&::-webkit-scrollbar]:hidden [&_[role=tab]]:h-11 [&_[role=tab]]:shrink-0 [&_[role=tab]]:rounded-xl [&_[role=tab]]:px-4 [&_[role=tab]]:text-xs [&_[role=tab]]:font-black [&_[data-state=active]]:bg-gradient-to-r [&_[data-state=active]]:from-orange-500 [&_[data-state=active]]:to-amber-500 [&_[data-state=active]]:text-white [&_[data-state=active]]:shadow-sm">
            <TabsTrigger value="meetings" className="gap-1.5"><VideoIcon className="h-3.5 w-3.5" />{ar ? "الاجتماعات" : "Meetings"}</TabsTrigger>
            <TabsTrigger value="live" className="gap-1.5"><Activity className="h-3.5 w-3.5" />{ar ? "الاجتماع المباشر" : "Live meeting"}</TabsTrigger>'''
    page = replace_once(page, old_tabs, new_tabs, 'five top tabs')

    meetings_content = '''
          <TabsContent value="meetings" className="mt-3 space-y-4">
            <div className="overflow-hidden rounded-2xl border border-orange-500/15 bg-gradient-to-r from-orange-500/[0.045] via-card to-violet-500/[0.035] p-3 md:p-4">
              <div className="flex items-center gap-3">
                <div className="relative h-12 w-12 shrink-0 overflow-hidden rounded-full border-2 border-background bg-muted shadow-sm">
                  <img src="/ai-staff/felfel-avatar.webp" alt="Felfel" className="h-full w-full object-cover object-[50%_18%]" />
                  <span className="absolute bottom-0 end-0 h-3 w-3 rounded-full border-2 border-background bg-emerald-500" />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-black">{ar ? "فلفل معاك في مساحة الاجتماعات" : "Felfel in your meeting workspace"}</p>
                  <p className="mt-0.5 text-xs text-muted-foreground">{ar ? "ابحث، فلتر، افتح الاجتماع وشاهد التسجيل والتفريغ والذكاء من مكان واحد." : "Search, filter, open a meeting, and review recording, transcript, and intelligence in one place."}</p>
                </div>
                <div className="ms-auto hidden items-center -space-x-2 md:flex">
                  <span className="grid h-8 w-8 place-items-center rounded-full border-2 border-background bg-blue-500/10 text-[10px] font-black text-blue-700">AM</span>
                  <span className="grid h-8 w-8 place-items-center rounded-full border-2 border-background bg-violet-500/10 text-[10px] font-black text-violet-700">CRM</span>
                  <span className="grid h-8 w-8 place-items-center rounded-full border-2 border-background bg-orange-500/10 text-[10px] font-black text-orange-700">AI</span>
                </div>
              </div>
            </div>
            <FelfelOperationalDashboard showHero={false} />
          </TabsContent>

'''
    anchor = '          {canManageAiProviders && (\n'
    if anchor not in page:
        raise RuntimeError('providers anchor not found')
    page = page.replace(anchor, meetings_content + anchor, 1)

if 'FELFEL_UI_V5_TOP_TABS_FILTERS_VISUALS' not in dash:
    dash = replace_once(dash,
        '// @ts-nocheck\n',
        '// @ts-nocheck\n// FELFEL_UI_V5_TOP_TABS_FILTERS_VISUALS\n',
        'dashboard marker')
    dash = replace_once(dash,
        'import { Input } from "@/components/ui/input";\n',
        'import { Input } from "@/components/ui/input";\nimport { Calendar } from "@/components/ui/calendar";\nimport { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";\n',
        'date ui imports')

    helper_anchor = '''function displayDate(value: unknown, ar: boolean) {
  if (!value) return "—";
  const date = new Date(String(value));
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString(ar ? "ar-EG" : "en-US", { dateStyle: "medium", timeStyle: "short" });
}

'''
    helper_new = helper_anchor + '''function localDateValue(date: Date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function dateRangeLabel(fromDate: string, toDate: string, ar: boolean) {
  if (!fromDate && !toDate) return ar ? "كل التواريخ" : "Any date";
  const fmt = (value: string) => {
    const date = new Date(`${value}T00:00:00`);
    return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString(ar ? "ar-EG" : "en-US", { month: "short", day: "numeric", year: "numeric" });
  };
  if (fromDate && toDate) return `${fmt(fromDate)} → ${fmt(toDate)}`;
  return fromDate ? `${ar ? "من" : "From"} ${fmt(fromDate)}` : `${ar ? "إلى" : "To"} ${fmt(toDate)}`;
}

'''
    dash = replace_once(dash, helper_anchor, helper_new, 'date helpers')

    state_anchor = '  const [toDate, setToDate] = useState("");\n  const [page, setPage] = useState(0);\n'
    state_new = '''  const [toDate, setToDate] = useState("");
  const [dateOpen, setDateOpen] = useState(false);
  const [page, setPage] = useState(0);

  const selectedDateRange = useMemo(() => {
    const from = fromDate ? new Date(`${fromDate}T00:00:00`) : undefined;
    const to = toDate ? new Date(`${toDate}T00:00:00`) : undefined;
    return from || to ? { from, to } : undefined;
  }, [fromDate, toDate]);
'''
    dash = replace_once(dash, state_anchor, state_new, 'date state')

    old_filters = '''      <Card className="rounded-[24px] border-border/70 shadow-sm">
        <CardContent className="p-4">
          <div className="mb-3 flex items-center justify-between gap-3"><div className="flex items-center gap-2 text-sm font-black"><SlidersHorizontal className="h-4 w-4 text-orange-500" />{ar ? "بحث ذكي وفلاتر" : "Smart Search & Filters"}</div>{filtersActive && <Button type="button" variant="ghost" size="sm" className="gap-1 rounded-xl" onClick={clearFilters}><X className="h-3.5 w-3.5" />{ar ? "مسح" : "Clear"}</Button>}</div>
          <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-8">
            <div className="relative md:col-span-2 xl:col-span-2"><Search className={`pointer-events-none absolute top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground ${isRTL ? "right-3" : "left-3"}`} /><Input value={search} onChange={(event) => setSearch(event.target.value)} className={isRTL ? "pr-9" : "pl-9"} placeholder={ar ? "ابحث بالعميل، عنوان الاجتماع، ID، المنصة أو المستدعي..." : "Search client, title, ID, platform, or invoker..."} /></div>
            <select value={platform} onChange={(event) => setPlatform(event.target.value)} className="h-10 rounded-md border border-input bg-background px-3 text-sm"><option value="all">{ar ? "كل المنصات" : "All platforms"}</option><option value="google_meet">Google Meet</option><option value="teams">Teams</option><option value="zoom">Zoom</option><option value="jitsi">Jitsi</option></select>
            <select value={status} onChange={(event) => setStatus(event.target.value)} className="h-10 rounded-md border border-input bg-background px-3 text-sm"><option value="all">{ar ? "كل الحالات" : "All statuses"}</option>{["scheduled","joining","waiting","live","ended","processing","completed","failed"].map((value) => <option key={value} value={value}>{value}</option>)}</select>
            <select value={recordingStatus} onChange={(event) => setRecordingStatus(event.target.value)} className="h-10 rounded-md border border-input bg-background px-3 text-sm"><option value="all">{ar ? "كل التسجيلات" : "All recordings"}</option>{["not_started","pending","uploaded","uploaded_audio_only","failed"].map((value) => <option key={value} value={value}>{value}</option>)}</select>
            {isAdmin && <select value={invokerUserId} onChange={(event) => setInvokerUserId(event.target.value)} className="h-10 rounded-md border border-input bg-background px-3 text-sm"><option value="all">{ar ? "كل المستدعين" : "All invokers"}</option>{invokerOptions.map((item: any) => <option key={item.id} value={String(item.id)}>{item.name || item.email || `#${item.id}`} · {item.role}</option>)}</select>}
            <div className="grid grid-cols-2 gap-2 md:col-span-2 xl:col-span-2"><Input type="date" value={fromDate} onChange={(event) => setFromDate(event.target.value)} title={ar ? "من تاريخ" : "From date"} /><Input type="date" value={toDate} onChange={(event) => setToDate(event.target.value)} title={ar ? "إلى تاريخ" : "To date"} /></div>
          </div>
        </CardContent>
      </Card>
'''
    new_filters = '''      <Card className="overflow-visible rounded-[24px] border-orange-500/15 bg-gradient-to-r from-orange-500/[0.035] via-card to-violet-500/[0.025] shadow-sm">
        <CardContent className="p-4 md:p-5">
          <div className="mb-3 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2 text-sm font-black"><span className="grid h-8 w-8 place-items-center rounded-xl bg-orange-500/10 text-orange-600"><SlidersHorizontal className="h-4 w-4" /></span>{ar ? "البحث والفلاتر" : "Search & Filters"}</div>
            {filtersActive && <Button type="button" variant="ghost" size="sm" className="gap-1 rounded-xl text-muted-foreground" onClick={clearFilters}><X className="h-3.5 w-3.5" />{ar ? "إعادة ضبط" : "Reset"}</Button>}
          </div>
          <div className="grid gap-2.5 md:grid-cols-2 xl:grid-cols-12">
            <div className="relative md:col-span-2 xl:col-span-4">
              <Search className={`pointer-events-none absolute top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground ${isRTL ? "right-3.5" : "left-3.5"}`} />
              <Input value={search} onChange={(event) => setSearch(event.target.value)} className={`h-11 rounded-xl bg-background/90 shadow-sm ${isRTL ? "pr-10" : "pl-10"}`} placeholder={ar ? "ابحث بالعميل، العنوان، ID، المنصة أو المستدعي..." : "Search client, title, ID, platform, or invoker..."} />
            </div>
            <select value={platform} onChange={(event) => setPlatform(event.target.value)} className="h-11 rounded-xl border border-input bg-background/90 px-3 text-sm font-medium shadow-sm xl:col-span-2"><option value="all">{ar ? "كل المنصات" : "All platforms"}</option><option value="google_meet">Google Meet</option><option value="teams">Teams</option><option value="zoom">Zoom</option><option value="jitsi">Jitsi</option></select>
            <select value={status} onChange={(event) => setStatus(event.target.value)} className="h-11 rounded-xl border border-input bg-background/90 px-3 text-sm font-medium shadow-sm xl:col-span-2"><option value="all">{ar ? "كل الحالات" : "All statuses"}</option>{["scheduled","joining","waiting","live","ended","processing","completed","failed"].map((value) => <option key={value} value={value}>{value}</option>)}</select>
            <select value={recordingStatus} onChange={(event) => setRecordingStatus(event.target.value)} className="h-11 rounded-xl border border-input bg-background/90 px-3 text-sm font-medium shadow-sm xl:col-span-2"><option value="all">{ar ? "كل التسجيلات" : "All recordings"}</option>{["not_started","pending","uploaded","uploaded_audio_only","failed"].map((value) => <option key={value} value={value}>{value}</option>)}</select>
            {isAdmin && <select value={invokerUserId} onChange={(event) => setInvokerUserId(event.target.value)} className="h-11 rounded-xl border border-input bg-background/90 px-3 text-sm font-medium shadow-sm xl:col-span-2"><option value="all">{ar ? "كل المستدعين" : "All invokers"}</option>{invokerOptions.map((item: any) => <option key={item.id} value={String(item.id)}>{item.name || item.email || `#${item.id}`} · {item.role}</option>)}</select>}

            <div className="md:col-span-2 xl:col-span-4">
              <Popover open={dateOpen} onOpenChange={setDateOpen}>
                <PopoverTrigger asChild>
                  <Button type="button" variant="outline" className="h-11 w-full justify-start gap-2 rounded-xl bg-background/90 px-3 text-start font-medium shadow-sm">
                    <CalendarDays className="h-4 w-4 shrink-0 text-orange-500" />
                    <span className="truncate">{dateRangeLabel(fromDate, toDate, ar)}</span>
                  </Button>
                </PopoverTrigger>
                <PopoverContent align={isRTL ? "end" : "start"} className="w-auto rounded-2xl border-border/70 p-0 shadow-xl">
                  <div className="border-b border-border/60 px-4 py-3">
                    <p className="text-sm font-black">{ar ? "نطاق التاريخ" : "Date range"}</p>
                    <p className="mt-0.5 text-[11px] text-muted-foreground">{ar ? "اختر البداية والنهاية من تقويم واحد." : "Choose start and end from one calendar."}</p>
                  </div>
                  <Calendar
                    mode="range"
                    numberOfMonths={2}
                    selected={selectedDateRange}
                    onSelect={(range: any) => {
                      setFromDate(range?.from ? localDateValue(range.from) : "");
                      setToDate(range?.to ? localDateValue(range.to) : "");
                      if (range?.from && range?.to) setDateOpen(false);
                    }}
                    defaultMonth={selectedDateRange?.from || new Date()}
                  />
                  <div className="flex items-center justify-between gap-2 border-t border-border/60 p-3">
                    <Button type="button" variant="ghost" size="sm" className="rounded-xl" onClick={() => { setFromDate(""); setToDate(""); }}>{ar ? "مسح التاريخ" : "Clear dates"}</Button>
                    <Button type="button" size="sm" className="rounded-xl" onClick={() => setDateOpen(false)}>{ar ? "تم" : "Done"}</Button>
                  </div>
                </PopoverContent>
              </Popover>
            </div>
          </div>
        </CardContent>
      </Card>
'''
    dash = replace_once(dash, old_filters, new_filters, 'filter redesign')

    old_empty = '        <div className="rounded-2xl border border-dashed border-border p-10 text-center text-sm text-muted-foreground">{ar ? "لا توجد اجتماعات مطابقة." : "No matching meetings."}</div>'
    new_empty = '''        <div className="overflow-hidden rounded-2xl border border-dashed border-orange-500/20 bg-gradient-to-br from-orange-500/[0.04] via-background to-violet-500/[0.04] p-6 text-center">
          <div className="mx-auto flex max-w-md flex-col items-center">
            <div className="relative h-20 w-20">
              <div className="absolute inset-0 rounded-full bg-orange-500/10 blur-xl" />
              <div className="relative h-20 w-20 overflow-hidden rounded-full border-4 border-background bg-muted shadow-lg"><img src="/ai-staff/felfel-avatar.webp" alt="Felfel" className="h-full w-full object-cover object-[50%_18%]" /></div>
              <span className="absolute -bottom-1 -end-1 grid h-7 w-7 place-items-center rounded-full border-2 border-background bg-emerald-500 text-[10px] font-black text-white">LIVE</span>
            </div>
            <p className="mt-3 text-sm font-black">{ar ? "فلفل جاهز للاجتماع التالي" : "Felfel is ready for the next meeting"}</p>
            <p className="mt-1 text-xs leading-5 text-muted-foreground">{ar ? "لا توجد اجتماعات مطابقة للفلاتر الحالية. غيّر البحث أو نطاق التاريخ." : "No meetings match the current filters. Adjust search or the date range."}</p>
          </div>
        </div>'''
    dash = replace_once(dash, old_empty, new_empty, 'meeting visual empty state')

write(PAGE, page)
write(DASH, dash)

print('FELFEL_UI_V5_PATCHED=YES')
print('FILES=2')
