#!/usr/bin/env python3
from pathlib import Path
import re
import sys

if len(sys.argv) != 3:
    raise SystemExit("usage: apply_phase3_v3.py REPO_DIR REPAIRED_PATCH")

repo = Path(sys.argv[1]).resolve()
patch_path = Path(sys.argv[2]).resolve()
patch = patch_path.read_text(encoding="utf-8")

NEW_FILES = {
    "server/services/darwish/aiProviders/darwishAiProviderSettingsService.ts",
    "server/routes/darwishAiProviders.ts",
    "client/src/components/DarwishAiProvidersSettingsTab.tsx",
}


def extract_new_file(section: str, path: str) -> str:
    if "new file mode 100644" not in section:
        raise RuntimeError(f"{path}: expected new file diff")
    lines = section.splitlines()
    out = []
    in_hunk = False
    for line in lines:
        if line.startswith("@@ "):
            in_hunk = True
            continue
        if not in_hunk:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            out.append(line[1:])
        elif line.startswith("\\ No newline at end of file"):
            continue
        elif line.startswith("diff --git "):
            break
        elif line.startswith(" "):
            out.append(line[1:])
        elif line.startswith("-"):
            raise RuntimeError(f"{path}: unexpected deletion in new file diff")
    if not out:
        raise RuntimeError(f"{path}: no file content extracted")
    return "\n".join(out) + "\n"

sections = re.split(r"(?=^diff --git )", patch, flags=re.M)
found = {}
for section in sections:
    m = re.match(r"diff --git a/(\S+) b/(\S+)", section)
    if not m:
        continue
    a_path, b_path = m.groups()
    if a_path == b_path and b_path in NEW_FILES:
        found[b_path] = extract_new_file(section, b_path)

missing = NEW_FILES.difference(found)
if missing:
    raise RuntimeError("missing new-file diffs: " + ", ".join(sorted(missing)))

for rel, content in found.items():
    target = repo / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        existing = target.read_text(encoding="utf-8")
        if existing != content:
            raise RuntimeError(f"{rel}: already exists with different content")
    else:
        target.write_text(content, encoding="utf-8")


def replace_once(rel: str, old: str, new: str, already_marker: str):
    target = repo / rel
    text = target.read_text(encoding="utf-8")
    if already_marker in text:
        return
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{rel}: expected anchor exactly once, found {count}: {old[:90]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")

# server/_core/index.ts — exact fcda02f anchors
replace_once(
    "server/_core/index.ts",
    'import { developerHubRouter } from "../routes/developerHub";\nimport { createTcrmDbBackupRouter } from "../routes/tcrmDatabaseBackup";',
    'import { developerHubRouter } from "../routes/developerHub";\nimport { createDarwishAiProvidersRouter } from "../routes/darwishAiProviders";\nimport { createTcrmDbBackupRouter } from "../routes/tcrmDatabaseBackup";',
    'from "../routes/darwishAiProviders"',
)
replace_once(
    "server/_core/index.ts",
    '  // Developer Hub routes (Super Admin only)\n  app.use("/api", developerHubRouter);\n  // Landing Page Public Lead Intake',
    '  // Developer Hub routes (Super Admin only)\n  app.use("/api", developerHubRouter);\n  // Darwish AI Provider Gateway settings (Admin / Developer only)\n  app.use("/api/darwish/ai-providers", createDarwishAiProvidersRouter());\n  // Landing Page Public Lead Intake',
    'app.use("/api/darwish/ai-providers", createDarwishAiProvidersRouter());',
)

# client/src/pages/AdminSettings.tsx — exact fcda02f anchors
replace_once(
    "client/src/pages/AdminSettings.tsx",
    'import CurrencySettingsTab from "@/components/CurrencySettingsTab";\nimport RakanSettingsTab from "@/components/RakanSettingsTab";\nimport TamaraSettingsTab from "@/components/TamaraSettingsTab";',
    'import CurrencySettingsTab from "@/components/CurrencySettingsTab";\nimport RakanSettingsTab from "@/components/RakanSettingsTab";\nimport DarwishAiProvidersSettingsTab from "@/components/DarwishAiProvidersSettingsTab";\nimport TamaraSettingsTab from "@/components/TamaraSettingsTab";',
    'from "@/components/DarwishAiProvidersSettingsTab"',
)
replace_once(
    "client/src/pages/AdminSettings.tsx",
    '    "rakan", "tamara", "paymob", "innocall", "currency", "demoSync", "developerHub", "dashboardAudit",',
    '    "rakan", "darwishAiProviders", "tamara", "paymob", "innocall", "currency", "demoSync", "developerHub", "dashboardAudit",',
    '"rakan", "darwishAiProviders",',
)
replace_once(
    "client/src/pages/AdminSettings.tsx",
    '        { value: "rakan", label: isRTL ? "راكان AI" : "Rakan AI", description: isRTL ? "مساعد النظام الذكي" : "AI assistant settings", icon: <Sparkles size={14} />, visible: true, badge: "AI" },\n        { value: "demoSync",',
    '        { value: "rakan", label: isRTL ? "راكان AI" : "Rakan AI", description: isRTL ? "مساعد النظام الذكي" : "AI assistant settings", icon: <Sparkles size={14} />, visible: true, badge: "AI" },\n        { value: "darwishAiProviders", label: isRTL ? "مزودو درويش AI" : "Darwish AI Providers", description: isRTL ? "المزودون والموديلات والتوجيه" : "Providers, models, and routing", icon: <Sparkles size={14} />, visible: isAdmin || isDeveloper, badge: "AI" },\n        { value: "demoSync",',
    '{ value: "darwishAiProviders",',
)
replace_once(
    "client/src/pages/AdminSettings.tsx",
    '      values: ["developerHub", "rakan"],',
    '      values: ["developerHub", "rakan", "darwishAiProviders"],',
    'values: ["developerHub", "rakan", "darwishAiProviders"]',
)
replace_once(
    "client/src/pages/AdminSettings.tsx",
    '          <TabsContent value="rakan" className="mt-4">\n            <RakanSettingsTab />\n          </TabsContent>\n\n          {/* ── Currency / Exchange Rates Tab ── */}',
    '          <TabsContent value="rakan" className="mt-4">\n            <RakanSettingsTab />\n          </TabsContent>\n\n          {(isAdmin || isDeveloper) && <TabsContent value="darwishAiProviders" className="mt-4">\n            <DarwishAiProvidersSettingsTab />\n          </TabsContent>}\n\n          {/* ── Currency / Exchange Rates Tab ── */}',
    '<TabsContent value="darwishAiProviders"',
)

print("PHASE3_V3=APPLIED")
print("NEW_FILES=3")
print("MODIFIED_FILES=2")
for rel in sorted(NEW_FILES):
    print(rel)
print("server/_core/index.ts")
print("client/src/pages/AdminSettings.tsx")
