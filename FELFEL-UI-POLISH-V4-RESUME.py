#!/usr/bin/env python3
# FELFEL_UI_POLISH_V4_RESUME
from pathlib import Path
import subprocess

ROOT = Path('/var/www/TCRM-MAIN')
EXPECTED = '7019ea102eddda2cbf3f40d3a35111058b7c56f0'

if not ROOT.exists():
    raise SystemExit('TCRM root not found')

head = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
if head != EXPECTED:
    raise SystemExit(f'BASE_MISMATCH expected={EXPECTED[:8]} actual={head[:8]}')


def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def write(rel, text):
    (ROOT / rel).write_text(text, encoding='utf-8')


def replace_once_if_needed(text, old, new, label):
    if new in text:
        return text, False
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected 1 anchor, found {count}')
    return text.replace(old, new, 1), True

# The first V4 run may already have created the workspace component before exiting.
workspace_rel = 'client/src/components/felfel/FelfelMeetingWorkspaceCard.tsx'
workspace_path = ROOT / workspace_rel
if not workspace_path.exists():
    raise RuntimeError('workspace component missing; rerun the original V4 patch first')
workspace_text = workspace_path.read_text(encoding='utf-8')
if 'FELFEL_UI_POLISH_V4_COMPACT_WORKSPACE' not in workspace_text:
    raise RuntimeError('workspace component exists without V4 marker')

changed = []

# Resume Operational Dashboard changes idempotently.
rel = 'client/src/components/felfel/FelfelOperationalDashboard.tsx'
text = read(rel)
original = text

text, _ = replace_once_if_needed(
    text,
    'import FelfelMeetingIntelligencePanel from "@/components/felfel/FelfelMeetingIntelligencePanel";\n',
    'import FelfelMeetingIntelligencePanel from "@/components/felfel/FelfelMeetingIntelligencePanel";\nimport FelfelMeetingWorkspaceCard from "@/components/felfel/FelfelMeetingWorkspaceCard";\n',
    'dashboard workspace import',
)

if 'data-felfel-operational-dashboard="ui-polish-v4"' not in text:
    text = text.replace('data-felfel-operational-dashboard="phase1-v1"', 'data-felfel-operational-dashboard="ui-polish-v4"', 1)

if 'className="grid gap-2 md:grid-cols-2 xl:grid-cols-8"' not in text:
    text = text.replace('className="grid gap-3 lg:grid-cols-4 2xl:grid-cols-7"', 'className="grid gap-2 md:grid-cols-2 xl:grid-cols-8"', 1)

if 'className="relative md:col-span-2 xl:col-span-2"' not in text:
    text = text.replace('className="relative lg:col-span-2 2xl:col-span-2"', 'className="relative md:col-span-2 xl:col-span-2"', 1)

if '<div className="grid grid-cols-2 gap-2 md:col-span-2 xl:col-span-2"><Input type="date" value={fromDate}' not in text:
    text = text.replace(
        '<div className="grid grid-cols-2 gap-2"><Input type="date" value={fromDate}',
        '<div className="grid grid-cols-2 gap-2 md:col-span-2 xl:col-span-2"><Input type="date" value={fromDate}',
        1,
    )

if '<FelfelMeetingWorkspaceCard' not in text:
    start_token = '            return (\n              <Card key={meeting.id} className="overflow-hidden rounded-[22px] border-border/70 shadow-sm">'
    end_token = '              </Card>\n            );'
    start = text.find(start_token)
    if start < 0:
        raise RuntimeError('dashboard meeting card start anchor not found')
    end = text.find(end_token, start)
    if end < 0:
        raise RuntimeError('dashboard meeting card end anchor not found')
    end += len(end_token)
    replacement = '''            return (\n              <FelfelMeetingWorkspaceCard\n                key={meeting.id}\n                meeting={meeting}\n                crmHref={crmHref}\n                isRTL={isRTL}\n                ar={ar}\n              />\n            );'''
    text = text[:start] + replacement + text[end:]

if text != original:
    write(rel, text)
    changed.append(rel)

# Resume Client Pool peer-tab no-wrap polish idempotently.
rel = 'client/src/pages/ClientPool.tsx'
text = read(rel)
original = text

if 'className="mb-4 flex gap-2 overflow-x-auto rounded-2xl border border-border bg-card p-1 [scrollbar-width:thin]"' not in text:
    old = '<div className="mb-4 flex flex-wrap gap-2 rounded-2xl border border-border bg-card p-1">'
    if text.count(old) != 1:
        raise RuntimeError(f'client pool tab row: expected 1 anchor, found {text.count(old)}')
    text = text.replace(old, '<div className="mb-4 flex gap-2 overflow-x-auto rounded-2xl border border-border bg-card p-1 [scrollbar-width:thin]">', 1)

old_button = '''                              size="sm"\n                              className="rounded-xl"\n                              onClick={e => {'''
new_button = '''                              size="sm"\n                              className="shrink-0 rounded-xl"\n                              onClick={e => {'''
if new_button not in text:
    if text.count(old_button) != 1:
        raise RuntimeError(f'client pool peer tab button: expected 1 anchor, found {text.count(old_button)}')
    text = text.replace(old_button, new_button, 1)

if text != original:
    write(rel, text)
    changed.append(rel)

print('FELFEL_UI_POLISH_V4_RESUME=OK')
print('WORKSPACE_COMPONENT=READY')
print('CHANGED=' + (','.join(changed) if changed else 'none'))
