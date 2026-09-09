#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path.cwd()
TSX = ROOT / "client/src/pages/LeadsList.tsx"

if not TSX.exists():
    raise SystemExit("ERROR=client/src/pages/LeadsList.tsx not found; run from EXISTING LIVE TCRM project root")

text = TSX.read_text(encoding="utf-8")
original = text

required = [
    'import "../leads-premium-v1-11.css";',
    'tcrm-leads-premium',
]
missing = [x for x in required if x not in text]
if missing:
    raise SystemExit("ERROR=LEADS_V111_REQUIRED_MISSING:" + ",".join(missing))

phrase = 'SMART_SEARCH_AUDIT_EXEMPT: specialized campaign selector, not the primary free-text entity search'

# Remove ONLY the exact Campaign audit marker from the ACTIVE LeadsList.tsx source.
# Accept JSX comment, raw block comment, or quoted string variants in case a previous transform altered syntax.
patterns = [
    re.compile(r'\{\s*/\*\s*' + re.escape(phrase) + r'\s*\*/\s*\}', re.S),
    re.compile(r'/\*\s*' + re.escape(phrase) + r'\s*\*/', re.S),
    re.compile(r'(["\'])/\*\s*' + re.escape(phrase) + r'\s*\*/\1', re.S),
]

removed = 0
for pat in patterns:
    text, n = pat.subn('', text)
    removed += n

# Also handle whitespace-normalized variants of the same exact marker semantics.
normalized = re.compile(
    r'\{?\s*/\*\s*SMART_SEARCH_AUDIT_EXEMPT\s*:\s*specialized\s+campaign\s+selector\s*,\s*not\s+the\s+primary\s+free-text\s+entity\s+search\s*\*/\s*\}?',
    re.I | re.S,
)
text, n = normalized.subn('', text)
removed += n

if phrase in text:
    raise SystemExit("ERROR=CAMPAIGN_AUDIT_MARKER_STILL_PRESENT_IN_ACTIVE_SOURCE")

if removed == 0:
    raise SystemExit("ERROR=CAMPAIGN_AUDIT_MARKER_NOT_FOUND_IN_ACTIVE_SOURCE")

TSX.write_text(text, encoding="utf-8")

print("PATCH=YES")
print("V111_BASE=YES")
print("CAMPAIGN_MARKER_REMOVED=YES")
print("CAMPAIGN_MARKER_REMOVAL_COUNT=" + str(removed))
print("ACTIVE_SOURCE_CLEAR=YES")
print("FUNCTIONALITY_CHANGED=NO")
print("FILES_CHANGED=client/src/pages/LeadsList.tsx")
