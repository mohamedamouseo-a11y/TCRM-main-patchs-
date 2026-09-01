#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re, shutil, sys

PATCH = "TCRM-Smart-Search-Systemwide-Parity-Hardening-V1"
MARK = "TCRM_SMART_SEARCH_SYSTEMWIDE_V1"
ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TCRM").resolve()
HERE = Path(__file__).resolve().parent
changed, skipped = [], []

def read(rel):
    p = ROOT / rel
    if not p.exists(): raise SystemExit(f"FAIL: required file missing: {p}")
    return p.read_text(encoding="utf-8")

def write(rel, text):
    p = ROOT / rel
    old = p.read_text(encoding="utf-8") if p.exists() else None
    if old == text: skipped.append(rel); return
    if p.exists():
        bak = p.with_name(p.name + ".smart-search-systemwide-v1.bak")
        if not bak.exists(): shutil.copy2(p, bak)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    changed.append(rel)

def imp(text, anchor, line, label):
    if line.strip() in text: return text
    if anchor not in text: raise SystemExit(f"FAIL: {label}: import anchor missing")
    return text.replace(anchor, anchor + line, 1)

def one(text, pattern, replacement, label):
    out, n = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if n != 1: raise SystemExit(f"FAIL: {label}: expected 1 anchor, got {n}")
    return out

def marked(text): return text if MARK in text else f"// {MARK}\n" + text

write("client/src/components/search/SmartSearchBar.tsx",
      (HERE / "SmartSearchBar.tsx").read_text(encoding="utf-8"))

rel = "client/src/components/GlobalSearch.tsx"; text = read(rel)
if "TCRM_SMART_SEARCH_GLOBAL_RACE_GUARD_V1" not in text:
    a = "  const [loading, setLoading] = useState(false);\n"
    if a not in text: raise SystemExit("FAIL: GlobalSearch state anchor")
    text = text.replace(a, a + "  const [searchError, setSearchError] = useState(false);\n  const searchRequestIdRef = useRef(0); // TCRM_SMART_SEARCH_GLOBAL_RACE_GUARD_V1\n", 1)
    old = '''  useEffect(() => {
    if (!open || normalizedQ.length < 2) {
      setLoading(false);
      if (open) setResults({ deals: [], companies: [], contacts: [] });
      return;
    }
    setLoading(true);
    const t = setTimeout(() => {
      bdApi.search(normalizedQ).then(setResults).catch(() => {}).finally(() => setLoading(false));
    }, 200);
    return () => clearTimeout(t);
  }, [normalizedQ, open]);
'''
    new = '''  useEffect(() => {
    const requestId = ++searchRequestIdRef.current;
    if (!open || normalizedQ.length < 2) {
      setLoading(false); setSearchError(false);
      if (open) setResults({ deals: [], companies: [], contacts: [] });
      return;
    }
    setLoading(true); setSearchError(false);
    const timer = setTimeout(() => {
      bdApi.search(normalizedQ)
        .then(next => { if (searchRequestIdRef.current === requestId) setResults(next); })
        .catch(() => {
          if (searchRequestIdRef.current !== requestId) return;
          setSearchError(true); setResults({ deals: [], companies: [], contacts: [] });
        })
        .finally(() => { if (searchRequestIdRef.current === requestId) setLoading(false); });
    }, 200);
    return () => {
      clearTimeout(timer);
      if (searchRequestIdRef.current === requestId) searchRequestIdRef.current += 1;
    };
  }, [normalizedQ, open]);
'''
    if old not in text: raise SystemExit("FAIL: GlobalSearch debounce anchor")
    text = text.replace(old, new, 1)
    text = text.replace("    else { setQ(''); setResults({ deals: [], companies: [], contacts: [] }); }\n",
                        "    else { setQ(''); setSearchError(false); setResults({ deals: [], companies: [], contacts: [] }); }\n", 1)
    text = text.replace(") : total === 0 ? (",
        ") : searchError ? (\n            <div className='p-8 text-center text-sm text-rose-500'>{isRTL ? 'تعذر تنفيذ البحث. حاول مرة أخرى.' : 'Search failed. Please try again.'}</div>\n          ) : total === 0 ? (", 1)
    write(rel, text)

rel = "server/utils/searchNormalizationSql.ts"; text = read(rel)
if "escapeNormalizedLikeLiteral" not in text:
    old = '''export function normalizedContains(column: any, query: unknown) {
  const normalized = normalizeSearchText(query);
  return sql`${normalizedSearchColumn(column)} LIKE ${`%${normalized}%`}`;
}
'''
    new = '''export function escapeNormalizedLikeLiteral(value: string) {
  return value.replace(/!/g, "!!").replace(/%/g, "!%").replace(/_/g, "!_");
}

export function normalizedContains(column: any, query: unknown) {
  const normalized = normalizeSearchText(query);
  const escaped = escapeNormalizedLikeLiteral(normalized);
  return sql`${normalizedSearchColumn(column)} LIKE ${`%${escaped}%`} ESCAPE '!'`;
}
'''
    if old not in text: raise SystemExit("FAIL: normalizedContains anchor")
    write(rel, text.replace(old, new, 1))

rel = "server/routes/bd/search.ts"; text = read(rel)
if "TCRM_SMART_SEARCH_PARALLEL_BD_V1" not in text:
    for old, new in [
        ("const dealsResult = await runExactFirstServerSearch({", "const dealsPromise = runExactFirstServerSearch({"),
        ("const companiesResult = await runExactFirstServerSearch({", "const companiesPromise = runExactFirstServerSearch({"),
        ("const contactsResult = await runExactFirstServerSearch({", "const contactsPromise = runExactFirstServerSearch({"),
    ]:
        if old not in text: raise SystemExit(f"FAIL: BD parallel anchor: {old}")
        text = text.replace(old, new, 1)
    anchor = "    res.json({\n"
    block = '''    // TCRM_SMART_SEARCH_PARALLEL_BD_V1
    const [dealsResult, companiesResult, contactsResult] = await Promise.all([
      dealsPromise, companiesPromise, contactsPromise,
    ]);

'''
    if anchor not in text: raise SystemExit("FAIL: BD response anchor")
    write(rel, text.replace(anchor, block + anchor, 1))

def migrate(rel, anchor, pattern, replacement):
    text = read(rel)
    if MARK in text: return
    text = imp(text, anchor, 'import SmartSearchBar from "@/components/search/SmartSearchBar";\n', rel)
    write(rel, marked(one(text, pattern, replacement, rel)))

rel = "client/src/pages/AdminSettings.tsx"; text = read(rel)
if MARK not in text:
    text = imp(text, 'import { cn } from "@/lib/utils";\n',
        'import VoiceSearchButton from "@/components/search/VoiceSearchButton";\nimport { rankSearchSuggestions } from "@shared/searchSuggestions";\n', rel)
    a = '  const visibleSettingsTabs = settingsTabGroups.flatMap((group) => group.tabs.filter((tab) => tab.visible !== false));\n'
    if a not in text: raise SystemExit("FAIL: AdminSettings tab anchor")
    calc = '''  const settingsSearchSuggestions = rankSearchSuggestions(
    settingsSearch,
    visibleSettingsTabs.map((tab: any) => ({
      value: { id: tab.value, label: String(tab.label ?? ""), secondary: String(tab.description ?? tab.badge ?? "") },
      fields: [tab.label, tab.description, tab.badge],
    })), 6,
  );
'''
    text = text.replace(a, a + calc, 1)
    m = re.search(r'(<Input\s+id="tcrm-settings-filter"[\s\S]*?/>)', text)
    if not m: raise SystemExit("FAIL: AdminSettings guarded input anchor")
    extra = m.group(1) + '''
              {/* TCRM_SETTINGS_SMART_UI_V1: guarded input retained */}
              <VoiceSearchButton
                language={isRTL ? "ar-EG" : "en-US"}
                onTranscript={(value) => { _searchUserTyped.current = true; setSettingsSearch(value); }}
                labels={{
                  start: isRTL ? "بحث بالصوت" : "Search by voice",
                  listening: isRTL ? "جاري الاستماع... اضغط للإيقاف" : "Listening... click to stop",
                  unsupported: isRTL ? "البحث الصوتي غير مدعوم في هذا المتصفح" : "Voice search is not supported in this browser",
                  error: isRTL ? "تعذر التقاط الصوت. حاول مرة أخرى." : "Could not capture speech. Please try again.",
                }}
                className={cn("absolute top-1/2 -translate-y-1/2", isRTL ? "left-2" : "right-2")}
              />
              {settingsSearch.trim().length >= 2 && settingsSearchSuggestions.length > 0 && (
                <div className="absolute start-0 end-0 top-full z-50 mt-1 overflow-hidden rounded-xl border bg-popover shadow-xl">
                  {settingsSearchSuggestions.map((s: any) => (
                    <button key={s.id} type="button" className="block w-full px-3 py-2 text-start text-sm hover:bg-muted"
                      onMouseDown={(e) => e.preventDefault()} onClick={() => { setActiveTab(s.id); setSettingsSearch(""); }}>
                      <span className="block truncate font-medium">{s.label}</span>
                      {s.secondary ? <span className="block truncate text-[11px] text-muted-foreground">{s.secondary}</span> : null}
                    </button>
                  ))}
                </div>
              )}'''
    write(rel, marked(text[:m.start()] + extra + text[m.end():]))

migrate("client/src/pages/BD/CompaniesList.tsx", "import CRMLayout from '@/components/CRMLayout';\n",
 r'''<div className='flex-1 relative min-w-\[240px\]'>[\s\S]*?<input placeholder=\{t\('bdSearchCompanies'\)\}[\s\S]*?value=\{search\}[\s\S]*?/>\s*</div>''',
 '''<SmartSearchBar value={search} onValueChange={setSearch} placeholder={t('bdSearchCompanies')}
          language={isRTL ? "ar-EG" : "en-US"}
          suggestions={rows.map((r: any) => ({ id: r.id, label: r.name || "", secondary: r.domain || r.industry || r.country }))}
          containerClassName='flex-1 min-w-[240px]' inputClassName='focus-visible:ring-emerald-500' />''')

migrate("client/src/pages/BD/ContactsList.tsx", "import CRMLayout from '@/components/CRMLayout';\n",
 r'''<div className='relative'>[\s\S]*?<input placeholder=\{t\('bdSearch'\)\}[\s\S]*?value=\{search\}[\s\S]*?/>\s*</div>''',
 '''<SmartSearchBar value={search} onValueChange={setSearch} placeholder={t('bdSearch')}
          language={isRTL ? "ar-EG" : "en-US"}
          suggestions={rows.map((r: any) => ({ id: r.id, label: r.fullName || "", secondary: r.jobTitle || r.email || r.phone }))}
          inputClassName='focus-visible:ring-purple-500' />''')

migrate("client/src/pages/BD/DealsKanban.tsx", "import CRMLayout from '@/components/CRMLayout';\n",
 r'''\{?/\* TFCRM_SEARCH_PARITY_INTEGRATED:[\s\S]*?<input\s+type='text'[\s\S]*?value=\{search\}[\s\S]*?/>''',
 '''<SmartSearchBar value={search} onValueChange={setSearch}
          placeholder={isRTL ? 'بحث في الصفقات...' : 'Search deals...'} language={isRTL ? "ar-EG" : "en-US"}
          suggestions={columns.flatMap((c: any) => c.deals ?? []).map((d: any) => ({ id: d.id, label: d.title || String(d.id), secondary: d.companyName }))}
          containerClassName='flex-1 min-w-[200px]' inputClassName='focus-visible:ring-indigo-500' />''')

migrate("client/src/pages/LeadsList.tsx", 'import CRMLayout from "@/components/CRMLayout";\n',
 r'''<div className="relative">\s*<Search[\s\S]*?<Input\s+placeholder=\{t\("search"\)\}[\s\S]*?value=\{search\}[\s\S]*?setPage\(0\);[\s\S]*?/>\s*</div>''',
 '''<SmartSearchBar value={search} onValueChange={(v) => { setSearch(v); setPage(0); }}
                  placeholder={t("search")} language={isRTL ? "ar-EG" : "en-US"}
                  suggestions={(data?.data ?? []).map((r: any) => ({ id: r.id, label: r.leadName || r.name || r.fullName || String(r.id), secondary: r.phone || r.email || r.campaignName }))} />''')

migrate("client/src/pages/RenewalPipeline.tsx", 'import CRMLayout from "../components/CRMLayout";\n',
 r'''<label className="relative block">\s*<Search[\s\S]*?<input[\s\S]*?value=\{filters\.search\}[\s\S]*?Search client / contract / owner[\s\S]*?/>\s*</label>''',
 '''<SmartSearchBar value={filters.search} onValueChange={(v) => setFilters((p) => ({ ...p, search: v }))}
              placeholder={isRTL ? "بحث باسم العميل / العقد / المسؤول" : "Search client / contract / owner"}
              language={isRTL ? "ar-EG" : "en-US"}
              suggestions={items.map((r: any) => ({ id: r.contractId ?? r.id, label: r.clientName || r.leadName || String(r.contractId ?? r.id), secondary: r.accountManagerName || r.ownerName || r.contractNumber }))} />''')

for rel, source, label, secondary in [
 ("client/src/pages/GoogleAdsCampaignsPage.tsx", "filtered", "r.campaignName", "r.objective || r.status"),
 ("client/src/pages/LinkedInCampaignsPage.tsx", "filtered", "r.campaignName", "r.type || r.status"),
 ("client/src/pages/SnapchatCampaignsPage.tsx", "filtered", "r.campaignName", "r.objective || r.status"),
 ("client/src/pages/TikTokCampaignsPage.tsx", "displayed", "r.name || r.campaignName", "r.objective || r.status"),
]:
    replacement = f'''<SmartSearchBar value={{search}} onValueChange={{(v) => {{ setSearch(v); setPage(1); }}}}
                      placeholder={{isRTL ? "بحث..." : "Search..."}} language={{isRTL ? "ar-EG" : "en-US"}}
                      suggestions={{{source}.slice(0, 12).map((r: any) => ({{ id: r.id ?? r.campaignId, label: {label} || String(r.id ?? r.campaignId ?? ""), secondary: {secondary} }}))}}
                      containerClassName="w-52" compact />'''
    migrate(rel, 'import CRMLayout from "@/components/CRMLayout";\n',
      r'''<div className="relative w-52">\s*<Search[\s\S]*?<Input[\s\S]*?value=\{search\}[\s\S]*?className="h-8 text-xs pl-8"\s*/>\s*</div>''',
      replacement)

migrate("client/src/pages/MetaCampaigns.tsx", 'import CRMLayout from "@/components/CRMLayout";\n',
 r'''<div className="relative flex-1 min-w-\[200px\]">\s*<Search[\s\S]*?<Input[\s\S]*?value=\{searchQuery\}[\s\S]*?className="pl-9 h-10 bg-muted/30 border-0 focus-visible:ring-1"[\s\S]*?/>\s*\{searchQuery && \([\s\S]*?</button>\s*\)\}\s*</div>''',
 '''<SmartSearchBar value={searchQuery} onValueChange={(v) => { setSearchQuery(v); setCurrentPage(1); }}
                  placeholder={isRTL ? "بحث باسم الحملة..." : "Search campaigns..."} language={isRTL ? "ar-EG" : "en-US"}
                  suggestions={filteredCampaigns.slice(0, 12).map((r: any) => ({ id: r.id ?? r.campaignId, label: r.campaignName || String(r.campaignId ?? r.id ?? ""), secondary: r.objective || r.status }))}
                  containerClassName="flex-1 min-w-[200px]" inputClassName="bg-muted/30 border-0 focus-visible:ring-1" />''')

migrate("client/src/components/wa/ConversationList.tsx", 'import { Input } from "@/components/ui/input";\n',
 r'''<div className="relative">\s*<Search[\s\S]*?<Input value=\{search\}[\s\S]*?onSearch\(event\.target\.value\)[\s\S]*?/>\s*</div>''',
 '''<SmartSearchBar value={search} onValueChange={onSearch} placeholder={copy.search} ariaLabel={copy.search}
          language={locale.toLowerCase().startsWith("ar") ? "ar-EG" : "en-US"}
          suggestions={chats.map((c) => ({ id: c.id, label: conversationLabel(c), secondary: conversationSecondaryLabel(c) || c.lastMessagePreview }))} />''')

rel = "client/src/components/wa/ForwardMessageDialog.tsx"
if (ROOT / rel).exists():
    text = read(rel)
    if MARK not in text and "SmartSearchBar" not in text:
        text = imp(text, 'import { Input } from "@/components/ui/input";\n',
                   'import SmartSearchBar from "@/components/search/SmartSearchBar";\n', rel)
        pat = r'''<div className="relative">\s*<Search[\s\S]*?<Input\s+autoFocus[\s\S]*?value=\{search\}[\s\S]*?setSearch\(event\.target\.value\)[\s\S]*?/>\s*</div>'''
        rep = '''<SmartSearchBar value={search} onValueChange={setSearch} placeholder={copy.forwardSearch} autoFocus
            language={isRTL ? "ar-EG" : "en-US"}
            suggestions={chats.map((c: any) => ({ id: c.id, label: c.displayName || c.contactName || c.pushName || c.phoneNumber || c.jid, secondary: c.phoneNumber || c.jid }))} />'''
        write(rel, marked(one(text, pat, rep, rel)))

print("PASS/FAIL: PASS")
print("PATCH:", PATCH)
print("FILES_CHANGED:", "; ".join(changed) if changed else "NONE")
print("FILES_SKIPPED:", "; ".join(skipped) if skipped else "NONE")
print("DB_CHANGED: NO")
print("SCHEMA_CHANGED: NO")
print("PERMISSIONS_CHANGED: NO")
print("NEXT: python3 VERIFY_PATCH.py <TCRM_ROOT> && python3 AUDIT_SEARCHES.py <TCRM_ROOT>")
