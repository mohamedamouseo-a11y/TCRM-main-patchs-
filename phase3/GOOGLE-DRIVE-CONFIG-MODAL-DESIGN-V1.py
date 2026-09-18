from pathlib import Path
import re

p = Path("client/src/components/GoogleDriveStoragePoolTab.tsx")
s = p.read_text()

MARKER = 'data-config-drive-modal-design="v1"'
if MARKER in s:
    print("PATCH=PASS already-applied")
    raise SystemExit(0)

# Ensure required icon import exists.
m = re.search(r'import \{([^}]+)\} from "lucide-react";', s)
if not m:
    raise SystemExit("PATCH=FAIL lucide-import-not-found")
icons = [x.strip() for x in m.group(1).split(",") if x.strip()]
for icon in ["ExternalLink"]:
    if icon not in icons:
        icons.append(icon)
s = s[:m.start()] + 'import { ' + ", ".join(icons) + ' } from "lucide-react";' + s[m.end():]

start = s.find('<Dialog open={Boolean(configId)}')
if start < 0:
    raise SystemExit("PATCH=FAIL config-dialog-start-not-found")

# The config dialog is the final Dialog before the component closing wrapper.
end_marker = '</Dialog>\n  </div>;\n}'
end = s.find(end_marker, start)
if end < 0:
    raise SystemExit("PATCH=FAIL config-dialog-end-not-found")
end += len('</Dialog>')

new_dialog = r'''<Dialog open={Boolean(configId)} onOpenChange={v=>{if(!v)setConfigId(null)}}>
      <DialogContent
        data-config-drive-modal-design="v1"
        className="overflow-hidden border-border/80 p-0 shadow-2xl sm:max-w-[780px]"
      >
        <div className="flex items-start gap-4 border-b border-border/70 px-7 pb-5 pt-6">
          <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl border border-border/60 bg-muted/40 shadow-sm">
            <svg viewBox="0 0 48 48" className="h-9 w-9" aria-hidden="true">
              <path fill="#0F9D58" d="M16.4 6.5h10.3l10.1 17.4-5.1 8.8L16.4 6.5Z"/>
              <path fill="#F4B400" d="M16.4 6.5 5.9 24.6l5.2 9h20.6L16.4 6.5Z"/>
              <path fill="#4285F4" d="M11.1 33.6h20.6l5.1-8.9H16.3l-5.2 8.9Z"/>
            </svg>
          </div>
          <div className="min-w-0 flex-1 pt-1">
            <DialogHeader className="space-y-1.5 p-0 text-start">
              <DialogTitle className="text-[22px] font-bold tracking-tight">
                {isRTL ? "إعداد Google Drive" : "Configure Google Drive"}
              </DialogTitle>
              <p className="text-sm leading-6 text-muted-foreground">
                {isRTL
                  ? "اربط Google Drive لتفعيل رفع الملفات والتخزين."
                  : "Connect your Google Drive to enable file uploads and storage."}
              </p>
            </DialogHeader>
          </div>
        </div>

        <div className="space-y-5 px-7 py-5">
          <label className="flex w-fit cursor-pointer items-center gap-3 text-sm font-medium">
            <Switch
              checked={Boolean(form.enabled)}
              onCheckedChange={v=>setForm((x:any)=>({...x,enabled:v}))}
            />
            <span>{isRTL ? "تفعيل التخزين" : "Storage enabled"}</span>
          </label>

          <div className="grid gap-5 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="drive-client-id" className="text-sm font-semibold">Client ID</Label>
              <Input
                id="drive-client-id"
                value={form.clientId||""}
                onChange={e=>setForm((x:any)=>({...x,clientId:e.target.value}))}
                placeholder={isRTL ? "أدخل Google Client ID" : "Enter your Google Client ID"}
                className="h-12 rounded-xl border-border/80 bg-background shadow-sm"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="drive-client-secret" className="text-sm font-semibold">Client Secret</Label>
              <Input
                id="drive-client-secret"
                type="password"
                placeholder={form.hasClientSecret ? "••••••••••••" : (isRTL ? "أدخل Google Client Secret" : "Enter your Google Client Secret")}
                value={secret}
                onChange={e=>setSecret(e.target.value)}
                className="h-12 rounded-xl border-border/80 bg-background shadow-sm"
              />
            </div>

            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="drive-redirect-uri" className="text-sm font-semibold">Redirect URI</Label>
              <Input
                id="drive-redirect-uri"
                value={form.redirectUri||""}
                onChange={e=>setForm((x:any)=>({...x,redirectUri:e.target.value}))}
                placeholder={isRTL ? "أدخل Redirect URI من Google Cloud Console" : "Enter redirect URI from Google Cloud Console"}
                className="h-12 rounded-xl border-border/80 bg-background shadow-sm"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="drive-root-folder" className="text-sm font-semibold">
                {isRTL ? "معرّف المجلد الرئيسي" : "Root Folder ID"}
              </Label>
              <Input
                id="drive-root-folder"
                value={form.rootFolderId||""}
                onChange={e=>setForm((x:any)=>({...x,rootFolderId:e.target.value}))}
                placeholder={isRTL ? "اختياري" : "Enter Google Drive folder ID (optional)"}
                className="h-12 rounded-xl border-border/80 bg-background shadow-sm"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="drive-folder-name" className="text-sm font-semibold">
                {isRTL ? "اسم المجلد" : "Folder Name"}
              </Label>
              <Input
                id="drive-folder-name"
                value={form.rootFolderName||""}
                onChange={e=>setForm((x:any)=>({...x,rootFolderName:e.target.value}))}
                placeholder="Tamiyouz CRM Uploads"
                className="h-12 rounded-xl border-border/80 bg-background shadow-sm"
              />
            </div>
          </div>

          <div className="flex flex-col gap-3 rounded-xl border border-blue-200/70 bg-blue-50/80 px-4 py-4 text-sm dark:border-blue-900/60 dark:bg-blue-950/25 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex min-w-0 items-start gap-3">
              <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-blue-300 bg-white text-blue-600 dark:border-blue-800 dark:bg-background">
                <Info className="h-4 w-4" />
              </div>
              <div className="min-w-0">
                <div className="font-semibold text-foreground">
                  {isRTL ? "كيف تحصل على هذه البيانات؟" : "How to get these values?"}
                </div>
                <p className="mt-0.5 leading-5 text-muted-foreground">
                  {isRTL
                    ? "أنشئ مشروعًا في Google Cloud Console، فعّل Google Drive API، ثم أنشئ بيانات OAuth 2.0."
                    : "Create a project in Google Cloud Console, enable Google Drive API, and create OAuth 2.0 credentials."}
                </p>
              </div>
            </div>
            <a
              href="https://console.cloud.google.com/apis/credentials"
              target="_blank"
              rel="noreferrer"
              className="inline-flex shrink-0 items-center gap-1.5 font-semibold text-blue-600 hover:text-blue-700 hover:underline dark:text-blue-400"
            >
              {isRTL ? "عرض الدليل" : "View Guide"} <ExternalLink className="h-4 w-4" />
            </a>
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 border-t border-border/70 bg-muted/10 px-7 py-5">
          <Button
            type="button"
            variant="outline"
            className="h-11 min-w-[108px] rounded-xl px-5 font-semibold"
            disabled={test.isPending || save.isPending}
            onClick={async()=>{
              if(!configId) return;
              try {
                await save.mutateAsync({
                  accountId:configId,
                  enabled:Boolean(form.enabled),
                  rootFolderId:form.rootFolderId||null,
                  rootFolderName:form.rootFolderName||"Tamiyouz CRM Uploads",
                  clientId:form.clientId||null,
                  redirectUri:form.redirectUri||null,
                  scope:form.scope||"https://www.googleapis.com/auth/drive.file",
                  clientSecretAction:secret?"set":"keep",
                  clientSecret:secret||null
                });
                await test.mutateAsync({accountId:configId});
              } catch {}
            }}
          >
            <RefreshCw size={15} className={test.isPending ? "animate-spin" : ""}/>
            {test.isPending ? (isRTL ? "جارٍ الاختبار..." : "Testing...") : (isRTL ? "اختبار" : "Test")}
          </Button>

          <Button
            type="button"
            className="h-11 min-w-[190px] rounded-xl !bg-blue-600 px-6 font-semibold !text-white shadow-md hover:!bg-blue-700 disabled:!bg-blue-400 disabled:!text-white disabled:!opacity-100 dark:!bg-blue-600 dark:hover:!bg-blue-500"
            disabled={
              save.isPending ||
              auth.isPending ||
              !String(form.clientId||"").trim() ||
              !String(form.redirectUri||"").trim() ||
              (!form.hasClientSecret && !secret.trim())
            }
            onClick={async()=>{
              if(!configId) return;
              try {
                await save.mutateAsync({
                  accountId:configId,
                  enabled:Boolean(form.enabled),
                  rootFolderId:form.rootFolderId||null,
                  rootFolderName:form.rootFolderName||"Tamiyouz CRM Uploads",
                  clientId:form.clientId||null,
                  redirectUri:form.redirectUri||null,
                  scope:form.scope||"https://www.googleapis.com/auth/drive.file",
                  clientSecretAction:secret?"set":"keep",
                  clientSecret:secret||null
                });
                await openConnect(configId);
              } catch {}
            }}
          >
            <svg viewBox="0 0 48 48" className="h-5 w-5" aria-hidden="true">
              <path fill="currentColor" d="M16.4 6.5h10.3l10.1 17.4-5.1 8.8L16.4 6.5Z"/>
              <path fill="currentColor" d="M16.4 6.5 5.9 24.6l5.2 9h20.6L16.4 6.5Z" opacity=".8"/>
              <path fill="currentColor" d="M11.1 33.6h20.6l5.1-8.9H16.3l-5.2 8.9Z" opacity=".65"/>
            </svg>
            {save.isPending || auth.isPending
              ? (isRTL ? "جارٍ الربط..." : "Connecting...")
              : (isRTL ? "ربط Google Drive" : "Connect Google Drive")}
          </Button>
        </div>
      </DialogContent>
    </Dialog>'''

s = s[:start] + new_dialog + s[end:]
p.write_text(s)
print("PATCH=PASS")
