from pathlib import Path

p = Path("client/src/components/GoogleDriveStoragePoolTab.tsx")
s = p.read_text()

if 'data-storage-visualization="v1"' in s:
    print("PATCH=PASS already-applied")
    raise SystemExit(0)

anchor = '''function bytes(value?: number | null) {
  const n = Number(value || 0);
  if (!n) return "—";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let x = n, i = 0;
  while (x >= 1024 && i < units.length - 1) { x /= 1024; i += 1; }
  return \`${x.toFixed(i > 1 ? 1 : 0)} ${units[i]}\`;
}
'''

helpers = anchor + '''
function percentage(part?: number | null, total?: number | null) {
  const p = Number(part || 0);
  const t = Number(total || 0);
  if (!Number.isFinite(p) || !Number.isFinite(t) || t <= 0) return 0;
  return Math.max(0, Math.min(100, (p / t) * 100));
}

function StorageDonut({ used, free, reserve, isRTL }: { used?: number | null; free?: number | null; reserve?: number | null; isRTL: boolean }) {
  const usedBytes = Math.max(0, Number(used || 0));
  const freeBytes = Math.max(0, Number(free || 0));
  const totalBytes = usedBytes + freeBytes;
  const reserveBytes = Math.min(freeBytes, Math.max(0, Number(reserve || 0)));
  const availableBytes = Math.max(0, freeBytes - reserveBytes);
  const usedPct = percentage(usedBytes, totalBytes);
  const reservePct = percentage(reserveBytes, totalBytes);
  const availablePct = Math.max(0, 100 - usedPct - reservePct);
  const lowSpace = totalBytes > 0 && percentage(availableBytes, totalBytes) <= 10;

  return <div className="flex flex-col items-center gap-4" data-storage-visualization="v1">
    <div className="relative h-44 w-44">
      <svg viewBox="0 0 42 42" className="h-full w-full -rotate-90" role="img" aria-label={isRTL ? "توزيع مساحة التخزين" : "Storage distribution"}>
        <circle cx="21" cy="21" r="15.9155" fill="none" strokeWidth="5" className="text-muted/35" stroke="currentColor" />
        <circle cx="21" cy="21" r="15.9155" fill="none" strokeWidth="5" strokeLinecap="butt" pathLength="100" strokeDasharray={\`${usedPct} ${100-usedPct}\`} strokeDashoffset="0" className="text-primary" stroke="currentColor" />
        <circle cx="21" cy="21" r="15.9155" fill="none" strokeWidth="5" strokeLinecap="butt" pathLength="100" strokeDasharray={\`${reservePct} ${100-reservePct}\`} strokeDashoffset={-usedPct} className="text-amber-500" stroke="currentColor" />
        <circle cx="21" cy="21" r="15.9155" fill="none" strokeWidth="5" strokeLinecap="butt" pathLength="100" strokeDasharray={\`${availablePct} ${100-availablePct}\`} strokeDashoffset={-(usedPct+reservePct)} className="text-emerald-500" stroke="currentColor" />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <div className="text-2xl font-bold tracking-tight">{Math.round(usedPct)}%</div>
        <div className="text-xs text-muted-foreground">{isRTL ? "مستخدم" : "Used"}</div>
      </div>
    </div>
    <div className="grid w-full grid-cols-3 gap-2 text-center text-xs">
      <div className="rounded-lg border bg-muted/20 px-2 py-2"><span className="mx-auto mb-1 block h-2 w-2 rounded-full bg-primary"/><div className="text-muted-foreground">{isRTL?"مستخدم":"Used"}</div><strong>{bytes(usedBytes)}</strong></div>
      <div className="rounded-lg border bg-muted/20 px-2 py-2"><span className="mx-auto mb-1 block h-2 w-2 rounded-full bg-amber-500"/><div className="text-muted-foreground">{isRTL?"محجوز":"Reserved"}</div><strong>{bytes(reserveBytes)}</strong></div>
      <div className="rounded-lg border bg-muted/20 px-2 py-2"><span className="mx-auto mb-1 block h-2 w-2 rounded-full bg-emerald-500"/><div className="text-muted-foreground">{isRTL?"متاح":"Available"}</div><strong>{bytes(availableBytes)}</strong></div>
    </div>
    {lowSpace && <div className="w-full rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs font-medium text-amber-700 dark:text-amber-300">{isRTL ? "المساحة المتاحة أقل من 10%" : "Less than 10% usable space remains"}</div>}
  </div>;
}

function DriveQuotaBar({ quota, isRTL }: { quota?: any; isRTL: boolean }) {
  const total = Math.max(0, Number(quota?.totalBytes || 0));
  const used = Math.max(0, Number(quota?.usedBytes || 0));
  const free = Math.max(0, Number(quota?.freeBytes || 0));
  const reserve = Math.min(free, Math.max(0, Number(quota?.reserveBytes || 0)));
  const available = Math.max(0, free - reserve);
  const usedPct = percentage(used, total);
  const reservePct = percentage(reserve, total);
  if (!total) return <div className="rounded-xl border border-dashed p-3 text-xs text-muted-foreground">{isRTL ? "بيانات المساحة غير متاحة حتى يتم ربط الحساب" : "Storage quota will appear after the Drive is connected"}</div>;
  return <div className="rounded-xl border bg-muted/10 p-3">
    <div className="mb-2 flex items-center justify-between gap-3 text-xs"><span className="font-medium">{isRTL?"استخدام المساحة":"Storage usage"}</span><span className="text-muted-foreground">{Math.round(usedPct)}% · {bytes(used)} / {bytes(total)}</span></div>
    <div className="flex h-2.5 w-full overflow-hidden rounded-full bg-emerald-500/20">
      <div className="h-full bg-primary transition-all" style={{width: \`${usedPct}%\`}} />
      <div className="h-full bg-amber-500 transition-all" style={{width: \`${reservePct}%\`}} />
    </div>
    <div className="mt-2 grid grid-cols-3 gap-2 text-xs">
      <div><span className="text-muted-foreground">{isRTL?"مستخدم":"Used"}</span><div className="font-medium">{bytes(used)}</div></div>
      <div><span className="text-muted-foreground">{isRTL?"محجوز":"Reserved"}</span><div className="font-medium">{bytes(reserve)}</div></div>
      <div><span className="text-muted-foreground">{isRTL?"متاح فعليًا":"Available"}</span><div className="font-medium">{bytes(available)}</div></div>
    </div>
  </div>;
}
'''

if anchor not in s:
    raise SystemExit("PATCH=FAIL helper-anchor")
s = s.replace(anchor, helpers, 1)

old = '''    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-3">
        <CardTitle className="flex items-center gap-2 text-base"><HardDrive size={18}/>{isRTL ? "مجموعة تخزين Google Drive" : "Google Drive Storage Pool"}</CardTitle>
        <Button size="sm" onClick={()=>setAddOpen(true)}><Plus size={14}/>{isRTL ? "إضافة حساب" : "Add Drive"}</Button>
      </CardHeader>
      <CardContent className="grid gap-3 md:grid-cols-5">
        {[
          [isRTL?"الحسابات":"Accounts", summary?.totalAccounts ?? 0],
          [isRTL?"القابلة للكتابة":"Writable", summary?.writableAccounts ?? 0],
          [isRTL?"السعة":"Capacity", bytes(summary?.totalBytes)],
          [isRTL?"المستخدم":"Used", bytes(summary?.usedBytes)],
          [isRTL?"المتاح":"Free", bytes(summary?.freeBytes)],
        ].map(([label,value])=><div key={String(label)} className="rounded-xl border p-3"><p className="text-xs text-muted-foreground">{label}</p><p className="mt-1 font-semibold">{value}</p></div>)}
      </CardContent>
    </Card>
'''

new = '''    <Card className="overflow-hidden">
      <CardHeader className="flex flex-row items-start justify-between gap-3 border-b bg-muted/10">
        <div className="space-y-1">
          <CardTitle className="flex items-center gap-2 text-base"><HardDrive size={18}/>{isRTL ? "مجموعة تخزين Google Drive" : "Google Drive Storage Pool"}</CardTitle>
          <p className="text-xs text-muted-foreground">{isRTL ? "نظرة موحدة على السعة والحسابات المتاحة للكتابة بنظام Priority Fill" : "Unified capacity and writable-account view using Priority Fill"}</p>
        </div>
        <Button size="sm" onClick={()=>setAddOpen(true)}><Plus size={14}/>{isRTL ? "إضافة حساب" : "Add Drive"}</Button>
      </CardHeader>
      <CardContent className="grid gap-6 p-5 lg:grid-cols-[290px_1fr]">
        <StorageDonut
          used={summary?.usedBytes}
          free={summary?.freeBytes}
          reserve={accounts.reduce((sum:any,a:any)=>sum+Number(a?.quota?.reserveBytes||0),0)}
          isRTL={isRTL}
        />
        <div className="grid content-start gap-3 sm:grid-cols-2">
          {[
            [isRTL?"إجمالي الحسابات":"Total drives", summary?.totalAccounts ?? 0],
            [isRTL?"القابلة للكتابة":"Writable", summary?.writableAccounts ?? 0],
            [isRTL?"السعة الكلية":"Total capacity", bytes(summary?.totalBytes)],
            [isRTL?"المساحة الحرة":"Raw free space", bytes(summary?.freeBytes)],
          ].map(([label,value])=><div key={String(label)} className="rounded-xl border bg-card p-4 shadow-sm"><p className="text-xs text-muted-foreground">{label}</p><p className="mt-1 text-lg font-semibold tracking-tight">{value}</p></div>)}
          <div className="sm:col-span-2 rounded-xl border bg-muted/15 p-4">
            <div className="flex items-center justify-between gap-3"><div><p className="text-sm font-medium">{isRTL?"استراتيجية التخزين":"Storage strategy"}</p><p className="mt-1 text-xs text-muted-foreground">{isRTL?"يتم ملء الحساب الأعلى أولوية أولًا ثم الانتقال تلقائيًا عند امتلائه":"Highest-priority writable Drive is filled first, then the pool fails over when capacity is exhausted."}</p></div><Badge variant="secondary">Priority Fill</Badge></div>
          </div>
        </div>
      </CardContent>
    </Card>
'''

if old not in s:
    raise SystemExit("PATCH=FAIL summary-block")
s = s.replace(old, new, 1)

old2 = '''          <div className="grid gap-3 md:grid-cols-5 text-sm">
            <div><span className="text-muted-foreground">{isRTL?"الاتصال":"Connection"}</span><div>{a.settings?.connected ? "Connected" : "Not connected"}</div></div>
            <div><span className="text-muted-foreground">{isRTL?"الحالة":"Storage"}</span><div>{a.settings?.storageReady ? "Ready" : "Blocked"}</div></div>
            <div><span className="text-muted-foreground">{isRTL?"المستخدم":"Used"}</span><div>{bytes(a.quota?.usedBytes)}</div></div>
            <div><span className="text-muted-foreground">{isRTL?"المتاح":"Free"}</span><div>{bytes(a.quota?.freeBytes)}</div></div>
            <div><span className="text-muted-foreground">{isRTL?"المراجع":"References"}</span><div>{a.referenceCount}</div></div>
          </div>
'''

new2 = '''          <div className="grid gap-3 md:grid-cols-4 text-sm">
            <div className="rounded-lg bg-muted/20 p-3"><span className="text-xs text-muted-foreground">{isRTL?"الاتصال":"Connection"}</span><div className="mt-1 font-medium">{a.settings?.connected ? (isRTL?"متصل":"Connected") : (isRTL?"غير متصل":"Not connected")}</div></div>
            <div className="rounded-lg bg-muted/20 p-3"><span className="text-xs text-muted-foreground">{isRTL?"الحالة":"Storage"}</span><div className="mt-1 font-medium">{a.settings?.storageReady ? (isRTL?"جاهز":"Ready") : (isRTL?"محظور":"Blocked")}</div></div>
            <div className="rounded-lg bg-muted/20 p-3"><span className="text-xs text-muted-foreground">{isRTL?"السعة":"Capacity"}</span><div className="mt-1 font-medium">{bytes(a.quota?.totalBytes)}</div></div>
            <div className="rounded-lg bg-muted/20 p-3"><span className="text-xs text-muted-foreground">{isRTL?"المراجع":"References"}</span><div className="mt-1 font-medium">{a.referenceCount}</div></div>
          </div>
          <DriveQuotaBar quota={a.quota} isRTL={isRTL}/>
'''

if old2 not in s:
    raise SystemExit("PATCH=FAIL account-block")
s = s.replace(old2, new2, 1)

p.write_text(s)
print("PATCH=PASS")
