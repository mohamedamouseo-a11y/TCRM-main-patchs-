#!/usr/bin/env python3
from __future__ import annotations

import shutil
import sys
from pathlib import Path

PATCH_ID = "TCRM-Smart-Search-Systemwide-Parity-Hardening-V1.1"
BACKUP_SUFFIX = ".smart-search-v1.1.bak"


def fail(message: str) -> None:
    raise SystemExit(f"[V1.1] ERROR: {message}")


def backup_once(path: Path) -> None:
    backup = path.with_name(path.name + BACKUP_SUFFIX)
    if not backup.exists():
        shutil.copy2(path, backup)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        fail(f"{label}: expected exactly 1 anchor, found {count}")
    return text.replace(old, new, 1)


def patch_file(path: Path, transform) -> bool:
    if not path.exists():
        fail(f"missing required file: {path}")
    original = path.read_text(encoding="utf-8")
    updated = transform(original)
    if updated == original:
        print(f"[V1.1] unchanged: {path}")
        return False
    backup_once(path)
    path.write_text(updated, encoding="utf-8")
    print(f"[V1.1] patched: {path}")
    return True


def patch_smart_search_bar(text: str) -> str:
    if "TCRM_SMART_SEARCH_SUGGESTION_RANKING_V1_1" in text:
        return text
    if "SMART_SEARCH_SYSTEMWIDE_V1" not in text:
        fail("SmartSearchBar V1 marker missing; apply V1 before V1.1")

    text = replace_once(
        text,
        'import { normalizeSearchText } from "@shared/searchNormalization";\n',
        'import { normalizeSearchText } from "@shared/searchNormalization";\n'
        'import { rankSearchSuggestions } from "@shared/searchSuggestions";\n',
        "SmartSearchBar import",
    )

    old = '''  const normalizedSuggestions = useMemo(() => {
    const seen = new Set<string>();
    const out: Array<{ id: string | number; label: string; secondary?: string | null }> = [];
    for (const item of suggestions) {
      const suggestion =
        typeof item === "string"
          ? { id: item, label: item, secondary: null }
          : {
              id: item.id,
              label: String(item.label ?? "").trim(),
              secondary: item.secondary ?? null,
            };
      if (!suggestion.label) continue;
      const key = normalizeSearchText(suggestion.label);
      if (!key || seen.has(key)) continue;
      seen.add(key);
      out.push(suggestion);
      if (out.length >= 6) break;
    }
    return out;
  }, [suggestions]);

  const visibleSuggestions = suggestionsReady ? normalizedSuggestions : [];
'''
    new = '''  const normalizedSuggestions = useMemo(() => {
    const seen = new Set<string>();
    const out: Array<{ id: string | number; label: string; secondary?: string | null }> = [];
    for (const item of suggestions) {
      const suggestion =
        typeof item === "string"
          ? { id: item, label: item, secondary: null }
          : {
              id: item.id,
              label: String(item.label ?? "").trim(),
              secondary: item.secondary ?? null,
            };
      if (!suggestion.label) continue;
      const key = normalizeSearchText(suggestion.label);
      if (!key || seen.has(key)) continue;
      seen.add(key);
      out.push(suggestion);
    }
    return out;
  }, [suggestions]);

  // TCRM_SMART_SEARCH_SUGGESTION_RANKING_V1_1:
  // Filter + rank against the actual query before limiting to six suggestions.
  const visibleSuggestions = useMemo(() => {
    if (!suggestionsReady) return [];
    return rankSearchSuggestions(
      value,
      normalizedSuggestions.map(suggestion => ({
        value: suggestion,
        fields: [suggestion.label, suggestion.secondary],
      })),
      6,
    );
  }, [normalizedSuggestions, suggestionsReady, value]);
'''
    return replace_once(text, old, new, "SmartSearchBar suggestion ranking")


def patch_global_search(text: str) -> str:
    if "TCRM_SMART_SEARCH_PARTIAL_RESULTS_V1_1" in text:
        return text
    if "TCRM_SMART_SEARCH_GLOBAL_RACE_GUARD_V1" not in text:
        fail("GlobalSearch V1 race-guard marker missing; apply V1 before V1.1")

    text = replace_once(
        text,
        ") : searchError ? (\n",
        ") : searchError && total === 0 ? (\n",
        "GlobalSearch hard-error condition",
    )
    text = replace_once(
        text,
        "            <div className='py-2'>\n",
        "            <div className='py-2'>\n"
        "              {/* TCRM_SMART_SEARCH_PARTIAL_RESULTS_V1_1: keep valid sections visible if another provider fails. */}\n"
        "              {searchError && total > 0 ? (\n"
        "                <div className='mx-4 mb-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800 dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-amber-300'>\n"
        "                  {isRTL ? 'تم عرض النتائج المتاحة، وتعذر تحميل بعض أقسام البحث.' : 'Showing available results; some search sections could not be loaded.'}\n"
        "                </div>\n"
        "              ) : null}\n",
        "GlobalSearch partial-results banner",
    )
    return text


def patch_admin_settings(text: str) -> str:
    if "TCRM_SETTINGS_SUGGESTION_NAV_V1_1" in text:
        return text
    if "TCRM_SETTINGS_SMART_UI_V1" not in text:
        fail("AdminSettings V1 Smart UI marker missing; apply V1 before V1.1")

    old = '''                      onMouseDown={(e) => e.preventDefault()} onClick={() => { setActiveTab(s.id); setSettingsSearch(""); }}>
'''
    new = '''                      onMouseDown={(e) => e.preventDefault()}
                      onClick={() => {
                        // TCRM_SETTINGS_SUGGESTION_NAV_V1_1: suggestion selection must escape the current category scope.
                        setActiveSettingsCategory("all");
                        handleSettingsTabChange(String(s.id));
                        setSettingsSearch("");
                      }}>
'''
    return replace_once(text, old, new, "AdminSettings suggestion navigation")


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TCRM").resolve()
    print(f"[V1.1] applying {PATCH_ID} to {root}")

    targets = [
        (root / "client/src/components/search/SmartSearchBar.tsx", patch_smart_search_bar),
        (root / "client/src/components/GlobalSearch.tsx", patch_global_search),
        (root / "client/src/pages/AdminSettings.tsx", patch_admin_settings),
    ]

    changed = 0
    for path, transform in targets:
        changed += int(patch_file(path, transform))

    print(f"[V1.1] complete. changed_files={changed}")
    print("[V1.1] No DB/schema/permission/TOS/Evolution/WhatsApp-send changes are part of this patch.")
    print("[V1.1] Next: python3 VERIFY_PATCH.py <TCRM_ROOT>, then normal build/typecheck/tests.")


if __name__ == "__main__":
    main()
