from pathlib import Path
import re

p = Path("client/src/components/GoogleDriveStoragePoolTab.tsx")
s = p.read_text()

MARKER = 'data-add-drive-modal-design="v4"'
if MARKER in s:
    print("PATCH=PASS already-applied")
    raise SystemExit(0)

icon_import = re.search(r'import \{([^}]+)\} from "lucide-react";', s)
if not icon_import:
    raise SystemExit("PATCH=FAIL lucide-import-not-found")

icons = [x.strip() for x in icon_import.group(1).split(",") if x.strip()]
for icon in ["Info", "UserRound"]:
    if icon not in icons:
        icons.append(icon)
s = s[:icon_import.start()] + 'import { ' + ", ".join(icons) + ' } from "lucide-react";' + s[icon_import.end():]

start = s.find('<Dialog open={addOpen}')
next_dialog = s.find('<Dialog open={Boolean(configId)}', start)
if start < 0 or next_dialog < 0:
    raise SystemExit("PATCH=FAIL add-dialog-boundary-not-found")

new_dialog = r'''<Dialog open={addOpen} onOpenChange={setAddOpen}>
      <DialogContent data-add-drive-modal-design="v4" className="overflow-hidden border-border/80 p-0 shadow-2xl sm:max-w-[620px]">
        <form
          onSubmit={(event) => {
            event.preventDefault();
            const name = newName.trim();
            if (name.length < 2 || add.isPending) return;
            add.mutate({ name, priority: Math.max(1, Number(newPriority) || nextPriority) });
          }}
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
                  {isRTL ? "إضافة حساب تخزين جديد" : "Add New Storage Account"}
                </DialogTitle>
                <p className="text-sm leading-6 text-muted-foreground">
                  {isRTL
                    ? "أضف حساب Google Drive إضافيًا إلى مجموعة التخزين"
                    : "Add an additional Google Drive account to the storage pool"}
                </p>
              </DialogHeader>
            </div>
          </div>

          <div className="space-y-6 px-7 py-6">
            <div className="space-y-2">
              <Label htmlFor="google-drive-account-name" className="text-sm font-semibold">
                {isRTL ? "اسم الحساب" : "Account Name"} <span className="text-destructive">*</span>
              </Label>
              <div className="relative">
                <UserRound className={`absolute top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground ${isRTL ? "right-4" : "left-4"}`} />
                <Input
                  id="google-drive-account-name"
                  autoFocus
                  value={newName}
                  onChange={(event) => setNewName(event.target.value)}
                  placeholder={isRTL ? "مثال: Google Drive 2" : "e.g. Google Drive 2"}
                  className={`h-12 rounded-xl border-border/80 bg-background text-[15px] shadow-sm focus-visible:ring-2 ${isRTL ? "pr-12" : "pl-12"}`}
                />
              </div>
              {newName.length > 0 && newName.trim().length < 2 && (
                <p className="text-xs font-medium text-destructive">
                  {isRTL ? "اكتب اسمًا مكوّنًا من حرفين على الأقل" : "Enter at least 2 characters"}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between gap-4">
                <Label htmlFor="google-drive-priority" className="text-sm font-semibold">
                  {isRTL ? "الأولوية" : "Priority"} <span className="text-destructive">*</span>
                </Label>
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <Info className="h-4 w-4" />
                  <span>{isRTL ? "الرقم الأقل = أولوية أعلى" : "Lower number = higher priority"}</span>
                </div>
              </div>
              <Input
                id="google-drive-priority"
                type="number"
                min={1}
                max={9999}
                value={newPriority}
                onChange={(event) => setNewPriority(event.target.value)}
                className="h-12 rounded-xl border-border/80 bg-background text-[15px] shadow-sm"
              />
            </div>

            <div className="flex items-start gap-3 rounded-xl border border-primary/15 bg-primary/[0.06] px-4 py-3.5 text-sm text-muted-foreground">
              <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-primary/30 bg-background text-primary">
                <Info className="h-4 w-4" />
              </div>
              <p className="leading-6">
                {isRTL
                  ? "الحساب الأساسي يستخدم الأولوية 1. الملفات الجديدة ستستخدم حساب Google Drive التالي المتاح والقابل للكتابة حسب ترتيب الأولوية."
                  : "The primary drive uses priority 1. New uploads will use the next available writable drive by priority."}
              </p>
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 border-t border-border/70 bg-muted/10 px-7 py-5">
            <Button
              type="button"
              variant="outline"
              className="h-11 min-w-[108px] rounded-xl px-5 font-semibold"
              onClick={() => setAddOpen(false)}
              disabled={add.isPending}
            >
              {isRTL ? "إلغاء" : "Cancel"}
            </Button>
            <Button
              type="submit"
              className="h-11 min-w-[132px] rounded-xl bg-primary px-6 font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 disabled:bg-primary/45 disabled:text-primary-foreground disabled:opacity-100"
              disabled={newName.trim().length < 2 || add.isPending}
            >
              {add.isPending
                ? (isRTL ? "جارٍ الإضافة..." : "Adding...")
                : (isRTL ? "إضافة الحساب" : "Add Drive")}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>

    '''

s = s[:start] + new_dialog + s[next_dialog:]
p.write_text(s)
print("PATCH=PASS")
