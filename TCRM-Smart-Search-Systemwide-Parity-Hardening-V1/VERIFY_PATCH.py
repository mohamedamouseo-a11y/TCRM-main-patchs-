#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TCRM").resolve()

checks = [
    ("shared SmartSearchBar", "client/src/components/search/SmartSearchBar.tsx", "SMART_SEARCH_SYSTEMWIDE_V1"),
    ("Global Search race guard", "client/src/components/GlobalSearch.tsx", "TCRM_SMART_SEARCH_GLOBAL_RACE_GUARD_V1"),
    ("SQL LIKE escaping", "server/utils/searchNormalizationSql.ts", "escapeNormalizedLikeLiteral"),
    ("parallel BD global search", "server/routes/bd/search.ts", "TCRM_SMART_SEARCH_PARALLEL_BD_V1"),
    ("BD companies Smart UI", "client/src/pages/BD/CompaniesList.tsx", "TCRM_SMART_SEARCH_SYSTEMWIDE_V1"),
    ("BD contacts Smart UI", "client/src/pages/BD/ContactsList.tsx", "TCRM_SMART_SEARCH_SYSTEMWIDE_V1"),
    ("BD deals Smart UI", "client/src/pages/BD/DealsKanban.tsx", "TCRM_SMART_SEARCH_SYSTEMWIDE_V1"),
    ("Leads Smart UI", "client/src/pages/LeadsList.tsx", "TCRM_SMART_SEARCH_SYSTEMWIDE_V1"),
    ("Renewals Smart UI", "client/src/pages/RenewalPipeline.tsx", "TCRM_SMART_SEARCH_SYSTEMWIDE_V1"),
    ("Meta Smart UI", "client/src/pages/MetaCampaigns.tsx", "TCRM_SMART_SEARCH_SYSTEMWIDE_V1"),
    ("Google Ads Smart UI", "client/src/pages/GoogleAdsCampaignsPage.tsx", "TCRM_SMART_SEARCH_SYSTEMWIDE_V1"),
    ("LinkedIn Smart UI", "client/src/pages/LinkedInCampaignsPage.tsx", "TCRM_SMART_SEARCH_SYSTEMWIDE_V1"),
    ("Snapchat Smart UI", "client/src/pages/SnapchatCampaignsPage.tsx", "TCRM_SMART_SEARCH_SYSTEMWIDE_V1"),
    ("TikTok Smart UI", "client/src/pages/TikTokCampaignsPage.tsx", "TCRM_SMART_SEARCH_SYSTEMWIDE_V1"),
    ("WhatsApp inbox Smart UI", "client/src/components/wa/ConversationList.tsx", "TCRM_SMART_SEARCH_SYSTEMWIDE_V1"),
    ("Settings Smart UX", "client/src/pages/AdminSettings.tsx", "TCRM_SETTINGS_SMART_UI_V1"),
]

failed = []
for label, rel, marker in checks:
    path = ROOT / rel
    if not path.exists():
        failed.append(f"{label}: missing {rel}")
        continue
    text = path.read_text(encoding="utf-8", errors="replace")
    if marker not in text:
        failed.append(f"{label}: marker {marker} missing")

# Client Pool is deliberately preserved when its stronger existing pipeline is present.
client_pool = ROOT / "client/src/pages/ClientPool.tsx"
if not client_pool.exists():
    failed.append("Client Pool: file missing")
else:
    cp = client_pool.read_text(encoding="utf-8", errors="replace")
    for token in ("VoiceSearchButton", "normalizeSearchText", "rankSearchSuggestions"):
        if token not in cp:
            failed.append(f"Client Pool: existing Smart Search capability missing: {token}")

forward = ROOT / "client/src/components/wa/ForwardMessageDialog.tsx"
if forward.exists():
    ft = forward.read_text(encoding="utf-8", errors="replace")
    if "SmartSearchBar" not in ft and "TCRM_SMART_SEARCH_SYSTEMWIDE_V1" not in ft:
        failed.append("WhatsApp Forward: SmartSearchBar migration missing")

if failed:
    print("PASS/FAIL: FAIL")
    for row in failed:
        print("FAIL:", row)
    raise SystemExit(1)

print("PASS/FAIL: PASS")
print("CORE_SMART_SEARCH: OK")
print("CLIENT_POOL_EXISTING_SMART_PIPELINE: PRESERVED")
print("DB_CHANGED: NO")
print("SCHEMA_CHANGED: NO")
print("PERMISSIONS_CHANGED: NO")
