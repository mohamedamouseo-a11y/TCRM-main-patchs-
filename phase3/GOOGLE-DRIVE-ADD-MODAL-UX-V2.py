from pathlib import Path
import re

p = Path("client/src/components/GoogleDriveStoragePoolTab.tsx")
s = p.read_text()

if 'data-add-drive-ux="v2"' in s:
    print("PATCH=PASS already-applied")
    raise SystemExit(0)

# 1) Never default/fallback to 999 in the UI.
s = s.replace('const [newPriority, setNewPriority] = useState("999");',
              'const [newPriority, setNewPriority] = useState("1");')

# 2) Derive the next real priority from the current ordered accounts.
accounts_anchor = 'const accounts:any[] = (pool.data as any)?.accounts || [];'
if accounts_anchor not in s:
    raise SystemExit("PATCH=FAIL accounts-anchor")

insert = '''const accounts:any[] = (pool.data as any)?.accounts || [];
  const nextPriority = useMemo(() => {
    const maxPriority = accounts.reduce((max, account) => Math.max(max, Number(account?.priority || 0)), 0);
    return Math.min(9999, Math.max(1, maxPriority + 1));
  }, [accounts]);
  const openAddDrive = () => {
    setNewName("");
    setNewPriority(String(nextPriority));
    setAddOpen(true);
  };
  useEffect(() => {
    if (addOpen) setNewPriority(String(nextPriority));
  }, [addOpen, nextPriority]);'''

s = s.replace(accounts_anchor, insert, 1)

# 3) Use the computed priority whenever the dialog is opened.
s = s.replace('onClick={()=>setAddOpen(true)}', 'onClick={openAddDrive}')
s = s.replace('onClick={() => setAddOpen(true)}', 'onClick={openAddDrive}')

# 4) Remove stale 999 fallback from submit paths.
s = s.replace('Math.max(1,Number(newPriority)||999)', 'Math.max(1,Number(newPriority)||nextPriority)')
s = s.replace('Math.max(1, Number(newPriority) || 999)', 'Math.max(1, Number(newPriority) || nextPriority)')

# 5) Make the primary Add button visibly primary even while disabled.
# Handles compact and polished versions by matching a Button that references add.isPending.
button_pat = re.compile(r'<Button(?P<attrs>[^>]*add\.isPending[^>]*)>(?P<body>.*?)</Button>', re.S)
m = button_pat.search(s)
if not m:
    raise SystemExit("PATCH=FAIL add-button")
attrs = m.group('attrs')
body = m.group('body')
if 'data-add-drive-ux=' not in attrs:
    # Remove existing className so we can set one deterministic style.
    attrs = re.sub(r'\sclassName="[^"]*"', '', attrs)
    attrs = re.sub(r"\sclassName=\{[^}]*\}", '', attrs)
    attrs += ' data-add-drive-ux="v2" className="min-w-[128px] bg-primary text-primary-foreground shadow-sm hover:bg-primary/90 disabled:bg-primary/55 disabled:text-primary-foreground disabled:opacity-100"'
    replacement = '<Button' + attrs + '>' + body + '</Button>'
    s = s[:m.start()] + replacement + s[m.end():]

# 6) Give Cancel a stable width when present.
cancel_patterns = [
    r'<Button([^>]*)>(\{isRTL\s*\?\s*"إلغاء"\s*:\s*"Cancel"\})</Button>',
    r'<Button([^>]*)>Cancel</Button>',
]
for pat in cancel_patterns:
    mm = re.search(pat, s, re.S)
    if mm:
        whole = mm.group(0)
        if 'min-w-[96px]' not in whole:
            if 'className=' in whole:
                whole2 = re.sub(r'className="([^"]*)"', lambda x: f'className="{x.group(1)} min-w-[96px]"', whole, count=1)
            else:
                whole2 = whole.replace('<Button', '<Button className="min-w-[96px]"', 1)
            s = s[:mm.start()] + whole2 + s[mm.end():]
        break

p.write_text(s)
print("PATCH=PASS")
