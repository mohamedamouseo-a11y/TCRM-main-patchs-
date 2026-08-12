// ZAGHLOUL_V5R1_NATIVE_SWITCHOVER_CORRECTIVE
// @ts-nocheck
import CRMLayout from "@/components/CRMLayout";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useLanguage } from "@/contexts/LanguageContext";
import { trpc } from "@/lib/trpc";
import {
  Bot,
  CheckCircle2,
  MessageSquare,
  RefreshCw,
  Shield,
  TrendingUp,
  Users,
  Zap,
} from "lucide-react";

function EmptyState({ ar, label }: { ar: boolean; label: string }) {
  return (
    <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
      {ar ? `لا توجد ${label} حاليًا` : `No ${label} available`}
    </div>
  );
}

function LoadingState({ ar }: { ar: boolean }) {
  return (
    <div className="flex items-center justify-center gap-2 p-8 text-sm text-muted-foreground">
      <RefreshCw className="h-4 w-4 animate-spin" />
      {ar ? "جار تحميل البيانات..." : "Loading data..."}
    </div>
  );
}

function ErrorState({ ar, message }: { ar: boolean; message?: string }) {
  return (
    <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
      {ar ? "تعذر تحميل البيانات" : "Unable to load data"}
      {message ? `: ${message}` : ""}
    </div>
  );
}

export default function ZaghloulV5Page() {
  const { lang, isRTL } = useLanguage();
  const ar = lang === "ar";

  const healthQ = trpc.zaghloulV5.health.useQuery();
  const featuresQ = trpc.zaghloulV5.features.useQuery();
  const inboxQ = trpc.zaghloulV5.inbox.list.useQuery({ page: 1, pageSize: 20 });
  const contactsQ = trpc.zaghloulV5.contacts.list.useQuery({ page: 1, pageSize: 20 });
  const pipelinesQ = trpc.zaghloulV5.pipelines.list.useQuery();
  const dealsQ = trpc.zaghloulV5.deals.list.useQuery({ page: 1, pageSize: 20 });
  const automationsQ = trpc.zaghloulV5.automations.list.useQuery();

  const healthy = healthQ.data?.status === "healthy";

  return (
    <CRMLayout>
      <div className="flex flex-col gap-6 p-6" dir={isRTL ? "rtl" : "ltr"}>
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-3xl font-black tracking-tight">{ar ? "زغلول" : "Zaghloul"}</h1>
            <p className="mt-1 text-muted-foreground">
              {ar ? "مركز واتساب وإدارة العملاء والأتمتة داخل TCRM" : "WhatsApp, CRM and automation center inside TCRM"}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={healthy ? "default" : "secondary"}>
              {healthy ? (ar ? "متصل" : "Connected") : (ar ? "جار الفحص" : "Checking")}
            </Badge>
            <Badge variant="outline">V5</Badge>
          </div>
        </div>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <CheckCircle2 className="h-5 w-5" />
              {ar ? "حالة التكامل" : "Integration status"}
            </CardTitle>
            <CardDescription>
              {ar ? "يستخدم زغلول خدمات TCRM الحالية بدل إنشاء بنية واتساب موازية." : "Zaghloul reuses existing TCRM services instead of creating a parallel WhatsApp stack."}
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {(featuresQ.data?.features || []).map((feature: any) => (
              <Badge key={feature.id} variant={feature.enabled ? "outline" : "secondary"}>
                {feature.name}
              </Badge>
            ))}
          </CardContent>
        </Card>

        <Tabs defaultValue="inbox" className="w-full">
          <TabsList className="grid h-auto w-full grid-cols-2 gap-1 md:grid-cols-4">
            <TabsTrigger value="inbox" className="gap-2"><MessageSquare className="h-4 w-4" />{ar ? "صندوق الوارد" : "Inbox"}</TabsTrigger>
            <TabsTrigger value="contacts" className="gap-2"><Users className="h-4 w-4" />{ar ? "جهات الاتصال" : "Contacts"}</TabsTrigger>
            <TabsTrigger value="pipelines" className="gap-2"><TrendingUp className="h-4 w-4" />{ar ? "المبيعات" : "Pipelines"}</TabsTrigger>
            <TabsTrigger value="automations" className="gap-2"><Zap className="h-4 w-4" />{ar ? "الأتمتة" : "Automations"}</TabsTrigger>
          </TabsList>

          <TabsContent value="inbox" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle>{ar ? "صندوق الوارد المشترك" : "Shared Inbox"}</CardTitle>
                <CardDescription>
                  {ar ? `${inboxQ.data?.total ?? 0} محادثة — غير مقروء ${inboxQ.data?.counters?.unread ?? 0}` : `${inboxQ.data?.total ?? 0} conversations — ${inboxQ.data?.counters?.unread ?? 0} unread`}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {inboxQ.isLoading ? <LoadingState ar={ar} /> : inboxQ.error ? <ErrorState ar={ar} message={inboxQ.error.message} /> : !inboxQ.data?.items?.length ? <EmptyState ar={ar} label={ar ? "محادثات" : "conversations"} /> : (
                  <div className="divide-y rounded-lg border">
                    {inboxQ.data.items.map((item: any) => (
                      <div key={item.id} className="flex items-center justify-between gap-4 p-4">
                        <div className="min-w-0">
                          <div className="font-medium">{item.contactName || item.phone}</div>
                          <div className="truncate text-sm text-muted-foreground">{item.lastMessage || item.phone}</div>
                        </div>
                        <div className="flex shrink-0 items-center gap-2">
                          {item.unreadCount > 0 && <Badge>{item.unreadCount}</Badge>}
                          <Badge variant="outline">{item.state}</Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="contacts" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle>{ar ? "جهات الاتصال" : "Contacts"}</CardTitle>
                <CardDescription>{ar ? `${contactsQ.data?.total ?? 0} جهة اتصال مرتبطة ببيانات TCRM` : `${contactsQ.data?.total ?? 0} contacts mapped from TCRM`}</CardDescription>
              </CardHeader>
              <CardContent>
                {contactsQ.isLoading ? <LoadingState ar={ar} /> : contactsQ.error ? <ErrorState ar={ar} message={contactsQ.error.message} /> : !contactsQ.data?.items?.length ? <EmptyState ar={ar} label={ar ? "جهات اتصال" : "contacts"} /> : (
                  <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                    {contactsQ.data.items.map((item: any) => (
                      <div key={item.id} className="rounded-lg border p-4">
                        <div className="font-semibold">{item.name}</div>
                        <div className="mt-1 text-sm text-muted-foreground">{item.phone || "—"}</div>
                        {item.email && <div className="truncate text-xs text-muted-foreground">{item.email}</div>}
                        {!!item.tags?.length && <div className="mt-3 flex flex-wrap gap-1">{item.tags.slice(0, 4).map((tag: string) => <Badge key={tag} variant="secondary">{tag}</Badge>)}</div>}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="pipelines" className="mt-4">
            <div className="grid gap-4 xl:grid-cols-[1fr_2fr]">
              <Card>
                <CardHeader><CardTitle>{ar ? "مراحل المبيعات" : "Pipeline stages"}</CardTitle></CardHeader>
                <CardContent>
                  {pipelinesQ.isLoading ? <LoadingState ar={ar} /> : pipelinesQ.error ? <ErrorState ar={ar} message={pipelinesQ.error.message} /> : !pipelinesQ.data?.length ? <EmptyState ar={ar} label={ar ? "مراحل" : "stages"} /> : (
                    <div className="space-y-2">{pipelinesQ.data.map((stage: any) => <div key={stage.id} className="flex items-center justify-between rounded-lg border p-3"><span>{ar ? (stage.nameAr || stage.name) : stage.name}</span><Badge variant="outline">#{stage.order}</Badge></div>)}</div>
                  )}
                </CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle>{ar ? "الصفقات" : "Deals"}</CardTitle><CardDescription>{dealsQ.data?.total ?? 0}</CardDescription></CardHeader>
                <CardContent>
                  {dealsQ.isLoading ? <LoadingState ar={ar} /> : dealsQ.error ? <ErrorState ar={ar} message={dealsQ.error.message} /> : !dealsQ.data?.items?.length ? <EmptyState ar={ar} label={ar ? "صفقات" : "deals"} /> : (
                    <div className="divide-y rounded-lg border">{dealsQ.data.items.map((deal: any) => <div key={deal.id} className="flex items-center justify-between gap-4 p-4"><div><div className="font-medium">{deal.contactName}</div><div className="text-sm text-muted-foreground">{deal.phone}</div></div><div className="text-end"><Badge variant="outline">{deal.status}</Badge>{deal.value != null && <div className="mt-1 text-sm font-semibold">{deal.value} {deal.currency}</div>}</div></div>)}</div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="automations" className="mt-4">
            <Card>
              <CardHeader><CardTitle>{ar ? "الأتمتة" : "Automations"}</CardTitle><CardDescription>{ar ? "الأتمتة المتاحة من تكامل TCRM الحالي" : "Automations exposed by the current TCRM integration"}</CardDescription></CardHeader>
              <CardContent>
                {automationsQ.isLoading ? <LoadingState ar={ar} /> : automationsQ.error ? <ErrorState ar={ar} message={automationsQ.error.message} /> : !automationsQ.data?.items?.length ? <EmptyState ar={ar} label={ar ? "قواعد أتمتة" : "automations"} /> : (
                  <div className="grid gap-3 md:grid-cols-2">{automationsQ.data.items.map((item: any) => <div key={item.id} className="rounded-lg border p-4"><div className="flex items-center justify-between"><span className="font-semibold">{item.name}</span><Badge variant={item.isActive ? "default" : "secondary"}>{item.isActive ? (ar ? "فعال" : "Active") : (ar ? "متوقف" : "Inactive")}</Badge></div>{item.description && <p className="mt-2 text-sm text-muted-foreground">{item.description}</p>}</div>)}</div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        <div className="flex flex-col gap-3 rounded-lg bg-muted/50 p-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <Bot className="h-8 w-8" />
            <div><p className="font-semibold">{ar ? "زغلول V5" : "Zaghloul V5"}</p><p className="text-xs text-muted-foreground">{ar ? "تكامل WACRM مع TCRM" : "WACRM integration with TCRM"}</p></div>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground"><Shield className="h-4 w-4" /><span>{ar ? "محمي بصلاحيات TCRM" : "Protected by TCRM access control"}</span></div>
        </div>
      </div>
    </CRMLayout>
  );
}
