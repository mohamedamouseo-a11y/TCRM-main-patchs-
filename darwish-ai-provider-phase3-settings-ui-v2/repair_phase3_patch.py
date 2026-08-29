#!/usr/bin/env python3
import re
import sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit("usage: repair_phase3_patch.py INPUT OUTPUT")

src = Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()
sections = []
current = []

def is_diff(line: str) -> bool:
    return line.startswith("diff --git ") or line.startswith("+diff --git ")

for line in src:
    if is_diff(line) and current:
        sections.append(current)
        current = [line]
    else:
        current.append(line)
if current:
    sections.append(current)

if len(sections) < 5:
    raise SystemExit(f"expected at least 5 diff sections, found {len(sections)}")

cleaned = []
for section in sections:
    nested = section[0].startswith("+diff --git ")
    normalized = []
    for index, line in enumerate(section):
        if not nested:
            normalized.append(line)
            continue

        if index == 0 or line.startswith("+new file mode ") or line.startswith("+--- ") or line.startswith("++++ ") or line.startswith("+@@ "):
            normalized.append(line[1:])
            continue

        new_file = any(
            (item[1:] if item.startswith("+new file mode ") else item).startswith("new file mode ")
            for item in section[:6]
        )
        if new_file:
            normalized.append(line)
        else:
            normalized.append(line[1:] if line.startswith("+") else line)

    if any(line.startswith("new file mode ") for line in normalized):
        for i, line in enumerate(normalized):
            if re.match(r"^@@ -0,0 \+1,\d+ @@$", line):
                body_count = sum(1 for body_line in normalized[i + 1:] if body_line.startswith("+"))
                normalized[i] = f"@@ -0,0 +1,{body_count} @@"
                break

    cleaned.extend(normalized)

output = "\n".join(cleaned).rstrip() + "\n"
Path(sys.argv[2]).write_text(output, encoding="utf-8")
print(f"SECTIONS={len(sections)}")
print(f"OUTPUT_LINES={len(output.splitlines())}")
