from pathlib import Path
import re

p = Path("client/src/components/GoogleDriveStoragePoolTab.tsx")
s = p.read_text()

MARKER = 'data-add-drive-modal-design="v4"'
if MARKER not in s:
    raise SystemExit("PATCH=FAIL modal-v4-not-found")

if 'data-add-drive-native-cta="v1"' in s:
    print("PATCH=PASS already-applied")
    raise SystemExit(0)

start = s.find(MARKER)
end = s.find('<Dialog open={Boolean(configId)}', start)
if start < 0 or end < 0:
    raise SystemExit("PATCH=FAIL modal-boundary")

block = s[start:end]

pat = re.compile(
    r'<Button\s+type="submit"(?P<attrs>.*?)>\s*(?P<body>\{add\.isPending.*?\})\s*</Button>',
    re.S
)
m = pat.search(block)
if not m:
    raise SystemExit("PATCH=FAIL submit-button-not-found")

native = r'''<button
              data-add-drive-native-cta="v1"
              type="submit"
              disabled={newName.trim().length < 2 || add.isPending}
              className="h-11 min-w-[132px] rounded-xl px-6 font-semibold shadow-md transition-colors disabled:cursor-not-allowed"
              style={{
                backgroundColor: newName.trim().length < 2 || add.isPending ? "#60a5fa" : "#2563eb",
                color: "#ffffff",
                opacity: 1,
              }}
            >
              {add.isPending
                ? (isRTL ? "جارٍ الإضافة..." : "Adding...")
                : (isRTL ? "إضافة الحساب" : "Add Drive")}
            </button>'''

block = block[:m.start()] + native + block[m.end():]
s = s[:start] + block + s[end:]
p.write_text(s)
print("PATCH=PASS")
