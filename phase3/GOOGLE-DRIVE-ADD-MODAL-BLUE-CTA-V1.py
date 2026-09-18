from pathlib import Path

p = Path("client/src/components/GoogleDriveStoragePoolTab.tsx")
s = p.read_text()

old = 'className="h-11 min-w-[132px] rounded-xl bg-primary px-6 font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 disabled:bg-primary/45 disabled:text-primary-foreground disabled:opacity-100"'
new = 'className="h-11 min-w-[132px] rounded-xl bg-blue-600 px-6 font-semibold text-white shadow-sm hover:bg-blue-700 focus-visible:ring-blue-500 disabled:bg-blue-300 disabled:text-white disabled:opacity-100 dark:bg-blue-600 dark:hover:bg-blue-500 dark:disabled:bg-blue-800/60"'

if new in s:
    print("PATCH=PASS already-applied")
    raise SystemExit(0)

if old not in s:
    raise SystemExit("PATCH=FAIL target-button-class-not-found")

s = s.replace(old, new, 1)
p.write_text(s)
print("PATCH=PASS")
