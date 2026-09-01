#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


def read(path: Path) -> str:
    if not path.exists():
        raise SystemExit(f"[VERIFY V1.1] MISSING: {path}")
    return path.read_text(encoding="utf-8")


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise SystemExit(f"[VERIFY V1.1] FAIL: {label}")


def forbid(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise SystemExit(f"[VERIFY V1.1] FAIL: {label}")


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TCRM").resolve()

    smart = read(root / "client/src/components/search/SmartSearchBar.tsx")
    global_search = read(root / "client/src/components/GlobalSearch.tsx")
    settings = read(root / "client/src/pages/AdminSettings.tsx")

    require(smart, "TCRM_SMART_SEARCH_SUGGESTION_RANKING_V1_1", "SmartSearchBar ranking marker")
    require(smart, "rankSearchSuggestions(", "SmartSearchBar uses shared ranking")
    require(smart, "fields: [suggestion.label, suggestion.secondary]", "SmartSearchBar ranks label + secondary")
    forbid(smart, "if (out.length >= 6) break;", "SmartSearchBar must not cap before query ranking")

    require(global_search, "TCRM_SMART_SEARCH_PARTIAL_RESULTS_V1_1", "GlobalSearch partial-results marker")
    require(global_search, "searchError && total === 0", "GlobalSearch only hard-fails when no usable results")
    require(global_search, "searchError && total > 0", "GlobalSearch partial-results warning")
    require(global_search, "TCRM_SMART_SEARCH_GLOBAL_RACE_GUARD_V1", "GlobalSearch V1 race guard preserved")

    require(settings, "TCRM_SETTINGS_SUGGESTION_NAV_V1_1", "Settings suggestion navigation marker")
    require(settings, 'setActiveSettingsCategory("all");', "Settings clears category restriction")
    require(settings, "handleSettingsTabChange(String(s.id));", "Settings uses canonical tab navigation")
    require(settings, 'id="tcrm-settings-filter"', "Settings guarded input preserved")
    require(settings, "_searchUserTyped", "Settings autofill guard preserved")

    print("[VERIFY V1.1] PASS")
    print("[VERIFY V1.1] 3/3 target files verified.")
    print("[VERIFY V1.1] V1 race guard + Admin guarded input preserved.")


if __name__ == "__main__":
    main()
