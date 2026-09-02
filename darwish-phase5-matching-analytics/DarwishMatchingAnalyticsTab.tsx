import { Activity, BarChart3, CheckCircle2, RefreshCw, ShieldCheck, TrendingUp, XCircle } from "lucide-react";
import type { ReactNode } from "react";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useLanguage } from "@/contexts/LanguageContext";
import { trpc } from "@/lib/trpc";
import { cn } from "@/lib/utils";

const SIGNAL_LABELS: Record<string, [string, string]> = {
  exact_phone: ["Exact phone", "تطابق رقم"], name: ["Name", "الاسم"], business_name: ["Business name", "اسم النشاط"],
  group_name: ["Group name", "اسم الجروب"], participant_name: ["Participant", "اسم مشارك"], sender_identity: ["Sender identity", "هوية المرسل"],
  message_context: ["Message context", "سياق الرسائل"], other: ["Other", "أخرى"],
};
function percent(value: unknown) { const n = Number(value || 0); return `${Number.isInteger(n) ? n : n.toFixed(1)}%`; }
function levelLabel(value: string, rtl: boolean) {
  if (value === "high") return rtl ? "عالية" : "High";
  if (value === "medium") return rtl ? "متوسطة" : "Medium";
  if (value === "low") return rtl ? "منخفضة" : "Low";
  return rtl ? "بدون تقييم" : "None";
}
function Metric({ title, value, hint, icon }: { title: string; value: string | number; hint: string; icon: ReactNode }) {
  return <Card className="border-border/70 shadow-sm"><CardContent className="p-5"><div className="flex items-start justify-between gap-4"><div><p className="text-xs font-medium text-muted-foreground">{title}</p><p className="mt-2 text-3xl font-bold">{value}</p><p className="mt-1 text-xs text-muted-foreground">{hint}</p></div><div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">{icon}</div></div></CardContent></Card>;
}

export default function DarwishMatchingAnalyticsTab() {
  const { isRTL } = useLanguage();
  const [days, setDays] = useState<7 | 30 | 90>(30);
  const q = trpc.darwish.groupMatchingAnalytics.useQuery({ days });
  const data = q.data;
  const s = data?.summary;
  const recommendationDecisions = s?.recommendationDecisions || 0;
  const trend = (data?.dailyTrend || []).slice(-14).reverse();

  return <div className="space-y-5" dir={isRTL ? "rtl" : "ltr"}>
    <Card className="overflow-hidden border-primary/15 shadow-sm"><CardContent className="p-0"><div className="flex flex-col gap-4 bg-gradient-to-br from-primary/10 via-background to-background p-6 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-start gap-4"><div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary text-primary-foreground"><BarChart3 size={20} /></div><div><div className="flex flex-wrap items-center gap-2"><h2 className="text-lg font-bold">{isRTL ? "جودة مطابقة جروبات درويش" : "Darwish Group Matching Quality"}</h2><Badge variant="secondary">{isRTL ? "مراقبة فقط" : "Monitoring only"}</Badge></div><p className="mt-1 max-w-3xl text-sm text-muted-foreground">{isRTL ? "قياس جودة الترشيحات من قرارات الأدمن المسجلة فقط، بدون Auto-Link أو Auto-Learning." : "Measures audited admin feedback only. No auto-linking, auto-learning, or matching behavior changes."}</p></div></div>
      <div className="flex flex-wrap gap-2">{([7, 30, 90] as const).map((p) => <Button key={p} size="sm" variant={days === p ? "default" : "outline"} onClick={() => setDays(p)}>{p} {isRTL ? "يوم" : "days"}</Button>)}<Button size="icon" variant="outline" onClick={() => q.refetch()} disabled={q.isFetching}><RefreshCw size={15} className={cn(q.isFetching && "animate-spin")} /></Button></div>
    </div></CardContent></Card>

    {q.isLoading ? <Card><CardContent className="p-10 text-center text-sm text-muted-foreground">{isRTL ? "جاري التحميل..." : "Loading matching analytics..."}</CardContent></Card> : !data?.available ? <Card className="border-dashed"><CardContent className="flex flex-col items-center gap-3 p-10 text-center"><ShieldCheck size={30} className="text-muted-foreground" /><div><p className="font-semibold">{isRTL ? "بيانات التدقيق غير متاحة" : "Audit data is unavailable"}</p><p className="mt-1 text-sm text-muted-foreground">{isRTL ? "تأكد أن Migration الخاصة بـ Phase 4 مطبقة على قاعدة البيانات." : "Apply the Phase 4 audit migration before using this dashboard."}</p></div></CardContent></Card> : <>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Metric title={isRTL ? "قرارات الربط" : "Audited decisions"} value={s?.totalDecisions || 0} hint={isRTL ? `آخر ${days} يوم` : `Last ${days} days`} icon={<Activity size={18} />} />
        <Metric title={isRTL ? "تغطية الترشيحات" : "Recommendation coverage"} value={percent(s?.recommendationCoveragePct)} hint={`${recommendationDecisions} ${isRTL ? "قرار به ترشيح" : "recommended decisions"}`} icon={<TrendingUp size={18} />} />
        <Metric title={isRTL ? "قبول ترشيح درويش" : "Acceptance rate"} value={percent(s?.acceptanceRatePct)} hint={`${s?.acceptedRecommendations || 0} ${isRTL ? "تم قبولها" : "accepted"}`} icon={<CheckCircle2 size={18} />} />
        <Metric title={isRTL ? "تجاوز الترشيح" : "Override rate"} value={percent(s?.overrideRatePct)} hint={`${s?.overrodeRecommendations || 0} ${isRTL ? "اختيار مختلف" : "human overrides"}`} icon={<XCircle size={18} />} />
      </div>

      <div className="grid gap-5 xl:grid-cols-2">
        <Card className="border-border/70 shadow-sm"><CardHeader><CardTitle className="text-sm">{isRTL ? "الجودة حسب مستوى الثقة" : "Quality by confidence level"}</CardTitle></CardHeader><CardContent className="space-y-4">{(data.confidence || []).map((item) => <div key={item.level} className="space-y-2"><div className="flex items-center justify-between text-sm"><span><Badge variant="outline">{levelLabel(item.level, isRTL)}</Badge> <span className="text-muted-foreground">{item.decisions}</span></span><strong>{percent(item.acceptanceRatePct)}</strong></div><div className="h-2 overflow-hidden rounded-full bg-muted"><div className="h-full rounded-full bg-primary/70" style={{ width: `${recommendationDecisions ? Math.round(item.decisions / recommendationDecisions * 100) : 0}%` }} /></div></div>)}</CardContent></Card>
        <Card className="border-border/70 shadow-sm"><CardHeader><CardTitle className="text-sm">{isRTL ? "إشارات الاختيار النهائي" : "Final-selection signals"}</CardTitle></CardHeader><CardContent><div className="flex flex-wrap gap-2">{(data.selectedSignalUsage || []).map((item) => <Badge key={item.signal} variant="secondary" className="px-3 py-2">{SIGNAL_LABELS[item.signal]?.[isRTL ? 1 : 0] || item.signal} · {item.count}</Badge>)}</div><div className="mt-5 rounded-2xl border bg-muted/20 p-4 text-xs text-muted-foreground">{isRTL ? `متوسط ثقة الترشيح: ${s?.averageRecommendedConfidence ?? "—"} · متوسط ثقة الاختيار: ${s?.averageSelectedConfidence ?? "—"}` : `Avg recommended confidence: ${s?.averageRecommendedConfidence ?? "—"} · Avg selected confidence: ${s?.averageSelectedConfidence ?? "—"}`}</div></CardContent></Card>
      </div>

      <Card className="border-border/70 shadow-sm"><CardHeader><CardTitle className="text-sm">{isRTL ? "اتجاه قرارات المطابقة" : "Matching feedback trend"}</CardTitle></CardHeader><CardContent className="p-0"><div className="overflow-x-auto"><table className="w-full min-w-[650px] text-sm"><thead><tr className="border-y bg-muted/25 text-muted-foreground"><th className="px-4 py-3 text-start">{isRTL ? "التاريخ" : "Date"}</th><th className="px-4 py-3 text-start">{isRTL ? "الإجمالي" : "Total"}</th><th className="px-4 py-3 text-start">{isRTL ? "مقبول" : "Accepted"}</th><th className="px-4 py-3 text-start">{isRTL ? "تجاوز" : "Override"}</th><th className="px-4 py-3 text-start">{isRTL ? "يدوي" : "Manual"}</th><th className="px-4 py-3 text-start">{isRTL ? "القبول" : "Acceptance"}</th></tr></thead><tbody>{trend.map((item) => <tr key={item.date} className="border-b last:border-0"><td className="px-4 py-3 font-mono text-xs">{item.date}</td><td className="px-4 py-3">{item.total}</td><td className="px-4 py-3">{item.accepted}</td><td className="px-4 py-3">{item.overridden}</td><td className="px-4 py-3">{item.manual}</td><td className="px-4 py-3 font-semibold">{percent(item.acceptanceRatePct)}</td></tr>)}{trend.length === 0 && <tr><td colSpan={6} className="px-4 py-10 text-center text-muted-foreground">{isRTL ? "لا توجد قرارات في الفترة." : "No audited decisions in this period."}</td></tr>}</tbody></table></div></CardContent></Card>
    </>}
  </div>;
}
