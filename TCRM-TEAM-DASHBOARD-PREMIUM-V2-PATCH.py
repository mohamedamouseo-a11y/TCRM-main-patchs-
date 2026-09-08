#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path.cwd()
TSX = ROOT / "client/src/pages/TeamDashboard.tsx"
CSS = ROOT / "client/src/team-dashboard-premium-v2.css"

if not TSX.exists():
    raise SystemExit("ERROR=client/src/pages/TeamDashboard.tsx not found; run from LIVE TCRM repo root")

text = TSX.read_text(encoding="utf-8")
original = text

# V2 is intentionally built on top of V1. Fail early if V1 is not present.
required_v1 = [
    'import "../team-dashboard-premium-v1.css";',
    'tcrm-team-dashboard-premium',
    'tcrm-team-hero',
    'tcrm-team-kpi-grid',
    'tcrm-team-performance-card',
]
missing_v1 = [x for x in required_v1 if x not in text]
if missing_v1:
    raise SystemExit("ERROR=V1_REQUIRED_MISSING:" + ",".join(missing_v1))

# Imports.
if "LabelList" not in text:
    text = text.replace("  Legend,\n} from \"recharts\";", "  Legend,\n  LabelList,\n} from \"recharts\";", 1)

old_lucide = 'import { AlertTriangle, CheckCircle, TrendingUp, Users } from "lucide-react";'
new_lucide = 'import { Activity, AlertTriangle, BarChart3, CheckCircle, PieChart as PieChartIcon, TrendingUp, Trophy, Users } from "lucide-react";'
if old_lucide in text:
    text = text.replace(old_lucide, new_lucide, 1)
elif "BarChart3" not in text or "PieChartIcon" not in text:
    raise SystemExit("ERROR=Could not update lucide imports")

v2_import = 'import "../team-dashboard-premium-v2.css";'
if v2_import not in text:
    anchor = 'import "../team-dashboard-premium-v1.css";'
    text = text.replace(anchor, anchor + "\n" + v2_import, 1)

helper_anchor = "  const revenueBreakdownText = formatOriginalBreakdown();"
helpers = r'''
  const stageData = stats?.leadsByStage ?? [];
  const qualityData = stats?.leadsByQuality ?? [];
  const dealsData = stats?.dealsByAgent ?? [];
  const stageTotal = stageData.reduce((sum: number, item: any) => sum + Number(item?.count ?? 0), 0);
  const qualityTotal = qualityData.reduce((sum: number, item: any) => sum + Number(item?.count ?? 0), 0);
  const hasDealsData = dealsData.some((item: any) => Number(item?.wonDeals ?? 0) > 0 || Number(item?.revenue ?? 0) > 0);
  const qualityColors: Record<string, string> = {
    Hot: "#ef4444",
    Warm: "#f97316",
    Cold: "#3b82f6",
    Bad: "#94a3b8",
    Unknown: "#cbd5e1",
  };
  const pct = (value: number, total: number) => total > 0 ? Math.round((Number(value || 0) / total) * 100) : 0;
  const clampPct = (value: number) => Math.max(0, Math.min(Number(value || 0), 100));
  const getInitials = (name: string) => String(name || "?").trim().split(/\s+/).slice(0, 2).map((part) => part[0] || "").join("").toUpperCase() || "?";
'''
if "const stageData = stats?.leadsByStage" not in text:
    if helper_anchor not in text:
        raise SystemExit("ERROR=Could not locate helper insertion point")
    text = text.replace(helper_anchor, helper_anchor + helpers, 1)


def replace_between(src: str, start: str, end: str, replacement: str) -> str:
    s = src.find(start)
    if s < 0:
        raise SystemExit(f"ERROR=Missing start marker: {start}")
    e = src.find(end, s + len(start))
    if e < 0:
        raise SystemExit(f"ERROR=Missing end marker: {end}")
    return src[:s] + replacement.rstrip() + "\n\n        " + src[e:]

kpis = r'''{/* Summary Cards - Staggered */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 stagger-children tcrm-team-kpi-grid">
          {[
            { title: t("totalLeads"), value: stats?.totalLeads ?? 0, icon: <Users size={19} />, color: tokens.primaryColor, href: leadsHref, tone: "blue" },
            { title: t("wonDeals"), value: stats?.wonDeals ?? 0, icon: <Trophy size={19} />, color: tokens.successColor, href: wonLeadsHref, tone: "green" },
            { title: t("totalRevenue"), value: formatSar(stats?.totalRevenue ?? 0), subtitle: isRTL ? "مطابق لفترة Export" : "Export-aligned period", icon: <TrendingUp size={19} />, color: tokens.accentColor, href: wonLeadsHref, tone: "violet" },
            { title: t("slaAlerts"), value: stats?.slaBreached ?? 0, icon: <AlertTriangle size={19} />, color: "#ef4444", href: slaLeadsHref, tone: "red" },
          ].map((card, i) => (
            <Link key={i} href={(card as any).href}>
              <Card className={`cursor-pointer group ${kpiGradients[i]} tcrm-team-kpi-card tcrm-team-kpi-${i}`}>
                <CardContent className="tcrm-team-kpi-content">
                  <div className="tcrm-team-kpi-topline">
                    <div className="kpi-icon tcrm-team-kpi-icon" style={{ background: card.color }}>
                      {card.icon}
                    </div>
                    <div className="tcrm-team-kpi-spark" aria-hidden="true">
                      <span /><span /><span /><span /><span /><span />
                    </div>
                  </div>
                  <div className="tcrm-team-kpi-value">
                    {isLoading ? <div className="h-8 w-16 bg-muted rounded animate-pulse" /> : card.value}
                  </div>
                  {(card as any).subtitle && (
                    <p className="tcrm-team-kpi-subtitle" title={(card as any).subtitle}>{(card as any).subtitle}</p>
                  )}
                  <div className="tcrm-team-kpi-footer">
                    <span className="tcrm-team-kpi-label">{card.title}</span>
                    <span className="tcrm-team-kpi-period">{isRTL ? "الفترة الحالية" : "Current period"}</span>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>'''
text = replace_between(text, "{/* Summary Cards - Staggered */}", "{revenueBreakdownText && (", kpis)

leads_agent = r'''{/* Leads by Agent */}
          <Card className="chart-container tcrm-team-chart-card">
            <CardHeader className="tcrm-team-chart-header">
              <div className="tcrm-team-chart-heading">
                <span className="tcrm-team-chart-icon"><BarChart3 size={18} /></span>
                <div>
                  <CardTitle>{isRTL ? "العملاء حسب الوكيل" : "Leads by Agent"}</CardTitle>
                  <p>{isRTL ? "إجمالي العملاء لكل موظف" : "Total leads per agent"}</p>
                </div>
              </div>
              <span className="tcrm-team-chart-chip">{t("totalLeads")}</span>
            </CardHeader>
            <CardContent className="tcrm-team-chart-content">
              {isLoading ? (
                <div className="h-[250px] bg-muted rounded-xl animate-pulse" />
              ) : isDeveloperVisualPreview && (stats?.leadsByAgent ?? []).length === 0 ? (
                <DeveloperVisualPreview variant="bars" className="h-[250px]" />
              ) : (
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={stats?.leadsByAgent ?? []} margin={{ top: 22, right: 12, left: 0, bottom: 4 }}>
                    <defs>
                      <linearGradient id="teamLeadsBar" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#8b7cff" />
                        <stop offset="55%" stopColor="#5e6fff" />
                        <stop offset="100%" stopColor="#4159df" />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 6" stroke="var(--team-grid)" vertical />
                    <XAxis dataKey="agentName" tick={{ fontSize: 11 }} tickLine={false} axisLine={{ stroke: "var(--team-grid)" }} />
                    <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "var(--team-tooltip)", border: "1px solid var(--team-border-strong)", borderRadius: 12, boxShadow: "0 18px 40px rgba(0,0,0,.18)" }} />
                    <Bar dataKey="count" fill="url(#teamLeadsBar)" radius={[7, 7, 1, 1]} animationDuration={850} maxBarSize={112}>
                      <LabelList dataKey="count" position="top" fill="var(--team-text)" fontSize={11} fontWeight={800} />
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>'''
text = replace_between(text, "{/* Leads by Agent */}", "{/* Leads by Stage */}", leads_agent)

leads_stage = r'''{/* Leads by Stage */}
          <Card className="chart-container tcrm-team-chart-card">
            <CardHeader className="tcrm-team-chart-header">
              <div className="tcrm-team-chart-heading">
                <span className="tcrm-team-chart-icon"><PieChartIcon size={18} /></span>
                <div>
                  <CardTitle>{isRTL ? "العملاء حسب المرحلة" : "Leads by Stage"}</CardTitle>
                  <p>{isRTL ? "توزيع العملاء عبر مراحل المبيعات" : "Distribution of leads across stages"}</p>
                </div>
              </div>
              <span className="tcrm-team-chart-chip">{isRTL ? "كل العملاء" : "All leads"}</span>
            </CardHeader>
            <CardContent className="tcrm-team-chart-content">
              {isLoading ? (
                <div className="h-[250px] bg-muted rounded-xl animate-pulse" />
              ) : isDeveloperVisualPreview && stageData.length === 0 ? (
                <DeveloperVisualPreview variant="donut" className="h-[250px]" />
              ) : (
                <div className="tcrm-team-donut-layout">
                  <div className="tcrm-team-donut-chart">
                    <ResponsiveContainer width="100%" height={250}>
                      <PieChart>
                        <Pie
                          data={stageData}
                          cx="50%"
                          cy="50%"
                          outerRadius={92}
                          innerRadius={58}
                          paddingAngle={1}
                          dataKey="count"
                          nameKey="stage"
                          animationDuration={850}
                          animationBegin={120}
                          stroke="transparent"
                        >
                          {stageData.map((_: any, i: number) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                        </Pie>
                        <Tooltip contentStyle={{ background: "var(--team-tooltip)", border: "1px solid var(--team-border-strong)", borderRadius: 12, boxShadow: "0 18px 40px rgba(0,0,0,.18)" }} />
                        <text x="50%" y="47%" textAnchor="middle" className="tcrm-team-donut-total">{stageTotal || Number(stats?.totalLeads ?? 0)}</text>
                        <text x="50%" y="55%" textAnchor="middle" className="tcrm-team-donut-caption">{t("totalLeads")}</text>
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="tcrm-team-side-legend">
                    {stageData.map((item: any, i: number) => (
                      <div className="tcrm-team-legend-row" key={`${item.stage}-${i}`}>
                        <span className="tcrm-team-legend-dot" style={{ background: COLORS[i % COLORS.length] }} />
                        <span className="tcrm-team-legend-name">{item.stage}</span>
                        <span className="tcrm-team-legend-pct">{pct(item.count, stageTotal)}%</span>
                        <strong>{item.count}</strong>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>'''
text = replace_between(text, "{/* Leads by Stage */}", "{/* Won Deals by Agent */}", leads_stage)

deals = r'''{/* Won Deals by Agent */}
          <Card className="chart-container tcrm-team-chart-card">
            <CardHeader className="tcrm-team-chart-header">
              <div className="tcrm-team-chart-heading">
                <span className="tcrm-team-chart-icon"><TrendingUp size={18} /></span>
                <div>
                  <CardTitle>{isRTL ? "الصفقات والإيرادات حسب الموظف" : "Deals & Revenue by Agent"}</CardTitle>
                  <p>{isRTL ? "عدد الصفقات والإيراد بالريال لكل موظف" : "Deals count and revenue (SAR) per agent"}</p>
                </div>
              </div>
              <div className="tcrm-team-chart-key"><span className="deals" />{t("wonDeals")}<span className="revenue" />{t("totalRevenue")}</div>
            </CardHeader>
            <CardContent className="tcrm-team-chart-content">
              {isLoading ? (
                <div className="h-[250px] bg-muted rounded-xl animate-pulse" />
              ) : isDeveloperVisualPreview && dealsData.length === 0 ? (
                <DeveloperVisualPreview variant="bars" className="h-[250px]" />
              ) : !hasDealsData ? (
                <div className="tcrm-team-empty-chart">
                  <div className="tcrm-team-empty-grid" aria-hidden="true" />
                  <div className="tcrm-team-empty-copy">
                    <span className="tcrm-team-empty-icon"><BarChart3 size={22} /></span>
                    <strong>{isRTL ? "لا توجد صفقات أو إيرادات حتى الآن" : "No deals or revenue data yet"}</strong>
                    <p>{isRTL ? "ستظهر البيانات هنا بمجرد إغلاق الصفقات." : "Data will appear here once deals are won."}</p>
                  </div>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={dealsData} margin={{ top: 18, right: 12, left: 0, bottom: 4 }}>
                    <defs>
                      <linearGradient id="teamDealsBar" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#5de0a0"/><stop offset="100%" stopColor="#18a968"/></linearGradient>
                      <linearGradient id="teamRevenueBar" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#9a72ff"/><stop offset="100%" stopColor="#6650db"/></linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 6" stroke="var(--team-grid)" />
                    <XAxis dataKey="agentName" tick={{ fontSize: 11 }} tickLine={false} axisLine={{ stroke: "var(--team-grid)" }} />
                    <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                    <Tooltip formatter={(value: any, name: any) => name === t("totalRevenue") ? [formatSar(value), name] : [value, name]} contentStyle={{ background: "var(--team-tooltip)", border: "1px solid var(--team-border-strong)", borderRadius: 12, boxShadow: "0 18px 40px rgba(0,0,0,.18)" }} />
                    <Bar dataKey="wonDeals" fill="url(#teamDealsBar)" radius={[6, 6, 1, 1]} name={t("wonDeals")} animationDuration={850} />
                    <Bar dataKey="revenue" fill="url(#teamRevenueBar)" radius={[6, 6, 1, 1]} name={t("totalRevenue")} animationDuration={850} animationBegin={150} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>'''
text = replace_between(text, "{/* Won Deals by Agent */}", "{/* Lead Quality Distribution */}", deals)

quality = r'''{/* Lead Quality Distribution */}
          <Card className="chart-container tcrm-team-chart-card">
            <CardHeader className="tcrm-team-chart-header">
              <div className="tcrm-team-chart-heading">
                <span className="tcrm-team-chart-icon"><PieChartIcon size={18} /></span>
                <div>
                  <CardTitle>{isRTL ? "توزيع جودة العملاء" : "Lead Quality Distribution"}</CardTitle>
                  <p>{isRTL ? "تفصيل جودة كل العملاء" : "Quality breakdown of all leads"}</p>
                </div>
              </div>
            </CardHeader>
            <CardContent className="tcrm-team-chart-content">
              {isLoading ? (
                <div className="h-[250px] bg-muted rounded-xl animate-pulse" />
              ) : isDeveloperVisualPreview && qualityData.length === 0 ? (
                <DeveloperVisualPreview variant="donut" className="h-[250px]" />
              ) : (
                <div className="tcrm-team-donut-layout">
                  <div className="tcrm-team-donut-chart">
                    <ResponsiveContainer width="100%" height={250}>
                      <PieChart>
                        <Pie data={qualityData} cx="50%" cy="50%" outerRadius={92} innerRadius={58} paddingAngle={1} dataKey="count" nameKey="quality" animationDuration={850} animationBegin={120} stroke="transparent">
                          {qualityData.map((entry: any, i: number) => <Cell key={i} fill={qualityColors[entry.quality] ?? COLORS[i % COLORS.length]} />)}
                        </Pie>
                        <Tooltip contentStyle={{ background: "var(--team-tooltip)", border: "1px solid var(--team-border-strong)", borderRadius: 12, boxShadow: "0 18px 40px rgba(0,0,0,.18)" }} />
                        <text x="50%" y="47%" textAnchor="middle" className="tcrm-team-donut-total">{qualityTotal || Number(stats?.totalLeads ?? 0)}</text>
                        <text x="50%" y="55%" textAnchor="middle" className="tcrm-team-donut-caption">{t("totalLeads")}</text>
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="tcrm-team-side-legend">
                    {qualityData.map((item: any, i: number) => (
                      <div className="tcrm-team-legend-row" key={`${item.quality}-${i}`}>
                        <span className="tcrm-team-legend-dot" style={{ background: qualityColors[item.quality] ?? COLORS[i % COLORS.length] }} />
                        <span className="tcrm-team-legend-name">{item.quality}</span>
                        <span className="tcrm-team-legend-pct">{pct(item.count, qualityTotal)}%</span>
                        <strong>{item.count}</strong>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>'''
text = replace_between(text, "{/* Lead Quality Distribution */}", "</div>\n\n        {/* Agent Performance Table */}", quality)

performance = r'''{/* Agent Performance Table */}
        <Card className="slide-up tcrm-team-performance-card" style={{ animationDelay: '0.3s' }}>
          <CardHeader className="tcrm-team-performance-header">
            <div className="tcrm-team-chart-heading">
              <span className="tcrm-team-chart-icon"><Activity size={18} /></span>
              <div>
                <CardTitle>{t("agentPerformance")}</CardTitle>
                <p>{isRTL ? "مؤشرات الأداء الرئيسية لكل موظف" : "Key performance metrics by agent"}</p>
              </div>
            </div>
            <span className="tcrm-team-performance-chip">{isRTL ? "أداء الفريق" : "Team performance"}</span>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm tcrm-team-performance-table">
                <thead>
                  <tr>
                    <th>{t("name")}</th>
                    <th>{t("totalLeads")}</th>
                    <th>{t("totalActivities")}</th>
                    <th>{t("wonDeals")}</th>
                    <th>{t("totalRevenue")}</th>
                    <th>{t("conversionRate")}</th>
                    <th>{isRTL ? "تواصل ← اجتماع" : "Contact → Meeting"}</th>
                    <th>{isRTL ? "اجتماع ← إغلاق" : "Meeting → Close"}</th>
                    <th>{t("slaAlerts")}</th>
                  </tr>
                </thead>
                <tbody>
                  {isLoading ? (
                    Array.from({ length: 4 }).map((_, i) => (
                      <tr key={i}>{Array.from({ length: 9 }).map((_, j) => <td key={j}><div className="h-4 bg-muted rounded animate-pulse" /></td>)}</tr>
                    ))
                  ) : (stats?.agentPerformance ?? []).length === 0 ? (
                    isDeveloperVisualPreview ? <DeveloperTablePreviewRows columns={9} rows={4} /> : <tr><td colSpan={9} className="py-10 text-center text-muted-foreground">{t("noData")}</td></tr>
                  ) : (
                    (stats?.agentPerformance ?? []).map((agent: any, index: number) => (
                      <tr key={agent.agentId}>
                        <td>
                          <div className="tcrm-team-agent-cell">
                            <span className={`tcrm-team-agent-avatar avatar-${index % 4}`}>{getInitials(agent.agentName)}</span>
                            <div><strong>{agent.agentName}</strong>{!agent.isActive && <span className="tcrm-team-inactive">Inactive</span>}</div>
                          </div>
                        </td>
                        <td>{agent.totalLeads}</td>
                        <td>{agent.totalActivities}</td>
                        <td><span className="tcrm-team-won-value">{agent.wonDeals}</span></td>
                        <td>{agent.revenue > 0 ? formatSar(agent.revenue) : "—"}</td>
                        <td>
                          <div className="tcrm-team-meter-cell">
                            <div className="tcrm-team-meter conversion"><span style={{ width: `${clampPct(agent.conversionRate)}%` }} /></div>
                            <span>{agent.conversionRate.toFixed(1)}%</span>
                          </div>
                        </td>
                        <td>
                          <div className="tcrm-team-meter-cell">
                            <div className="tcrm-team-meter contact"><span style={{ width: `${clampPct(agent.contactToMeetingRate ?? 0)}%` }} /></div>
                            <span>{(agent.contactToMeetingRate ?? 0).toFixed(1)}%</span>
                          </div>
                        </td>
                        <td>
                          <div className="tcrm-team-meter-cell">
                            <div className="tcrm-team-meter close"><span style={{ width: `${clampPct(agent.meetingToCloseRate ?? 0)}%` }} /></div>
                            <span>{(agent.meetingToCloseRate ?? 0).toFixed(1)}%</span>
                          </div>
                        </td>
                        <td>{agent.slaBreached > 0 ? <Badge variant="destructive" className="tcrm-team-sla-badge">{agent.slaBreached}</Badge> : <span className="text-muted-foreground">0</span>}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>'''
text = replace_between(text, "{/* Agent Performance Table */}", "</div>\n    </CRMLayout>", performance)

# Final sanity checks.
required_v2 = [
    v2_import,
    "tcrm-team-kpi-spark",
    "tcrm-team-donut-layout",
    "tcrm-team-empty-chart",
    "tcrm-team-agent-avatar",
    "tcrm-team-meter contact",
]
missing_v2 = [x for x in required_v2 if x not in text]
if missing_v2:
    raise SystemExit("ERROR=V2_HOOKS_MISSING:" + ",".join(missing_v2))

css = r'''
/* TCRM Team Dashboard Premium V2 — high fidelity to approved Light/Dark concept */
.tcrm-team-dashboard-premium{--team-tooltip:rgba(255,255,255,.98);}
.dark .tcrm-team-dashboard-premium{--team-tooltip:rgba(10,22,42,.98);}

/* Hero — stronger aurora depth and concept-like proportions */
.tcrm-team-dashboard-premium .tcrm-team-hero{border-radius:20px;box-shadow:0 18px 50px -26px rgba(73,69,255,.62),0 0 0 1px rgba(255,255,255,.18) inset;}
.tcrm-team-dashboard-premium .tcrm-team-hero::before{inset:-120% -16%;background:radial-gradient(ellipse at 18% 48%,rgba(89,70,255,.94),transparent 27%),radial-gradient(ellipse at 56% 40%,rgba(51,129,255,.68),transparent 30%),radial-gradient(ellipse at 86% 55%,rgba(139,63,255,.78),transparent 31%),linear-gradient(108deg,#4936b8,#2850b2 48%,#7543d7);animation:tcrmTeamAurora 14s ease-in-out infinite alternate;}
.tcrm-team-dashboard-premium .tcrm-team-hero::after{content:"PEOPLE  •  PIPELINE  •  PROGRESS";position:absolute;z-index:3;right:31%;top:50%;transform:translateY(-50%);font-size:9px;font-weight:800;letter-spacing:.28em;color:rgba(255,255,255,.48);pointer-events:none;white-space:nowrap;}
[dir="rtl"].tcrm-team-dashboard-premium .tcrm-team-hero::after{right:auto;left:31%;}
.tcrm-team-dashboard-premium .tcrm-team-hero>*{min-height:78px!important;padding-top:14px!important;padding-bottom:14px!important;background:linear-gradient(112deg,rgba(55,51,170,.92),rgba(38,77,164,.82) 50%,rgba(107,61,202,.90))!important;}
.tcrm-team-dashboard-premium .tcrm-team-hero h1,.tcrm-team-dashboard-premium .tcrm-team-hero h2{font-size:20px!important;font-weight:850!important;letter-spacing:-.035em!important;text-shadow:0 2px 18px rgba(0,0,0,.18);}

/* KPI row — compact, luminous, information-dense */
.tcrm-team-dashboard-premium .tcrm-team-kpi-grid{gap:14px!important;}
.tcrm-team-dashboard-premium .tcrm-team-kpi-card{min-height:128px!important;}
.tcrm-team-dashboard-premium .tcrm-team-kpi-content{position:relative;z-index:2;padding:17px 18px 15px!important;height:100%;display:flex;flex-direction:column;}
.tcrm-team-dashboard-premium .tcrm-team-kpi-topline{display:flex;align-items:flex-start;justify-content:space-between;gap:10px;}
.tcrm-team-dashboard-premium .tcrm-team-kpi-icon{width:44px!important;height:44px!important;border-radius:14px!important;display:flex;align-items:center;justify-content:center;color:#fff;}
.tcrm-team-dashboard-premium .tcrm-team-kpi-value{margin-top:10px;color:var(--team-text);font-size:29px;line-height:1;font-weight:880;letter-spacing:-.045em;}
.tcrm-team-dashboard-premium .tcrm-team-kpi-subtitle{margin-top:5px;font-size:9px;color:var(--team-muted);line-height:1.2;}
.tcrm-team-dashboard-premium .tcrm-team-kpi-footer{margin-top:auto;padding-top:8px;display:flex;align-items:flex-end;justify-content:space-between;gap:10px;}
.tcrm-team-dashboard-premium .tcrm-team-kpi-label{font-size:11px;font-weight:700;color:var(--team-muted);}
.tcrm-team-dashboard-premium .tcrm-team-kpi-period{font-size:8px;color:var(--team-muted);opacity:.62;white-space:nowrap;}
.tcrm-team-dashboard-premium .tcrm-team-kpi-spark{width:76px;height:34px;display:flex;align-items:flex-end;gap:4px;opacity:.78;filter:drop-shadow(0 0 9px rgba(var(--team-accent),.22));}
.tcrm-team-dashboard-premium .tcrm-team-kpi-spark span{display:block;flex:1;border-radius:6px 6px 2px 2px;background:linear-gradient(180deg,rgba(var(--team-accent),.92),rgba(var(--team-accent),.16));}
.tcrm-team-dashboard-premium .tcrm-team-kpi-spark span:nth-child(1){height:24%}.tcrm-team-dashboard-premium .tcrm-team-kpi-spark span:nth-child(2){height:37%}.tcrm-team-dashboard-premium .tcrm-team-kpi-spark span:nth-child(3){height:54%}.tcrm-team-dashboard-premium .tcrm-team-kpi-spark span:nth-child(4){height:43%}.tcrm-team-dashboard-premium .tcrm-team-kpi-spark span:nth-child(5){height:68%}.tcrm-team-dashboard-premium .tcrm-team-kpi-spark span:nth-child(6){height:88%}
.dark .tcrm-team-dashboard-premium .tcrm-team-kpi-card{border-color:rgba(var(--team-accent),.32)!important;box-shadow:0 24px 56px -34px rgba(0,0,0,.92),0 0 30px -22px rgba(var(--team-accent),.75),inset 0 1px 0 rgba(255,255,255,.06)!important;}

/* Analytics cards */
.tcrm-team-dashboard-premium .tcrm-team-chart-grid{gap:16px!important;}
.tcrm-team-dashboard-premium .tcrm-team-chart-card{min-height:330px;}
.tcrm-team-dashboard-premium .tcrm-team-chart-header,.tcrm-team-dashboard-premium .tcrm-team-performance-header{padding:16px 18px 8px!important;display:flex;align-items:flex-start;justify-content:space-between;gap:14px;}
.tcrm-team-dashboard-premium .tcrm-team-chart-heading{display:flex;align-items:flex-start;gap:10px;min-width:0;}
.tcrm-team-dashboard-premium .tcrm-team-chart-icon{width:34px;height:34px;flex:0 0 34px;border-radius:11px;display:inline-flex;align-items:center;justify-content:center;color:#6572ff;background:linear-gradient(145deg,rgba(99,102,241,.14),rgba(99,102,241,.05));border:1px solid rgba(99,102,241,.16);box-shadow:0 8px 22px -14px rgba(79,70,229,.42);}
.dark .tcrm-team-dashboard-premium .tcrm-team-chart-icon{color:#8da2ff;background:linear-gradient(145deg,rgba(95,100,255,.20),rgba(46,91,190,.08));border-color:rgba(113,129,255,.26);box-shadow:0 0 22px -12px rgba(94,98,255,.8);}
.tcrm-team-dashboard-premium .tcrm-team-chart-heading [class*="CardTitle"],.tcrm-team-dashboard-premium .tcrm-team-chart-heading .font-semibold,.tcrm-team-dashboard-premium .tcrm-team-performance-header [class*="CardTitle"]{font-size:13px!important;line-height:1.15;font-weight:820!important;color:var(--team-text)!important;letter-spacing:-.02em;}
.tcrm-team-dashboard-premium .tcrm-team-chart-heading p{margin-top:4px;font-size:9px;color:var(--team-muted);line-height:1.25;}
.tcrm-team-dashboard-premium .tcrm-team-chart-chip,.tcrm-team-dashboard-premium .tcrm-team-performance-chip{height:30px;padding:0 10px;border-radius:9px;display:inline-flex;align-items:center;justify-content:center;font-size:9px;font-weight:750;color:var(--team-text);background:rgba(99,102,241,.055);border:1px solid var(--team-border);white-space:nowrap;}
.dark .tcrm-team-dashboard-premium .tcrm-team-chart-chip,.dark .tcrm-team-dashboard-premium .tcrm-team-performance-chip{background:rgba(84,103,180,.11);}
.tcrm-team-dashboard-premium .tcrm-team-chart-content{padding:4px 16px 14px!important;}
.tcrm-team-dashboard-premium .recharts-bar-rectangle path{filter:drop-shadow(0 6px 11px rgba(82,91,235,.22));}
.dark .tcrm-team-dashboard-premium .recharts-bar-rectangle path{filter:drop-shadow(0 8px 14px rgba(82,99,255,.30));}
.tcrm-team-dashboard-premium .recharts-cartesian-axis-tick-value{font-weight:600;}

/* Donut cards — large center metric + side legend */
.tcrm-team-dashboard-premium .tcrm-team-donut-layout{display:grid;grid-template-columns:minmax(210px,.95fr) minmax(180px,1.05fr);align-items:center;gap:8px;min-height:250px;}
.tcrm-team-dashboard-premium .tcrm-team-donut-chart{min-width:0;}
.tcrm-team-dashboard-premium .tcrm-team-donut-total{font-size:20px;font-weight:880;fill:var(--team-text);letter-spacing:-.04em;}
.tcrm-team-dashboard-premium .tcrm-team-donut-caption{font-size:9px;font-weight:650;fill:var(--team-muted);}
.tcrm-team-dashboard-premium .tcrm-team-side-legend{display:flex;flex-direction:column;gap:3px;padding:4px 6px;}
.tcrm-team-dashboard-premium .tcrm-team-legend-row{display:grid;grid-template-columns:10px minmax(0,1fr) 38px 28px;align-items:center;gap:8px;min-height:30px;padding:0 7px;border-radius:9px;border-bottom:1px solid rgba(99,102,241,.07);font-size:9px;color:var(--team-muted);}
.tcrm-team-dashboard-premium .tcrm-team-legend-row:hover{background:rgba(99,102,241,.045);}
.tcrm-team-dashboard-premium .tcrm-team-legend-dot{width:8px;height:8px;border-radius:999px;box-shadow:0 0 10px currentColor;}
.tcrm-team-dashboard-premium .tcrm-team-legend-name{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--team-text);font-weight:650;}
.tcrm-team-dashboard-premium .tcrm-team-legend-pct{text-align:right;}
.tcrm-team-dashboard-premium .tcrm-team-legend-row strong{text-align:right;color:var(--team-text);font-weight:800;}

/* Deals empty state mirrors approved concept instead of a dead graph */
.tcrm-team-dashboard-premium .tcrm-team-chart-key{display:flex;align-items:center;gap:5px;color:var(--team-muted);font-size:8px;white-space:nowrap;}
.tcrm-team-dashboard-premium .tcrm-team-chart-key span{width:8px;height:8px;border-radius:50%;display:inline-block;margin-left:5px}.tcrm-team-dashboard-premium .tcrm-team-chart-key .deals{background:#4f7cff}.tcrm-team-dashboard-premium .tcrm-team-chart-key .revenue{background:#8b5cf6}
.tcrm-team-dashboard-premium .tcrm-team-empty-chart{position:relative;height:250px;overflow:hidden;border-radius:14px;display:flex;align-items:center;justify-content:center;}
.tcrm-team-dashboard-premium .tcrm-team-empty-grid{position:absolute;inset:12px 2px;background-image:linear-gradient(var(--team-grid) 1px,transparent 1px),linear-gradient(90deg,var(--team-grid) 1px,transparent 1px);background-size:100% 52px,92px 100%;mask-image:linear-gradient(to bottom,transparent,black 16%,black 86%,transparent);opacity:.7;}
.tcrm-team-dashboard-premium .tcrm-team-empty-copy{position:relative;z-index:2;text-align:center;display:flex;flex-direction:column;align-items:center;max-width:280px;padding:20px;border-radius:16px;background:radial-gradient(circle at 50% 0,rgba(99,102,241,.10),transparent 70%);}
.tcrm-team-dashboard-premium .tcrm-team-empty-icon{width:48px;height:48px;border-radius:14px;display:flex;align-items:center;justify-content:center;color:#6674ff;background:linear-gradient(145deg,rgba(99,102,241,.16),rgba(99,102,241,.05));border:1px solid rgba(99,102,241,.18);box-shadow:0 12px 28px -18px rgba(79,70,229,.55);}
.tcrm-team-dashboard-premium .tcrm-team-empty-copy strong{margin-top:12px;color:var(--team-text);font-size:12px;font-weight:800;}.tcrm-team-dashboard-premium .tcrm-team-empty-copy p{margin-top:5px;color:var(--team-muted);font-size:9px;}

/* Performance table — avatars + 3 performance meters */
.tcrm-team-dashboard-premium .tcrm-team-performance-card{overflow:hidden;}
.tcrm-team-dashboard-premium .tcrm-team-performance-header{padding-bottom:12px!important;}
.tcrm-team-dashboard-premium .tcrm-team-performance-table{border-collapse:separate;border-spacing:0;}
.tcrm-team-dashboard-premium .tcrm-team-performance-table thead tr{background:linear-gradient(90deg,rgba(99,102,241,.065),rgba(59,130,246,.035));}
.dark .tcrm-team-dashboard-premium .tcrm-team-performance-table thead tr{background:linear-gradient(90deg,rgba(91,104,216,.16),rgba(41,74,140,.10));}
.tcrm-team-dashboard-premium .tcrm-team-performance-table th{height:38px;padding:0 12px;text-align:start;font-size:8px;font-weight:720;color:var(--team-muted);border-top:1px solid rgba(99,102,241,.055);border-bottom:1px solid rgba(99,102,241,.10);white-space:nowrap;}
.tcrm-team-dashboard-premium .tcrm-team-performance-table td{height:48px;padding:7px 12px;color:var(--team-text);font-size:9px;border-bottom:1px solid rgba(99,102,241,.09);vertical-align:middle;}
.tcrm-team-dashboard-premium .tcrm-team-performance-table tbody tr{transition:background .2s ease,transform .2s ease;}.tcrm-team-dashboard-premium .tcrm-team-performance-table tbody tr:hover{background:rgba(99,102,241,.045);}
.dark .tcrm-team-dashboard-premium .tcrm-team-performance-table tbody tr:hover{background:rgba(94,104,235,.08);}
.tcrm-team-dashboard-premium .tcrm-team-agent-cell{display:flex;align-items:center;gap:9px;min-width:142px;}.tcrm-team-dashboard-premium .tcrm-team-agent-cell strong{display:block;font-size:9px;font-weight:780;color:var(--team-text);}
.tcrm-team-dashboard-premium .tcrm-team-agent-avatar{width:27px;height:27px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#fff;font-size:8px;font-weight:850;box-shadow:0 6px 16px -9px rgba(36,43,96,.8),inset 0 1px 0 rgba(255,255,255,.45);}
.tcrm-team-dashboard-premium .tcrm-team-agent-avatar.avatar-0{background:linear-gradient(145deg,#805cff,#5a46df)}.tcrm-team-dashboard-premium .tcrm-team-agent-avatar.avatar-1{background:linear-gradient(145deg,#4f8cff,#3265df)}.tcrm-team-dashboard-premium .tcrm-team-agent-avatar.avatar-2{background:linear-gradient(145deg,#48cbb7,#2b9f91)}.tcrm-team-dashboard-premium .tcrm-team-agent-avatar.avatar-3{background:linear-gradient(145deg,#ff9a4e,#e66a31)}
.tcrm-team-dashboard-premium .tcrm-team-inactive{display:inline-block;margin-top:2px;padding:1px 5px;border-radius:999px;font-size:7px;color:#ef4444;background:rgba(239,68,68,.09);}
.tcrm-team-dashboard-premium .tcrm-team-won-value{color:#13b96d;font-weight:800;}
.tcrm-team-dashboard-premium .tcrm-team-meter-cell{display:flex;align-items:center;gap:7px;min-width:100px;}.tcrm-team-dashboard-premium .tcrm-team-meter-cell>span{width:34px;font-size:8px;font-weight:650;color:var(--team-muted);}
.tcrm-team-dashboard-premium .tcrm-team-meter{position:relative;width:64px;height:6px;border-radius:999px;background:rgba(148,163,184,.15);overflow:hidden;box-shadow:inset 0 1px 2px rgba(0,0,0,.05);}.dark .tcrm-team-dashboard-premium .tcrm-team-meter{background:rgba(130,151,188,.17);}
.tcrm-team-dashboard-premium .tcrm-team-meter span{display:block;height:100%;border-radius:inherit;min-width:0;transition:width .7s ease;}.tcrm-team-dashboard-premium .tcrm-team-meter.conversion span{background:linear-gradient(90deg,#6a77ff,#8d72ff);box-shadow:0 0 8px rgba(108,100,255,.45)}.tcrm-team-dashboard-premium .tcrm-team-meter.contact span{background:linear-gradient(90deg,#28d59a,#56e6b0);box-shadow:0 0 8px rgba(40,213,154,.42)}.tcrm-team-dashboard-premium .tcrm-team-meter.close span{background:linear-gradient(90deg,#4f8cff,#775cff);box-shadow:0 0 8px rgba(84,105,255,.42)}
.tcrm-team-dashboard-premium .tcrm-team-sla-badge{min-width:24px;height:21px;border-radius:999px!important;display:inline-flex;align-items:center;justify-content:center;padding:0 7px!important;font-size:8px!important;box-shadow:0 0 14px -6px rgba(239,68,68,.75);}

/* Light mode gets pearl/pastel depth instead of washed white */
:not(.dark) .tcrm-team-dashboard-premium .tcrm-team-chart-card,:not(.dark) .tcrm-team-dashboard-premium .tcrm-team-performance-card{background:linear-gradient(145deg,rgba(255,255,255,.98),rgba(248,250,255,.94))!important;box-shadow:0 22px 54px -38px rgba(63,72,170,.36),inset 0 1px 0 rgba(255,255,255,.98)!important;border-color:rgba(99,102,241,.14)!important;}
:not(.dark) .tcrm-team-dashboard-premium .tcrm-team-kpi-card{background:radial-gradient(circle at 90% 95%,rgba(var(--team-accent),.10),transparent 34%),linear-gradient(145deg,#fff,#f8faff)!important;border-color:rgba(var(--team-accent),.22)!important;box-shadow:0 20px 48px -38px rgba(var(--team-accent),.48),inset 0 1px 0 #fff!important;}

@media(max-width:1100px){.tcrm-team-dashboard-premium .tcrm-team-hero::after{display:none}.tcrm-team-dashboard-premium .tcrm-team-donut-layout{grid-template-columns:1fr}.tcrm-team-dashboard-premium .tcrm-team-side-legend{display:grid;grid-template-columns:1fr 1fr}.tcrm-team-dashboard-premium .tcrm-team-chart-card{min-height:390px}}
@media(max-width:720px){.tcrm-team-dashboard-premium .tcrm-team-kpi-spark{display:none}.tcrm-team-dashboard-premium .tcrm-team-kpi-value{font-size:24px}.tcrm-team-dashboard-premium .tcrm-team-side-legend{grid-template-columns:1fr}.tcrm-team-dashboard-premium .tcrm-team-chart-chip,.tcrm-team-dashboard-premium .tcrm-team-performance-chip,.tcrm-team-dashboard-premium .tcrm-team-chart-key{display:none}.tcrm-team-dashboard-premium .tcrm-team-chart-header,.tcrm-team-dashboard-premium .tcrm-team-performance-header{padding:14px!important}}
'''.strip() + "\n"

TSX.write_text(text, encoding="utf-8")
CSS.write_text(css, encoding="utf-8")

print("PATCH=YES")
print("V1_BASE=YES")
print(f"TSX_CHANGED={'YES' if text != original else 'NO'}")
print("V2_CSS_WRITTEN=YES")
print("V2_CSS_IMPORTED=YES")
print("FIDELITY_HOOKS=YES")
print("TARGET=TeamDashboard 1:1 concept fidelity")
