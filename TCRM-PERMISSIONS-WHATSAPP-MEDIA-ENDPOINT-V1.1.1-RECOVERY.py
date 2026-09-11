#!/usr/bin/env python3
from pathlib import Path
import subprocess
import hashlib
import os
import tempfile

ROOT = Path('/var/www/TCRM-MAIN')
BASELINE = '3a5434a4049c8c5582bfdded91504905f599999a'
SOURCE_COMMIT = '90b5af4766cf4115bca861a2a5fcb02396c7d726'
VERSION = 'V1.1.1'
WORKFLOW_ID = 'TCRM-PERMISSIONS-WHATSAPP-MEDIA-ENDPOINT-V1.1.1-RECOVERY'

FILES = [
    'TSHEETS_NEXUS_GRID_V1_7R2_7R6R6R7R1_REBASED_EXACT_CURRENT_HEAD.patch',
    'TSHEETS_NEXUS_GRID_V1_7R2_7R6R6R7_REBASED_CURRENT_HEAD.patch',
    'TSHEETS_NEXUS_GRID_V1_7R2_7R6R6R7_REBASED_LATEST_CURRENT_SOURCE.patch',
    'TSHEETS_NEXUS_GRID_V1_7R2_7R6_R6R1.patch',
]


def git(*args: str) -> bytes:
    return subprocess.check_output(['git', *args], cwd=ROOT, stderr=subprocess.STDOUT)


def fail(message: str) -> None:
    raise SystemExit(message)


head = git('rev-parse', 'HEAD').decode().strip()
if head != BASELINE:
    fail(f'BASELINE_MISMATCH expected={BASELINE} actual={head}')

dirty_before = [line for line in git('diff', '--name-only').decode().splitlines() if line.strip()]
if dirty_before:
    fail('WORKTREE_NOT_CLEAN=' + ','.join(dirty_before))

for rel in FILES:
    target = ROOT / rel
    if target.exists():
        fail(f'UNEXPECTED_EXISTING_FILE={rel}')
    try:
        source = git('show', f'{SOURCE_COMMIT}:{rel}')
    except subprocess.CalledProcessError as exc:
        fail(f'SOURCE_READ_FAILED={rel}:{exc.output.decode(errors="replace").strip()}')
    if not source:
        fail(f'EMPTY_SOURCE={rel}')

    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f'.{target.name}.', dir=str(target.parent))
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(source)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, target)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)

    restored = target.read_bytes()
    if restored != source:
        fail(f'RESTORE_VERIFY_FAILED={rel}')
    print(f'RESTORED={rel}:sha256={hashlib.sha256(restored).hexdigest()}')

changed = [line for line in git('diff', '--name-only').decode().splitlines() if line.strip()]
if set(changed) != set(FILES) or len(changed) != len(FILES):
    fail('UNEXPECTED_CHANGED_FILES=' + ','.join(changed))

for rel in FILES:
    source = git('show', f'{SOURCE_COMMIT}:{rel}')
    restored = (ROOT / rel).read_bytes()
    if restored != source:
        fail(f'FINAL_CONTENT_MISMATCH={rel}')

print(f'VERSION={VERSION}')
print(f'WORKFLOW_ID={WORKFLOW_ID}')
print(f'BASELINE={BASELINE}')
print(f'SOURCE_COMMIT={SOURCE_COMMIT}')
print('TRACKED_PATCH_ARTIFACTS_RESTORED=YES')
print('RUNTIME_SOURCE_CHANGED=NO')
print('FILES_CHANGED=' + ','.join(FILES))
print('ERROR=NONE')
