#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('/var/www/TCRM-MAIN')
BASELINE = '935ed0510c3dfa66b1742ca314403937597058d1'
PATCH = 'TCRM-PERMISSIONS-CAMPAIGNS-API-V1'


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.exists():
        raise SystemExit(f'MISSING_FILE={rel}')
    return path.read_text(encoding='utf-8')


def write(rel: str, content: str):
    path = ROOT / rel
    before = path.read_text(encoding='utf-8')
    if before == content:
        print(f'SKIP={rel}:already_current')
        return
    path.write_text(content, encoding='utf-8')
    print(f'UPDATED={rel}')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'ANCHOR_ERROR={label}:expected=1:actual={count}')
    return text.replace(old, new, 1)


# ---------------------------------------------------------------------------
# 1) Add campaigns to the central protectedProcedure permission resolver.
#    Existing mediaBuyerOrAdminProcedure remains additive and untouched.
# ---------------------------------------------------------------------------
rel = 'server/security/corePermissionPolicy.ts'
text = read(rel)

if '// TCRM_PERMISSIONS_CAMPAIGNS_API_V1' not in text:
    text = replace_once(
        text,
        '// TCRM_PERMISSIONS_DASHBOARD_FILES_API_V1\n',
        '// TCRM_PERMISSIONS_DASHBOARD_FILES_API_V1\n// TCRM_PERMISSIONS_CAMPAIGNS_API_V1\n',
        'policy_marker',
    )

text = replace_once(
    text,
    '  | "meetings"\n  | "contracts";\n',
    '  | "meetings"\n  | "contracts"\n  | "campaigns";\n',
    'campaigns_union',
)

text = replace_once(
    text,
    '  "meetings",\n  "contracts",\n]);\n',
    '  "meetings",\n  "contracts",\n  "campaigns",\n]);\n',
    'campaigns_core_set',
)

write(rel, text)


# ---------------------------------------------------------------------------
# 2) Focused resolver tests for actual Campaigns router operation vocabulary.
# ---------------------------------------------------------------------------
rel = 'server/security/corePermissionPolicy.test.ts'
test = read(rel)

insert_before = '''  it("maps dashboard reads to dashboard.view without inventing dashboard writes", () => {\n'''
new_tests = '''  it("maps campaigns through the effective permission catalog", () => {\n    expect(resolveCorePermissionKey("campaigns.list", "query")).toBe("campaigns.view");\n    expect(resolveCorePermissionKey("campaigns.distinctNames", "query")).toBe("campaigns.view");\n    expect(resolveCorePermissionKey("campaigns.create", "mutation")).toBe("campaigns.create");\n    expect(resolveCorePermissionKey("campaigns.update", "mutation")).toBe("campaigns.edit");\n    expect(resolveCorePermissionKey("campaigns.delete", "mutation")).toBe("campaigns.delete");\n    expect(resolveCorePermissionKey("campaigns.export", "query")).toBe("campaigns.export");\n  });\n\n'''
if 'maps campaigns through the effective permission catalog' not in test:
    test = replace_once(test, insert_before, new_tests + insert_before, 'campaigns_policy_tests')

write(rel, test)


# ---------------------------------------------------------------------------
# 3) Static post-apply checks. No routers/frontend/data changes.
# ---------------------------------------------------------------------------
checks = {
    'server/security/corePermissionPolicy.ts': [
        'TCRM_PERMISSIONS_CAMPAIGNS_API_V1',
        '| "campaigns";',
        '"campaigns",',
    ],
    'server/security/corePermissionPolicy.test.ts': [
        'campaigns.list',
        'campaigns.distinctNames',
        'campaigns.create',
        'campaigns.update',
        'campaigns.delete',
        'campaigns.export',
    ],
}
for rel, needles in checks.items():
    data = read(rel)
    missing = [needle for needle in needles if needle not in data]
    if missing:
        raise SystemExit(f'POSTCHECK_FAILED={rel}:{missing}')

print(f'PATCH={PATCH}')
print(f'BASELINE={BASELINE}')
print('MODULES=campaigns')
print('CAMPAIGNS_PERMISSIONS=campaigns.view,campaigns.create,campaigns.edit,campaigns.delete,campaigns.export')
print('EXISTING_MEDIA_BUYER_ADMIN_GUARD_PRESERVED=YES')
print('ROUTERS_CHANGED=NO')
print('FRONTEND_CHANGED=NO')
print('DB_SCHEMA_CHANGED=NO')
print('DATA_CHANGED=NO')
print('FILES_CHANGED=server/security/corePermissionPolicy.ts,server/security/corePermissionPolicy.test.ts')
