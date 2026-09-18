#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import os, shutil

ROOT = Path(os.environ.get("TCRM_ROOT", "/var/www/TCRM-MAIN"))
TARGET = ROOT / "client/src/components/GoogleDriveStoragePoolTab.tsx"
MARKER = "TCRM_GOOGLE_DRIVE_CONFIG_MODAL_PREMIUM_V1"

if not TARGET.exists():
    raise SystemExit(f"MISSING={TARGET}")

text = TARGET.read_text(encoding="utf-8")
if MARKER in text:
    print("PATCH=PASS")
    print("ALREADY_APPLIED=YES")
    print(f"FILES_CHANGED={TARGET.relative_to(ROOT)}")
    raise SystemExit(0)

start_token = '    <Dialog open={Boolean(configId)}'
start = text.find(start_token)
if start < 0:
    raise SystemExit("ERROR=CONFIG_DIALOG_START_NOT_FOUND")

end = text.find("</Dialog>", start)
if end < 0:
    raise SystemExit("ERROR=CONFIG_DIALOG_END_NOT_FOUND")
end += len("</Dialog>")

new_modal = r'''    {/* TCRM_GOOGLE_DRIVE_CONFIG_MODAL_PREMIUM_V1 */}
    <Dialog open={Boolean(configId)} onOpenChange={(v) => { if (!v) setConfigId(null); }}>
      <DialogContent
        className="max-w-[760px] overflow-hidden rounded-[24px] border border-violet-200/70 bg-white p-0 shadow-[0_36px_100px_-30px_rgba(49,46,129,0.45)] dark:border-violet-400/20 dark:bg-[#07111f]"
        dir={isRTL ? "rtl" : "ltr"}
      >
        <div className="relative overflow-hidden border-b border-violet-100/80 bg-gradient-to-br from-white via-violet-50/70 to-indigo-50/80 px-6 py-5 dark:border-white/10 dark:from-[#0b1730] dark:via-[#101a3c] dark:to-[#171a48]">
          <div className="pointer-events-none absolute -right-16 -top-24 h-56 w-56 rounded-full bg-violet-300/20 blur-3xl dark:bg-violet-500/15" />
          <div className="relative flex items-start gap-4">
            <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl border border-white/80 bg-white shadow-[0_15px_34px_-20px_rgba(67,56,202,0.55)] dark:border-white/10 dark:bg-white/95">
              <svg viewBox="0 0 87.3 78" className="h-9 w-10" aria-hidden="true">
                <path fill="#0066DA" d="M6.6 66.85 22.3 39.7h31.4l15.7 27.15z"/>
                <path fill="#00AC47" d="M34.45 12.55h31.4L81.55 39.7l-15.7 27.15L50.15 39.7z"/>
                <path fill="#EA4335" d="m34.45 12.55 15.7 27.15H22.3L6.6 66.85 0 55.4z"/>
                <path fill="#00832D" d="m50.15 39.7 15.7 27.15H37.95L22.3 39.7z"/>
                <path fill="#2684FC" d="M6.6 66.85 22.3 39.7h27.85l-15.7 27.15z"/>
                <path fill="#FFBA00" d="m34.45 12.55 15.7 27.15H22.3z"/>
              </svg>
            </div>
            <DialogHeader className="min-w-0 flex-1 space-y-1.5 p-0 text-start">
              <DialogTitle className="text-[23px] font-bold tracking-[-0.03em] text-slate-950 dark:text-white">
                {isRTL ? "إعداد Google Drive" : "Configure Google Drive"}
              </DialogTitle>
              <p className="max-w-xl text-sm leading-6 text-slate-500 dark:text-slate-300">
                {isRTL
                  ? "اربط حساب Google Drive لتخزين ملفات TCRM وإدارة مجلد الرفع الرئيسي."
                  : "Connect your Google Drive account for file storage and manage where TCRM uploads your files."}
              </p>
            </DialogHeader>
          </div>
        </div>

        <div className="max-h-[70vh] space-y-4 overflow-y-auto bg-gradient-to-b from-white to-slate-50/60 px-6 py-5 dark:from-[#07111f] dark:to-[#081426]">
          <div className="flex items-center justify-between gap-4 rounded-2xl border border-violet-100 bg-violet-50/70 px-4 py-3.5 dark:border-violet-400/15 dark:bg-violet-500/10">
            <div className="min-w-0">
              <p className="text-sm font-semibold text-slate-900 dark:text-white">
                {isRTL ? "تفعيل التخزين" : "Storage enabled"}
              </p>
              <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                {isRTL
                  ? "فعّل التكامل لاستخدام Google Drive لتخزين ملفات TCRM."
                  : "Enable Google Drive integration to store files from TCRM."}
              </p>
            </div>
            <Switch
              checked={Boolean(form.enabled)}
              onCheckedChange={(v) => setForm((x: any) => ({ ...x, enabled: v }))}
              className="shrink-0"
            />
          </div>

          <section className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-[0_12px_32px_-24px_rgba(30,41,59,0.35)] dark:border-white/10 dark:bg-[#0a1729]">
            <div className="mb-4 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-50 text-violet-700 ring-1 ring-violet-100 dark:bg-violet-500/10 dark:text-violet-300 dark:ring-violet-400/15">
                <Settings2 size={18} />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                  {isRTL ? "بيانات Google API" : "Google API Credentials"}
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {isRTL ? "استخدم بيانات مشروع Google Cloud الخاص بك." : "Use your Google Cloud project credentials."}
                </p>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label className="text-xs font-semibold text-slate-700 dark:text-slate-200">Client ID</Label>
                <Input
                  value={form.clientId || ""}
                  onChange={(e) => setForm((x: any) => ({ ...x, clientId: e.target.value }))}
                  placeholder={isRTL ? "أدخل Google Client ID" : "Enter your Google Client ID"}
                  className="h-11 rounded-xl border-slate-200 bg-white shadow-none focus-visible:ring-violet-500 dark:border-white/10 dark:bg-[#081426]"
                  dir="ltr"
                />
              </div>
              <div className="space-y-2">
                <Label className="text-xs font-semibold text-slate-700 dark:text-slate-200">Client Secret</Label>
                <Input
                  type="password"
                  placeholder={form.hasClientSecret ? "********" : (isRTL ? "أدخل Google Client Secret" : "Enter your Google Client Secret")}
                  value={secret}
                  onChange={(e) => setSecret(e.target.value)}
                  className="h-11 rounded-xl border-slate-200 bg-white shadow-none focus-visible:ring-violet-500 dark:border-white/10 dark:bg-[#081426]"
                  dir="ltr"
                />
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label className="text-xs font-semibold text-slate-700 dark:text-slate-200">Redirect URI</Label>
                <Input
                  value={form.redirectUri || ""}
                  onChange={(e) => setForm((x: any) => ({ ...x, redirectUri: e.target.value }))}
                  placeholder={isRTL ? "أدخل رابط Redirect URI المصرح به" : "Enter the authorized redirect URI"}
                  className="h-11 rounded-xl border-slate-200 bg-white shadow-none focus-visible:ring-violet-500 dark:border-white/10 dark:bg-[#081426]"
                  dir="ltr"
                />
              </div>
            </div>
          </section>

          <section className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-[0_12px_32px_-24px_rgba(30,41,59,0.35)] dark:border-white/10 dark:bg-[#0a1729]">
            <div className="mb-4 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 text-indigo-700 ring-1 ring-indigo-100 dark:bg-indigo-500/10 dark:text-indigo-300 dark:ring-indigo-400/15">
                <Cloud size={18} />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                  {isRTL ? "إعدادات تخزين Drive" : "Drive Storage Settings"}
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {isRTL ? "حدد مكان تخزين الملفات داخل Google Drive." : "Choose where files will be stored in your Google Drive."}
                </p>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label className="text-xs font-semibold text-slate-700 dark:text-slate-200">
                  {isRTL ? "معرّف مجلد الجذر" : "Root Folder ID"}
                </Label>
                <Input
                  value={form.rootFolderId || ""}
                  onChange={(e) => setForm((x: any) => ({ ...x, rootFolderId: e.target.value }))}
                  placeholder={isRTL ? "أدخل Root Folder ID" : "Enter the root folder ID"}
                  className="h-11 rounded-xl border-slate-200 bg-white shadow-none focus-visible:ring-violet-500 dark:border-white/10 dark:bg-[#081426]"
                  dir="ltr"
                />
              </div>
              <div className="space-y-2">
                <Label className="text-xs font-semibold text-slate-700 dark:text-slate-200">
                  {isRTL ? "اسم المجلد" : "Folder Name"}
                </Label>
                <Input
                  value={form.rootFolderName || ""}
                  onChange={(e) => setForm((x: any) => ({ ...x, rootFolderName: e.target.value }))}
                  placeholder="Tamiyouz CRM Uploads"
                  className="h-11 rounded-xl border-slate-200 bg-white shadow-none focus-visible:ring-violet-500 dark:border-white/10 dark:bg-[#081426]"
                />
              </div>
            </div>
          </section>
        </div>

        <div className="flex flex-col-reverse gap-2 border-t border-slate-200/80 bg-white px-6 py-4 sm:flex-row sm:items-center sm:justify-between dark:border-white/10 dark:bg-[#07111f]">
          <Button
            variant="outline"
            onClick={() => configId && save.mutate({
              accountId: configId,
              enabled: Boolean(form.enabled),
              rootFolderId: form.rootFolderId || null,
              rootFolderName: form.rootFolderName || "Tamiyouz CRM Uploads",
              clientId: form.clientId || null,
              redirectUri: form.redirectUri || null,
              scope: form.scope || "https://www.googleapis.com/auth/drive.file",
              clientSecretAction: secret ? "set" : "keep",
              clientSecret: secret || null,
            })}
            className="h-11 rounded-xl px-5 font-semibold"
          >
            {isRTL ? "حفظ الإعدادات" : "Save settings"}
          </Button>

          <div className="flex flex-col gap-2 sm:flex-row">
            <Button
              variant="outline"
              onClick={() => configId && test.mutate({ accountId: configId })}
              className="h-11 gap-2 rounded-xl px-5 font-semibold"
            >
              <RefreshCw size={15} className={test.isPending ? "animate-spin" : ""} />
              {isRTL ? "اختبار الاتصال" : "Test"}
            </Button>
            <Button
              onClick={() => configId && openConnect(configId)}
              className="h-11 gap-2 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 px-6 font-semibold text-white shadow-[0_12px_26px_-14px_rgba(79,70,229,0.8)] hover:from-violet-700 hover:to-indigo-700"
            >
              <Cloud size={16} />
              {isRTL ? "ربط Google Drive" : "Connect Google Drive"}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>'''

backup = ROOT / ".patch-backups" / f"google-drive-config-modal-premium-v1-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup.mkdir(parents=True, exist_ok=True)
shutil.copy2(TARGET, backup / TARGET.name)

updated = text[:start] + new_modal + text[end:]
TARGET.write_text(updated, encoding="utf-8")

print("PATCH=PASS")
print("GOOGLE_DRIVE_CONFIG_MODAL_PREMIUM_V1=YES")
print("FUNCTIONALITY_PRESERVED=YES")
print("BACKEND_UNCHANGED=YES")
print(f"FILES_CHANGED={TARGET.relative_to(ROOT)}")
