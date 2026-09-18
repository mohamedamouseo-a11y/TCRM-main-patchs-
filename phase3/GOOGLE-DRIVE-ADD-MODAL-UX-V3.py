from pathlib import Path
import re

p = Path("client/src/components/GoogleDriveStoragePoolTab.tsx")
s = p.read_text()

if 'data-add-drive-modal-v3="true"' in s:
    print("PATCH=PASS already-applied")
    raise SystemExit(0)

start = s.find('<Dialog open={addOpen}')
if start < 0:
    raise SystemExit("PATCH=FAIL add-dialog-not-found")

# Find the end of this Dialog block by locating the next config dialog.
next_dialog = s.find('<Dialog open={Boolean(configId)}', start)
if next_dialog < 0:
    raise SystemExit("PATCH=FAIL next-dialog-not-found")

block = s[start:next_dialog]

# Normalize DialogContent to a cleaner card with explicit footer area.
block = re.sub(
    r'<DialogContent(?:\s+className="[^"]*")?>',
    '<DialogContent data-add-drive-modal-v3="true" className="overflow-hidden p-0 sm:max-w-[540px]">',
    block,
    count=1,
)

# Improve header spacing if not already structured.
block = block.replace(
    '<DialogHeader>',
    '<DialogHeader className="border-b px-6 pb-4 pt-5 text-start">',
    1,
)

# Add a subtle body wrapper if the current form is a single space-y container.
block = block.replace(
    '<div className="space-y-4">',
    '<div className="space-y-5 px-6 py-5">',
    1,
)
block = block.replace(
    '<div className="space-y-5">',
    '<div className="space-y-5 px-6 py-5">',
    1,
)

# Ensure priority helper does not look detached.
block = block.replace(
    'Lower number = higher priority',
    'Lower number = higher priority',
)

# Replace the existing action row with a proper footer.
# Matches polished variants with Cancel/Add Drive buttons and the compact legacy version.
footer_re = re.compile(
    r'<div[^>]*className="[^"]*(?:flex|grid)[^"]*"[^>]*>\s*'
    r'(?P<body>(?:(?!</div>).)*?(?:Cancel|إلغاء).*?(?:Add Drive|إضافة|Adding|جار).*?)'
    r'</div>',
    re.S
)

m = footer_re.search(block)
if m:
    footer = m.group(0)

    # Extract any existing cancel button.
    cancel_m = re.search(r'<Button(?P<a>[^>]*)>(?P<b>.*?(?:Cancel|إلغاء).*?)</Button>', footer, re.S)
    add_m = re.search(r'<Button(?P<a>[^>]*)>(?P<b>.*?(?:Add Drive|إضافة|Adding|جار).*?)</Button>', footer, re.S)

    if cancel_m and add_m:
        cancel_btn = cancel_m.group(0)
        add_btn = add_m.group(0)

        # Force consistent visible styling.
        cancel_btn = re.sub(r'\sclassName="[^"]*"', '', cancel_btn, count=1)
        cancel_btn = cancel_btn.replace(
            '<Button',
            '<Button variant="outline" className="min-w-[96px]"',
            1
        ) if 'variant=' not in cancel_btn else cancel_btn.replace(
            '<Button',
            '<Button className="min-w-[96px]"',
            1
        )

        add_btn = re.sub(r'\sclassName="[^"]*"', '', add_btn, count=1)
        add_btn = add_btn.replace(
            '<Button',
            '<Button className="min-w-[132px] bg-primary text-primary-foreground shadow-sm hover:bg-primary/90 disabled:bg-primary/45 disabled:text-primary-foreground disabled:opacity-100"',
            1
        )

        new_footer = (
            '<div className="flex items-center justify-end gap-2 border-t bg-muted/20 px-6 py-4">'
            + cancel_btn + add_btn + '</div>'
        )
        block = block[:m.start()] + new_footer + block[m.end():]
else:
    # Legacy one-button form: replace the final Add button and add Cancel explicitly.
    add_btn_re = re.compile(r'<Button(?P<a>[^>]*)>(?P<b>.*?(?:Add Drive|Add|إضافة).*?)</Button>', re.S)
    am = add_btn_re.search(block)
    if not am:
        raise SystemExit("PATCH=FAIL action-buttons-not-found")
    add_btn = am.group(0)
    add_btn = re.sub(r'\sclassName="[^"]*"', '', add_btn, count=1)
    add_btn = add_btn.replace(
        '<Button',
        '<Button className="min-w-[132px] bg-primary text-primary-foreground shadow-sm hover:bg-primary/90 disabled:bg-primary/45 disabled:text-primary-foreground disabled:opacity-100"',
        1
    )
    footer = (
        '<div className="flex items-center justify-end gap-2 border-t bg-muted/20 px-6 py-4">'
        '<Button type="button" variant="outline" className="min-w-[96px]" onClick={()=>setAddOpen(false)}>'
        '{isRTL?"إلغاء":"Cancel"}</Button>'
        + add_btn +
        '</div>'
    )
    block = block[:am.start()] + footer + block[am.end():]

# Make sure the body itself doesn't accidentally contain old action row whitespace.
block = block.replace('className="text-primary-foreground shadow-sm hover:bg-primary/90 disabled:bg-primary/55 disabled:text-primary-foreground disabled:opacity-100"',
                      'className="min-w-[132px] bg-primary text-primary-foreground shadow-sm hover:bg-primary/90 disabled:bg-primary/45 disabled:text-primary-foreground disabled:opacity-100"')

s = s[:start] + block + s[next_dialog:]
p.write_text(s)
print("PATCH=PASS")
