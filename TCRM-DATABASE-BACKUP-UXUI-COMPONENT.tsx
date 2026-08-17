import { useEffect, useState } from "react";
import { Archive, CheckCircle2, Cloud, Database, ExternalLink, KeyRound, Link2, Loader2, Play, Save, ShieldCheck, Unplug } from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { useLanguage } from "@/contexts/LanguageContext";
import { cn } from "@/lib/utils";

const BASE="/admin/database-backup";
async function api(path:string,init:RequestInit={}){const r=await fetch(BASE+path,{credentials:"same-origin",headers:{"Content-Type":"application/json"},...init});const j=await r.json().catch(()=>({}));if(!r.ok)throw Error(j.error||`HTTP ${r.status}`);return j}
const date=(v?:string|null)=>v?new Date(v).toLocaleString():"—";
const size=(v?:string|number)=>{let n=Number(v||0);if(!n)return"—";const u=["B","KB","MB","GB"];let i=0;while(n>=1024&&i<u.length-1){n/=1024;i++}return`${n.toFixed(i?1:0)} ${u[i]}`};

export default function DatabaseBackupSettingsTab(){
  const {isRTL}=useLanguage(); const t=(ar:string,en:string)=>isRTL?ar:en;
  const [data,setData]=useState<any>(null),[loading,setLoading]=useState(true),[busy,setBusy]=useState(""),[msg,setMsg]=useState(""),[editSecret,setEditSecret]=useState(false);
  const [f,setF]=useState({enabled:false,scheduleTime:"02:00",timeZone:"Africa/Cairo",clientId:"",clientSecret:"",redirectUri:"",folderName:"TCRM Database Backups",folderId:""});
  const load=async()=>{try{const x=await api("/status");setData(x);const g=x.config?.googleDrive||{};setF(v=>({...v,enabled:!!x.config?.enabled,scheduleTime:x.config?.scheduleTime||"02:00",timeZone:x.config?.timeZone||"Africa/Cairo",clientId:g.clientId||"",clientSecret:"",redirectUri:g.redirectUri||`${location.origin}${BASE}/google-drive/callback`,folderName:g.folderName||"TCRM Database Backups",folderId:g.folderId||""}));setEditSecret(false)}catch(e:any){toast.error(e.message)}finally{setLoading(false)}};
  useEffect(()=>{load()},[]);
  const save=async()=>{setBusy("save");setMsg("");try{await api("/settings",{method:"PUT",body:JSON.stringify({enabled:f.enabled,scheduleTime:f.scheduleTime,timeZone:f.timeZone,googleDrive:{clientId:f.clientId.trim(),clientSecret:editSecret?f.clientSecret:"",updateClientSecret:editSecret,redirectUri:f.redirectUri.trim(),folderName:f.folderName.trim(),folderId:f.folderId.trim()}})});toast.success(t("تم الحفظ","Settings saved"));await load()}catch(e:any){setMsg(e.message)}finally{setBusy("")}};
  const connect=async()=>{setBusy("connect");try{const x=await api("/google-drive/auth-url");location.href=x.url}catch(e:any){setMsg(e.message);setBusy("")}};
  const disconnect=async()=>{if(!confirm(t("فصل Google Drive؟","Disconnect Google Drive?")))return;setBusy("disconnect");try{await api("/google-drive/disconnect",{method:"DELETE"});await load()}catch(e:any){setMsg(e.message)}finally{setBusy("")}};
  const backup=async()=>{if(!confirm(t("إنشاء نسخة مشفرة الآن؟","Create encrypted backup now?")))return;setBusy("backup");setMsg(t("جاري إنشاء النسخة...","Backup running..."));try{await api("/backup-now",{method:"POST"});setMsg("");toast.success(t("اكتمل النسخ","Backup completed"));await load()}catch(e:any){setMsg(e.message)}finally{setBusy("")}};
  if(loading)return <Card className="rounded-2xl"><CardContent className="flex min-h-52 items-center justify-center text-muted-foreground"><Loader2 className="me-2 h-5 w-5 animate-spin"/>{t("جاري التحميل...","Loading backup settings...")}</CardContent></Card>;

  const c=data?.config||{},s=data?.state||{},g=c.googleDrive||{},backups=data?.backups||[],connected=!!(g.connected||g.accountEmail),retention=data?.retentionCount||3;
  return <div className="space-y-4" dir={isRTL?"rtl":"ltr"}>
    <Card className="rounded-2xl border-border/70 shadow-sm"><CardContent className="p-5">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="flex items-start gap-3"><div className="rounded-xl bg-primary/10 p-3 text-primary"><Database className="h-5 w-5"/></div><div><h2 className="text-xl font-bold">{t("نسخ قاعدة البيانات","Database Backup")}</h2><p className="mt-1 text-sm text-muted-foreground">{t("نسخ MySQL مشفرة إلى Google Drive مع تشغيل تلقائي.","Encrypted MySQL backups to Google Drive with daily automation.")}</p></div></div>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          <Stat icon={<ShieldCheck/>} label={t("التشفير","Encryption")} value={c.encryptionReady?t("جاهز","Ready"):t("غير جاهز","Not ready")} ok={!!c.encryptionReady}/>
          <Stat icon={<Cloud/>} label="Google Drive" value={connected?t("متصل","Connected"):t("غير متصل","Disconnected")} ok={connected}/>
          <Stat icon={<Archive/>} label={t("النسخ","Backups")} value={`${backups.length}/${retention}`} ok={backups.length>0}/>
          <Stat icon={<CheckCircle2/>} label={t("آخر نجاح","Last success")} value={s.lastSuccessAt?new Date(s.lastSuccessAt).toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"}):"—"} ok={!!s.lastSuccessAt}/>
        </div>
      </div>
    </CardContent></Card>

    <Card className="rounded-2xl border-border/70 shadow-sm"><CardHeader><CardTitle className="text-base">{t("جدول النسخ الاحتياطي","Backup Schedule")}</CardTitle></CardHeader><CardContent className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Field label={t("النسخ التلقائي","Automatic Backup")}><div className="flex h-11 items-center justify-between rounded-xl border px-3"><span className="text-sm text-muted-foreground">{f.enabled?t("مفعّل","Enabled"):t("متوقف","Disabled")}</span><Switch checked={f.enabled} onCheckedChange={v=>setF(x=>({...x,enabled:v}))}/></div></Field>
        <Field label={t("الوقت اليومي","Daily Time")}><Input className="h-11 rounded-xl" type="time" value={f.scheduleTime} onChange={e=>setF(x=>({...x,scheduleTime:e.target.value}))}/></Field>
        <Field label={t("المنطقة الزمنية","Time Zone")}><Input className="h-11 rounded-xl" value={f.timeZone} onChange={e=>setF(x=>({...x,timeZone:e.target.value}))}/></Field>
        <Field label={t("الاحتفاظ","Retention")}><Input className="h-11 rounded-xl bg-muted/30" readOnly value={t(`أحدث ${retention} نسخ`,`Latest ${retention} backups`)}/></Field>
      </div>
      <div className="grid gap-3 md:grid-cols-3"><Info label={t("التشفير","Encryption")} value={c.encryptionReady?t("جاهز","READY"):t("غير مهيأ","NOT CONFIGURED")} ok={!!c.encryptionReady}/><Info label={t("آخر نجاح","Last success")} value={date(s.lastSuccessAt)} ok={!!s.lastSuccessAt}/><Info label={t("آخر خطأ","Last error")} value={s.lastError||"—"} ok={!s.lastError}/></div>
    </CardContent></Card>

    <Card className="rounded-2xl border-border/70 shadow-sm"><CardHeader><CardTitle className="text-base">{t("Google Drive المخصص","Dedicated Google Drive")}</CardTitle></CardHeader><CardContent className="space-y-4">
      <div className="grid gap-4 lg:grid-cols-3">
        <Field label="Client ID"><Input className="h-11 rounded-xl" autoComplete="off" value={f.clientId} onChange={e=>setF(x=>({...x,clientId:e.target.value}))}/></Field>
        <Field label="Client Secret"><div className="flex gap-2"><Input className="h-11 min-w-0 rounded-xl" type="password" readOnly={!editSecret} autoComplete="new-password" placeholder={t("محفوظ بأمان","Stored securely")} value={f.clientSecret} onChange={e=>setF(x=>({...x,clientSecret:e.target.value}))}/><Button type="button" variant="outline" className="h-11 rounded-xl" onClick={()=>{setEditSecret(true);setF(x=>({...x,clientSecret:""}))}}><KeyRound className="me-1 h-4 w-4"/>{t("تغيير","Change")}</Button></div></Field>
        <Field label="OAuth Redirect URI"><Input className="h-11 rounded-xl" value={f.redirectUri} onChange={e=>setF(x=>({...x,redirectUri:e.target.value}))}/></Field>
        <Field label={t("اسم المجلد","Folder Name")}><Input className="h-11 rounded-xl" value={f.folderName} onChange={e=>setF(x=>({...x,folderName:e.target.value}))}/></Field>
        <Field label={t("Folder ID (اختياري)","Folder ID (optional)")}><Input className="h-11 rounded-xl" value={f.folderId} onChange={e=>setF(x=>({...x,folderId:e.target.value}))}/></Field>
        <Field label={t("الحساب المتصل","Connected Account")}><Input className="h-11 rounded-xl bg-muted/30" readOnly value={g.accountEmail||t("غير متصل","Not connected")}/></Field>
      </div>
      <div className="flex flex-wrap gap-2">
        <Button className="rounded-xl" disabled={!!busy} onClick={save}>{busy==="save"?<Loader2 className="me-2 h-4 w-4 animate-spin"/>:<Save className="me-2 h-4 w-4"/>}{t("حفظ","Save")}</Button>
        <Button variant="outline" className="rounded-xl text-primary" disabled={!!busy} onClick={connect}>{busy==="connect"?<Loader2 className="me-2 h-4 w-4 animate-spin"/>:<Link2 className="me-2 h-4 w-4"/>}{t("ربط / إعادة ربط","Connect / Reconnect")}</Button>
        <Button variant="outline" className="rounded-xl text-destructive" disabled={!!busy||!connected} onClick={disconnect}>{busy==="disconnect"?<Loader2 className="me-2 h-4 w-4 animate-spin"/>:<Unplug className="me-2 h-4 w-4"/>}{t("فصل","Disconnect")}</Button>
        <Button className="rounded-xl" disabled={!!busy||!connected} onClick={backup}>{busy==="backup"?<Loader2 className="me-2 h-4 w-4 animate-spin"/>:<Play className="me-2 h-4 w-4"/>}{t("نسخ الآن","Backup Now")}</Button>
      </div>
      {msg&&<div className="rounded-xl border bg-muted/20 px-3 py-2 text-sm text-muted-foreground">{msg}</div>}
    </CardContent></Card>

    <Card className="rounded-2xl border-border/70 shadow-sm"><CardHeader><div className="flex items-center justify-between"><CardTitle className="text-base">{t("أحدث النسخ","Latest backups")}</CardTitle><Badge variant="secondary">{backups.length}/{retention}</Badge></div></CardHeader><CardContent className="p-0">
      <div className="overflow-x-auto"><table className="w-full min-w-[700px] text-sm"><thead><tr className="border-y bg-muted/20 text-muted-foreground"><th className="px-5 py-3 text-start">{t("الاسم","Name")}</th><th className="px-5 py-3 text-start">{t("الإنشاء","Created")}</th><th className="px-5 py-3 text-start">{t("الحجم","Size")}</th><th className="px-5 py-3 text-start">{t("الحالة","Status")}</th><th className="px-5 py-3 text-start">{t("الإجراء","Action")}</th></tr></thead><tbody>
        {backups.length?backups.map((b:any,i:number)=><tr key={b.id||b.name||i} className="border-b last:border-0"><td className="max-w-[350px] px-5 py-3 font-medium"><span className="block truncate">{b.name||"—"}</span></td><td className="px-5 py-3 text-muted-foreground">{date(b.createdTime)}</td><td className="px-5 py-3 text-muted-foreground">{size(b.size)}</td><td className="px-5 py-3"><Badge className="border-0 bg-emerald-500/10 text-emerald-700">{t("محفوظ","Stored")}</Badge></td><td className="px-5 py-3">{b.webViewLink?<a className="inline-flex items-center gap-1 text-primary hover:underline" href={b.webViewLink} target="_blank" rel="noreferrer"><ExternalLink className="h-3.5 w-3.5"/>{t("فتح","Open")}</a>:"—"}</td></tr>):<tr><td colSpan={5} className="px-5 py-10 text-center text-muted-foreground">{t("لا توجد نسخ حتى الآن","No backups yet")}</td></tr>}
      </tbody></table></div>
    </CardContent></Card>
  </div>
}
function Field({label,children}:{label:string,children:any}){return <div className="space-y-2"><Label>{label}</Label>{children}</div>}
function Stat({icon,label,value,ok}:{icon:any,label:string,value:string,ok:boolean}){return <div className="min-w-0 rounded-xl border bg-muted/10 px-3 py-2"><div className="flex items-center gap-1 text-[11px] text-muted-foreground">{icon&&<span className="[&>svg]:h-3.5 [&>svg]:w-3.5">{icon}</span>}{label}</div><div className={cn("mt-1 truncate text-sm font-semibold",ok&&"text-emerald-700")}>{value}</div></div>}
function Info({label,value,ok}:{label:string,value:string,ok:boolean}){return <div className="rounded-xl border bg-muted/10 px-4 py-3"><div className="text-xs text-muted-foreground">{label}</div><div className={cn("mt-1 break-words text-sm font-medium",!ok&&"text-destructive")}>{value}</div></div>}
