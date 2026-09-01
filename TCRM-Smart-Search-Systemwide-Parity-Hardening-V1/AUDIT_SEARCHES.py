#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys
from collections import defaultdict

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TCRM").resolve()
CLIENT = ROOT / "client" / "src"
SERVER = ROOT / "server"
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "/tmp/TCRM_SMART_SEARCH_SYSTEMWIDE_AUDIT.md")

if not CLIENT.exists():
    raise SystemExit(f"FAIL: client/src not found under {ROOT}")

SOURCE_SUFFIXES = {".ts", ".tsx", ".js", ".jsx"}
SKIP_PARTS = {"node_modules", "dist", "build", ".git"}

UI_PATTERNS = [
    ("TYPE_SEARCH", re.compile(r'type\s*=\s*["\']search["\']', re.I)),
    ("ROLE_SEARCH", re.compile(r'role\s*=\s*["\'](?:search|searchbox|combobox)["\']', re.I)),
    ("PLACEHOLDER_EN", re.compile(r'placeholder[^\n]{0,200}(?:search|find|lookup)', re.I)),
    ("PLACEHOLDER_AR", re.compile(r'placeholder[^\n]{0,200}(?:ابحث|بحث|اعثر)', re.I)),
    ("SEARCH_COMPONENT", re.compile(r'<(?:SmartSearchBar|CommandInput|SearchInput|GlobalSearch)\b', re.I)),
]

BACKEND_PATTERNS = [
    ("SEARCH_INPUT", re.compile(r'\bsearch\s*:\s*z\.', re.I)),
    ("SEARCH_FILTER", re.compile(r'filters?\.search|input\.search|req\.query\.q', re.I)),
    ("LIKE", re.compile(r'\b(?:like|ilike)\s*\(', re.I)),
    ("SMART_CORE", re.compile(r'normalizedContains|fuzzyContains|runExactFirstServerSearch|matchesSystemSmartSearch|normalizeSearchText', re.I)),
]

def iter_sources(base: Path):
    if not base.exists():
        return
    for path in base.rglob("*"):
        if not path.is_file() or path.suffix not in SOURCE_SUFFIXES:
            continue
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.name.endswith((".test.ts", ".test.tsx", ".spec.ts", ".spec.tsx")):
            continue
        yield path

def compact(line: str, width: int = 220) -> str:
    value = re.sub(r"\s+", " ", line.strip())
    return value[:width] + ("…" if len(value) > width else "")

def ui_capabilities(text: str) -> list[str]:
    caps = []
    if "SmartSearchBar" in text:
        caps.append("SHARED_UI")
    if "VoiceSearchButton" in text or "useSmartSearchVoice" in text:
        caps.append("VOICE")
    if "rankSearchSuggestions" in text or "suggestions={" in text or "autocompleteSuggestions" in text:
        caps.append("SUGGESTIONS")
    if "matchesSystemSmartSearch" in text or "normalizeSearchText" in text:
        caps.append("NORMALIZED_LOGIC")
    if "rankSearchCandidates" in text or "searchLearning" in text:
        caps.append("RANKING_LEARNING")
    if "TCRM_SMART_SEARCH_SYSTEMWIDE_V1" in text or "SMART_SEARCH_SYSTEMWIDE_V1" in text:
        caps.append("SYSTEMWIDE_V1")
    return caps

ui_hits = defaultdict(list)
ui_meta = {}
for path in iter_sources(CLIENT):
    text = path.read_text(encoding="utf-8", errors="replace")
    rel = str(path.relative_to(ROOT))
    hits = []
    for idx, line in enumerate(text.splitlines(), 1):
        kinds = [name for name, pattern in UI_PATTERNS if pattern.search(line)]
        if kinds:
            hits.append((idx, ",".join(kinds), compact(line)))
    if hits:
        ui_hits[rel] = hits
        ui_meta[rel] = ui_capabilities(text)

server_hits = defaultdict(list)
for path in iter_sources(SERVER):
    text = path.read_text(encoding="utf-8", errors="replace")
    rel = str(path.relative_to(ROOT))
    for idx, line in enumerate(text.splitlines(), 1):
        kinds = [name for name, pattern in BACKEND_PATTERNS if pattern.search(line)]
        if kinds:
            server_hits[rel].append((idx, ",".join(kinds), compact(line)))

all_ui = sorted(ui_hits)
shared_ui = [p for p in all_ui if "SHARED_UI" in ui_meta.get(p, [])]
voice_ui = [p for p in all_ui if "VOICE" in ui_meta.get(p, [])]
logic_only = [
    p for p in all_ui
    if "NORMALIZED_LOGIC" in ui_meta.get(p, [])
    and "SHARED_UI" not in ui_meta.get(p, [])
    and "VOICE" not in ui_meta.get(p, [])
]
plain_pending = [
    p for p in all_ui
    if "SHARED_UI" not in ui_meta.get(p, [])
    and "VOICE" not in ui_meta.get(p, [])
    and "NORMALIZED_LOGIC" not in ui_meta.get(p, [])
]

lines = [
    "# TCRM Smart Search — System-wide Audit",
    "",
    f"- Target: `{ROOT}`",
    f"- UI files with user-facing search signals: **{len(all_ui)}**",
    f"- Shared SmartSearchBar files: **{len(shared_ui)}**",
    f"- Voice-enabled search files: **{len(voice_ui)}**",
    f"- Smart logic but legacy/plain UI: **{len(logic_only)}**",
    f"- Plain/pending search files: **{len(plain_pending)}**",
    f"- Server files with search-related signals: **{len(server_hits)}**",
    "",
    "## Rule",
    "",
    "A search is not considered fully migrated just because its matching logic is fuzzy/normalized.",
    "For a normal user-facing text search field, Systemwide V1 expects the shared SmartSearchBar or an explicitly documented exception where replacing the native input would break a security/accessibility/autofill contract.",
    "Server-data searches must retain the original permission scope, filters, pagination, and API source.",
    "",
    "## UI Inventory",
    "",
]
for rel in all_ui:
    caps = ui_meta.get(rel, [])
    status = (
        "SMART_UI" if "SHARED_UI" in caps
        else "EXPLICIT_SMART_UI" if "VOICE" in caps and "SUGGESTIONS" in caps
        else "LOGIC_ONLY" if "NORMALIZED_LOGIC" in caps
        else "PENDING"
    )
    lines.append(f"### `{rel}` — `{status}` — capabilities: `{','.join(caps) or 'NONE'}`")
    for idx, kind, snippet in ui_hits[rel]:
        safe = snippet.replace("`", "'")
        lines.append(f"- L{idx} `{kind}` — `{safe}`")
    lines.append("")

lines.extend(["## Server Inventory", ""])
for rel in sorted(server_hits):
    lines.append(f"### `{rel}`")
    for idx, kind, snippet in server_hits[rel]:
        safe = snippet.replace("`", "'")
        lines.append(f"- L{idx} `{kind}` — `{safe}`")
    lines.append("")

lines.extend([
    "## Exceptions / review notes",
    "",
    "- Credential/autofill-sensitive inputs (for example a specially guarded Settings search control) must be reviewed before component replacement.",
    "- Structured IDs, email, phone, account IDs, cursor tokens, and numeric-only queries must not gain unsafe fuzzy semantics merely because the UI is migrated.",
    "- Client Pool may remain an explicit Smart UI when it already has normalization, ranked suggestions, and VoiceSearchButton wired to the same search state.",
    "",
    "## Safety",
    "",
    "This audit makes no source, database, schema, migration, PM2, WhatsApp/Evolution, or TOS changes.",
])

OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("PASS/FAIL: PASS")
print(f"AUDIT_REPORT: {OUT}")
print(f"UI_SEARCH_FILES: {len(all_ui)}")
print(f"SHARED_SMART_UI_FILES: {len(shared_ui)}")
print(f"VOICE_SEARCH_FILES: {len(voice_ui)}")
print(f"LOGIC_ONLY_FILES: {len(logic_only)}")
print(f"PENDING_FILES: {len(plain_pending)}")
print(f"SERVER_SEARCH_FILES: {len(server_hits)}")
print("SOURCE_CHANGED: NO")
print("DB_CHANGED: NO")
