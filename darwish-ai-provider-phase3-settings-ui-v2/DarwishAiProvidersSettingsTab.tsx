// @ts-nocheck
import { useEffect, useMemo, useState } from "react";
import { trpc } from "@/lib/trpc";
import { useLanguage } from "@/contexts/LanguageContext";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Bot, BrainCircuit, ChevronDown, KeyRound, Layers3, Plus, Route, Save, ShieldCheck, Trash2 } from "lucide-react";
import { toast } from "sonner";

const EMPTY_PROVIDER = { providerKey:"", displayName:"", adapterType:"", baseUrl:"", enabled:true };

export default function DarwishAiProvidersSettingsTab() {
  const { lang } = useLanguage();
  const ar = lang === "ar";
  const u = trpc.useUtils();
  const q = trpc.darwish.aiProviderSettings.useQuery();
  const stateQ = trpc.darwish.aiProviderSettingsState.useQuery();
  const refresh = () => Promise.all([u.darwish.aiProviderSettings.invalidate(), u.darwish.aiProviderSettingsState.invalidate()]);
  const opts = { onSuccess:async()=>{await refresh();toast.success(ar?"تم الحفظ":"Saved");}, onError:(e:any)=>toast.error(e.message) };

  const saveProvider = trpc.darwish.saveAiProvider.useMutation(opts);
  const deleteProvider = trpc.darwish.deleteAiProvider.useMutation(opts);
  const saveModel = trpc.darwish.saveAiProviderModel.useMutation(opts);
  const deleteModel = trpc.darwish.deleteAiProviderModel.useMutation(opts);
  const setSecret = trpc.darwish.setAiProviderSecret.useMutation(opts);
  const deleteSecret = trpc.darwish.deleteAiProviderSecret.useMutation(opts);
  const savePolicy = trpc.darwish.saveAiRoutingPolicy.useMutation(opts);
  const deletePolicy = trpc.darwish.deleteAiRoutingPolicy.useMutation(opts);
  const saveTarget = trpc.darwish.saveAiRoutingTarget.useMutation(opts);
  const deleteTarget = trpc.darwish.deleteAiRoutingTarget.useMutation(opts);

  const d = q.data ?? { providers:[], models:[], secrets:[], policies:[], targets:[] };
  const [providerId,setProviderId] = useState<number|null>(null);
  const [provider,setProvider] = useState(EMPTY_PROVIDER);
  const [modelKey,setModelKey] = useState(""); const [modelName,setModelName] = useState("");
  const [secretKey,setSecretKey] = useState("api_key"); const [secretValue,setSecretValue] = useState("");
  const [policy,setPolicy] = useState({routeKey:"",displayName:"",selectionStrategy:"priority",maxAttempts:3,timeoutMs:60000,enabled:true});
  const [target,setTarget] = useState({policyId:"",providerId:"",modelId:"",priority:100,weight:1,timeoutMs:""});

  useEffect(()=>{ if(providerId==null && d.providers.length) setProviderId(d.providers[0].id); },[d.providers,providerId]);
  useEffect(()=>{
    const p=d.providers.find((x:any)=>x.id===providerId);
    if(p) setProvider({id:p.id,providerKey:p.providerKey,displayName:p.displayName,adapterType:p.adapterType,baseUrl:p.baseUrl??"",enabled:p.enabled});
  },[d.providers,providerId]);
  const models=d.models.filter((m:any)=>m.providerId===providerId);
  const secrets=d.secrets.filter((s:any)=>s.providerId===providerId);
  const targetModels=d.models.filter((m:any)=>String(m.providerId)===target.providerId && m.enabled);
  const lookup=useMemo(()=>({
    p:new Map(d.providers.map((x:any)=>[x.id,x])),
    m:new Map(d.models.map((x:any)=>[x.id,x])),
    r:new Map(d.policies.map((x:any)=>[x.id,x])),
  }),[d]);

  if(q.isLoading) return <Card><CardContent className="py-12 text-center text-muted-foreground">{ar?"جاري التحميل...":"Loading..."}</CardContent></Card>;
  if(q.error) return <Card><CardContent className="py-12 text-center text-destructive">{q.error.message}</CardContent></Card>;

  const commitProvider=async()=>{
    if(!provider.providerKey.trim()||!provider.displayName.trim()||!provider.adapterType.trim()) return toast.error(ar?"أكمل بيانات المزود":"Complete provider fields");
    const r=await saveProvider.mutateAsync({...provider,baseUrl:provider.baseUrl.trim()||null,config:null});
    setProviderId(Number(r.id));
  };
  const addModel=async()=>{
    if(!providerId||!modelKey.trim()) return;
    await saveModel.mutateAsync({providerId,modelKey:modelKey.trim(),displayName:modelName.trim()||null,enabled:true,config:null});
    setModelKey("");setModelName("");
  };
  const addSecret=async()=>{
    if(!providerId||!secretKey.trim()||!secretValue) return;
    await setSecret.mutateAsync({providerId,secretKey:secretKey.trim(),value:secretValue});
    setSecretValue("");
  };
  const addPolicy=async()=>{
    if(!policy.routeKey.trim()||!policy.displayName.trim()) return;
    await savePolicy.mutateAsync({...policy,config:null});
    setPolicy({routeKey:"",displayName:"",selectionStrategy:"priority",maxAttempts:3,timeoutMs:60000,enabled:true});
  };
  const addTarget=async()=>{
    if(!target.policyId||!target.providerId||!target.modelId) return toast.error(ar?"اختر السياسة والمزود والموديل":"Select policy, provider and model");
    await saveTarget.mutateAsync({
      policyId:Number(target.policyId),providerId:Number(target.providerId),modelId:Number(target.modelId),
      priority:Number(target.priority),weight:Number(target.weight),enabled:true,
      timeoutMs:target.timeoutMs?Number(target.timeoutMs):null,config:null
    });
  };

  return <div className="space-y-5" dir={ar?"rtl":"ltr"}>
    <div className="relative overflow-hidden rounded-[28px] border border-primary/15 bg-gradient-to-br from-primary/10 via-background to-background p-6 shadow-sm">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-md"><BrainCircuit size={22}/></div>
          <div>
            <div className="flex flex-wrap items-center gap-2"><h2 className="text-xl font-bold">{ar?"مزودو درويش AI":"Darwish AI Providers"}</h2><Badge>Phase 3</Badge><Badge variant="outline">{stateQ.data?.status??"settings"}</Badge></div>
            <p className="mt-1 text-sm text-muted-foreground">{ar?"مزودون وموديلات ومفاتيح وتوجيه ديناميكي بدون قوائم ثابتة.":"Dynamic providers, models, secrets and routing with no hardcoded provider catalog."}</p>
          </div>
        </div>
        <div className="flex gap-2"><Badge variant="outline" className="gap-1"><ShieldCheck size={13}/>{ar?"Secrets مشفرة":"Encrypted secrets"}</Badge><Badge variant="outline" className="gap-1"><Route size={13}/>Routing</Badge></div>
      </div>
    </div>

    <div className="grid gap-5 xl:grid-cols-[320px_1fr]">
      <Card className="rounded-[24px]">
        <CardHeader className="border-b pb-4"><div className="flex items-center justify-between"><CardTitle className="flex items-center gap-2 text-base"><Bot size={16}/>{ar?"المزودون":"Providers"}</CardTitle><Button size="sm" variant="outline" onClick={()=>{setProviderId(null);setProvider(EMPTY_PROVIDER);}}><Plus size={14}/></Button></div></CardHeader>
        <CardContent className="space-y-2 p-3">
          {d.providers.length===0?<div className="rounded-2xl border border-dashed p-6 text-center text-sm text-muted-foreground">{ar?"لا يوجد مزودون":"No providers yet"}</div>:d.providers.map((p:any)=>
            <button key={p.id} onClick={()=>setProviderId(p.id)} className={`w-full rounded-2xl border p-3 text-start ${providerId===p.id?"border-primary/30 bg-primary/10":"border-transparent bg-muted/25 hover:bg-muted/45"}`}>
              <div className="flex justify-between gap-2"><div className="min-w-0"><p className="truncate text-sm font-semibold">{p.displayName}</p><p className="truncate font-mono text-[10px] text-muted-foreground">{p.providerKey}</p></div><span className={`mt-1 h-2.5 w-2.5 rounded-full ${p.enabled?"bg-emerald-500":"bg-muted-foreground/40"}`}/></div>
              <div className="mt-2 flex gap-2"><Badge variant="secondary" className="text-[10px]">{p.adapterType}</Badge><span className="text-[10px] text-muted-foreground">{d.models.filter((m:any)=>m.providerId===p.id).length} models</span></div>
            </button>)}
        </CardContent>
      </Card>

      <div className="space-y-5">
        <Card className="rounded-[24px]">
          <CardHeader><CardTitle className="text-base">{provider.id?(ar?"إعدادات المزود":"Provider settings"):(ar?"إضافة مزود":"Add provider")}</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 md:grid-cols-2">
              <F l="Provider Key"><Input value={provider.providerKey} onChange={e=>setProvider({...provider,providerKey:e.target.value})} placeholder="company.endpoint" dir="ltr"/></F>
              <F l={ar?"اسم العرض":"Display name"}><Input value={provider.displayName} onChange={e=>setProvider({...provider,displayName:e.target.value})}/></F>
              <F l="Adapter Type"><Input value={provider.adapterType} onChange={e=>setProvider({...provider,adapterType:e.target.value})} placeholder="openai-compatible" dir="ltr"/></F>
              <F l="Base URL"><Input value={provider.baseUrl} onChange={e=>setProvider({...provider,baseUrl:e.target.value})} placeholder="https://..." dir="ltr"/></F>
            </div>
            <div className="flex flex-wrap items-center justify-between gap-3 border-t pt-4"><div className="flex items-center gap-2"><Switch checked={provider.enabled} onCheckedChange={v=>setProvider({...provider,enabled:v})}/><Label>{ar?"نشط":"Enabled"}</Label></div><div className="flex gap-2">
              {provider.id?<Button variant="outline" className="text-destructive" onClick={async()=>{if(confirm(ar?"حذف المزود؟":"Delete provider?")){await deleteProvider.mutateAsync({id:provider.id});setProviderId(null);setProvider(EMPTY_PROVIDER);}}}><Trash2 size={14}/></Button>:null}
              <Button onClick={commitProvider} className="gap-1"><Save size={14}/>{ar?"حفظ":"Save"}</Button>
            </div></div>
          </CardContent>
        </Card>

        {providerId?<div className="grid gap-5 lg:grid-cols-2">
          <Card className="rounded-[24px]"><CardHeader><CardTitle className="flex items-center gap-2 text-base"><Layers3 size={16}/>{ar?"الموديلات":"Models"}</CardTitle></CardHeader><CardContent className="space-y-3">
            <div className="grid gap-2 sm:grid-cols-2"><Input value={modelKey} onChange={e=>setModelKey(e.target.value)} placeholder="model-key" dir="ltr"/><Input value={modelName} onChange={e=>setModelName(e.target.value)} placeholder={ar?"اسم اختياري":"Optional name"}/></div><Button size="sm" variant="outline" onClick={addModel}><Plus size={14}/>{ar?"إضافة":"Add"}</Button>
            {models.map((m:any)=><div key={m.id} className="flex items-center justify-between rounded-xl border px-3 py-2"><div><p className="text-sm font-medium">{m.displayName||m.modelKey}</p><p className="font-mono text-[10px] text-muted-foreground">{m.modelKey}</p></div><Button size="icon" variant="ghost" className="text-destructive" onClick={()=>deleteModel.mutate({id:m.id})}><Trash2 size={14}/></Button></div>)}
          </CardContent></Card>
          <Card className="rounded-[24px]"><CardHeader><CardTitle className="flex items-center gap-2 text-base"><KeyRound size={16}/>{ar?"Secrets":"Secrets"}</CardTitle></CardHeader><CardContent className="space-y-3">
            <p className="text-xs text-muted-foreground">{ar?"القيمة لا تُعرض مرة أخرى؛ الواجهة تعرض metadata فقط.":"Values are never read back; only configured metadata is shown."}</p>
            <div className="grid gap-2 sm:grid-cols-2"><Input value={secretKey} onChange={e=>setSecretKey(e.target.value)} dir="ltr"/><Input type="password" value={secretValue} onChange={e=>setSecretValue(e.target.value)} autoComplete="new-password" placeholder="••••••••" dir="ltr"/></div><Button size="sm" variant="outline" onClick={addSecret}><ShieldCheck size={14}/>{ar?"حفظ مشفر":"Save encrypted"}</Button>
            {secrets.map((s:any)=><div key={s.id} className="flex items-center justify-between rounded-xl border px-3 py-2"><div><p className="font-mono text-xs">{s.secretKey}</p><p className="text-[10px] text-muted-foreground">{s.keyVersion}</p></div><Button size="icon" variant="ghost" className="text-destructive" onClick={()=>deleteSecret.mutate({providerId,secretKey:s.secretKey})}><Trash2 size={14}/></Button></div>)}
          </CardContent></Card>
        </div>:null}
      </div>
    </div>

    <details className="group overflow-hidden rounded-[24px] border bg-background shadow-sm">
      <summary className="flex cursor-pointer list-none items-center justify-between p-5"><div className="flex items-center gap-3"><div className="rounded-xl bg-primary/10 p-2 text-primary"><Route size={18}/></div><div><p className="font-semibold">{ar?"متقدم — Routing & Fallback":"Advanced — Routing & Fallback"}</p><p className="text-xs text-muted-foreground">{ar?"مغلق افتراضياً لتبسيط الإعدادات.":"Collapsed by default to keep basic setup simple."}</p></div></div><ChevronDown className="transition group-open:rotate-180" size={18}/></summary>
      <div className="grid gap-5 border-t p-5 xl:grid-cols-2">
        <Card className="shadow-none"><CardHeader><CardTitle className="text-sm">{ar?"السياسات":"Policies"}</CardTitle></CardHeader><CardContent className="space-y-3">
          <div className="grid gap-2 md:grid-cols-2"><Input value={policy.routeKey} onChange={e=>setPolicy({...policy,routeKey:e.target.value})} placeholder="darwish.default" dir="ltr"/><Input value={policy.displayName} onChange={e=>setPolicy({...policy,displayName:e.target.value})} placeholder={ar?"اسم السياسة":"Policy name"}/>
            <Select value={policy.selectionStrategy} onValueChange={v=>setPolicy({...policy,selectionStrategy:v})}><SelectTrigger><SelectValue/></SelectTrigger><SelectContent><SelectItem value="priority">priority</SelectItem><SelectItem value="weighted_random">weighted_random</SelectItem></SelectContent></Select>
            <div className="grid grid-cols-2 gap-2"><Input type="number" value={policy.maxAttempts} onChange={e=>setPolicy({...policy,maxAttempts:Number(e.target.value)})}/><Input type="number" value={policy.timeoutMs} onChange={e=>setPolicy({...policy,timeoutMs:Number(e.target.value)})}/></div>
          </div><Button size="sm" variant="outline" onClick={addPolicy}><Plus size={14}/>{ar?"إضافة سياسة":"Add policy"}</Button>
          {d.policies.map((r:any)=><div key={r.id} className="flex items-center justify-between rounded-xl border px-3 py-2"><div><p className="text-sm font-medium">{r.displayName}</p><p className="font-mono text-[10px] text-muted-foreground">{r.routeKey} · {r.selectionStrategy}</p></div><Button size="icon" variant="ghost" className="text-destructive" onClick={()=>deletePolicy.mutate({id:r.id})}><Trash2 size={14}/></Button></div>)}
        </CardContent></Card>

        <Card className="shadow-none"><CardHeader><CardTitle className="text-sm">{ar?"Fallback Targets":"Fallback Targets"}</CardTitle></CardHeader><CardContent className="space-y-3">
          <div className="grid gap-2 md:grid-cols-2">
            <S value={target.policyId} set={v=>setTarget({...target,policyId:v})} placeholder={ar?"السياسة":"Policy"} items={d.policies.map((x:any)=>[String(x.id),x.displayName])}/>
            <S value={target.providerId} set={v=>setTarget({...target,providerId:v,modelId:""})} placeholder={ar?"المزود":"Provider"} items={d.providers.filter((x:any)=>x.enabled).map((x:any)=>[String(x.id),x.displayName])}/>
            <S value={target.modelId} set={v=>setTarget({...target,modelId:v})} placeholder={ar?"الموديل":"Model"} items={targetModels.map((x:any)=>[String(x.id),x.displayName||x.modelKey])}/>
            <div className="grid grid-cols-3 gap-2"><Input type="number" value={target.priority} onChange={e=>setTarget({...target,priority:Number(e.target.value)})}/><Input type="number" value={target.weight} onChange={e=>setTarget({...target,weight:Number(e.target.value)})}/><Input type="number" value={target.timeoutMs} onChange={e=>setTarget({...target,timeoutMs:e.target.value})} placeholder="ms"/></div>
          </div><Button size="sm" variant="outline" onClick={addTarget}><Plus size={14}/>{ar?"إضافة Target":"Add target"}</Button>
          {d.targets.map((t:any)=>{const p:any=lookup.p.get(t.providerId),m:any=lookup.m.get(t.modelId),r:any=lookup.r.get(t.policyId);return <div key={t.id} className="flex items-center justify-between rounded-xl border px-3 py-2"><div><p className="text-sm font-medium">{r?.displayName||`#${t.policyId}`}</p><p className="text-[10px] text-muted-foreground">{p?.displayName} → {m?.displayName||m?.modelKey} · P{t.priority} · W{t.weight}</p></div><Button size="icon" variant="ghost" className="text-destructive" onClick={()=>deleteTarget.mutate({id:t.id})}><Trash2 size={14}/></Button></div>})}
        </CardContent></Card>
      </div>
    </details>

    <p className="text-xs text-muted-foreground">{ar?"Phase 3 إعدادات فقط؛ تحويل مكالمات درويش الفعلية للـGateway يتم في Phase 4.":"Phase 3 is configuration only; Darwish runtime rewiring is Phase 4."}</p>
  </div>;
}
function F({l,children}:any){return <div className="space-y-1.5"><Label className="text-xs text-muted-foreground">{l}</Label>{children}</div>}
function S({value,set,placeholder,items}:any){return <Select value={value||undefined} onValueChange={set}><SelectTrigger><SelectValue placeholder={placeholder}/></SelectTrigger><SelectContent>{items.map(([v,l]:any)=><SelectItem key={v} value={v}>{l}</SelectItem>)}</SelectContent></Select>}
